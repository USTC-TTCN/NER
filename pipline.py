# -*- coding: UTF-8 -*-
'''
@desc: generate eval file for eval
'''
import json
from tqdm import tqdm
import sentencepiece
from nltk.corpus import words
from binja.utils.utils import split_func_name, split_sentence_piece, merge_suffix
from binja.utils.lexer import tokenize_raw_code_hexray
from typing import List

MODEL_PATH = "./data/binja/model/sentencepiece.model"
sp = sentencepiece.SentencePieceProcessor()
sp.load(MODEL_PATH)
vocab = words.words()
def my_split_func_name(name):
    return merge_suffix(split_sentence_piece(sp, split_func_name(name)), vocab)

def save(src:List, tgt:List, src_type, set_type):
    with open(f"src-{set_type}-{src_type}.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(src))
    with open(f"tgt-{set_type}-{src_type}.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(tgt))


def pipline_for_eval(raw_pcode:str, func_name:str):
    '''
    raw_pcode is like: "size_t __fastcall <FUNCTION>(wchar_t *pwc, char *s, size_t a3, mbstate_t *a4)\n{\n  size_t v4; // rbx\n  wchar_t *v5; // r12\n  char *v6; // rbp\n  char v8; // [rsp+Ch] [rbp-1Ch] BYREF\n\n  if ( !s )\n  {\n    a3 = 1LL;\n    v6 = (_BYTE *)(\"%s: invalid option -- '%c'\\n\" + 27);\nLABEL_7:\n    v5 = (wchar_t *)&v8;\n    goto LABEL_4;\n  }\n  v4 = -2LL;\n  if ( !a3 )\n    return v4;\n  v5 = pwc;\n  v6 = s;\n  if ( !pwc )\n    goto LABEL_7;\nLABEL_4:\n  v4 = mbrtowc(v5, v6, a3, a4);\n  if ( v4 > 0xFFFFFFFFFFFFFFFDLL && !(unsigned __int8)sub_4098C0(0LL) )\n  {\n    v4 = 1LL;\n    *v5 = (unsigned __int8)*v6;\n  }\n  return v4;\n}\n"
    '''
    if func_name in raw_pcode:
        raw_pcode = raw_pcode.replace(func_name, "<FUNCTION>")
    pseudo_code = tokenize_raw_code_hexray(raw_pcode, my_split_func_name)
    pseudo_code = " ".join(pseudo_code).replace(" < function > ( ", " <FUNCTION> ( ") # fix it
    split_name = my_split_func_name(func_name)
    split_name = " ".join(split_name)
    return pseudo_code, split_name


if __name__ == "__main__":
    src,tgt = [],[]
    # each item in dataset is a dict storing pseudo code and function name
    with open("./dataset.json", "r", encoding="utf-8") as f:
        for data in tqdm(json.load(f), desc="processing"):
            pseudo_code = data['pcode']
            func_name = data['func_name']
            pseudo_code, split_name = pipline_for_eval(pseudo_code, func_name)
            src.append(pseudo_code)
            tgt.append(split_name)
    save(src, tgt, "eval", "pc")
