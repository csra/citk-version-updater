#!/bin/bash

set -e
set -o pipefail

NC='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
WHITE='\033[0;37m'

APP_NAME='citk-version-updater'
APP_NAME=${BLUE}${APP_NAME}${NC}
echo -e "=== ${APP_NAME} project ${WHITE}cleanup${NC}" &&
rm -rf build/ dist/ src/*.egg-info &&
echo -e "=== ${APP_NAME} project ${WHITE}installation${NC}"

if [ -z ${prefix+x} ]; then
    python setup.py install > /dev/null $@
else 
    python setup.py install --prefix=$prefix > /dev/null $@
fi
echo -e "=== ${APP_NAME} project ${WHITE}cleanup${NC}" &&
rm -rf build/ dist/ src/*.egg-info

if [ -z ${prefix+x} ]; then
    echo -e "=== ${APP_NAME} was ${GREEN}successfully${NC} installed"
else 
    echo -e "=== ${APP_NAME} was ${GREEN}successfully${NC} installed to ${WHITE}${prefix}${NC}"
fi


