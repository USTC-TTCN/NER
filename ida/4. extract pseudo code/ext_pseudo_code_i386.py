from __future__ import print_function, division
import os
import shutil
import logging
import sys
import glob
import time
from multiprocessing import Pool, Queue, Process, cpu_count


logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(message)s",
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )


DIR_IDB = 'i386_idb'
DIR_CODE = 'i386_pseudo_code'
IDB_EXT = r'*.idb'
PSEUDO_CODE_EXT = ".pseudo_code_c"
IDA_FILE = 'ida'
IDAPYTHON_PATH = "<full path to>ext_pseudo_code_idapython.py"


if not os.path.exists(DIR_CODE):
    os.mkdir(DIR_CODE)

def process(p_fs, process_id=0):
    count_handled_files = 0
    for idb_path in p_fs:
        count_handled_files += 1
        # Extracting Function Name
        logging.debug('[t{}]{}/{} Extracting {}'.format(\
            process_id, count_handled_files, len(p_fs), idb_path))
        cmd_gen_code = r'{} -A -S{} {}'.format(IDA_FILE, IDAPYTHON_PATH, idb_path)
        os.system(cmd_gen_code)

def process_queue(file_queue, process_id=0):
    while not file_queue.empty():
        idb_file = file_queue.get()
        remain_count = file_queue.qsize()
        # Extracting Function Name
        logging.debug('[t{}]remain {} Extracting {}'.format(process_id, remain_count, idb_file))
        cmd_gen_code = r'{} -A -S{} {}'.format(IDA_FILE, IDAPYTHON_PATH, idb_file)
        os.system(cmd_gen_code)

def split_list(alist, wanted_parts):
    length = len(alist)
    return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts] for i in range(wanted_parts) ]

def multi_process(files):
    threads = cpu_count()//2
    filelists = split_list(list(files), threads)
    pool = Pool(threads)
    for idx, filelist in enumerate(filelists):
        pool.apply_async(process, (filelist,idx,))
    pool.close()
    pool.join()

def multi_process_queue(files):
    threads = cpu_count()//2
    queue = Queue()
    for f in files:
        queue.put(f)
    processes = [Process(target=process_queue, args=(queue, i)) for i in range(threads)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()


if __name__ == '__main__':
    start_time = time.time()

    projects = os.listdir(DIR_IDB)

    all_p_fs = []

    for p in projects:
        dir_p_mname = os.path.join(DIR_CODE, p)

        if not os.path.exists(dir_p_mname):
            os.mkdir(dir_p_mname)
        for f in glob.glob(os.path.join(DIR_IDB, p, IDB_EXT)):
            if os.path.exists(f[:-4]+PSEUDO_CODE_EXT) \
                and os.path.getsize(f[:-4]+PSEUDO_CODE_EXT)!=0: 
                continue # skip if already generated
            all_p_fs.append(f)

    # single process
    # process(all_p_fs)

    # multi process
    multi_process_queue(all_p_fs)

    end_time = time.time()

    logging.debug('Time cost: {}s'.format(int(end_time-start_time)))