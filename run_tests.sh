#!/bin/bash

PYTHONPATH=".:./pyanaconda/isys/.libs/:../blivet/:../pykickstart-2/:../dnf/" ./tests/nosetests.sh
PYTHONPATH=".:./pyanaconda/isys/.libs/:../blivet/:../pykickstart/:../dnf/" ./tests/pylint/runpylint.sh
