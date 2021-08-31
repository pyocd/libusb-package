# Container package for libusb

This Python package functions as an installation vehicle for libusb shared libraries, to
simplify installation of tools that require libusb. The main use case is so that users
don't have to install libusb manually for projects that use pyusb. However, any Python
project that uses a libusb wrapper can also benefit.


Usage example:

```
import libusb_package
import usb.core
import usb.backend.libusb1

libusb1_backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
# calls usb.libloader.load_locate_library(
#                ('usb-1.0', 'libusb-1.0', 'usb'),
#                'cygusb-1.0.dll', 'Libusb 1',
#                win_cls=win_cls,
#                find_library=find_library, check_symbols=('libusb_init',))
#
# -> calls find_library(candidate) with candidate in ('usb-1.0', 'libusb-1.0', 'usb')
#   returns lib name or path (as appropriate for OS) if matching lib is found

usb.core.show_devices(backend=libusb1_backend)

```


