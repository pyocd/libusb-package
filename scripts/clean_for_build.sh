#!/bin/bash

#
# Clean the repository of build detritus.
# Run this prior to building a distribution locally.
#

# Change to the repo's root.
root=$(realpath $(dirname ${BASH_SOURCE[0]})/..)
cd $root

# Remove Python build output and temporaries.
rm -rf build dist src/*.egg-info

# Remove *all* untracked files from libusb.
git -C src/libusb clean -dfx

