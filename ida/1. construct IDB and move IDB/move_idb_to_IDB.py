import shutil

import os

import sys


DIR_IDB = 'IDB_without_debug'
DIR_BINARY = 'Binaries_without_debug'

if not os.path.exists(DIR_IDB):
    os.mkdir(DIR_IDB)

for p in os.listdir(DIR_BINARY):
    for f in os.listdir(os.path.join(DIR_BINARY, p)):
        if f.endswith('.i64'):
            shutil.move(os.path.join(DIR_BINARY, p, f), os.path.join(DIR_IDB, p, f))