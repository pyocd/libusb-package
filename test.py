#!/usr/bin/env python3

import sys
import libusb_package
import usb.core
import usb.backend.libusb1

def main():
    # Test get_library_path().
    path = libusb_package.get_library_path()
    print(f"Path to included library: {path}")

    # Test find_library().
    libusb1_backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
    if not libusb1_backend:
        print("Unable to load libusb backend!")
        sys.exit(1)
    print(f"libusb1_backend = {libusb1_backend}")

    # Test get_libusb1_backend().
    print("usb.core.show_devices output:")
    print(usb.core.show_devices(backend=libusb_package.get_libusb1_backend()))

    # Try out the find() wrapper.
    print("libusb_package.find output:")
    for dev in libusb_package.find(find_all=True):
        try:
            print(f"{dev.idVendor:04x}:{dev.idProduct:04x}: {dev.manufacturer} {dev.product} ({dev.serial_number})")
        except Exception as err:
            print(f"{dev.idVendor:04x}:{dev.idProduct:04x}: error reading strings ({err})")

if __name__ == "__main__":
    main()

