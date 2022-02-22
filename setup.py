# Copyright (c) 2021 Chris Reed
# Copyright (c) 2022 Mitchell Kline
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Import setuptools_scm and tomli so a more understandable error is reported if not installed.
import setuptools_scm  # noqa: F401
import tomli  # noqa: F401

from contextlib import contextmanager
import glob
import os
from pathlib import Path
import sys
from setuptools import setup, Extension, Distribution
from setuptools.command.build_ext import build_ext
import shutil
import sysconfig

# Use os.path.abspath() instead of Path.resolve() because the build on Windows won't work
# if the resulting path is a UNC path, and resolve() likes to convert network shares mapped
# to drive letters to their UNC form.
ROOT_DIR = Path(os.path.abspath(__file__)).parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
VSENV_SCRIPT = SCRIPTS_DIR / "vsenv.bat"
LIBUSB_DIR = ROOT_DIR / "src" / "libusb"
BOOTSTRAP_SCRIPT = LIBUSB_DIR / "bootstrap.sh"
CONFIGURE_SCRIPT = LIBUSB_DIR / "configure"
VS_PROJ = LIBUSB_DIR / "msvc" / "libusb_dll_2019.vcxproj"

PACKAGE_NAME = 'libusb_package'

# check for mingw environment (recommended method from msys2.org/docs/python)
IS_CPYTHON_MINGW = os.name == "nt" and sysconfig.get_platform().startswith("mingw")

if IS_CPYTHON_MINGW:
    # if running cpython-mingw, path names get butchered in windows-posix conversion (or lack thereof),
    # so fix them here
    print("cpython-mingw detected!")
    os.environ['ACLOCAL_PATH'] = os.environ.get('ACLOCAL_PATH').replace('\\', '/')

# Check if we're running 64-bit Python
IS_64_BIT = sys.maxsize > 2**32

class LibusbBuildError(RuntimeError):
    """@brief Exception raised for errors attempting to build the libusb library."""

@contextmanager
def temp_chdir(path: Path):
    saved_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(saved_cwd)

def get_relative_sibling_path(from_path: Path, to_path: Path) -> Path:
    # Get common path base of absolute from and to paths. We don't want to resolve symlinks, though.
    from_path_abs = Path(os.path.abspath(from_path))
    to_path_abs = Path(os.path.abspath(to_path))
    common = Path(os.path.commonpath([from_path_abs, to_path_abs]))

    # Generate a sequence of '..' steps to move from from_path to common.
    from_rel = from_path_abs.relative_to(common)
    up_path = os.path.join('', *([os.path.pardir] * len(from_rel.parts)))

    # Combine into the final path.
    result = up_path / to_path_abs.relative_to(common)
    return result


# Based on code from https://github.com/libdynd/dynd-python
class libusb_build_ext(build_ext):
  description = "Build libusb for libusb-package"

  def run(self):
    # Don't call the origin build_ext and ignore the default behavior.

    self._found_names = []
    self._found_paths = []

    # The staging directory for the module being built.
    if self.inplace:
        build_py = self.get_finalized_command('build_py')
        build_lib = ROOT_DIR / Path(build_py.get_package_dir(PACKAGE_NAME)).parent
    else:
        build_lib = Path(os.path.abspath(self.build_lib))
#     build_temp = Path(os.path.abspath(self.build_temp))

    # Build in-tree for the time being. libusb commit 1001cb5 adds support for out of tree builds, but
    # this is not yet supported in an existing release. Once libusb version 1.0.25 is released, we can
    # build out of tree.
    build_temp = LIBUSB_DIR

    print(f"build_temp = {build_temp}")
    print(f"build_lib = {build_lib}")

    # Make sure the build directory exists.
    if not build_temp.is_dir():
        self.mkpath(str(build_temp))

    try:
        # Change to the build directory during the build.
        with temp_chdir(build_temp):
            if sys.platform != 'win32' or IS_CPYTHON_MINGW:
                # Set optimization and enable extra warnings.
                # These flags are taken from libusb/.private/ci-build.sh.
                cflags = [
                    "-O2",
                    "-Winline",
                    "-Wmissing-include-dirs",
                    "-Wnested-externs",
                    "-Wpointer-arith",
                    "-Wredundant-decls",
                    "-Wswitch-enum",
                    ]

                if sys.platform.startswith('linux'):
                    # Don't include libudev (for now) on Linux since it isn't in the CI runner image. It's
                    # excluded even on non-CI builds to keep the same feature set.
                    extra_configure_args = ['--disable-udev']
                else:
                    extra_configure_args = []

                # Special conditions when cibuildwheel is building us.
                if os.environ.get('CIBUILDWHEEL') == '1':
                    if sys.platform == 'darwin':
                        # Support arm64 cross-compile builds from x86-64 on macOS from cibuildwheel.
                        archflags = os.environ.get('ARCHFLAGS', '')
                        if archflags:
                            # Wrap in exception handler just in case something goes unexpectedly wrong, it
                            # won't totally break all builds.
                            try:
                                arch = archflags.split()[-1]
                                cflags += [archflags]
                                extra_configure_args += [f'--host={arch}-apple-darwin']
                            except Exception as err:
                                print(f"Warning: failure to extract architecture from ARCHFLAGS='{archflags}' ({err})")

                os.environ['CFLAGS'] = ' '.join(cflags)

                # Run bootstrap.sh, configure, and make.
                try:
                    self.spawn(['env']) # Dump environment for debugging purposes.
                    self.spawn(['bash', str(BOOTSTRAP_SCRIPT)])
                    self.spawn(['bash', str(CONFIGURE_SCRIPT), *extra_configure_args])
                    self.spawn(['make', 'clean'])
                    self.spawn(['make', f'-j{os.cpu_count() or 4}', 'all'])
                except Exception as err:
                    # Exception is caught here and reraised as our specific Exception class because the actual
                    # DistutilsExecError class raised on exceptions appears to be difficult to import to use in
                    # the except clause, and may differ depending on the setuptools version (not confirmed).
                    # Otoh, catching and ignoring all Exceptions (below) would be bad.
                    raise LibusbBuildError(str(err)) from err

                if sys.platform == 'darwin':
                    shared_library_suffix = 'dylib'
                elif sys.platform == 'cygwin' or sys.platform == 'win32':
                    shared_library_suffix = 'dll'
                else:
                    shared_library_suffix = 'so'
                lib_paths = [Path(g) for g in glob.glob(f"libusb/.libs/*.{shared_library_suffix}")]

                # Sort libs by filename length. The shortest filename should be the most generic version.
                lib_paths = sorted(lib_paths, key=lambda x: len(x.name))
            else:
                platform = "x64" if IS_64_BIT else "x86"
                config = "Release"

                try:
                    self.spawn(['cmd.exe', '/c', f'{VSENV_SCRIPT} && '
                            f'msbuild -p:Configuration={config} -p:Platform={platform} {VS_PROJ}'])
                except Exception as err:
                    # See comment above for notes about this exception handler.
                    raise LibusbBuildError(str(err)) from err

                out_dir = "x64" if IS_64_BIT else "Win32"
                lib_paths = [Path(g) for g in glob.glob(f"{out_dir}\\{config}\\dll\\*.dll")]

            if not lib_paths:
                raise LibusbBuildError(f"libusb failed to build: no libraries found in {build_temp}")

            lib_path = lib_paths[0]
            print(f"lib_path={lib_path}")

            # Copy the built C-extension to the place expected by the Python build.
            name = lib_path.name
            dest_path = build_lib / PACKAGE_NAME / name
            if dest_path.exists() or dest_path.is_symlink():
                print(f"{dest_path} already exists; unlinking")
                dest_path.unlink()
            self.mkpath(str(dest_path.parent))
            if not self.inplace:
                print(f"Copying built {lib_path} to output path {dest_path}")
                shutil.copy(lib_path, dest_path, follow_symlinks=True)
            else:
                print(f"Inplace: linking output path {dest_path} to built {lib_path}")
                link_dest = get_relative_sibling_path(dest_path.parent, lib_path)
                print(f"Link dest is {link_dest}")
                # Sadly, creating symlinks on Windows requires elevated permissions.
                try:
                    dest_path.symlink_to(link_dest)
                except OSError as err:
                    print(f"Error attempting to create symlink: {err}")
                    shutil.copy(lib_path, dest_path, follow_symlinks=True)
                    print(f"Falling back to copying built {lib_path} to output path {dest_path}")
            if not Path(dest_path).exists():
                raise LibusbBuildError(f"failed to copy/link destination file at {dest_path}")
            self._found_names.append(name)
            self._found_paths.append(str(lib_path))
    except LibusbBuildError as err:
        print(f"Error while building libusb: {err}")

        # If we're building wheels in CI, re-raise the error!
        if os.environ.get('CIBUILDWHEEL', 'x') != '1':
            print("Ignoring build failure and creating system-only libusb-package")
        else:
            raise

  def get_names(self):
    return self._found_names

  def get_outputs(self):
    return self._found_paths


class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True


setup(
    distclass=BinaryDistribution,
    # Dummy extension to trigger build_ext
    ext_modules=[Extension('', sources=[])],
    cmdclass={
        'build_ext': libusb_build_ext
    },
)
