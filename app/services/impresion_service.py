from escpos.printer import Usb
from flask import current_app
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
import time
import textwrap
from contextlib import suppress

ANCHO_80MM = 576
ANCHO_LINEA = 48

class PrinterFallbackToMock(Exception):
    """Señal interna para reiniciar impresión en modo MOCK"""
    pass

class ImpresionService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.printer = None
        self._initialized = True

    def _is_mock_mode(self):
        return current_app.config.get("PRINT_MODE", "usb") == "mock"

    def _init_printer(self):
        """Inicializa impresora según configuración"""

        if self._is_mock_mode():
            self.printer = MockPrinter()
            print("[IMPRESIÓN] Modo MOCK activo")
            return

        if self.printer:
            with suppress(Exception):
                self.printer.close()
            self.printer = None

        for attempt in range(3):
            try:
                self.printer = Usb(
                    0x0416,
                    0x5011,
                    timeout=0
                )
                
                self.printer.profile.profile_data['media']['width']['pixels'] = ANCHO_80MM
                self.printer.profile.profile_data['media']['width']['mm'] = 80
                
                print("[IMPRESIÓN] Impresora USB conectada")
                return
            except Exception as e:
                print(f"[IMPRESIÓN] Intento {attempt + 1} fallido: {e}")
                time.sleep(1)

        raise RuntimeError("No se pudo conectar con la impresora USB")

    def _close_printer(self):
        if self.printer:
            with suppress(Exception):
                self.printer.close()
            self.printer = None

    def _load_font(self, size, bold=False, italic=False):
        fonts = []

        if bold and italic:
            fonts = ["arialbi.ttf", "DejaVuSans-BoldOblique.ttf"]
        elif bold:
            fonts = ["arialbd.ttf", "DejaVuSans-Bold.ttf"]
        elif italic:
            fonts = ["ariali.ttf", "DejaVuSans-Oblique.ttf"]
        else:
            fonts = ["arial.ttf", "DejaVuSans.ttf"]

        for f in fonts:
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue

        return ImageFont.load_default()

    def _render_text_bitmap(self, lines, font, line_spacing=8):
        dummy = Image.new("L", (ANCHO_80MM, 10), 255)
        d = ImageDraw.Draw(dummy)

        total_height = 0
        for line in lines:
            bbox = d.textbbox((0, 0), line, font=font)
            total_height += (bbox[3] - bbox[1]) + line_spacing

        total_height += line_spacing * 2

        img = Image.new("L", (ANCHO_80MM, total_height), 255)
        draw = ImageDraw.Draw(img)

        y = line_spacing
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            x = (ANCHO_80MM - w) // 2
            draw.text((x, y), line, font=font, fill=0)
            y += h + line_spacing

        return img

    def _save_temp_file(self, chunk):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        chunk.save(tmp.name)
        tmp.close()
        return tmp.name

    def _save_and_print_chunk(self, p, chunk):
        tmp_name = self._save_temp_file(chunk)
        try:
            with suppress(Exception):
                p._raw(b'\x1b\x40')
            time.sleep(0.05)

            p.image(tmp_name)
            time.sleep(0.2)

        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def _print_bitmap(self, p, img, chunk_height=140):
        if isinstance(p, MockPrinter):
            print("[IMPRESIÓN] Bitmap enviado a MOCK")
            return

        if not hasattr(p, "device") or not p.device:
            print("[IMPRESIÓN] USB no disponible, solicitando fallback a MOCK")
            raise PrinterFallbackToMock()

        img = img.convert("1")
        width, height = img.size
        y = 0

        while y < height:
            chunk_end = min(y + chunk_height, height)
            chunk = img.crop((0, y, width, chunk_end))

            self._save_and_print_chunk(p, chunk)

            y = chunk_end

        p.text("\n")

    def print_ticket(self, ticket: dict):
        """
        Imprime ticket con fallback automático a MOCK si USB falla.
        """

        try:
            self._init_printer()
            self._print_ticket_internal(ticket)

        except PrinterFallbackToMock:
            print("[IMPRESIÓN] Reintentando impresión en modo MOCK")
            self._close_printer()
            self.printer = MockPrinter()
            self._print_ticket_internal(ticket)

        except Exception as e:
            print(f"[IMPRESIÓN] Error inesperado: {e}")
            raise

        finally:
            self._close_printer()

    def _check_usb_device(self, p):
        """Verifica si el dispositivo USB está disponible, lanza fallback si no"""
        if isinstance(p, MockPrinter):
            return
        
        try:
            # Intentar acceder al dispositivo - esto puede lanzar excepciones
            if not hasattr(p, "device") or not p.device:
                print("[IMPRESIÓN] USB no disponible en verificación")
                raise PrinterFallbackToMock()
        except Exception as e:
            # Cualquier error al acceder al USB activa el fallback
            print(f"[IMPRESIÓN] Error al verificar USB: {e}")
            raise PrinterFallbackToMock()

    def _print_ticket_internal(self, ticket: dict):
        # Usar self.printer para asegurar que usamos el objeto actualizado después del fallback
        p = self.printer
        
        # Verificar disponibilidad de USB antes de empezar
        self._check_usb_device(p)

        with suppress(Exception):
            p._raw(b'\x1b\x40')

        time.sleep(0.2)

        self._print_centered_bitmap_text(
            p,
            ["BIENVENIDO"],
            font_size=60,
            bold=True,
            line_spacing=5
        )

        with suppress(Exception):
            p.set(align='center', bold=False)

        p.text(
            "\nConserve su turno\n"
            "Recuerde que sera el mismo para todos los\n"
            "tramites/servicios seleccionados.\n\n"
            "SU NUMERO DE TURNO ES:"
        )

        self._print_centered_bitmap_text(
            p,
            [ticket["turno"]],
            font_size=110,
            bold=True,
            line_spacing=10
        )

        advertencia = [
            "Si tarda mas de 3 minutos en acudir a la",
            "ventanilla asignada, puede perder el turno",
            "del tramite/servicio para el que fue llamado",
        ]

        self._print_centered_bitmap_text(
            p,
            advertencia,
            font_size=28,
            italic=True,
            line_spacing=6
        )
        
        with suppress(Exception):
            p.set(align='center', bold=True)

        p.text("\nTRAMITES / SERVICIOS\n")
        p.text("-" * 48 + "\n")
        
        with suppress(Exception):
            p.set(bold=False, align="left")

        for t in ticket.get("tramites", []):
            lineas = textwrap.wrap(f"• {t}", width=ANCHO_LINEA)
            for linea in lineas:
                p.text(linea + "\n")
                
        with suppress(Exception):
            p.set(align="center")

        p.text("\nPor favor espere su turno\n\n")
        
        with suppress(Exception):
            p.set(align="right")
        
        p.text(ticket.get("fecha_hora", "") + "\n")

        p.cut()
        time.sleep(0.3)

    def _safe_print_bitmap(self, p, img):
        with suppress(Exception):
            self._print_bitmap(p, img)

    def _print_centered_bitmap_text(self, p, lines, font_size, bold=False, italic=False, line_spacing=8):
        img = self._render_text_bitmap(
            lines,
            self._load_font(font_size, bold=bold, italic=italic),
            line_spacing=line_spacing
        )
        self._safe_print_bitmap(p, img)

class MockPrinter:
    def image(self, path):
        print(f"[MOCK IMG] {path}")

    def text(self, content):
        print(content, end="")

    def cut(self):
        print("\n--- CORTE MOCK ---\n")

    def set(self, **kwargs):
        if kwargs:
            print(f"[MOCK STYLE] {kwargs}")

    def close(self):
        print("[MOCK] Impresora cerrada")

    def _raw(self, data):
        print(f"[MOCK RAW] {data}")