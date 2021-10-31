# Copyright (c) 2021 Chris Reed
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

import glob
import os
from pathlib import Path
import sys
from setuptools import setup, Extension, Distribution
from setuptools.command.build_ext import build_ext
import shutil
import sysconfig

ROOT_DIR = Path(__file__).resolve().parent
LIBUSB_DIR = ROOT_DIR / "src" / "libusb"
BOOTSTRAP_SCRIPT = LIBUSB_DIR / "bootstrap.sh"
CONFIGURE_SCRIPT = LIBUSB_DIR / "configure"

PACKAGE_NAME = 'libusb_package'

# Based on code from https://github.com/libdynd/dynd-python
class libusb_build_ext(build_ext):
  description = "Build libusb for libusb-package"

  def run(self):
    # We don't call the origin build_ext and ignore the default behavior.

    # The staging directory for the module being built.
    if self.inplace:
        build_py = self.get_finalized_command('build_py')
        build_lib = ROOT_DIR / build_py.get_package_dir(PACKAGE_NAME).parent
    else:
        build_lib = Path(self.build_lib).resolve()
    build_temp = Path(self.build_temp).resolve()

    print(f"build_temp = {build_temp}")
    print(f"build_lib = {build_lib}")

    # Change to the build directory
    saved_cwd = Path.cwd()
    if not build_temp.is_dir():
        self.mkpath(str(build_temp))
    os.chdir(build_temp)

    if sys.platform != 'win32':
        # First run bootstrap.sh.
        self.spawn(['bash', str(BOOTSTRAP_SCRIPT)])

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

        os.environ['CFLAGS'] = ' '.join(cflags)

        # Next, configure.
        self.spawn(['bash', str(CONFIGURE_SCRIPT)])

        # And now make.
        self.spawn(['make', f'-j{os.cpu_count() or 4}'])

        if sys.platform == 'darwin':
            shared_library_suffix = 'dylib'
        else:
            shared_library_suffix = 'so'
        lib_paths = [Path(g) for g in glob.glob(f"libusb/.libs/*.{shared_library_suffix}")]
    else:
        raise RuntimeError("no win32 support yet!")

    if not lib_paths:
        raise RuntimeError(f"libusb failed to build: no libraries found in {build_temp}")

    # Sort libs by filename length.
    lib_paths.sort(key=lambda x: len(x.name))
    print(f"lib_paths={lib_paths}")

    # Take the shortest filename, which should be the most generic version.
    lib_path = lib_paths[0]

    # Move the built C-extension to the place expected by the Python build
    self._found_names = []
    self._found_paths = []

    name = lib_path.name
    ext_path = build_lib / PACKAGE_NAME / name
    if ext_path.exists():
        ext_path.unlink()
    self.mkpath(str(ext_path.parent))
    if not self.inplace:
        print(f'Copying built {lib_path} to output path {ext_path}')
        shutil.copy(lib_path, ext_path, follow_symlinks=True)
    else:
        print(f'Inplace: linking output path {ext_path} to built {lib_path}')
        ext_path.symlink_to(lib_path)
    self._found_names.append(name)
    self._found_paths.append(str(lib_path))

    os.chdir(saved_cwd)

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
