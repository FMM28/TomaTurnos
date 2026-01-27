from escpos.printer import Usb
import usb.core

print("=== DISPOSITIVOS USB ===")
devices = usb.core.find(find_all=True)
for device in devices:
    try:
        print(f"Vendor ID: 0x{device.idVendor:04x}")
        print(f"Product ID: 0x{device.idProduct:04x}")
        print(f"Manufacturer: {usb.util.get_string(device, device.iManufacturer)}")
        print(f"Product: {usb.util.get_string(device, device.iProduct)}")
        print("-" * 40)
    except:
        pass

print("\n=== PROBANDO IMPRESORA ===")
try:
    printer = Usb(0x0416, 0x5011, timeout=0)
    print(f"Impresora conectada exitosamente")
    print(f"Perfil actual: {printer.profile}")
    
    # Ver datos del perfil
    if hasattr(printer.profile, 'profile_data'):
        print(f"Datos del perfil: {printer.profile.profile_data}")
    
    printer.close()
except Exception as e:
    print(f"Error: {e}")