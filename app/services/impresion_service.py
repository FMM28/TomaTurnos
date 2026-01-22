from escpos.printer import Usb
from flask import current_app
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
import time

ANCHO_80MM = 576

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

    def _init_printer(self):
        """Inicializa la impresora con manejo robusto de recursos"""
        if current_app.config.get("PRINT_MODE", "usb") != "usb":
            self.printer = MockPrinter()
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
                return
            except Exception as e:
                print(f"[IMPRESIÓN] Intento {attempt + 1} fallido: {e}")
                if attempt < 2:
                    time.sleep(1)
                else:
                    raise Exception("No se pudo conectar con la impresora después de 3 intentos")

    def _close_printer(self):
        """Cierra la conexión con la impresora de forma segura"""
        if self.printer and hasattr(self.printer, 'close'):
            try:
                self.printer.close()
            except Exception as e:
                print(f"[IMPRESIÓN] Error al cerrar: {e}")
            finally:
                self.printer = None

    def _load_font(self, size, bold=False, italic=False):
        """Carga fuentes con fallback a DejaVu"""
        fonts_to_try = []
        
        if bold and italic:
            fonts_to_try = ["arialbi.ttf", "DejaVuSans-BoldOblique.ttf"]
        elif bold:
            fonts_to_try = ["arialbd.ttf", "DejaVuSans-Bold.ttf"]
        elif italic:
            fonts_to_try = ["ariali.ttf", "DejaVuSans-Oblique.ttf"]
        else:
            fonts_to_try = ["arial.ttf", "DejaVuSans.ttf"]

        for font_name in fonts_to_try:
            try:
                return ImageFont.truetype(font_name, size)
            except Exception:
                continue

        return ImageFont.load_default()

    def _render_text_bitmap(self, lines, font, line_spacing=8):
        """Renderiza texto como bitmap centrado"""
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

    def _print_bitmap(self, p, img, chunk_height=128):
        """
        Impresión bitmap con chunks y verificación completa
        """
        img = img.convert("1")
        width, height = img.size
        
        y = 0
        chunk_num = 0
        
        while y < height:
            chunk_num += 1
            
            chunk_end = min(y + chunk_height, height)
            
            box = (0, y, width, chunk_end)
            chunk = img.crop(box)

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            try:
                chunk.save(tmp.name)
                tmp.close()

                if hasattr(p, '_raw'):
                    try:
                        p._raw(b'\x1b\x40')
                        time.sleep(0.05)
                    except Exception as e:
                        print(f"[IMPRESIÓN] Error en reset: {e}")
                
                p.image(tmp.name)
                
                time.sleep(0.2)
                
            except Exception as e:
                print(f"[IMPRESIÓN] Error en chunk {chunk_num}: {e}")
                raise
            finally:
                try:
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                except Exception as e:
                    print(f"[IMPRESIÓN] Error limpiando temp: {e}")

            y = chunk_end
        
        p.text("\n")

    def print_ticket(self, ticket: dict):
        """Imprime un ticket con manejo robusto de errores"""
        
        try:
            self._init_printer()
            p = self.printer

            if hasattr(p, '_raw'):
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
            self._print_bitmap(p, img, chunk_height=128)

            try:
                p.set(align='center', bold=False)
            except Exception:
                pass
            
            p.text(
                "\nConserve su turno\n"
                "Recuerde que sera el mismo para todos los\n"
                "tramites/servicios seleccionados.\n\n"
            )

            try:
                p.set(align='center', bold=True)
            except Exception:
                pass
            
            p.text("SU NUMERO DE TURNO ES:\n")
            
            try:
                p.set(align='left', bold=False)
            except Exception:
                pass
            
            img_turno = self._render_text_bitmap(
                [ticket["turno"]],
                self._load_font(110, bold=True),
                line_spacing=10
            )

            self._print_bitmap(p, img_turno, chunk_height=128)

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
            self._print_bitmap(p, img_adv, chunk_height=128)

            p.text("\n")
            
            try:
                p.set(align='center', bold=True)
            except Exception:
                pass
            
            p.text("TRAMITES / SERVICIOS\n")
            
            try:
                p.set(bold=False)
            except Exception:
                pass
            
            p.text("-" * 48 + "\n")
            
            for t in ticket.get("tramites", []):
                p.text(f"{t}\n")

            p.text("\n")
            
            try:
                p.set(align='center')
            except Exception:
                pass
            
            p.text("Por favor espere su turno\n")
            p.text(ticket.get("fecha_hora", "") + "\n\n")
            
            try:
                p.set(align='left')
            except Exception:
                pass

            p.cut()
            
            time.sleep(0.5)

        except Exception as e:
            print(f"[IMPRESIÓN] Error crítico: {e}")
            import traceback
            traceback.print_exc()
            raise

        finally:
            self._close_printer()

class MockPrinter:
    def image(self, path):
        print(f"[IMG] {path}")

    def text(self, content):
        print(content, end="")

    def cut(self):
        print("\n--- CORTE ---\n")
    
    def set(self, **kwargs):
        if kwargs:
            print(f"[STYLE] {kwargs}")
    
    def close(self):
        print("[MOCK] Impresora cerrada")
    
    def _raw(self, data):
        print(f"[RAW] {data}")