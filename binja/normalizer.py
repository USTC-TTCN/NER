from typing import List
from binaryninja.architecture import InstructionTextToken, InstructionTextTokenType
from utils.utils import split_func_name

NUM_THRESHOLD = 0x0

def normalize_instruction(func, bv, symbol_maps: dict) -> List[List[str]]:
    tstart = bv.sections['.text'].start
    tend = bv.sections['.text'].end

    fstart = func.lowest_address
    fend = func.highest_address

    instructions: List[List[InstructionTextToken]] = list(func.instructions)
    nlzed_instructions = []
    for (inst, addr) in instructions:
        nlzed_inst = []
        for token in inst:
            if token.type in [InstructionTextTokenType.CodeRelativeAddressToken,
                              InstructionTextTokenType.PossibleAddressToken]:
                if token.value in symbol_maps:
                    nlzed_inst.append(symbol_maps[token.value])
                elif token.value >= fstart and token.value <= fend:
                    nlzed_inst.append("<LOCADDR>")
                elif token.value >= tstart and token.value <= tend:
                    nlzed_inst.append("<INTERADDR>")
                else:
                    nlzed_inst.append("<ADDR>")
            elif token.type == InstructionTextTokenType.IntegerToken:
                if token.value > NUM_THRESHOLD:
                    nlzed_inst.append("<NUM>")
                else:
                    nlzed_inst.append(str(token))
            else:
                nlzed_inst.append(str(token))
        nlzed_instructions.append(nlzed_inst)
    return nlzed_instructions


def normalize_LLIL(func, bv, symbol_maps: dict) -> List[List[str]]:
    tstart = bv.sections['.text'].start
    tend = bv.sections['.text'].end

    fstart = func.lowest_address
    fend = func.highest_address

    llils = list(func.llil.instructions)
    nlzed_llils = []
    for llil in llils:
        nlzed_llil = []
        for token in llil.tokens:  # type(token)==InstructionTextToken
            if token.type in [InstructionTextTokenType.CodeRelativeAddressToken,
                              InstructionTextTokenType.PossibleAddressToken]:
                if token.value in symbol_maps:
                    nlzed_llil.append(symbol_maps[token.value])
                elif token.value >= fstart and token.value <= fend:
                    nlzed_llil.append("<LOCADDR>")
                elif token.value >= tstart and token.value <= tend:
                    nlzed_llil.append("<INTERADDR>")
                else:
                    nlzed_llil.append("<ADDR>")
            elif token.type == InstructionTextTokenType.IntegerToken:
                if token.value > NUM_THRESHOLD:
                    nlzed_llil.append("<NUM>")
                else:
                    nlzed_llil.append(str(token))
            else:
                nlzed_llil.append(str(token))
        nlzed_llils.append(nlzed_llil)
    return nlzed_llils


def normalize_MLIL(func, bv, symbol_maps: dict) -> List[List[str]]:
    tstart = bv.sections['.text'].start
    tend = bv.sections['.text'].end

    fstart = func.lowest_address
    fend = func.highest_address

    mlils = list(func.mlil.instructions)
    nlzed_mlils = []
    for mlil in mlils:
        nlzed_mlil = []
        for token in mlil.tokens:  # type(token)==InstructionTextToken
            if token.type in [InstructionTextTokenType.CodeRelativeAddressToken,
                              InstructionTextTokenType.PossibleAddressToken]:
                if token.value in symbol_maps:
                    nlzed_mlil.append(symbol_maps[token.value])
                elif token.value >= fstart and token.value <= fend:
                    nlzed_mlil.append("<LOCADDR>")
                elif token.value >= tstart and token.value <= tend:
                    nlzed_mlil.append("<INTERADDR>")
                else:
                    nlzed_mlil.append("<ADDR>")
            elif token.type == InstructionTextTokenType.IntegerToken:
                if token.value > NUM_THRESHOLD:
                    nlzed_mlil.append("<NUM>")
                else:
                    nlzed_mlil.append(str(token))
            elif token.type == InstructionTextTokenType.StringToken:
                nlzed_mlil.append(str(token).replace("\""," \" ").replace("_"," ").strip())
            else:
                nlzed_mlil.append(str(token))
        nlzed_mlils.append(nlzed_mlil)
    return nlzed_mlils