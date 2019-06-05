#!/bin/bash
# Based off instructions from:
# https://gist.github.com/domenic/ec8b0fc8ab45f39403dd

set -o errexit -o nounset

PACKAGE="cedar"

DOCS=$(dirname $(readlink -f $0))/../
APIDOC="${DOCS}/source/${PACKAGE}"

KEY_FILE=.deploy_key

SRC=_build  # defined in conf.py
DST=ghpages

REPO=$(git config remote.origin.url)
SSH_REPO=${REPO/https:\/\/github.com\//git@github.com:}
REV=$(git rev-parse --short HEAD)

DST_BRANCH=gh-pages

# Determine SRC_BRANCH
set +u
if [ "$TRAVIS" == "true" ]; then
    set -u

    echo "On Travis CI"
    if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
        echo "Not building docs for PR"
        exit 0
    fi

    # Override what git says
    if [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
        SRC_BRANCH=$TRAVIS_BRANCH
    else
        SRC_BRANCH=$TRAVIS_PULL_REQUEST_BRANCH
    fi

    # CONFIGURE GIT
    ENCRYPTED_KEY_VAR="encrypted_${ENCRYPTION_LABEL}_key"
    ENCRYPTED_IV_VAR="encrypted_${ENCRYPTION_LABEL}_iv"
    ENCRYPTED_KEY=${!ENCRYPTED_KEY_VAR}
    ENCRYPTED_IV=${!ENCRYPTED_IV_VAR}
    openssl aes-256-cbc \
            -K $ENCRYPTED_KEY \
            -iv $ENCRYPTED_IV \
            -in ${KEY_FILE}.enc \
            -out ${KEY_FILE} \
            -d
    chmod 600 ${KEY_FILE}
    eval `ssh-agent -s`
    ssh-add ${KEY_FILE}

    git config --global user.email $COMMIT_AUTHOR_EMAIL
    git config --global user.name $COMMIT_AUTHOR_NAME
else
    SRC_BRANCH=$(git rev-parse --abbrev-ref HEAD)
fi
set -u

echo "Building docs for branch: $SRC_BRANCH"

DEST=$DST/$SRC_BRANCH/

# START
cd $DOCS/

# Clean
rm -rf $DST

# Create branch directory and grab Git repo
git clone $SSH_REPO $DST/
cd $DST/
git checkout $DST_BRANCH || git checkout --orphan $DST_BRANCH
git reset

# Generate API doc
cd $DOCS/
sphinx-apidoc -f -e -o $APIDOC ../${PACKAGE}/

# Build docs
make html
rm -rf $DEST
mkdir -p $DEST
cp -R ${SRC}/html/* $DEST

# If there's test coverage results, add it in!
HTMLCOV=../htmlcov
if [ -d $HTMLCOV ]; then
    # Copy to new directory name since "htmlcov" is in gitignore
    echo "Copying coverage HTML report to docs"
    cp -vR $HTMLCOV $DEST/coverage
    # Generate a badge
    badge=$DEST/coverage_badge.svg
    if [ -f ../badge.svg ]; then
        echo "Copying coverage badge to $badge"
        cp -v ../badge.svg $badge
    else
        echo "Cannot find coverage badge"
        wget https://img.shields.io/badge/docs-error-lightgrey.svg -O $badge
    fi
fi

# Commit and push to GH
cd $DST/
git add -A $SRC_BRANCH
git commit -m "Rebuild $DST_BRANCH docs on $SRC_BRANCH: ${REV}"
git push origin HEAD:$DST_BRANCH
