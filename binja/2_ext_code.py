import os
import logging
import pickle
from glob import glob
from binaryninja import *
import sentencepiece
from nltk.corpus import words
from binaryninja.function import DisassemblySettings, DisassemblyOption
from multiprocessing import Pool, cpu_count, set_start_method

from normalizer import normalize_instruction, normalize_LLIL, normalize_MLIL
from utils.utils import split_func_name, split_sentence_piece, merge_suffix
from utils.lexer import tokenize_raw_code_binja
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s| %(levelname)s| %(message)s')


BIN_DIR = "D:/PythonProject/NER/binja/amd64/*"
MODEL_PATH = "D:/PythonProject/NER/binja/model/sentencepiece.model"
MEANINGLESS_FUNC_PATH = "D:/PythonProject/NER/binja/model/meaningless_funcs.txt"
FILTER_MEANINGLESS = True # slightly slow the speed

sp = sentencepiece.SentencePieceProcessor()
sp.load(MODEL_PATH)
vocab = words.words()
with open(MEANINGLESS_FUNC_PATH,"r",encoding="utf-8") as f:
    meaningless = [line.strip() for line in f.readlines() if line.strip()]


def is_meaningful_name(name:str):
    for token in meaningless:
        if name == token:
            return False
        if name.startswith(token):
            return False
    return True


def my_split_func_name(name):
    return merge_suffix(split_sentence_piece(sp, split_func_name(name)), vocab)


def get_pseudo_c(func, bv):
    lines = ''
    settings = DisassemblySettings()
    settings.set_option(DisassemblyOption.ShowAddress, False)
    settings.set_option(DisassemblyOption.WaitForIL, True)
    obj = lineardisassembly.LinearViewObject.language_representation(bv, settings)
    cursor_end = lineardisassembly.LinearViewCursor(obj)
    cursor_end.seek_to_address(func.highest_address)
    body = bv.get_next_linear_disassembly_lines(cursor_end)
    cursor_end.seek_to_address(func.highest_address)
    header = bv.get_previous_linear_disassembly_lines(cursor_end)
    for line in header:
        lines += str(line) + '\n'
    for line in body:
        lines += str(line) + '\n'
    return lines


def get_startaddr_name_maps(file, filter_meaningless=False):
    '''
    get startaddr_name_maps from pickle file,
    and filter or not filter meaningless function name
    '''
    with open(f"{file}.name_and_addr", 'rb') as f:
        name_addr_maps = pickle.load(f)
    addr_name_maps = {}
    for k, v in name_addr_maps.items(): # funcname -> [addr1,addr2]
        if filter_meaningless and not is_meaningful_name(k):
            continue
        addr_name_maps[v[0]] = k
    return addr_name_maps


def filter_binary_file(files):
    res = []
    for file in files:
        if file.endswith(".name_and_addr") or file.endswith(".bndb") or file.endswith(".json"):
            continue
        res.append(file)
    return res


def main(binaries_path):
    files = filter_binary_file(glob(binaries_path))
    cnt_all = len(files)
    for idx, file in enumerate(files):
        # do not overwrite json file
        if os.path.exists(file+".json") and os.path.getsize(file+".json") > 0:
            logging.debug(f"[-] {file}.json already exists")
            continue
        if not os.path.exists(file+".name_and_addr"):
            logging.error(f"[!] {file}.name_and_addr not exists")
            continue

        logging.debug(f"[-] {idx+1}/{cnt_all} processing {file}")

        startaddr_name_maps = get_startaddr_name_maps(file,filter_meaningless=FILTER_MEANINGLESS)

        if os.path.exists(file+".bndb"):
            bv = BinaryViewType.get_view_of_file(file+".bndb")
        else:
            bv = BinaryViewType.get_view_of_file(file)
        if '.text' not in bv.sections:
            continue
        # get symbols
        symbol_maps = {}
        for sym in bv.get_symbols():
            symbol_maps[sym.address] = " ".join(my_split_func_name(sym.full_name))

        tstart = bv.sections['.text'].start
        tend = bv.sections['.text'].end

        methods = {}
        for idx,func in enumerate(bv.functions):
            if not (func.lowest_address >= tstart and func.highest_address <= tend):
                continue
            if func.lowest_address not in startaddr_name_maps:
                continue
            if func is not None and func.analysis_skipped:
                continue
                # force analysis large function
                # func.analysis_skip_override = FunctionAnalysisSkipOverride.NeverSkipFunctionAnalysis
                # bv.update_analysis_and_wait()
            addr = f"{func.lowest_address}_{func.highest_address}"
            name = startaddr_name_maps[func.lowest_address]
            instructions = normalize_instruction(func,bv,symbol_maps)
            llils = normalize_LLIL(func,bv,symbol_maps)
            mlils = normalize_MLIL(func, bv, symbol_maps)
            pseudo_code = tokenize_raw_code_binja(get_pseudo_c(func, bv),
                                            my_split_func_name)
            methods[addr] = {
                "start_addr": func.lowest_address,
                "addr": addr,
                "name": name,
                "instructions": instructions,
                "llils": llils,
                "mlils": mlils,
                "pseudo_code": pseudo_code
            }

        # save func to file
        with open(f"{file}.json", 'w', encoding="utf-8") as f:
            json.dump(methods, f, indent=4)
        logging.debug(f"[-] save {file}.json, {len(methods)} functions")

        # save bndb
        bv.create_database(f"{file}.bndb")
        logging.debug(f"[-] save {file}.bndb")


def spawn(file, logprogress):
    logging.debug(f"[-] {logprogress} processing {file}")
    # do not overwrite json file
    if os.path.exists(file + ".json") and os.path.getsize(file + ".json") > 0:
        logging.debug(f"[-] {file}.json already exists")
        return
    if not os.path.exists(file + ".name_and_addr"):
        logging.error(f"[!] {file}.name_and_addr not exists")
        return

    startaddr_name_maps = get_startaddr_name_maps(file,filter_meaningless=FILTER_MEANINGLESS)

    binaryninja.set_worker_thread_count(1)
    if os.path.exists(file + ".bndb"):
        bv = BinaryViewType.get_view_of_file(file + ".bndb")
    else:
        bv = BinaryViewType.get_view_of_file(file)

    if '.text' not in bv.sections:
        return
    # get symbols
    symbol_maps = {}
    for sym in bv.get_symbols():
        symbol_maps[sym.address] = " ".join(my_split_func_name(sym.full_name))

    tstart = bv.sections['.text'].start
    tend = bv.sections['.text'].end

    methods = {}
    for idx, func in enumerate(bv.functions):
        if not (func.lowest_address >= tstart and func.highest_address <= tend):
            continue
        if func.lowest_address not in startaddr_name_maps:
            continue
        if func is not None and func.analysis_skipped:
            continue
            # force analysis large function
            # func.analysis_skip_override = FunctionAnalysisSkipOverride.NeverSkipFunctionAnalysis
            # bv.update_analysis_and_wait()
        addr = f"{func.lowest_address}_{func.highest_address}"
        name = startaddr_name_maps[func.lowest_address]
        instructions = normalize_instruction(func, bv, symbol_maps)
        llils = normalize_LLIL(func, bv, symbol_maps)
        mlils = normalize_MLIL(func, bv, symbol_maps)
        pseudo_code = tokenize_raw_code_binja(get_pseudo_c(func, bv),
                                              my_split_func_name)
        methods[addr] = {
            "start_addr": func.lowest_address,
            "addr": addr,
            "name": name,
            "instructions": instructions,
            "llils": llils,
            "mlils": mlils,
            "pseudo_code": pseudo_code
        }

    # save func to file
    with open(f"{file}.json", 'w', encoding="utf-8") as f:
        json.dump(methods, f, indent=4)
    logging.debug(f"[-] save {file}.json, {len(methods)} functions")

    # save bndb
    bv.create_database(f"{file}.bndb")
    logging.debug(f"[-] save {file}.bndb")


def multi_thread_main(binaries_path):
    files = filter_binary_file(glob(binaries_path))
    cnt_all = len(files)

    set_start_method("spawn")
    processes = cpu_count() // 2 if cpu_count() > 1 else 1
    pool = Pool(processes=processes)
    results = []
    for idx, file in enumerate(files):
        results.append(pool.apply_async(spawn, (file, f"{idx + 1}/{cnt_all}",)))
    pool.close()
    pool.join()

if __name__ == '__main__':
    # main(BIN_DIR)

    multi_thread_main(BIN_DIR)

