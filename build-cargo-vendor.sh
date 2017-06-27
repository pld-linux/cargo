#!/bin/sh

# Script to build vendor tarball
#
# Prerequisites:
# - installed cargo and rust
# - installed cargo-vendor from https://github.com/alexcrichton/cargo-vendor

CARGO_VER=$1
VENDOR_FILTER=../vendor-tarball-filter.txt

tar xzf cargo-${CARGO_VER}.tar.gz
cd cargo-${CARGO_VER}
cargo vendor --explicit-version --verbose

grep -v '^#' ${VENDOR_FILTER} | xargs  -I% sh -c 'rm -rf vendor/%'
for i in vendor/* ; do
	../cargo-checksums-prune.py "$i"
done

tar cJvf cargo-${CARGO_VER}-vendor.tar.xz vendor
