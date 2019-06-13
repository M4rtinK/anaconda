#!/bin/bash

python3 -m compileall -f . | grep -v Compiling | grep -v Listing
#python3 -m compileall -f .
