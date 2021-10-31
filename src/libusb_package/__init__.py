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

import atexit
import importlib.resources
import functools
import sys
from typing import (Any, Optional, TYPE_CHECKING)

from ._version import version as __version__

if TYPE_CHECKING:
    from usb.backend import IBackend

@functools.lru_cache
def find_library(candidate: str) -> Optional[str]:
    """@brief Look for a package resource starting with the provided candidate name.

    This function effectively implements the `find_library` callback used by pyusb's backends.
    However, it is general enough to be used for any code that needs a libusb library.

    @retval str Path to the contained library matching the candidate name.
    @retval None No library matching the candidate name is contained in libusb_package.
    """
    for item in importlib.resources.contents('libusb_package'):
#         print(f"find_library({candidate}): item={item}")
        if not item.endswith(".py") and item.startswith(candidate):
            path_resource = importlib.resources.path('libusb_package', item)
            path = path_resource.__enter__()

            @atexit.register
            def cleanup():
                path_resource.__exit__(None, None, None)

#             print(f"find_library({candidate}): p={p}")
            return str(path)

    # We don't have a matching library.
    return None

@functools.lru_cache
def get_libusb1_backend() -> "IBackend":
    """@brief Return a usb backend for pyusb."""
    import usb.backend.libusb1
    return usb.backend.libusb1.get_backend(find_library=find_library)


def find(*args: Any, **kwargs: Any) -> Any:
    """@brief Wrap pyusb's usb.core,find() function."""
    # Import here so pyusb isn't strictly required as a dependency unless this function is used.
    import usb.core
    return usb.core.find(*args, backend=get_libusb1_backend(), **kwargs)


