#!/usr/bin/env python3

import sys
import libusb_package
import usb.core
import usb.backend.libusb1

def main():
    libusb1_backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
    if not libusb1_backend:
        print("Unable to load libusb backend!")
        sys.exit(1)
    print(f"libusb1_backend = {libusb1_backend}")

    # Use pyusb directly with the loaded backend.
    print("usb.core.show_devices output:")
    usb.core.show_devices(backend=libusb1_backend)

    # Try out the find() wrapper.
    print("libusb_package.find output:")
    for dev in libusb_package.find(find_all=True):
        print(dev)

if __name__ == "__main__":
    main()

