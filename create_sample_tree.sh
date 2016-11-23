#!/bin/bash

set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

mkdir -p sample
cd sample

if [[ ! -d DualBootPatcher ]]; then
    git clone https://github.com/chenxiaolong/DualBootPatcher.git
fi

pushd DualBootPatcher
git pull
popd

rm -rf tree
mkdir -p tree/files
pushd tree/files

versions=(
    8.0.0.r2703.g553e762
    8.0.0.r2706.g06da5cc
    8.0.0.r2708.g243c37d
    8.0.0.r2709.g554d8f9
    9.0.0.r0.ge75b10c
    9.0.0.r2.g058f60a
    9.0.0.r3.g52c69fd
    9.0.0.r5.g78614f9
    9.0.0.r7.gae0ed2e
    9.0.0.r9.g3a82ef1
    9.0.0.r12.g499d389
    9.0.0.r14.g69ea40f
    9.0.0.r17.g6428cf6
    9.0.0.r20.g799b1e5
    9.0.0.r21.g024526a
    9.0.0.r22.ge90ba62
    9.0.0.r31.g6046c0e
    9.0.0.r33.gc20099c
    9.0.0.r35.g47c80d0
    9.0.0.r37.g0f443fb
    9.0.0.r39.g9e90a5f
    9.0.0.r41.g8c2ca30
    9.0.0.r43.gb284be9
    9.0.0.r45.ge916253
    9.0.0.r47.gd65a6fd
    9.0.0.r49.g43e7dfa
    9.0.0.r56.ga5fde5c
    9.0.0.r60.g7294c90
    9.0.0.r61.g05501e3
    9.0.0.r62.g53c2501
    9.0.0.r63.g9def582
    9.0.0.r67.g33be691
    9.0.0.r69.gfcd8ec1
    9.0.0.r71.g0e7407e
)

for v in "${versions[@]}"; do
    mkdir -p "${v}/Android" "${v}/Utilities"
    apk_path="${v}/Android/DualBootPatcherAndroid-${v}-snapshot.apk"
    utilities_path="${v}/Utilities/DualBootUtilities-${v}.zip"

    dd if=/dev/zero of="${apk_path}" bs=1M count=$((RANDOM % 5))
    dd if=/dev/zero of="${utilities_path}" bs=1M count=$((RANDOM % 5))

    md5sum "${apk_path}" > "${apk_path}.md5sum"
    sha1sum "${apk_path}" > "${apk_path}.sha1sum"
    sha512sum "${apk_path}" > "${apk_path}.sha512sum"
    md5sum "${utilities_path}" > "${utilities_path}.md5sum"
    sha1sum "${utilities_path}" > "${utilities_path}.sha1sum"
    sha512sum "${utilities_path}" > "${utilities_path}.sha512sum"
done

popd
