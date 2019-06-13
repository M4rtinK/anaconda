#!/bin/bash

#FIXERS="-x unicode -x raw_input -x next -x xrange -x metaclass -x long -x sys_exc -x map -x urllib -x print -x dict -x import -x has_key -x basestring -x filter -v"
FIXERS="-w -f next"

2to3 -j 4 $FIXERS . 2>&1 | grep -v RefactoringTool
