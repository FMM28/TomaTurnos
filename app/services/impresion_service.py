from escpos.printer import Usb
from flask import current_app
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
import time
import textwrap

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
            try:
                self.printer.close()
            except Exception:
                pass
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
            try:
                self.printer.close()
            except Exception:
                pass
            finally:
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

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            try:
                chunk.save(tmp.name)
                tmp.close()

                try:
                    p._raw(b'\x1b\x40')
                    time.sleep(0.05)
                except Exception:
                    pass

                p.image(tmp.name)
                time.sleep(0.2)

            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)

            y = chunk_end

        p.text("\n")

    def print_ticket(self, ticket: dict):
        """
        Imprime ticket.
        """

        try:
            self._init_printer()
            self._print_ticket_internal(ticket)

        except PrinterFallbackToMock:
            print("[IMPRESIÓN] Reintentando impresión en modo MOCK")
            self.printer = MockPrinter()
            self._print_ticket_internal(ticket)

        finally:
            self._close_printer()

    def _print_ticket_internal(self, ticket: dict):
        p = self.printer

        try:
            p._raw(b'\x1b\x40')
        except Exception:
            pass

        time.sleep(0.2)

        img = self._render_text_bitmap(
            ["BIENVENIDO"],
            self._load_font(60, bold=True),
            line_spacing=5
        )
        self._print_bitmap(p, img)
        
        try:
            p.set(align='center', bold=False)
        except Exception:
            pass

        p.text(
            "\nConserve su turno\n"
            "Recuerde que sera el mismo para todos los\n"
            "tramites/servicios seleccionados.\n\n"
            "SU NUMERO DE TURNO ES:"
        )

        img_turno = self._render_text_bitmap(
            [ticket["turno"]],
            self._load_font(110, bold=True),
            line_spacing=10
        )
        self._print_bitmap(p, img_turno)

        advertencia = [
            "Si tarda mas de 3 minutos en acudir a la",
            "ventanilla asignada, puede perder el turno",
            "del tramite/servicio para el que fue llamado",
        ]

        img_adv = self._render_text_bitmap(
            advertencia,
            self._load_font(28, italic=True),
            line_spacing=6
        )
        self._print_bitmap(p, img_adv)
        
        try:
            p.set(align='center', bold=True)
        except Exception:
            pass

        p.text("\nTRAMITES / SERVICIOS\n")
        p.text("-" * 48 + "\n")
        
        try:
            p.set(bold=False)
        except Exception:
            pass

        for t in ticket.get("tramites", []):
            lineas = textwrap.wrap(t, width=ANCHO_LINEA)
            for linea in lineas:
                p.text(linea + "\n")

        p.text("\nPor favor espere su turno\n\n")
        
        try:
            p.set(align="right")
        except Exception:
            pass
        
        p.text(ticket.get("fecha_hora", "") + "\n")

        p.cut()
        time.sleep(0.3)

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