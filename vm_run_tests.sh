#!/bin/bash

echo "starting tests in a VM"
date
BASE_DIR=".."
TDIR="/home/user/mkolman/anaconda_run"
RSYNC="rsync -aAhHxX --delete"

$RSYNC ${BASE_DIR}/anaconda pylint:${TDIR}/
# runpylint needs the Anaconda Git history
echo "rsynced anaconda"
$RSYNC --exclude .git ${BASE_DIR}/blivet pylint:${TDIR}/
echo "rsynced blivet"
$RSYNC --exclude .git ${BASE_DIR}/pykickstart pylint:${TDIR}/
echo "rsynced pykickstart"
$RSYNC --exclude .git ${BASE_DIR}/dnf pylint:${TDIR}/
echo "rsynced dnf"

echo "running tests"

ssh pylint "bash ${TDIR}/run_tests.sh"

echo "VM test run done"
date
