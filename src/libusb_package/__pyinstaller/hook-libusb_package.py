from PyInstaller.utils.hooks import collect_dynamic_libs

# copy the libusb shared library to the package root directory
binaries = collect_dynamic_libs('libusb_package', destdir='.')
