from __future__ import print_function, division
import os
import shutil
import logging
import sys
import glob


logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(message)s",
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )


DIR_IDB = r'IDB_with_debug'
ida_file = 'ida64'
idb_ext = r'*.i64'

def items_dir(rootname):
    l = []
    for main_dir, _, file_name_list in os.walk(rootname):

        for f in file_name_list:
            file_path = os.path.join(main_dir, f)
            l.append(file_path)
    return l


all_files = items_dir(DIR_IDB)

projects = os.listdir(DIR_IDB)

count_handled_files = 0

for p in projects:

    p_fs = glob.glob(os.path.join(DIR_IDB, p, idb_ext))

    for idb_path in p_fs:

        count_handled_files += 1


        # Extracting Function Name
        logging.info('[{}/{}] Extracting Function Name {}'.format(count_handled_files, len(all_files), idb_path))
        cmd_gen_code = r'{} -S../../ext_func_name_and_addr_idapython.py {}'.format(ida_file, idb_path)
        try:
            os.system(cmd_gen_code)
        except Exception as e:
            logging.error('Error : {}'.format(idb_path))
