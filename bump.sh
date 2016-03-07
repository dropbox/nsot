#!/usr/bin/bash

USAGE=`cat <<EOF
Usage: bump [OPTIONS]...

    Bump version of NSoT, updating the python package and Dockerfile

Options:
    -v, --version VERSION       Version to bump to
                                [default: false]
EOF
`

function proceed() {
    echo "Replace ${CURVER} with ${VERSION}? [Y\\n]"
    read confirm
    case ${confirm} in
        y|Y|'' ) replace;;
        n|N ) echo "Canceled" >&2 && exit 1;;
        * ) proceed;;
    esac
}

function replace() {
    sed -i "s/'${CURVER}'/'${VERSION}'/" nsot/version.py && \
        echo "Updated nsot/version.py"

    sed "s/{{ NSOT_VERSION }}/${VERSION}/" docker/Dockerfile.sub > \
        docker/Dockerfile && echo "Updated docker/Dockerfile"
}

function usage() {
    echo "$USAGE" >&2
    exit
}

# Entrypoint actually starts here

while [[ $# > 0 ]]; do

    key="$1"

    case $key in
        -h|--help)
            usage
            ;;
        -v|--version)
            VERSION="$2" && shift;;
        *) ;;
    esac
    shift
done

if [ -z $VERSION ]; then echo "You must provide -v|--version!" >&2; usage; fi

CURVER=`sed "s/^.*'\(\S*\)'/\1/" nsot/version.py`
proceed
