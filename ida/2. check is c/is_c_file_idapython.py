from __future__ import print_function
import sark
import pickle
import idc
import sys


inputFileName = idc.GetInputFile()

text_segment = sark.Segment(name='.text')
if len(list(text_segment.functions)) == 0:
    idc.Exit(0)

# check whether cplusplus file
func_names = [func.demangled for func in text_segment.functions]

is_c_file = True

for func_name in func_names:
    if '::' in func_name or '(' in func_name:
        is_c_file = False
        break

if is_c_file:
    open('{}.type_c'.format(inputFileName), 'w')
else:
    open('{}.type_cplusplus'.format(inputFileName), 'w')

idc.Exit(0)
