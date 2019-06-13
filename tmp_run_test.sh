#!/bin/bash
echo "starting tests"
date
BASE_DIR=".."
TDIR="/tmp/anaconda_run"
RSYNC="rsync -aAhHxX --delete"

mkdir $TDIR

$RSYNC ${BASE_DIR}/anaconda ${TDIR}/
# runpylint needs the Anaconda Git history
echo "rsynced anaconda"
$RSYNC --exclude .git ${BASE_DIR}/blivet ${TDIR}/
echo "rsynced blivet"
$RSYNC --exclude .git ${BASE_DIR}/pykickstart ${TDIR}/
echo "rsynced pykickstart"
$RSYNC --exclude .git ${BASE_DIR}/dnf ${TDIR}/
echo "rsynced dnf"

echo "running tests"
pwd
cd ${TDIR}/anaconda
pwd
export PYTHONPATH=".:./pyanaconda/isys/.libs/:../blivet/:../pykickstart/:../dnf/"
echo $PYTHONPATH
./tests/pylint/runpylint.sh
echo "test run done"
date
