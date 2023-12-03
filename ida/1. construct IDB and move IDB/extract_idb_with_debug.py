from __future__ import print_function, division
import os
import shutil
import sys
import time


DIR_BINARY = 'Binaries_with_debug'
DIR_IDB = 'IDB_with_debug'


if not os.path.exists(DIR_IDB):
    os.mkdir(DIR_IDB)

start_time = time.time()

projects = os.listdir(DIR_BINARY)

for p in projects:
    dir_p_idb = os.path.join(DIR_IDB, p)

    if not os.path.exists(dir_p_idb):
        os.mkdir(dir_p_idb)

    p_fs = os.listdir(os.path.join(DIR_BINARY, p))
    for p_f in p_fs:
        # path of elf file
        p_f_path = os.path.join(DIR_BINARY, p, p_f)

        print('Disassembling File {}'.format(p_f_path))
        cmd_disasm = r'ida64 -B {}'.format(p_f_path)
        os.system(cmd_disasm)

end_time = time.time()


print('Time cost:', int(end_time-start_time))

