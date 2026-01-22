import usb.core

for d in usb.core.find(find_all=True):
    print(hex(d.idVendor), hex(d.idProduct))

import usb.core

dev = usb.core.find(idVendor=0x0416, idProduct=0x5011)
print(dev)
