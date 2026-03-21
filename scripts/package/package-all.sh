#!/bin/bash

set -e

echoerr() { echo "$@" 1>&2; }

function get_platform() {
    # Will return "linux" for GNU/Linux
    #   I'd just like to interject for a moment...
    #   https://wiki.installgentoo.com/index.php/Interjection
    # Will return "macos" for macOS/OS X
    # Will return "windows" for Windows/MinGW/msys

    _platform=$(uname | tr '[:upper:]' '[:lower:]')
    if [[ $_platform == "darwin" ]]; then
        _platform="macos";
    elif [[ $_platform == "msys"* ]]; then
        _platform="windows";
    elif [[ $_platform == "mingw"* ]]; then
        _platform="windows";
    elif [[ $_platform == "linux" ]]; then
        # Nothing to do
        true;
    else
        echoerr "ERROR: $_platform is not a valid platform";
        exit 1;
    fi

    echo $_platform;
}

function get_version() {
    $(dirname "$0")/getversion.sh;
}

function get_arch() {
    _arch="$(uname -m)"
    echo $_arch;
}

platform=$(get_platform)
version=$(get_version)
arch=$(get_arch)
echo "Platform: $platform, arch: $arch, version: $version"

function build_zip() {
    echo "Zipping executables..."
    pushd dist;
    filename="activitywatch-${version}-${platform}-${arch}.zip"
    echo "Name of package will be: $filename"

    if [[ $platform == "windows"* ]]; then
        7z a $filename activitywatch;
    else
        zip -r $filename activitywatch;
    fi
    popd;
    echo "Zip built!"
}

build_zip

echo
echo "-------------------------------------"
echo "Contents of ./dist"
ls -l dist
echo "-------------------------------------"
