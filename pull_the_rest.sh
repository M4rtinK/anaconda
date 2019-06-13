#!/bin/bash

cd ../pykickstart
echo "pulling Pykickstart"
git pull --rebase
cd ../blivet
echo "pulling Blivet"
git pull --rebase
cd ../dnf
echo "pulling DNF"
git pull --rebase
