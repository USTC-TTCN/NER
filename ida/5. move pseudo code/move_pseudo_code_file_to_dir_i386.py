import shutil
import os
import sys

DIR_IDB = 'i386_idb'
DIR_CODE = 'i386_pseudo_code'

for p in os.listdir(DIR_IDB):
    for f in os.listdir(os.path.join(DIR_IDB, p)):
        if f.endswith('.pseudo_code_c'):
            shutil.move(os.path.join(DIR_IDB, p, f), os.path.join(DIR_CODE, p, f))