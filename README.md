# Container package for libusb

This Python package functions as an installation vehicle for libusb shared libraries, to
simplify installation of tools that require libusb. The main use case is so that users
don't have to install libusb manually for projects that use pyusb. However, any Python
project that uses a libusb wrapper can also benefit.

See [libusb.info](https://libusb.info) for more information about libusb.

Note: Currently the included libusb is built _without_ udev support on Linux.

Note: The libusb upstream git repository is included as a submodule, so you need to clone with submodules
enabled. You can either clone with `--recurse-submodules` or run `git submodule update --init` after cloning.


## Installation

All releases include wheels for Linux, macOS, and Windows for multiple architectures. In addition, a source
distribution is released.

If a matching wheel is not available, the source distribution will be installed and libusb will be compiled.
This means the libusb build requirements must be installed:

- Linux and macOS: autoconf, automake, libtool, and m4. As mentioned above, libusb is built without udev support,
    so libudev-dev is not required on Linux.
- Windows: Visual Studio 2019 (Community is ok).

If the libusb build fails when installing from a source distribution, the `libusb-package` install _will still
succeed_. In this case, an "empty" `libusb-package` is installed that doesn't contain a libusb shared library.
`get_library_path()` returns None and `find_library()` falls back to returning a system installation of libusb,
if available.

You can also install from a clone of the git repository by running `pip install .` from the repository root directory.
Editable installs are supported. Please note that running `setup.py` directly is no longer supported for PEP 517
compliant packages. Building libusb is done out of tree in an automatically created build directory for libusb 1.0.25
and later.


## APIs

There are four public functions exported by `libusb_package`.

- `find(*args, **kwargs)`: Wrapper around pyusb's `usb.core.find()` that sets the `backend`
    parameter to a libusb1 backend created from the libusb library included in `libusb_package`.
    All other parameters are passed unmodified.

- `get_libusb1_backend()`: Returns a `pyusb` backend object for the libusb version contained
    in `libusb_package`.

- `find_library(candidate)`: Lower level function that returns either the full path to a
    library contained in `libusb_package` with a name starting with `candidate`, or None if
    no matching library is found. This function is suitable for use with the `find_library`
    callback parameter for pyusb's `get_backend()` functions.

    If `get_library_path()` returns None, indicating there is no included library, this function
    will fall back to `ctypes.util.find_library()`.

- `get_library_path()`: Returns an absolute Path object for the included library. If there is not
    an included library, None is returned.

Both `get_libusb1_backend()` and `get_library_path()` cache their return values.


## Versioning

The version of libusb-package is composed of the libusb version plus an additional field for
the version of the Python code. For instance, 1.0.24.0. The Python code version will be reset
to 0 when the libusb version is incremented for new libusb release.


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


### Source distribution

Before building a source distribution, be sure to clean all untracked files from the libusb
submodule using `git -C src/libusb clean -dfx`.


### License

The Python code for `libusb-package` is licensed with Apache 2.0.\
The libusb library and its source code are licensed with GPLv2.
