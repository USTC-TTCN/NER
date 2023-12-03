from __future__ import print_function
import sark
import pickle
import idc
import sys

inputFileName = idc.GetInputFile()

text_segment = sark.Segment(name='.text')
if len(list(text_segment.functions)) == 0:
    idc.Exit(0)


methods = dict()

for func in text_segment.functions:
    methods[func.demangled] = [func.startEA, func.endEA]

pickle.dump(methods, open('{}.name_and_addr'.format(inputFileName), 'wb'), protocol=2)

idc.Exit(0)
