# -*- coding: UTF-8 -*-
import logging
import os
import sys
import time
import torch
import datetime
import pickle


# parameters need define and you also need modify in main()
load_summarization = False
summarization_path = '../summarization.txt'
vocab_path = './processed/data-pc.vocab.pt'
tgt_path = "./test/tgt-test-len3000.txt"
src_path = "./test/src-test-len3000.txt"
# speed up data loading
vocab_pickle_path = vocab_path+".pkl"
summarization_pickle_path = summarization_path+".pkl"


def read_vocab(path):
    '''
    read vocab file for OpenNMT-py 2.2.0+, in this version vocab in a text file with line like: "set	91064\n"
    '''
    vocab = []
    with open(path, "r") as f:
        lines = f.readlines()
        for line in lines:
            vocab.append(line.split("\t")[0])
    return vocab


if vocab_path.endswith(".pt"): # ONMT<=1.2.0
    vocab_fields = torch.load(vocab_path)
    vocab = vocab_fields["tgt"].base_field.vocab.stoi.keys() # variable vocab is all word in vocab.
elif os.path.exists(vocab_pickle_path): # exist cache
    # load from pkl
    with open(vocab_pickle_path, "rb") as f:
        vocab = pickle.load(f)
else: # not exist cache
    vocab = read_vocab(vocab_path)
    # save to pkl
    with open(vocab_pickle_path, "wb") as f:
        pickle.dump(vocab,f)
print('vocab size: ', len(vocab))


if load_summarization:
    if os.path.exists(summarization_pickle_path):
        # load from pkl
        with open(summarization_pickle_path, "rb") as f:
           summarization_list = pickle.load(f)
    else:
        with open(summarization_path, 'r', encoding='utf-8') as f:
            content = f.read().split('\n')
        summarization_list = list(map(lambda x: x.split(','), content))
        # save to pkl
        with open(summarization_pickle_path, "wb") as f:
            pickle.dump(summarization_list,f)


def get_aprf(preds:list, refs:list):

    assert len(preds) == len(refs)
    
    accs = []
    precisions = []
    recalls = []
    f1s = []
    for p, r in zip(preds, refs):

        p_tokens = p.split(' ')
        r_tokens = r.split(' ')


        r_tokens = list(filter(lambda x: x in vocab, r_tokens))
        if len(r_tokens) == 0:
            continue

        if load_summarization:
            r_tokens_extend = []
            for r_t in r_tokens:
                r_tokens_extend.append(r_t)
                for summ_l in summarization_list:
                    if r_t in summ_l:
                        r_tokens_extend.extend(summ_l)
            r_tokens_extend = list(set(r_tokens_extend))

            acc = len([x for x in p_tokens if x in r_tokens_extend]) / len(p_tokens)

            precision = sum([1 if p_t in r_tokens_extend else 0 for p_t in p_tokens]) / len(p_tokens)
            recall = sum([1 if p_t in r_tokens_extend else 0 for p_t in p_tokens]) / len(r_tokens)

        else:
            acc = len([x for x in p_tokens if x in r_tokens]) / len(p_tokens)

            precision = sum([1 if p_t in r_tokens else 0 for p_t in p_tokens]) / len(p_tokens)
            recall = sum([1 if p_t in r_tokens else 0 for p_t in p_tokens]) / len(r_tokens)

            # precision = sum([1 if p_t in r_tokens else 0 for p_t in p_tokens]) / (sum([1 if p_t in r_tokens else 0 for p_t in p_tokens]) + sum([1 if p_t not in r_tokens else 0 for p_t in p_tokens]))
            # recall = sum([1 if p_t in r_tokens else 0 for p_t in p_tokens]) / (sum([1 if p_t in r_tokens else 0 for p_t in p_tokens]) + sum([1 if r_t not in p_tokens else 0 for r_t in r_tokens]))

        f1 = 2*precision*recall / (precision+recall+0.0001)

        accs.append(acc)
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)


    avg_accuracy = sum(accs) / len(accs)
    avg_precision = sum(precisions) / len(precisions)
    avg_recall = sum(recalls) / len(recalls)
    avg_f1 = sum(f1s) / len(f1s)

    return {'accuracy': avg_accuracy,'precision':avg_precision, 'recall':avg_recall, 'f1':avg_f1}


def print_result(pred_path=None, tgt_path=None):
    if not pred_path or not tgt_path:
        logger.error("undefine result txt path")
        return

    with open(tgt_path, 'r', encoding='utf-8') as f:
        refs = f.read().split('\n')
    with open(pred_path, 'r', encoding='utf-8') as f:
        preds = f.read().split('\n')

    if refs[-1] == '':
        refs = refs[:-1]

    if preds[-1] == '':
        preds = preds[:-1]

    print(len(preds), len(refs))

    remove_index = []
    for i, s in enumerate(zip(refs, preds)):
        if s[0] == '' or s[1] == '':
            remove_index.append(i)

    for i in remove_index[::-1]:
        refs.pop(i)
        preds.pop(i)

    print(len(preds), len(refs))

    metrics = get_aprf(preds, refs)

    logger.info('A: {}'.format(metrics['accuracy']))
    logger.info('P: {}'.format(metrics['precision']))
    logger.info('R: {}'.format(metrics['recall']))
    logger.info('F: {}'.format(metrics['f1']))



if __name__ == '__main__':
    gpu_idx = 0
    try:
        model_name = sys.argv[1]
    except:
        print("[!]need model name as parameter!")
        exit(-1)
    try:
        gpu_idx = sys.argv[2]
    except:
        pass

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()

    fh = logging.FileHandler("evaluate_test_{}.log".format(model_name))
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    time_start = time.time()
    for i in range(10000,1000001,10000):
        cmd = "onmt_translate -model models/{0}_step_{1}.pt -src {5} -output results/pred_test_{2}_step_{3}.txt -min_length 1 -max_length 30 -beam_size 10 -batch_size 16 -n_best 1 -gpu {4}".format(model_name,i,model_name,i,gpu_idx,src_path)
        if not os.path.exists("models/{0}_step_{1}.pt".format(model_name,i)):
            continue
        logger.info("[+]start cmd: {}".format(cmd))
        os.system(cmd)
        logger.info("[+]finish cmd: {}".format(cmd))
        print_result("results/pred_test_{0}_step_{1}.txt".format(model_name,i),tgt_path)
    time_end = time.time()
    time_cost = int(time_end - time_start)
    time_cost = str(datetime.timedelta(seconds=time_cost))
    print("[+]evaluate done, use {}".format(time_cost))
