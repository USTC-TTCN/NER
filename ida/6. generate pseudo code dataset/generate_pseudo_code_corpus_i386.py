import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.realpath(__file__), "..", "..")))
import joblib
import random
import sentencepiece as spm
from utils.utils import split_func_name, split_sentence_piece, merge_suffix, md5
from utils.lexer import tokenize_raw_code
from collections import namedtuple
from nltk.corpus import words
from glob import glob


DIR_CODE = 'i386_pseudo_code'
CODE_EXT = '*.pseudo_code_c'
TRAIN,VALID,TEST = 0.8,0.1,0.1


InternalMethod = namedtuple('InternalMethod', ['name', 'start_addr', 'end_addr', 'pseudo_code'])
sp = spm.SentencePieceProcessor()
sp.load(os.path.join('model', 'sentencepiece.model'))
vocab = words.words()

files = []
projects = os.listdir(DIR_CODE)
for p in projects:
    dir_p_mname = os.path.join(DIR_CODE, p)
    files.extend(glob(os.path.join(DIR_CODE, p, CODE_EXT)))


def my_split_func_name(name):
    return merge_suffix(split_sentence_piece(sp, split_func_name(name)), vocab)


for idx, file in enumerate(files):
    method_names = []
    method_bodies = []
    # method_library_funcs = []
    if idx % 1 == 0:
        print("{}/{}, {}".format(idx, len(files), file))

    try:
        methods = joblib.load(file)

        for m in methods.values():
            pseudo_code = m.pseudo_code
            if m.name in pseudo_code:  # erase func name in pseudo code
                pseudo_code = pseudo_code.replace(m.name, "sub_0")
            # add item into dataset
            body = "\n".join([line.strip() for line in pseudo_code.split('\n') if line != ""])
            body_token_list = tokenize_raw_code(body, my_split_func_name)
            method_names.append(my_split_func_name(m.name))
            method_bodies.append(body_token_list)
    except Exception as e:
        os.system('echo "{} {}" >> {}-error.txt'.format(file, str(e), DIR_CODE))

    method_names = list(map(lambda x: ' '.join(x), method_names))
    method_bodies = list(map(lambda x: ' '.join(x), method_bodies))

    method_names = list(map(lambda x: x.replace('\r', ''), method_names))
    method_bodies = list(map(lambda x: x.replace('\r', ''), method_bodies))

    assert len(method_names) == len(method_bodies)

    with open('i386-src-all.txt', 'a+', encoding='utf-8') as f:
        f.write('\n'.join(method_bodies))
        f.write("\n")
    with open('i386-tgt-all.txt', 'a+', encoding='utf-8') as f:
        f.write('\n'.join(method_names))
        f.write("\n")

# read out
input("type any key to continue, distinct data, may need huge memory.")
with open('i386-src-all.txt', 'r', encoding='utf-8') as f:
    method_bodies = f.readlines()
with open('i386-tgt-all.txt', 'r', encoding='utf-8') as f:
    method_names = f.readlines()
count = len(method_names)
print('Original count: ', count)


# distinct
method_hashes = [md5('|'.join(mn)) for mn in zip(method_names, method_bodies)]

hash_index_map = dict(zip(method_hashes, range(len(method_hashes))))

distincted_method_names = []
distincted_method_bodies = []

for v in hash_index_map.values():
    distincted_method_names.append(method_names[v])
    distincted_method_bodies.append(method_bodies[v])
count = len(distincted_method_names)
print('Distinct: ', count)


# shuffle and save to files
random.seed(233)
random.shuffle(distincted_method_names)
random.seed(233)
random.shuffle(distincted_method_bodies)
train,valid = int(TRAIN*count), int(TRAIN*count)+int(VALID*count)
with open("i386-tgt-train.txt", "w", encoding="utf-8") as f:
    for i in range(train):
        f.write(distincted_method_names[i])
with open("i386-src-train.txt", "w", encoding="utf-8") as f:
    for i in range(train):
        f.write(distincted_method_bodies[i])
with open("i386-tgt-valid.txt", "w", encoding="utf-8") as f:
    for i in range(train, valid):
        f.write(distincted_method_names[i])
with open("i386-src-valid.txt", "w", encoding="utf-8") as f:
    for i in range(train, valid):
        f.write(distincted_method_bodies[i])
with open("i386-tgt-test.txt", "w", encoding="utf-8") as f:
    for i in range(valid, count):
        f.write(distincted_method_names[i])
with open("i386-src-test.txt", "w", encoding="utf-8") as f:
    for i in range(valid, count):
        f.write(distincted_method_bodies[i])
