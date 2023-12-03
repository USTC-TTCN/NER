# Lexes "raw_code" strings using a modified version of the Pygments C lexer.
#
# There are two problems with using the base C Lexer from Pygments:
# - Pygments does not lex two-character operators (e.g., >>, ->) as single
#   tokens. This is a problem when tokens are treated as "words".
# - Hex-Rays augments C syntax with the '::' operator borrowed from C++ to
#   reference shadowed global variables. We throw away this operator.

from pygments import lex
from pygments.token import Token
from pygments.token import is_token_subtype
from pygments.lexers.c_cpp import CLexer, inherit, CppLexer


class TokenError(Exception):
    def __init__(self, message):
        self.message = message


class Lexer:
    def __init__(self, raw_code, name_split_func, lexer_cls):
        self.raw_code = raw_code
        self.lexer_cls = lexer_cls
        self.tokens = list(lex(self.raw_code, lexer_cls()))
        self.func = name_split_func

    def get_tokens(self):
        if self.lexer_cls == HexRaysLexer:
            return self.get_tokens_hexrays()
        elif self.lexer_cls == BinJaLexer:
            return self.get_tokens_binja()

    def get_tokens_hexrays(self):
        """Hex-Rays, Generate tokens from a raw_code string, skipping comments.
        """
        previous_string = None
        for (token_type, token) in self.tokens:
            # Pygments breaks up strings into individual tokens representing
            # things like opening quotes and escaped characters. We want to
            # collapse all of these into a single string literal token.
            if previous_string and not is_token_subtype(token_type, Token.String):
                yield (Token.String, f'" {previous_string[1:-1].replace("_"," ")} "')
                previous_string = None
            if is_token_subtype(token_type, Token.String):
                if previous_string:
                    previous_string += token
                else:
                    previous_string = token
            # Normalize function names
            elif token_type == Token.Name.Function:
                if token.startswith('sub_'):
                    yield (token_type, "<FUNCTION>")
                else:
                    yield (token_type, " ".join(self.func(token[:-1]))+" (" ) # split func name
            elif token_type == Token.Name:
                if not token.startswith('a') and not token.startswith('v'):
                    yield (token_type, " ".join(self.func(token))) # split symbol name
                else:
                    yield (token_type, token)
            elif is_token_subtype(token_type, Token.Number):
                if token == "0":
                    yield (token_type, token)
                else:
                    yield (token_type, "<Number>")
            # Skip comments
            elif is_token_subtype(token_type, Token.Comment):
                continue
            # Skip the :: token added by HexRays
            elif is_token_subtype(token_type, Token.Operator) and token == '::':
                continue
            elif not is_token_subtype(token_type, Token.Text):
                yield (token_type, token.strip())
            # Skip whitespace
            elif is_token_subtype(token_type, Token.Text):
                continue
            else:
                raise TokenError(f"No token ({token_type}, {token})")

    def get_tokens_binja(self):
        """BinaryNinja, Generate tokens from a raw_code string, skipping comments.
        """
        previous_string = None
        for (token_type, token) in self.tokens:
            # Pygments breaks up strings into individual tokens representing
            # things like opening quotes and escaped characters. We want to
            # collapse all of these into a single string literal token.
            if previous_string and not is_token_subtype(token_type, Token.String):
                yield (Token.String, f'" {previous_string[1:-1].replace("_"," ")} "')
                previous_string = None
            if is_token_subtype(token_type, Token.String):
                if previous_string:
                    previous_string += token
                else:
                    previous_string = token
            # Normalize function names
            elif token_type == Token.Name.Function:
                if token.startswith('sub_'):
                    yield (token_type, "<FUNCTION>")
                else:
                    yield (token_type, " ".join(self.func(token)))  # split func name
            elif is_token_subtype(token_type, Token.Name):
                if token_type == Token.Name.Var:
                    yield (token_type, "<VARIBLE>")
                elif token_type == Token.Name.RegVar:
                    yield (token_type, token.split("_")[0]) # rax_2 -> rax
                elif token_type == Token.Name.Label:
                    yield (token_type, "<LABEL>")
                elif token_type == Token.Name.Cond:
                    yield (token_type, "<CONDITION>")
                else:
                    yield (token_type, " ".join(self.func(token)))
            elif is_token_subtype(token_type, Token.Number):
                if token == "0":
                    yield (token_type, token)
                else:
                    yield (token_type, "<Number>")
            # Skip comments
            elif is_token_subtype(token_type, Token.Comment):
                continue
            # Skip the :: token added by HexRays
            elif is_token_subtype(token_type, Token.Operator) and token == '::':
                continue
            elif not is_token_subtype(token_type, Token.Text):
                yield (token_type, token.strip())
            # Skip whitespace
            elif is_token_subtype(token_type, Token.Text):
                continue
            else:
                raise TokenError(f"No token ({token_type}, {token})")



class HexRaysLexer(CLexer):
    # Additional tokens
    tokens = {
        'statements' : [
            (r'->', Token.Operator),
            (r'\+\+', Token.Operator),
            (r'--', Token.Operator),
            (r'==', Token.Operator),
            (r'!=', Token.Operator),
            (r'>=', Token.Operator),
            (r'<=', Token.Operator),
            (r'&&', Token.Operator),
            (r'\|\|', Token.Operator),
            (r'\+=', Token.Operator),
            (r'-=', Token.Operator),
            (r'\*=', Token.Operator),
            (r'/=', Token.Operator),
            (r'%=', Token.Operator),
            (r'&=', Token.Operator),
            (r'\^=', Token.Operator),
            (r'\|=', Token.Operator),
            (r'<<=', Token.Operator),
            (r'>>=', Token.Operator),
            (r'<<', Token.Operator),
            (r'>>', Token.Operator),
            (r'\.\.\.', Token.Operator),
            (r'##', Token.Operator),
            (r'::', Token.Operator),
            (r'_?[Q|D|LO|HI]?WORD', Token.Keyword.Type),
            (r'_?[LO|HI]?BYTE', Token.Keyword.Type),
            (r'_?[LONG]?LONG', Token.Keyword.Type),
            (r'sub_[A-F0-9]+', Token.Name.Function),
            (r'\w+\(', Token.Name.Function),
            inherit
        ],
    }


class BinJaLexer(CLexer):
    # Additional tokens
    tokens = {
        'statements' : [
            (r'->', Token.Operator),
            (r'\+\+', Token.Operator),
            (r'--', Token.Operator),
            (r'==', Token.Operator),
            (r'!=', Token.Operator),
            (r'>=', Token.Operator),
            (r'<=', Token.Operator),
            (r'&&', Token.Operator),
            (r'\|\|', Token.Operator),
            (r'\+=', Token.Operator),
            (r'-=', Token.Operator),
            (r'\*=', Token.Operator),
            (r'/=', Token.Operator),
            (r'%=', Token.Operator),
            (r'&=', Token.Operator),
            (r'\^=', Token.Operator),
            (r'\|=', Token.Operator),
            (r'<<=', Token.Operator),
            (r'>>=', Token.Operator),
            (r'<<', Token.Operator),
            (r'>>', Token.Operator),
            (r'\.\.\.', Token.Operator),
            (r'##', Token.Operator),
            (r'::', Token.Operator),
            (r'sub_[A-F0-9]+', Token.Name.Function),
            (r'cond:\w+', Token.Name.Cond),
            (r'label_\w+', Token.Name.Label),
            (r'var_\w+', Token.Name.Var),
            (r'data_\w+', Token.Name.Var),
            (r'(r|e)[a-z0-9]{1,2}([_][\d]+)', Token.Name.RegVar),
            (r'[u]?int[0-9]*_t', Token.Keyword.Type),
            inherit
        ],
    }

def tokenize_raw_code(raw_code, func, flag_string=True, flag_call=True):
    return tokenize_raw_code_hexray(raw_code, func, flag_string, flag_call)

def tokenize_raw_code_hexray(raw_code, func, keep_string=True, keep_call=True):
    lexer = Lexer(raw_code, func, HexRaysLexer)
    tokens = []
    for token_type, token in lexer.get_tokens():
        if not keep_call: # erase the function call
            if token_type == Token.Name.Function:
                if token != "<FUNCTION>":
                    token = "<FUNCTION> ("
        if not keep_string: # erase the string
            if token_type == Token.String:
                token = "<STRING>"
        tokens.append(token)
    return tokens


def tokenize_raw_code_binja(raw_code, func, keep_string=True, keep_call=True):
    lexer = Lexer(raw_code, func, BinJaLexer)
    tokens = []
    func_def_flag = True
    func_def_name = ""
    for token_type, token in lexer.get_tokens():
        if func_def_flag and token_type == Token.Name.Function:
            func_def_name = token
            token = "<FUNCTION>"
            func_def_flag = False
        if token_type == Token.Name and token == func_def_name: # remove the label
            token = "<FUNCTION>"
        if not keep_call: # erase the function call
            if token_type == Token.Name.Function:
                if token != "<FUNCTION>":
                    token = "<FUNCTION>"
        if not keep_string: # erase the string
            if token_type == Token.String:
                token = "<STRING>"
        tokens.append(token)
    return tokens


if __name__ == '__main__':
    with open("binja_pseudocode_demo.txt", "r", encoding="utf-8") as f:
        code = f.read()
    code = "\n".join([line.strip() for line in code.split("\n") if line.strip() != ""])
    print(" ".join(tokenize_raw_code_binja(code, func=lambda x:x.split('_'), keep_string=True, keep_call=True)))