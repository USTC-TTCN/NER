import os
import json
import logging
from glob import glob
from typing import List
import sentencepiece
from nltk.corpus import words
from utils.utils import split_func_name, split_sentence_piece, merge_suffix
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s| %(levelname)s| %(message)s')


CODE_DIR = "D:/PythonProject/NER/binja/amd64/TRAIN/*.json"
MODEL_PATH = "D:/PythonProject/NER/binja/model/sentencepiece.model"
# MEANINGLESS_FUNC_PATH = "D:/PythonProject/NER/binja/model/meaningless_funcs.txt"
CORPUS_DIR = "D:/PythonProject/NER/binja/amd64/"
SAVE_TYPE = "train"

sp = sentencepiece.SentencePieceProcessor()
sp.load(MODEL_PATH)
vocab = words.words()
# with open(MEANINGLESS_FUNC_PATH,"r",encoding="utf-8") as f:
#     meaningless = [line.strip() for line in f.readlines() if line.strip()]
#
#
# def is_meaningful_name(name:str):
#     for token in meaningless:
#         if name == token:
#             return False
#         if name.startswith(token):
#             return False
#     return True


def my_split_func_name(name):
    return merge_suffix(split_sentence_piece(sp, split_func_name(name)), vocab)


def save(src:List, tgt:List, src_type, set_type):
    with open(os.path.join(CORPUS_DIR,f"src-{set_type}-{src_type}.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(src))
    with open(os.path.join(CORPUS_DIR,f"tgt-{set_type}-{src_type}.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(tgt))


def process_inst(instructions:List[List[str]]) -> str:
    line = ""
    for inst in instructions:
        if "call" == inst[0]: # call \t malloc
            line += " call "+" ".join(my_split_func_name(inst[2]))
        else:
            line += " "+" ".join([token.strip() for token in inst if token.strip()!=""])
    return line


def process_llil(llils:List[List[str]]) -> str:
    line = ""
    for inst in llils:
        if "call" == inst[0]: # call ( malloc )
            line += " call " + " ".join(my_split_func_name(inst[2]))
        elif inst[0].startswith("if"):
            line += " " + " ".join(inst)
        else:
            line += " " + " ".join([token.strip() for token in inst if token.strip() != ""])
    return line

def process_mlil(mlils:List[List[str]]) -> str:
    line = ""
    for inst in mlils:
        line += " " + " ".join([token.strip() for token in inst if token.strip() != ""])
    return line


def process_pc(pseudocode:List[str]) -> str:
    return " ".join(pseudocode)


def process_label(label:str) -> str:
    return " ".join(my_split_func_name(label))


def main(code_path):
    data_inst = []
    data_llil = []
    data_mlil = []
    data_pseudocode = []
    data_label = []
    files = glob(code_path)
    cnt_all = len(files)

    for idx,file in enumerate(files):
        logging.debug(f"[-] inst {idx+1}/{cnt_all} processing {file}")
        with open(file, "r", encoding="utf-8") as f:
            methods = json.load(f)
        for _addr, method in methods.items():
            data_inst.append(process_inst(method["instructions"]))
            data_label.append(process_label(method["name"]))
    logging.debug(f"[+] save to path {CORPUS_DIR}")
    save(data_inst,data_label,src_type="inst",set_type=SAVE_TYPE)
    del data_inst

    for idx,file in enumerate(files):
        logging.debug(f"[-] llil {idx+1}/{cnt_all} processing {file}")
        with open(file, "r", encoding="utf-8") as f:
            methods = json.load(f)
        for _addr, method in methods.items():
            data_llil.append(process_llil(method["llils"]))
            # data_label.append(process_label(method["name"]))
    logging.debug(f"[+] save to path {CORPUS_DIR}")
    save(data_llil,data_label,src_type="llil",set_type=SAVE_TYPE)
    del data_llil

    for idx,file in enumerate(files):
        logging.debug(f"[-] mlil {idx+1}/{cnt_all} processing {file}")
        with open(file, "r", encoding="utf-8") as f:
            methods = json.load(f)
        for _addr, method in methods.items():
            data_mlil.append(process_mlil(method["mlils"]))
            # data_label.append(process_label(method["name"]))
    logging.debug(f"[+] save to path {CORPUS_DIR}")
    save(data_mlil,data_label,src_type="mlil",set_type=SAVE_TYPE)
    del data_mlil

    for idx,file in enumerate(files):
        logging.debug(f"[-] pc {idx+1}/{cnt_all} processing {file}")
        with open(file, "r", encoding="utf-8") as f:
            methods = json.load(f)
        for _addr, method in methods.items():
            data_pseudocode.append(process_pc(method["pseudo_code"]))
            # data_label.append(process_label(method["name"]))
    save(data_pseudocode,data_label,src_type="pc",set_type=SAVE_TYPE)


if __name__ == '__main__':
    main(CODE_DIR)