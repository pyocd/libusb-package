# Container package for libusb

This Python package functions as an installation vehicle for libusb shared libraries, to
simplify installation of tools that require libusb. The main use case is so that users
don't have to install libusb manually for projects that use pyusb. However, any Python
project that uses a libusb wrapper can also benefit.


## APIs

There are three public functions exported by `libusb_package`.

- `find(*args, **kwargs)`: Wrapper around pyusb's `usb.core.find()` that sets the `backend`
    parameter to a libusb1 backend created from the libusb library included in `libusb_package`.
    All other parameters are passed unmodified

- `get_libusb1_backend()`: Returns a `pyusb` backend object for the libusb version contained
    in `libusb_package`.

- `find_library(candidate)`: Lower level function that returns either the full path to a
    library contained in `libusb_package` with a name starting with `candidate`, or None if
    no matching library is found. This function is suitable for use with the `find_library`
    callback parameter for pyusb's `get_backend()` functions.

Both `get_libusb1_backend()` and `find_library(candidate)` cache their return values.


## Examples

Usage example for `find()`:

```py
import libusb_package

for dev in libusb_package.find(find_all=True):
    print(dev)
```


Usage example for `find_library()`:

```py
import libusb_package
import usb.core
import usb.backend.libusb1

libusb1_backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
# -> calls usb.libloader.load_locate_library(
#                ('usb-1.0', 'libusb-1.0', 'usb'),
#                'cygusb-1.0.dll', 'Libusb 1',
#                win_cls=win_cls,
#                find_library=find_library, check_symbols=('libusb_init',))
#
# -> calls find_library(candidate) with candidate in ('usb-1.0', 'libusb-1.0', 'usb')
#   returns lib name or path (as appropriate for OS) if matching lib is found

# It would also be possible to pass the output of libusb_package.get_libsusb1_backend()
# to the backend parameter here. In fact, that function is simply a shorthand for the line
# above.
print(list(usb.core.find(find_all=True, backend=libusb1_backend)))
```


