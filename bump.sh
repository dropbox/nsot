#!/usr/bin/bash

USAGE=`cat <<EOF
Usage: bump [OPTIONS]...

    Bump version of NSoT, updating the python package and Dockerfile

Options:
    -v, --version VERSION       Version to bump to
    -b, --build                 Build and push dropbox/nsot docker image
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

function docker_build() {
    # docker build -t dropbox/nsot -t dropbox/nsot:${VERSION} docker/ && \
    #     docker push dropbox/nsot && \
    #     docker push dropbox/nsot:${VERSION}
    docker build -t blah docker/
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
        -b|--build)
            BUILD=1
            ;;
        *) ;;
    esac
    shift
done

if [ -z $VERSION ]; then echo "You must provide -v|--version!" >&2; usage; fi

CURVER=`sed "s/^.*'\(\S*\)'/\1/" nsot/version.py`
proceed

if [ -z $BUILD ]; then
    exit
else
    docker_build
fi
