#!/usr/bin/env bash
# exit on error
set -o errexit

STORAGE_DIR=/opt/render/project/.render

echo "...Downloading Chrome"
mkdir -p $STORAGE_DIR/chrome
cd $STORAGE_DIR/chrome
wget -P ./ https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -x ./google-chrome-stable_current_amd64.deb $STORAGE_DIR/chrome
rm ./google-chrome-stable_current_amd64.deb
cd $HOME/project/src # Make sure we return to where we were

# add your own build commands...
