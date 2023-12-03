from __future__ import print_function
import os
import sark
import pickle
import joblib
import idc
import ida_nalt
import ida_pro

from collections import namedtuple
from ida_hexrays import decompile, DecompilationFailure


InternalMethod = namedtuple('InternalMethod', ['name', 'start_addr', 'end_addr', 'pseudo_code'])

inputFileName = ida_nalt.get_root_filename()

if idc.get_idb_path().endswith('.i64'):
    cpu_width = 64
else:
    cpu_width = 32


if not os.path.exists('{}.name_and_addr'.format(inputFileName)):
    ida_pro.qexit(0)

if os.path.exists('{}.type_c'.format(inputFileName)):
    file_type = 'C'
elif os.path.exists('{}.type_cplusplus'.format(inputFileName)):
    file_type = 'C++'
else:
    file_type = 'unknown'

method_dict = joblib.load('{}.name_and_addr'.format(inputFileName))

# key: startEA_endEA value: function name
method_dict = dict(
    [('_'.join(map(lambda x:str(x), item[1])), item[0]) for item in method_dict.items()]
    )

all_segments = [seg.name for seg in sark.segments()]
if '.plt' in all_segments:
    plt_segment = sark.Segment(name='.plt')
    plt_funcs = plt_segment.functions
    # replace "." to "_"
    plt_funcs_name = [plt_func.name.replace('.', '_') for plt_func in plt_funcs]
else:
    plt_funcs_name = []

text_segment = sark.Segment(name='.text')
if len(list(text_segment.functions)) == 0:
    ida_pro.qexit(0)

# get functions with unknown names
funcs = list(text_segment.functions)
#funcs = list(filter(lambda x: not x.has_name, funcs))

methods = {}

for func in funcs:
    if '{}_{}'.format(func.start_ea, func.end_ea) not in method_dict.keys():
        continue

    func_name = method_dict['{}_{}'.format(func.start_ea, func.end_ea)]

    if func_name.startswith('sub_'):
        continue
        
    try:
        pseudo_code = str(decompile(func.ea))
        pseudo_code = "\n".join([line.strip() for line in pseudo_code.split('\n') if line != ""])
    except DecompilationFailure:
        continue

    methods[func_name] = InternalMethod(name=func_name, start_addr=func.start_ea, end_addr=func.end_ea, pseudo_code=pseudo_code)

if file_type == 'C':
    pickle.dump(methods, open('{}.pseudo_code_c'.format(inputFileName), 'wb'), protocol=2)
if file_type == 'C++':
    pickle.dump(methods, open('{}.pseudo_code_cplusplus'.format(inputFileName), 'wb'), protocol=2)


ida_pro.qexit(0)