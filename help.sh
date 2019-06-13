#!/bin/bash

export ANACONDA_DATADIR="/home/mkolman/devel/anaconda/data"
#PYTHONPATH=".:./pyanaconda/isys/.libs/:../blivet/:../pykickstart/:../dnf/" python anaconda --help
PYTHONPATH=".:./pyanaconda/isys/.libs/:../blivet/:../pykickstart/:../dnf/" python /home/mkolman/devel/anaconda/anaconda --help
