from escpos.printer import Usb
from flask import current_app


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

        mode = current_app.config.get("PRINT_MODE", "usb")

        if mode == "usb":
            self.printer = Usb(
                0x04b8,
                0x0e15,
                timeout=0,
                in_ep=0x82,
                out_ep=0x01
            )
        else:
            self.printer = MockPrinter()

        self._initialized = True

    def print_ticket(self, ticket: dict):
        p = self.printer

        p.set(align='center')
        p.text("=" * 32 + "\n")
        p.text("SISTEMA DE TURNOS\n")
        p.text("=" * 32 + "\n\n")

        p.set(text_type='B', width=2, height=2)
        p.text("TURNO\n")
        p.text(f"{ticket['turno']}\n\n")

        p.set(text_type='normal', width=1, height=1)

        p.set(align='left')
        p.text("-" * 32 + "\n")
        p.text("TRÁMITES SOLICITADOS\n")
        p.text("-" * 32 + "\n")

        for tramite in ticket["tramites"]:
            p.text(f"• {tramite}\n")

        p.text("\n")

        p.text("-" * 32 + "\n")
        p.text("Fecha y hora:\n")
        p.text(f"{ticket['fecha_hora']}\n\n")

        p.set(align='center')
        p.text("Por favor espere su turno\n")

        p.cut()


class MockPrinter:
    def set(self, *args, **kwargs):
        pass

    def text(self, content):
        print(content, end="")

    def cut(self):
        print("\n--- CORTE DE PAPEL ---\n")
