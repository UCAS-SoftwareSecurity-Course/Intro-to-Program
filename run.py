#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: h1k0
# Created: 2023-05-17

import sys
import os
import textwrap
import pathlib
import tree_sitter
import subprocess
import readline
import glob
import difflib
import signal
import time
import tempfile
import lief
import hashlib
from tree_sitter import Language, Parser
from typing import List, Dict, Tuple

original_print = print
def sanitized_print(*args, **kwargs):
    dangerous = "sesame{"
    for arg in args:
        if type(arg) == str:
            if dangerous in arg:
                print("[-] being naughty? try harder")
                sys.exit(1)
    
    for key, value in kwargs.items():
        if type(value) == str:
            if dangerous in value:
                print("[-] being naughty? try harder")
                sys.exit(1)
    
    original_print(*args, **kwargs)

print = sanitized_print

def completer(text, state):
    text = text.replace("~", os.path.expanduser("~"))
    return (glob.glob(text+'*')+[None])[state]

# Change autocomplete settings
readline.set_completer_delims('\t')
readline.parse_and_bind("tab: complete")
readline.set_completer(completer)

config = (pathlib.Path(__file__).parent / ".config").read_text().strip()
level = int(config)

description = textwrap.dedent

def get_sesame():
    # just like read flag
    sesame = pathlib.Path("../../flag").read_text().strip()
    os.write(1, f"{sesame}\n".encode())

def current_field_name(node: tree_sitter.Node) -> str:
    """
    Get the field name of a `node`. (cause default method of getting field name is worked on cursor)
    Such as: declarator, value, left, right
    """
    index = 0
    for child in node.parent.children:
        if child == node:
            break
        index += 1
    return node.parent.field_name_for_child(index)

def check_file_exists(path: str) -> bool:
    if not os.path.exists(path):
        return False
    else:
        return True

def try_read_file(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read()
    except:
        print(f"Can not read content from file {path}")
        sys.exit(1)

def strip_empty_line(code: str) -> str:
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        if line.strip() == "":
            continue
        new_lines.append(line)
    return '\n'.join(new_lines)
    
def try_compile(commands) -> Tuple[str, str]:
    try:
        with tempfile.TemporaryFile() as temp_file, tempfile.TemporaryFile() as temp_file2:
            process = subprocess.Popen(commands, stdout=temp_file, stderr=temp_file2)
            process.wait()
            temp_file.seek(0)
            temp_file2.seek(0)
            stdout = temp_file.read()
            stderr = temp_file2.read()
    except:
         print(f"Can not run {' '.join(commands)}")
         sys.exit(1)
    
    return stdout.decode('utf-8').strip(), stderr.decode('utf-8').strip()

"""
Class PreprocessAnalyzeBase is the base class of challenges related to preprocess.
"""
class PreprocessAnalyzeBase():
    def __init__(self):
        C_LANGUAGE = Language("./c-language.so", "c")
        self.parser = Parser()
        self.parser.set_language(C_LANGUAGE)

        self.defined_constants = {}
        self.defined_functions = {}

        self.defined_constants_uses = {}
        self.defined_functions_uses = {}

    def get_node_line_num(self, node: tree_sitter.Node) -> int:
        """
        Get the line number of a node
        """
        return node.start_point[0] + 1

    def walk_node(self, node: tree_sitter.Node) -> tree_sitter.Node:
        """
        Walk through the node and its children until the leaf
        """
        yield node
        for child in node.children:
            yield from self.walk_node(child)

    def traverse_tree(self, mode: str="post_order") -> tree_sitter.Node:
        if mode not in ["post_order", "depth_first"]:
            raise ValueError("mode must be either post_order or depth_first")
        cursor = self.tree.walk()
        while True:
            if mode == "depth_first":
                yield cursor
            if cursor.goto_first_child():
                continue
            if mode == "post_order":
                yield cursor
            if cursor.goto_next_sibling():
                continue
            while True:
                if not cursor.goto_parent():
                    return
                if mode == "post_order":
                    yield cursor
                if cursor.goto_next_sibling():
                    break

    def find_constant_define(self, cursor: tree_sitter.TreeCursor):
        """
        Find #define of integers, floats and strings etc.
        """
        if cursor.node.type == "preproc_def":
            defined_name = cursor.node.child_by_field_name("name").text.decode('utf-8').strip()
            defined_value = cursor.node.child_by_field_name("value").text.decode('utf-8').strip()
            defined_line_num = cursor.node.start_point[0] + 1   #? line num in tree_sitter is start from 0, so add 1

            self.defined_constants[defined_name] = {
                "value": defined_value,
                "line_num": defined_line_num
            }
            print(f"Found constant define: {defined_name} = {defined_value} at line {defined_line_num}")
    
    def find_constant_define_use(self, cursor: tree_sitter.TreeCursor):
        """
        Find the use of defined constants
        """
        if cursor.node.type == "identifier" or cursor.node.type == "preproc_arg" \
                or cursor.node.type == "type_identifier":
            identifier_name = cursor.node.text.decode('utf-8').strip()

            # use defined constant directly
            if identifier_name in self.defined_constants.keys() \
                    and self.get_node_line_num(cursor.node) > self.defined_constants[identifier_name]["line_num"]:
                defined_name = identifier_name
                if defined_name not in self.defined_constants_uses.keys():
                    self.defined_constants_uses[defined_name] = []
                    self.defined_constants_uses[defined_name].append(cursor.node)
                else:
                    self.defined_constants_uses[defined_name].append(cursor.node)
                print(f"Found constant use: {defined_name} at line {cursor.node.start_point[0] + 1}")
            
            #?" use defined constant in expression/string
            #? e.g. #define C A+B
            else:
                for defined_name in self.defined_constants.keys():
                    if defined_name in identifier_name \
                            and self.get_node_line_num(cursor.node) > self.defined_constants[defined_name]["line_num"]:
                        if defined_name not in self.defined_constants_uses.keys():
                            self.defined_constants_uses[defined_name] = []
                            self.defined_constants_uses[defined_name].append(cursor.node)
                        else:
                            self.defined_constants_uses[defined_name].append(cursor.node)
                        print(f"Found constant use: {defined_name} at line {cursor.node.start_point[0] + 1}")

    def find_function_define(self, cursor: tree_sitter.TreeCursor):
        """
        Find #define of functions
        """
        if cursor.node.type == "preproc_function_def":
            defined_func_name = cursor.node.child_by_field_name("name").text.decode('utf-8').strip()
            defined_func_line_num = cursor.node.start_point[0] + 1
            defined_func_body = cursor.node.child_by_field_name("value").text.decode('utf-8').strip()

            self.defined_functions[defined_func_name] = {
                "body": defined_func_body,
                "line_num": defined_func_line_num
            }
            print(f"Found function define: {defined_func_name} at line {defined_func_line_num}")

    def find_function_define_use(self, cursor: tree_sitter.TreeCursor):
        """
        Find #define of functions
        """
        if cursor.node.type == "identifier":
            identifier_name = cursor.node.text.decode('utf-8').strip()
            # use defined constant directly
            if identifier_name in self.defined_functions.keys() \
                    and self.get_node_line_num(cursor.node) > self.defined_functions[identifier_name]["line_num"]:
                defined_name = identifier_name
                if defined_name not in self.defined_functions_uses.keys():
                    self.defined_functions_uses[defined_name] = []
                    self.defined_functions_uses[defined_name].append(cursor.node)
                else:
                    self.defined_functions_uses[defined_name].append(cursor.node)
                print(f"Found function use: {defined_name} at line {cursor.node.start_point[0] + 1}")

    def check_func_macro_implementation(self, macros: List[str], keywords: List[str]) -> bool:
        for macro, keyword in zip(macros, keywords):
            if keyword not in self.defined_functions[macro]["body"]:
                print(f"Maybe you should use {keyword} in your macro {macro} !")
                sys.exit(1)

            return True

    def get_input_file(self):
        print_split_line()
        print("(Hint: You can use tab completion here. )")
        print("Please input the path of your submitted file: ")

        self.input_path = input('filename> ')
        self.input_path = pathlib.Path(self.input_path).resolve()
        if not check_file_exists(self.input_path):
            print("File not found !")
            sys.exit(1)
        
        submitted_code = try_read_file(self.input_path)
        print("Following is your submitted code: ")
        print_split_line()
        print(submitted_code)
        print_split_line()
        return submitted_code

    def diff_output(self, str1: str, str2: str):
        differ = difflib.Differ()
        diff_lines = list(differ.compare(str1.splitlines(), str2.splitlines()))
        for line in diff_lines:
            if line.startswith('-') or line.startswith('+'):
                print(line)

    def run(self, given_code: str = None):

        if not given_code:
            source_code = self.get_input_file()
        else:
            source_code = given_code

        try:
            self.tree = self.parser.parse(source_code.encode('utf-8'))
            self.root_node = self.tree.root_node
        except:
            print("Parse error! Please check your source code.")
            sys.exit(1)
        
        try:
            for cursor in self.traverse_tree("depth_first"):
                self.find_constant_define(cursor)
                self.find_constant_define_use(cursor)
                self.find_function_define(cursor)
                self.find_function_define_use(cursor)
        except:
            print("Traverse error! Please check the grammar of your source code.")
            print("If you are sure that your source code is correct, please contact the TA.")
            sys.exit(1)

    def check_macro_define(self, macros: List[str]) -> bool:
        """
        Check if the submitted code has defined the macros we give.
        """
        for macro in macros:
            if macro not in self.defined_constants.keys() and macro not in self.defined_functions.keys():
                print(f"You should define macro {macro} !")
                sys.exit(1)
        return True
    
    def check_constant_macro_use_cnt(self, macros: List[str], use_cnt: List[int]) -> bool:
        """
        check if the submitted code has used the macros we give.
        """
        try:
            for macro, cnt in zip(macros, use_cnt):
                if len(self.defined_constants_uses[macro]) != cnt:
                    print(f"You should use macro {macro} {cnt} times !")
                    sys.exit(1)
        except Exception:
            print("Remember to use the macros you defined !")
            sys.exit(1)
        return True
    
    def check_function_macro_use_cnt(self, macros: List[str], use_cnt: List[int]) -> bool:
        """
        check if the submitted code has used the macros we give.
        """
        try:
            for macro, cnt in zip(macros, use_cnt):
                if len(self.defined_functions_uses[macro]) != cnt:
                    print(f"You should use macro {macro} {cnt} times !")
                    sys.exit(1)
        except Exception:
            print("Remember to use the macros you defined !")
            sys.exit(1)
        return True

    def check_directive(self, directive, direct_cnt) -> bool:
        """
        check if the submitted code has directives we want.
        """
        preprocessed_given = try_read_file(self.input_path).strip()
        if preprocessed_given.count(directive) != direct_cnt:
            print(f"You should use directive {directive} {direct_cnt} times !")
            return False
        return True
    
    def check_line_num(self, line_num: int = None, max_line_num: int = None, min_line_num: int = None):
        preprocessed_given = try_read_file(self.input_path).strip()
        preprocessed_lines = preprocessed_given.split('\n')
        if line_num:
            if len(preprocessed_lines) != line_num:
                print(f"You should have {line_num} lines of preprocessed code !")
                return False
        if max_line_num:
            if len(preprocessed_lines) > max_line_num:
                print(f"You should have less than {max_line_num} lines of preprocessed code !")
                return False
        if min_line_num:
            if len(preprocessed_lines) < min_line_num:
                print(f"You should have more than {min_line_num} lines of preprocessed code !")
                return False
        return True

    def check_preprocess(self, defined_macros: List[Dict] = None , check_target:str = None, remove_empty_line = None) -> bool:
        """
        Check if the preprocessed submitted code is same as the give preprocessed code.
        """
        try:
            if not defined_macros:
                with tempfile.TemporaryFile() as temp_file, tempfile.TemporaryFile() as temp_file2:
                    process = subprocess.Popen(["clang", "-E", "-P", "-x", "c", self.input_path], stdout=temp_file, stderr=temp_file2)
                    process.wait()
                    temp_file.seek(0)
                    temp_file2.seek(0)
                    stdout = temp_file.read()
                    stderr = temp_file2.read()
            else:
                command = ["clang", "-E", "-P", "-x", "c"]
                for macro in defined_macros:
                    if macro["value"]:
                        command.append(f"-D{macro['name']}={macro['value']}")
                    else:
                        command.append(f"-D{macro['name']}")
                command.append(self.input_path)
                with tempfile.TemporaryFile() as temp_file, tempfile.TemporaryFile() as temp_file2:
                    process = subprocess.Popen(command, stdout=temp_file, stderr=temp_file2)
                    process.wait()
                    temp_file.seek(0)
                    temp_file2.seek(0)
                    stdout = temp_file.read()
                    stderr = temp_file2.read()
        except:
            print("Can not run clang -E -P on your submitted code !")
            sys.exit(1)
        
        if stderr:
            print(stderr.decode('utf-8').strip())
            print("Your submitted code has some errors, can not be compiled !")
            sys.exit(1)
        
        preprocessed_submitted = stdout.decode('utf-8').strip()

        if not check_target:
            preprocessed_given = try_read_file(self.given_code).strip()
        else:
            preprocessed_given = try_read_file(check_target).strip()

        if remove_empty_line:
            preprocessed_given = strip_empty_line(preprocessed_given)
            preprocessed_submitted = strip_empty_line(preprocessed_submitted)

        if preprocessed_submitted == preprocessed_given:
            return True
        else:
            print("Your submitted code after preprocess: ")
            print_split_line()
            print(preprocessed_submitted)
            print_split_line()
            print("The given code after preprocess: ")
            print_split_line()
            print(preprocessed_given)
            print_split_line()
            print("Your submitted code is not same as the given code !")
            sys.exit(1)


"""
    Compile Base Class
"""
class CompileBase():
    def __init__(self, given_original_path, given_processed_path):
        self.submitted_file_path = None
        self.given_original_code = try_read_file(given_original_path)
        self.given_processed_code = try_read_file(given_processed_path)

    def get_submitted_file(self):
        print_split_line()
        print("(Hint: You can use tab completion here. )")
        print("Please input the path of your submitted file: ")

        submitted_file = input('filename> ')
        self.submitted_file_path = pathlib.Path(submitted_file).resolve()
        if not check_file_exists(self.submitted_file_path):
            print("File not found !")
            sys.exit(1)
        
        submitted_code = try_read_file(self.submitted_file_path)

        print("Following is your submitted code: ")
        print_split_line()
        print(submitted_code)
        print_split_line()
        return submitted_code

    def try_process(self, command: List[str]):
        try:
            with tempfile.TemporaryFile() as temp_file, tempfile.TemporaryFile() as temp_file2:
                process = subprocess.Popen(command, stdout=temp_file, stderr=temp_file2)
                process.wait()
                temp_file.seek(0)
                temp_file2.seek(0)
                stdout = temp_file.read()
                stderr = temp_file2.read()
        except Exception as e:
            print(e)
            print(f"Error when running command: {' '.join(command)} !")
            sys.exit(1)
        
        if stderr:
            print(stderr.decode('utf-8').strip())
            print("Your submitted code has some errors!")
            sys.exit(1)

        processed_submitted_code = stdout.decode('utf-8')
        return processed_submitted_code

    def diff_output(self, str1: str, str2: str):
        differ = difflib.Differ()
        diff_lines = list(differ.compare(str1.splitlines(), str2.splitlines()))
        for line in diff_lines:
            if line.startswith('-') or line.startswith('+'):
                print(line)

    def diff_error(self, str1: str, str2: str):
        print("Your submitted code is not correct !")
        print("Following is the diff of (processed) submitted code and (processed) given code:")
        print_split_line()
        self.diff_output(str1, str2)

    def pass_sanitizer(self, passname: str):
        allowed_passes = [
            "-adce", "-always-inline", "-argpromotion", "-attributor", "-barrier", "-basiccg", "-bdce",
            "-block-freq", "-bounds-checking", "-break-crit-edges", "-bugpoint", "-called-value-propagation",
            "-mem2reg", "-reg2mem", "-sccp", "-ipsccp", "-constmerge", "-consthoist",
            "-loop-simplify", "-loop-simplifycfg", "-loop-rotate", "-loop-unroll", "-loop-unswitch", "-licm"
        ]
        passname = passname.strip()
        if not passname.startswith("-"):
            print("You should add a '-' before the pass name !")
            sys.exit(1)
        if len(passname.split()) > 1:
            print("You should only input one pass name !")
            sys.exit(1)
        if passname not in allowed_passes:
            print("This pass is not allowed !")
            sys.exit(1)
        return passname

    def trim_ast(self, code: str):
        """
        remove useless data
        """
        new_lines = []
        lines = code.split('\n')
        for line in lines:
            if "-BuiltinAttr" in line or "-AllocSizeAttr" in line:
                continue
            tokens = line.split(' ')
            new_tokens = []
            for token in tokens:
                if token.startswith("0x") or \
                    "line:" in token or \
                    "col:" in token or \
                    "<" in token:
                    continue
                new_tokens.append(token)
            new_lines.append(' '.join(new_tokens))
        
        return '\n'.join(new_lines)

    def trim_llvmir(self, code: str):
        """
        remove useless data
        """
        new_lines = []
        lines = code.split('\n')
        for line in lines:
            if line.startswith(";"):    # comment
                continue
            elif line.startswith("target datalayout") or line.startswith("target triple"):
                continue
            elif line.startswith("!"): # metadata
                continue
            elif line.startswith("source_filename"):
                continue
            elif line.startswith("attributes"):
                continue
            elif line == "":
                continue
            new_lines.append(line)

        return "\n".join(new_lines).strip()

    def run(self, command_prefix: List[str]):
        self.get_submitted_file()
        command = command_prefix + [self.submitted_file_path]
        self.submitted_processed_code = self.try_process(command)

"""
A base class for ELF related challenges
"""
class ELFBase():
    def __init__(self):
        self.submitted_file_path = None
        self.functions = []
        self.bss = []
        self.data = []
        self.rodata = []
    
    def get_submitted_file(self):
        print_split_line()
        print("(Hint: You can use tab completion here. )")
        print("Please input the path of your submitted file: ")

        submitted_file = input('filename> ')
        self.submitted_file_path = pathlib.Path(submitted_file).resolve()
        if not check_file_exists(self.submitted_file_path):
            print("File not found !")
            sys.exit(1)

        print_split_line()
    
    def check_hash(self, correct: str, offset = None):
        """
        check the correct hash of the submitted file
        """
        if not offset:
            with open(self.submitted_file_path, 'rb') as f:
                submitted_hash = hashlib.sha256(f.read()).hexdigest()
        
        else:
            with open(self.submitted_file_path, 'rb') as f:
                f.seek(offset)
                submitted_hash = hashlib.sha256(f.read()).hexdigest()
        
        return submitted_hash == correct

    def check_function(self, func_name: str, section: str):
        """
        check if func_name in section
        """
        for symbol in self.binary.symbols:
            if symbol.name == func_name:
                if symbol.section.name == section:
                    if symbol.type == lief.ELF.SYMBOL_TYPES.FUNC:
                        return True
                    else:
                        print(f"`{func_name}` is not a function !")
                        return False
                else:
                    print(f"`{func_name}` is not in `{section}`, but in `{symbol.section.name}` !")
                    return False

        print(f"`{func_name}` not found !")
        return False

    def check_symbol(self, symbol_name: str, symbol_value = None, symbol_size = None, symbol_type = None,
                            symbol_bind = None, symbol_ndx = None,
                            external:bool = False, check_prefix = False,
                            check_not_exist = False) -> bool:
        symbol = None
        if check_prefix:
            for s in self.binary.symbols:
                if s.name.startswith(symbol_name):
                    symbol = self.binary.get_symbol(s.name)
                    break
        else:
            symbol = self.binary.get_symbol(symbol_name)

        if symbol:
            if check_not_exist:
                print(f"Symbol {symbol.name} should not exist here!")
                return False

            if symbol_value:
                if symbol.value != symbol_value:
                    print(f"Symbol {symbol_name}'s value is {hex(symbol.value)}, not {hex(symbol_value)} !")
                    return False
            if symbol_size:
                if symbol.size != symbol_size:
                    print(f"Symbol {symbol_name}'s size is {hex(symbol.size)}, not {hex(symbol_size)} !")
                    return False
            if symbol_type:
                if symbol.type != symbol_type:
                    print(f"Symbol {symbol_name}'s type is {symbol.type}, not {symbol_type} !")
                    return False
            if symbol_bind:
                if symbol.binding != symbol_bind:
                    print(f"Symbol {symbol_name}'s bind is {symbol.binding}, not {symbol_bind} !")
                    return False
            if symbol_ndx:
                if symbol.shndx != symbol_ndx:
                    print(f"Symbol {symbol_name}'s ndx is {symbol.ndx}, not {symbol_ndx} !")
                    return False
            if external:
                if symbol.shndx != lief.ELF.SYMBOL_SECTION_INDEX.UNDEF.value:
                    print(f"Symbol {symbol_name} is not external !")
                    return False
            return True
        
        else:
            if check_not_exist:
                return True
            
            print(f"Can not find symbol {symbol_name} in the ELF.")
            return False


    def check_section_data(self, section_name: str, data_name: str, value):
        for symbol in self.binary.symbols:
            if symbol.name == data_name:
                if symbol.section.name == section_name:
                    if symbol.type == lief.ELF.SYMBOL_TYPES.OBJECT:
                        symbol_data = self.get_memory_data(symbol.section.content, symbol.value, symbol.size)
                        symbol_data = int.from_bytes(symbol_data, byteorder='little')
                        if symbol_data == value:
                            return True
                        else:
                            print(f"`{data_name}` should hold {hex(value)}, not {hex(symbol_data)}!")
                            return False
                    elif symbol.type == lief.ELF.SYMBOL_TYPES.FUNC:
                        if self.binary_type == lief.ELF.E_TYPE.RELOCATABLE:
                            function_prologue = self.get_memory_data(symbol.section.content, symbol.value, 4)
                        elif self.binary_type == lief.ELF.E_TYPE.EXECUTABLE or self.binary_type == lief.ELF.E_TYPE.DYNAMIC:
                            section_vaddr = symbol.section.virtual_address
                            symbol_vaddr = symbol.value
                            offset = symbol_vaddr - section_vaddr
                            function_prologue = self.get_memory_data(symbol.section.content, offset, 4)

                        if function_prologue == value:
                            return True
                        else:
                            print(f"Function `{data_name}`'s prologue should be `{value}`! Not `{function_prologue}`!")
                            return False
                    else:
                        print(f"`{data_name}` is not a variable or function !")
                        return False
                else:
                    print(f"`{data_name}` is not in `{section_name}`, but in `{symbol.section.name}` !")
                    return False
                
        print(f"`{data_name}` not found !")
        return False

    def check_bss(self, bss_name: str):
        """
        check if bss_name in bss
        """
        for symbol in self.binary.symbols:
            if symbol.name == bss_name:
                if symbol.type == lief.ELF.SYMBOL_TYPES.OBJECT:
                    if symbol.section.name == ".bss":
                        return True
                    else:
                        print(f"`{bss_name}` is not in .bss, but in `{symbol.section.name}` with value `{symbol.value}` !")
                        return False
                else:
                    print(f"`{bss_name}` is not a variable !")
                    return False
                
        print(f"`{bss_name}` not found !")
        return False

    def check_data(self, data_name: str, value: int):
        """
        check if data_name in data
        """
        for symbol in self.binary.symbols:
            if symbol.name == data_name:
                if symbol.type == lief.ELF.SYMBOL_TYPES.OBJECT:
                    if symbol.section.name == ".data":
                        symbol_data = self.get_memory_data(symbol.section.content, symbol.value, symbol.size)
                        symbol_data = int.from_bytes(symbol_data, byteorder='little')
                        if symbol_data == value:
                            return True
                        else:
                            print(f"`{data_name}` should hold {hex(value)}, not {hex(symbol_data)}!")
                            return False
                    else:
                        print(f"`{data_name}` is not in .data, but in `{symbol.section.name}` with value `{symbol.value}` !")
                        return False
                else:
                    print(f"`{data_name}` is not a variable !")
                    return False
                
        print(f"`{data_name}` not found !")
        return False

    def check_rodata(self, rodata_content: str):
        """
        check if rodata_name in rodata
        """
        for symbol in self.binary.symbols:
            if symbol.type == lief.ELF.SYMBOL_TYPES.OBJECT and \
                symbol.section.name.startswith(".rodata"):
                symbol_data = self.get_memory_data(symbol.section.content, symbol.value, symbol.size)
                
                if isinstance(rodata_content, str):
                    symbol_data = symbol_data.decode('utf-8').strip().rstrip('\x00')
                    if rodata_content == symbol_data:
                        return True
                    
        print(f"`{rodata_content}` not found !")
        return False

    def get_memory_data(self, memory, offset, size) -> bytes:
        """
        get data from memory
        """
        return memory[offset:offset+size].tobytes()

    def run(self):
        self.get_submitted_file()
        binary = lief.parse(str(self.submitted_file_path))
        if isinstance(binary, lief.ELF.Binary):
            self.binary = binary
            self.binary_type = binary.header.file_type
        else:
            print("Your submitted file is not correct !")
            sys.exit(1)

def get_preprocess_description(preprocessed_code):
    preprocess_description = description(f"""
    ============================================================
    I believe that many of you have written C code. In order to 
    convert C code into a program that a machine can execute, we need 
    to use compilers like gcc/clang/msvc/... to build the source code 
    into a binary program. The first step of this build process is 
    preprocessing the source code.

    In this challenge, we present you with the preprocessed source code, 
    {preprocessed_code}. 
    This code constitutes simple programs that have been preprocessed 
    using the 'clang -E -P' command. 
    Your task, guided by the description of the challenge, is to 
    restore the original source code from the given preprocessed code.
    ============================================================
    """)
    return preprocess_description

def get_compilation_description(given_code):
    compilation_description = description(f"""
    ============================================================
    In this challenge, we present you with the following code, 
    {given_code}
    Your task, guided by the description of the challenge, 
    is to **complete** the given code, make it produces the same 
    output as another processed file.
    ============================================================
    """)
    return compilation_description

def get_ast_description():
    ast_description = description(f"""
    After the compiler preprocesses the C code, it proceeds with 
    subsequent analysis such as lexical analysis, syntax analysis, and so on. 
    However, since this is not a compiler course, we won't introduce those details. 
    But it's important to note that during the compilation process, 
    the compiler generates a structure called Abstract Syntax Tree (AST).

    In this challenge, you will explore the ** clang AST ** and gradually
    become familiar with it. If you not know what is AST, you can ask 
    ChatGPT or Google it.

    ** Your task **:
    1. complete function `main` in the given code `level{level}.c`, make it 
       produce the same AST structure as the given file `level{level}.ast`.
    2. Only ensure that the structure and values of the AST nodes are the same. 
       Ignore line and column numbers, object addresses, etc.

    Hint:
        1. You can use `clang -Xclang -ast-dump -fsyntax-only <source_code>` to 
           dump the AST of the source code.
        2. You can use `clang -Xclang -ast-dump -fsyntax-only -fno-color-diagnostics <source_code>` 
           to dump the AST of the source code without color.
        3. Your submitted code is a fixed version of `level{level}.c`.
    """)
    return ast_description

def get_llvmir_description():
    llvmir_description = description(f"""
    In build workflow, the compiler will transform the clang AST into 
    LLVM IR(Intermediate Representation), which is core component of 
    LLVM compiler infrastructure project. LLVM IR is a low-level programming 
    language that is rich in types and supports the Static Single Assignment (SSA) 
    form, the LLVM optimizer can perform various program optimizations on it. 
    Finally, LLVM's code generator translates the optimized LLVM IR into 
    target machine code.
    
    For software security, LLVM IR provides a universal way to understand
    and analyze the behavior of source code, regardless of the programming 
    language used. Moreover, by performing analysis and modifications at the LLVM IR level, 
    we can develop powerful tools such as security vulnerability detectors, 
    automatic patch generators, and various software protection mechanisms.
    Therefore, understanding and leveraging LLVM IR is important for enhancing 
    our software security capabilities.
    
    If you are not familiar with LLVM IR, following the principle of "standing on the shoulders of giants," 
    I highly recommend you to read the following links.
    1. https://buaa-se-compiling.github.io/miniSysY-tutorial/pre/llvm_ir_quick_primer.html
    2. https://buaa-se-compiling.github.io/miniSysY-tutorial/pre/llvm_ir_ssa.html (Optional)
    Thanks to the BUAA-SE-Compiling team for providing such a great tutorial.
    """)
    return llvmir_description

def get_llvmir_task_description():
    task_description = description(f"""
        ** Your task **:
        1. complete function `main` in the given code `level{level}.c`, 
           make it produce the "same" llvm-ir as the given `level{level}.ll`.
        2. "same" means that the two llvm-ir files should be same after 
           removing all the comments, all the unnecessary metadata and all 
           the unnecessary instructions. In other words, you don't need to pay 
           attention to certain metadata in LLVM IR, such as `target data layout` 
           and `attributes`, etc.
        3. Your submitted code is a fixed version of `level{level}.c`.                
    """)
    return task_description

def get_llvmpass_description():
    llvmpass_description = description(f"""
    LLVM Pass is a core concept in the LLVM compiler framework. LLVM Pass is a unit of work 
    that performs a specific transformation or analysis on LLVM IR. These passes can be 
    optimization (such as constant folding, dead code elimination), code generation
    (such as instruction selection, register allocation), or analysis (such as calculating 
    possible values of expressions, building Control flow graph).
    To learn more about LLVM Pass, you can read the following links.
    1. https://llvm.org/docs/WritingAnLLVMPass.html#introduction-what-is-a-pass
    2. https://llvm.org/docs/Passes.html#introduction
    In this challenge, you will learn how to use built-in LLVM Passes to optimize LLVM IR. 
    """)
    return llvmpass_description

def get_llvmpass_task_description():
    task_description = description(f"""
        ** Your task **:
        1. You should find the correct built-in LLVM Pass to optimize the given `level{level}.ll`
           file. Make it produce the "same" llvm-ir as the given `opt_level{level}.ll`.
        2. You should give the built-in LLVM Pass's name to finish this challenge.
    """)
    return task_description

def get_object_file_description():
    assembly_description = description(f"""
    Up to now, we have learned how source code is compiled into assembly code. 
    The next step is to use an ** assembler ** to convert the assembly code 
    into instructions that the machine can "execute". This step is ** assembly **, 
    and its output is a ** relocatable object file ** in ELF format. 
    Of course, the object file cannot be executed directly. To generate the final 
    executable file, we need to use a linker to link the object files together. 
    However, the structure and content of object files are not significantly different 
    from executable files. The main difference may be that some symbols and 
    addresses are not resolved. Therefore, understanding the structure of object files 
    is important for comprehending what is Program.

    You can get a relocatable object file by using the following command.
    1. run `clang -c -o <object_file> <source_code / asm_code>` to generate a 
       relocatable object file from C source code or assembly code.
    2. run `llc -march=x86-64 -filetype=obj -o <object_file> <llvm_ir_code>` to 
       generate a relocatable object file from LLVM IR.
    3. ... (You can also try other commands to generate object files)
    """)
    return assembly_description

def get_elf_structure_description():
    elf_description = description(f"""
    After finishing the previous challenges, I believe that you have gained a 
    general understanding of the outline of an ELF object file. Now let's take 
    a look at the overall structure of an ELF object file. We have omitted 
    some tedious details of the ELF and extracted the most important structures, 
    as shown below:
        +-----------------------------+
        |  ELF Header                 |
        +-----------------------------+
        |                             |
        |  .text                      |
        |                             |
        +-----------------------------+
        |  .data                      | 
        |  .rodata                    |
        +-----------------------------+
        |  .bss                       |
        +-----------------------------+
        |  ...                        |
        |  ...                        |
        |  other sections             |
        +-----------------------------+
        |                             |
        |  section header table       |
        |                             |
        +-----------------------------+
    At the very beginning of the ELF (Executable and Linkable Format) file is 
    **ELF Header**, which contains metadata describing the entire ELF file, 
    including the ELF file version, target machine type, program entry address, etc. 
    By parsing the ELF header, we can understand the structure of the entire ELF file.
    Another important structure related to ELF is the **Section Header Table**, which 
    contains information about all sections in the ELF file, such as the name of section, 
    the size of section, the read/write/execute permission of section, etc.
    """)
    return elf_description

def print_split_line():
    print("=" * 60)



"""
    Following are the challenges of each level
"""

class IntroLevel2(PreprocessAnalyzeBase):
    def __init__(self):
        super().__init__()
        self.given_code = pathlib.Path(__file__).parent.resolve() / "./level2.c"
        self.description = get_preprocess_description(self.given_code)

        challenge_description = description(f"""
        ** Your task **:
        1. rewrite the provided source code {self.given_code} 
            and integrating the following 2 macros into it.
            a. Define a macro `STUDENT_COUNT` with a value of 90.
            b. Define a macro `STUDENT_PASS_GRADE` with a value of 60.
        2. Be sure to replace any corresponding values within the source code with the macros you've defined as much as possible.
        """)

        self.description += challenge_description
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run()
        print_split_line()
        self.check_macro_define(["STUDENT_COUNT", "STUDENT_PASS_GRADE"])
        self.check_constant_macro_use_cnt(["STUDENT_COUNT", "STUDENT_PASS_GRADE"], [3, 2])
        if self.check_preprocess():
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()

class IntroLevel3(PreprocessAnalyzeBase):
    def __init__(self):
        super().__init__()
        self.given_code = pathlib.Path(__file__).parent.resolve() / "./level3.c"
        self.description = get_preprocess_description(self.given_code)

        challenge_description = description(f"""
        ** Your task **:
        1. rewrite the provided source code {self.given_code}, and integrating the following 4 macros into it.
            a. Define a macro `SOFTWARE_VERSION` with a value of "v1.0.0".
            b. Define a macro `SOFTWARE_NAME` with a value of "SoftwareSecCourse".
            c. Define a macro `AUTHOR` with a value of "TA".
            d. Define a macro `BANNER` that is composed of the above 3 macros.
        2. Be sure to replace any corresponding values within the source code with the macros you've defined as much as possible.
        3. Make sure every macro you've defined is used
        """)

        self.description += challenge_description
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run()
        print_split_line()
        self.check_macro_define(["SOFTWARE_VERSION", "SOFTWARE_NAME", "AUTHOR", "BANNER"])
        self.check_constant_macro_use_cnt(["SOFTWARE_VERSION", "SOFTWARE_NAME", "AUTHOR", "BANNER"], [1, 1, 1, 1])
        if self.check_preprocess():
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()

class IntroLevel4(PreprocessAnalyzeBase):
    def __init__(self):
        super().__init__()
        self.given_code = pathlib.Path(__file__).parent.resolve() / "./level4.c"
        self.description = get_preprocess_description(self.given_code)

        challenge_description = description(f"""
        ** Your task **:
        1. rewriting the provided source code {self.given_code} and integrating following 2 function-like macros into it.
            a. Define a macro `FUNC(n)`, which will yield `function_n`
            b. Define a macro `VAR(n)` which will yield `variable_n`
        2. Be sure to replace any corresponding values within the source code with the macros you've defined as much as possible.

        Hint: 
        1. You can utilize the `##` operator in your `#define` statement.
        """)

        self.description += challenge_description
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run()
        print_split_line()
        self.check_macro_define(["FUNC", "VAR"])
        self.check_function_macro_use_cnt(["FUNC", "VAR"], [4, 4])
        if self.check_preprocess():
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()


class IntroLevel5(PreprocessAnalyzeBase):
    def __init__(self):
        super().__init__()
        self.given_code = pathlib.Path(__file__).parent.resolve() / "./level5.c"
        self.description = get_preprocess_description(self.given_code)

        challenge_description = description(f"""
        ** Your task **:
        1. rewrite the provided source code {self.given_code}, and integrating the following macro into it.
            a. Define a *do-while-zero* macro `HANDLE_ERROR(condition, error_code)`, 
               which will yield a *do-while-zero* block.
        2. Be sure to replace any corresponding values within the source code with the macros you've defined as much as possible.
        """)

        extra_description = description(f"""
        The *do-while-zero* macro is a commonly used macro definition 
        in the C language that allows developers to create a block of 
        code that appears like a regular do-while loop but is executed 
        only once. It is typically used to wrap multiple statements into
        a single unit for better code organization or to handle complex
        control flow scenarios. Developers often prefer using the do-while-zero 
        macro because it provides a concise and reliable way to encapsulate code 
        without introducing additional if conditions or unnecessary function calls, 
        resulting in cleaner and more readable code.
        """)

        self.description += challenge_description
        self.description += extra_description 
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run()
        print_split_line()
        self.check_macro_define(["HANDLE_ERROR"])
        self.check_function_macro_use_cnt(["HANDLE_ERROR"], [1])
        self.check_func_macro_implementation(["HANDLE_ERROR"], ["while"])
        if self.check_preprocess():
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()


class IntroLevel6(PreprocessAnalyzeBase):
    def __init__(self):
        super().__init__()
        self.given_code = [
            pathlib.Path(__file__).parent.resolve() / "./level6-1.c", 
            pathlib.Path(__file__).parent.resolve() / "./level6-2.c", 
            pathlib.Path(__file__).parent.resolve() / "./level6-3.c", 
            pathlib.Path(__file__).parent.resolve() / "./level6-4.c"
        ]
        self.given_code = [str(path) for path in self.given_code]
        self.description = get_preprocess_description(self.given_code)

        challenge_description = description(f"""
        It's fascinating! I used the following 4 commands to preprocess the same source code 
        and ended up with four different files:
        {self.given_code}.
        1. clang -E -P -DVERSION=1 [solve_level6.c]
        2. clang -E -P -DVERSION=2 [solve_level6.c]
        3. clang -E -P -DVERSION=3 [solve_level6.c]
        4. clang -E -P -DVERSION=1 -DDEBUG [solve_level6.c]
        Can you assist me in recovering the original source code?
        
        ** Your task **:
        1. recover the original source code (only 1 file) from the given preprocessed code.

        Hint: 
        1. Utilizing `#if` statements and similar techniques may be helpful in solving this challenge.
        """)

        self.description += challenge_description
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run()
        self.check_preprocess(defined_macros = [{"name": "VERSION", "value": "1"}], check_target=self.given_code[0])
        self.check_preprocess(defined_macros = [{"name": "VERSION", "value": "2"}], check_target=self.given_code[1])
        self.check_preprocess(defined_macros = [{"name": "VERSION", "value": "3"}], check_target=self.given_code[2])
        self.check_preprocess(defined_macros = [{"name": "VERSION", "value": "1"}, {"name": "DEBUG", "value": None}], check_target=self.given_code[3])

        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()


class IntroLevel7(PreprocessAnalyzeBase):
    def __init__(self):
        super().__init__()
        self.given_code = pathlib.Path(__file__).parent.resolve() / "./level7.c"
        self.description = get_preprocess_description(self.given_code)

        challenge_description = description(f"""
        Holy s**t! I'm just trying to take a look at the preprocessed code, 
        but it's too long to read! Can you assist me in recovering the 
        original source code?

        ** Your task **:
        1. recover the original source code (only 1 file) from the given preprocessed code.
                                            
        Hint:
        1. I remember that the original source code includes 3 `#include` directives.
        """)

        self.description += challenge_description
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run()
        
        if not all([
            self.check_directive("#include", 3),
            self.check_line_num(max_line_num = 25)
        ]):
            print("Your submitted code is not correct !")
            sys.exit(1)
        
        self.check_preprocess(remove_empty_line = True)

        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()


class IntroLevel8(PreprocessAnalyzeBase):
    def __init__(self):
        super().__init__()
        self.given_code = [
            pathlib.Path(__file__).parent.resolve() / "./level8.c", 
            pathlib.Path(__file__).parent.resolve() / "./level8_1.h", 
            pathlib.Path(__file__).parent.resolve() / "./level8_2.h"
        ]
        self.given_code = [str(path) for path in self.given_code]
        self.description = description(f"""
            ============================================================
            In this challenge, we present you with the following source code, 
            {self.given_code}. 
            Your task, guided by the description of the challenge, is to fix
            the errors in the code and make it compilable.
            ============================================================
        """)

        challenge_description = description(f"""
        I think my code is correct, but it can't be compiled. Can you help me fix it?

        ** Your task **:
        1. Only Fix the source file `level8_2.h` and submit it, then we will compile it with `level8.c` and `level8_1.h` and check if it can be compiled.
        2. The file name of your submitted file should be `solve_level8.h`.
        """)

        self.description += challenge_description
        print(self.description)

    def check(self):
        self.get_input_file()
        input_path = pathlib.Path(self.input_path)
        if input_path.name != "solve_level8.h":
            print("The file name of your submitted file should be `solve_level8.h` !")
            sys.exit(1)
        
        include_dir = input_path.parent.resolve()
        try:
            process = subprocess.Popen(["clang", "-E", "-P", "-x", "c", "-I", include_dir, self.given_code[0]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            print("Can not run clang -E -P on your submitted code !")
            sys.exit(1)
        process.wait()
        stdout, stderr = process.communicate()
        if stderr:
            print(stderr.decode('utf-8').strip())
            print("Your submitted code has some errors, can not be compiled !")
        
        preprocessed_submitted = stdout.decode('utf-8').strip()

        print("Your submitted code after preprocess: ")
        print_split_line()
        print(preprocessed_submitted)
        print_split_line()

        submitted_code = try_read_file(self.input_path)

        # if submitted code appears twice in preprocessed code, it means the code is not correct
        if preprocessed_submitted.count(submitted_code) < 2:
            stdout, stderr = try_compile(["clang", "-x", "c", "-I", include_dir, "-o", "/dev/null", self.given_code[0]])
            if stderr:
                print("Your submitted code is not correct !")
                print(stderr)
                sys.exit(1)

        else:
            print("Your submitted code is not correct !")
            print("There are some repulicated definitions in your submitted code !")
            sys.exit(1)

        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame() 

class IntroLevel9(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ast"
        super().__init__(self.given_original_path, self.given_processed_path)
        self.description = get_compilation_description(self.given_original_path)
        challenge_description = get_ast_description()
        self.description += challenge_description
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-Xclang", "-ast-dump", "-fsyntax-only", "-fno-color-diagnostics"])

        given_trimmed = self.trim_ast(self.given_processed_code).strip()
        submitted_trimmed = self.trim_ast(self.submitted_processed_code).strip()

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)

class IntroLevel10(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ast"
        super().__init__(self.given_original_path, self.given_processed_path)
        self.description = get_compilation_description(self.given_original_path)
        challenge_description = get_ast_description()
        self.description += challenge_description
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-Xclang", "-ast-dump", "-fsyntax-only", "-fno-color-diagnostics"])

        given_trimmed = self.trim_ast(self.given_processed_code).strip()
        submitted_trimmed = self.trim_ast(self.submitted_processed_code).strip()

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)


class IntroLevel11(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ast"
        super().__init__(self.given_original_path, self.given_processed_path)
        self.description = get_compilation_description(self.given_original_path)
        challenge_description = get_ast_description()
        self.description += challenge_description
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-Xclang", "-ast-dump", "-fsyntax-only", "-fno-color-diagnostics"])

        given_trimmed = self.trim_ast(self.given_processed_code).strip()
        submitted_trimmed = self.trim_ast(self.submitted_processed_code).strip()

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)


class IntroLevel12(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ast"
        super().__init__(self.given_original_path, self.given_processed_path)
        self.description = get_compilation_description(self.given_original_path)
        challenge_description = get_ast_description()
        self.description += challenge_description
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-Xclang", "-ast-dump", "-fsyntax-only", "-fno-color-diagnostics"])

        given_trimmed = self.trim_ast(self.given_processed_code).strip()
        submitted_trimmed = self.trim_ast(self.submitted_processed_code).strip()

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)


class IntroLevel13(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ast"
        super().__init__(self.given_original_path, self.given_processed_path)
        self.description = get_compilation_description(self.given_original_path)
        challenge_description = get_ast_description()
        self.description += challenge_description
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-Xclang", "-ast-dump", "-fsyntax-only", "-fno-color-diagnostics"])

        given_trimmed = self.trim_ast(self.given_processed_code).strip()
        submitted_trimmed = self.trim_ast(self.submitted_processed_code).strip()

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)

class IntroLevel14(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        compilation_description = get_compilation_description(self.given_original_path)
        challenge_description = get_llvmir_description()
        task_description = get_llvmir_task_description()
        hint = description(f"""
        Hint:
            1. You can use `clang -S -c -emit-llvm -o <source.ll> <source.c>` to generate readable llvm-ir of a c file.
            2. You just need to write an assignment statement, it's very simple, isn't it?
        """)
        self.description = compilation_description + challenge_description + task_description + hint
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-S", "-c", "-emit-llvm", "-o", "/dev/stdout"])

        given_trimmed = self.trim_llvmir(self.given_processed_code)
        submitted_trimmed = self.trim_llvmir(self.submitted_processed_code)

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)


class IntroLevel15(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        compilation_description = get_compilation_description(self.given_original_path)
        challenge_description = get_llvmir_description()
        task_description = get_llvmir_task_description()
        hint = description(f"""
        Hint:
            1. You can use `clang -S -c -emit-llvm -o <source.ll> <source.c>` to generate readable llvm-ir of a c file.
            2. Where are strings stored in LLVM IR?
        """)
        self.description = compilation_description + challenge_description + task_description + hint
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-S", "-c", "-emit-llvm", "-o", "/dev/stdout"])

        given_trimmed = self.trim_llvmir(self.given_processed_code)
        submitted_trimmed = self.trim_llvmir(self.submitted_processed_code)

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)

class IntroLevel16(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        compilation_description = get_compilation_description(self.given_original_path)
        challenge_description = get_llvmir_description()
        task_description = get_llvmir_task_description()
        hint = description(f"""
        Hint:
            1. You can use `clang -S -c -emit-llvm -o <source.ll> <source.c>` to generate readable llvm-ir of a c file.
            2. In LLVM IR, GEP (GetElementPtr) instructions is very important, you need to be familiar with it.
        """)
        self.description = compilation_description + challenge_description + task_description + hint
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-S", "-c", "-emit-llvm", "-o", "/dev/stdout"])

        given_trimmed = self.trim_llvmir(self.given_processed_code)
        submitted_trimmed = self.trim_llvmir(self.submitted_processed_code)

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)

class IntroLevel17(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        compilation_description = get_compilation_description(self.given_original_path)
        challenge_description = get_llvmir_description()
        task_description = get_llvmir_task_description()
        hint = description(f"""
        Hint:
            1. You can use `clang -S -c -emit-llvm -o <source.ll> <source.c>` to generate readable llvm-ir of a c file.
            2. The `if/else` and `call` are the most common statements for modifying 
               the program's control flow. You should learn their representations in 
               LLVM IR. In addition, you also need to understand the concept of basic blocks
               (https://en.wikipedia.org/wiki/Basic_block).
        """)
        self.description = compilation_description + challenge_description + task_description + hint
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-S", "-c", "-emit-llvm", "-o", "/dev/stdout"])

        given_trimmed = self.trim_llvmir(self.given_processed_code)
        submitted_trimmed = self.trim_llvmir(self.submitted_processed_code)

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)

class IntroLevel18(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        compilation_description = get_compilation_description(self.given_original_path)
        challenge_description = get_llvmir_description()
        task_description = get_llvmir_task_description()
        hint = description(f"""
        Hint:
            1. You can use `clang -S -c -emit-llvm -o <source.ll> <source.c>` to generate readable llvm-ir of a c file.
        """)
        self.description = compilation_description + challenge_description + task_description + hint
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-S", "-c", "-emit-llvm", "-o", "/dev/stdout"])

        given_trimmed = self.trim_llvmir(self.given_processed_code)
        submitted_trimmed = self.trim_llvmir(self.submitted_processed_code)

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)

class IntroLevel19(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        compilation_description = get_compilation_description(self.given_original_path)
        challenge_description = get_llvmir_description()
        task_description = get_llvmir_task_description()
        hint = description(f"""
        Hint:
            1. You can use `clang -S -c -emit-llvm -o <source.ll> <source.c>` to generate readable llvm-ir of a c file.
            2. I guess you won't find `while` and `for` in LLVM IR anymore. So how are they represented?
        """)
        self.description = compilation_description + challenge_description + task_description + hint
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-S", "-c", "-emit-llvm", "-o", "/dev/stdout"])

        given_trimmed = self.trim_llvmir(self.given_processed_code)
        submitted_trimmed = self.trim_llvmir(self.submitted_processed_code)

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)


class IntroLevel20(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        compilation_description = get_compilation_description(self.given_original_path)
        challenge_description = get_llvmir_description()
        task_description = get_llvmir_task_description()
        hint = description(f"""
        Hint:
            1. You can use `clang -S -c -emit-llvm -o <source.ll> <source.c>` to generate readable llvm-ir of a c file.
            2. In the C language, the "static" keyword will make a significant 
               difference in your code. Just using the "static" when complete your code.
        """)
        self.description = compilation_description + challenge_description + task_description + hint
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-S", "-c", "-emit-llvm", "-o", "/dev/stdout"])

        given_trimmed = self.trim_llvmir(self.given_processed_code)
        submitted_trimmed = self.trim_llvmir(self.submitted_processed_code)

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)

class IntroLevel21(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        compilation_description = get_compilation_description(self.given_original_path)
        challenge_description = get_llvmir_description()
        task_description = get_llvmir_task_description()
        hint = description(f"""
        Hint:
            1. You can use `clang -S -c -emit-llvm -o <source.ll> <source.c>` to generate readable llvm-ir of a c file.
            2. "inline" is a common optimization technique in the C language 
                used to reduce the overhead of function calls and improve program execution 
                efficiency. You can use the `inline` keyword and `__attribute__((always_inline))`
                to make a function inline.
        """)
        self.description = compilation_description + challenge_description + task_description + hint
        print(self.description)

    def check(self):
        # analyze the submitted code
        self.run(["clang", "-x", "c", "-S", "-c", "-emit-llvm", "-o", "/dev/stdout"])

        given_trimmed = self.trim_llvmir(self.given_processed_code)
        submitted_trimmed = self.trim_llvmir(self.submitted_processed_code)

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)


class IntroLevel22(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./opt_level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        challenge_description = get_llvmpass_description()
        task_description = get_llvmpass_task_description()
        hint = description(f"""
        Hint:
             1. Transfer the memory access into register access is a common optimization. 
                You should find the corresponding LLVM Pass's name.
             2. You can use `opt -S -<pass-name> -o <output-file> <input-file>` to run 
                the built-in LLVM Pass.
             3. We give you the source code, you can read it to understand the meaning of 
                the LLVM IR. If you want to compile the IR from source and try LLVM Passes, 
                remember to add the `-Xclang -disable-O0-optnone` option.
             4. You should give the command line option of LLVM Pass, for example, 
                give me `-dce` if you want to run the Dead Code Elimination Pass.
        """)
        self.description = challenge_description + task_description + hint
        print(self.description)

    def check(self):
        # analyze the submitted code
        pass_name = input("LLVM Pass Name> ")
        pass_name = self.pass_sanitizer(pass_name)
        command = ["opt", "-S", f"-{pass_name}", "-o", "/dev/stdout", self.given_original_path]
        self.submitted_processed_code = self.try_process(command)

        given_trimmed = self.trim_llvmir(self.given_processed_code)
        submitted_trimmed = self.trim_llvmir(self.submitted_processed_code)

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)

class IntroLevel23(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./opt_level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        challenge_description = get_llvmpass_description()
        task_description = get_llvmpass_task_description()
        hint = description(f"""
        Hint:
             1. Sparse Constant Propagation is a technique in compiler optimization where 
                the values of known constants are propagated into the program code, thus simplifying it. 
                'Sparse' refers to the method of only applying the 
                propagation to places where it will have an effect, rather than to the entire program.
             2. Many LLVM built-in passes only works on SSA form IR. In other words, we should 
                run the `-mem2reg` pass first. Don't worry, we have done this for you. 
                (level{level}.ll is already in SSA form)
             3. You can use `opt -S -<pass-name> -o <output-file> <input-file>` to run the built-in LLVM Pass.
             4. We give you the source code, you can read it to understand the meaning of the LLVM IR. 
                If you want to compile the IR from source and try LLVM Passes, remember to add the 
                `-Xclang -disable-O0-optnone` option.
             5. You should give the command line option of LLVM Pass, for example, give me `-dce` if you
                want to run the Dead Code Elimination Pass.
        """)
        self.description = challenge_description + task_description + hint
        print(self.description)

    def check(self):
        # analyze the submitted code
        pass_name = input("LLVM Pass Name> ")
        pass_name = self.pass_sanitizer(pass_name)
        command = ["opt", "-S", f"-{pass_name}", "-o", "/dev/stdout", self.given_original_path]
        self.submitted_processed_code = self.try_process(command)

        given_trimmed = self.trim_llvmir(self.given_processed_code)
        submitted_trimmed = self.trim_llvmir(self.submitted_processed_code)

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)


class IntroLevel24(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./opt_level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        challenge_description = get_llvmpass_description()
        task_description = get_llvmpass_task_description()
        hint = description(f"""
        Hint:
             1. Loop invariant code motion is a compiler optimization technique that
                moves computations that yield the same result irrespective of the number 
                of iterations, out of the loop. By doing this, the computation is done 
                just once, instead of repeating for each iteration, thus improving efficiency.
             2. Many LLVM built-in passes only works on SSA form IR. In other words, we 
                should run the `-mem2reg` pass first. Don't worry, we have done this for you. 
                (level{level}.ll is already in SSA form)
             3. You can use `opt -S -<pass-name> -o <output-file> <input-file>` to run the 
                built-in LLVM Pass.
             4. We give you the source code, you can read it to understand the meaning 
                of the LLVM IR. If you want to compile the IR from source and try LLVM Passes, 
                remember to add the `-Xclang -disable-O0-optnone` option.
             5. You should give the command line option of LLVM Pass, for example, give me 
                `-dce` if you want to run the Dead Code Elimination Pass.
        """)
        self.description = challenge_description + task_description + hint
        print(self.description)

    def check(self):
        # analyze the submitted code
        pass_name = input("LLVM Pass Name> ")
        pass_name = self.pass_sanitizer(pass_name)
        command = ["opt", "-S", f"-{pass_name}", "-o", "/dev/stdout", self.given_original_path]
        self.submitted_processed_code = self.try_process(command)

        given_trimmed = self.trim_llvmir(self.given_processed_code)
        submitted_trimmed = self.trim_llvmir(self.submitted_processed_code)

        if given_trimmed == submitted_trimmed:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_trimmed, given_trimmed)
            sys.exit(1)


class IntroLevel25(CompileBase):
    def __init__(self):
        self.given_original_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.c"
        self.given_processed_path = pathlib.Path(__file__).parent.resolve() / f"./level{level}.ll"
        super().__init__(self.given_original_path, self.given_processed_path)
        challenge_description = description(f"""
            Congratulations!
            you are about to complete the final step of your compilation journey, 
            which is code generation. In simple terms, it means generating assembly
            code that is supported by the target architecture. However, we won't 
            dive into assembly here, as the details of assembly will be covered in 
            subsequent chapters. Nonetheless, you still need to explore how to generate 
            assembly code in this challenge.
        """)
        task_description = description(f"""
            ** Your task **:
            1. You should generate the target assembly code (with Intel syntax 
               and x86-64 arch) from the given llvm IR.
            2. You should submit the generated assembly code file to 
               finish this challenge.
            3. (Optional, WON'T check) You can try observing the structure and 
               content of the generated assembly code, and see how the assembly code 
               differs when using different compilation methods and parameters. 
               This might be useful for your subsequent learning :)
        """)
        hint = description(f"""
        Hint:
             1. `llc` tool maybe useful.
        """)
        self.description = challenge_description + task_description + hint
        print(self.description)

    def check(self):
        submitted_asm = self.get_submitted_file()
        given_asm = self.try_process(["llc", "-march=x86-64", "-filetype=asm", "-x86-asm-syntax=intel", "-o", "/dev/stdout", self.given_processed_path])
        if submitted_asm == given_asm:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            self.diff_error(submitted_asm, given_asm)
            sys.exit(1)


class IntroLevel26(ELFBase):
    def __init__(self):
        super().__init__()
        challenge_description = get_object_file_description()
        task_description = description(f"""
            We can guess that the contents in object files include compiled machine instructions and data. 
            In addition to these, it also includes some information required during linking, such as 
            symbol tables and strings. Generally, object files store this information in the form of 
            "Section" based on their different attributes. In most cases, these sections represent a 
            certain length of memory region.

            The machine instructions compiled from the program source code are typically placed in the 
            `.text/.code` section. Uninitialized global variables and local static variables are stored 
            in the `.bss` section, while initialized global variables and local static variables are 
            saved in the `.data` section.
                                       
            ** Your task **:
            1. define 3 functions `foo`, `bar`, `main` in the `.text` section.
            2. define a global variable `global_var` in the `.bss` section.
            3. You should submit the `.o` file to finish this challenge.
        """)
        hint = description(f"""
        Hint:
             1. use `objdump -x <ELF_file>` to check the sections of the ELF file.
        """)

        self.description = challenge_description + task_description + hint
        print(self.description)

    def check(self):
        self.run()
        
        if not (self.binary_type == lief.ELF.E_TYPE.RELOCATABLE):
            print("The type of the binary should be relocatable object file!")
            sys.exit(1)

        if not all([
            self.check_function("main", ".text"),
            self.check_function("foo", ".text"),
            self.check_function("bar", ".text"),
            self.check_bss("global_var")
        ]):
            sys.exit(1)

        else:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()

class IntroLevel27(ELFBase):
    def __init__(self):
        super().__init__()
        challenge_description = get_object_file_description()
        task_description = description(f"""
            We can guess that the contents in object files include compiled machine instructions and data. 
            In addition to these, it also includes some information required during linking, such as 
            symbol tables and strings. Generally, object files store this information in the form of 
            "Section" based on their different attributes. In most cases, these sections represent a 
            certain length of memory region.

            The machine instructions compiled from the program source code are typically placed in the
            `.text/.code` section. Uninitialized global variables and local static variables are stored 
            in the `.bss` section, while initialized global variables and local static variables are 
            saved in the `.data` section. And the `.rodata` section is used to store read-only data, 
            such as string constants.
                                       
            ** Your task **:
            1. define 3 functions `foo`, `bar`, `main` in the `.text` section.
            2. define a global variable `uninitialized_global` in the `.bss` section.
            3. define a global variable `global_var` with initial value `0xdeadbeef` in the `.data` section.
            4. define a global variable `global_var2` with initial value `0xbeabdeef` in the `.data` section.
            5. define a string constant "HelloWorld" in the `.rodata` section.
            6. You should submit the `.o` file to finish this challenge.
        """)
        hint = description(f"""
        Hint:
             1. use `objdump -x <ELF_file>` to check the sections of the ELF file.
        """)

        self.description = challenge_description + task_description + hint
        print(self.description)

    def check(self):
        self.run()
        
        if not (self.binary_type == lief.ELF.E_TYPE.RELOCATABLE):
            print("The type of the binary should be relocatable object file!")
            sys.exit(1)

        if not all([
            self.check_function("main", ".text"),
            self.check_function("foo", ".text"),
            self.check_function("bar", ".text"),
            self.check_bss("uninitialized_global"),
            self.check_data("global_var", 0xdeadbeef),
            self.check_data("global_var2", 0xbeabdeef),
            self.check_rodata("HelloWorld")
        ]):
            sys.exit(1)

        else:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()


class IntroLevel28(ELFBase):
    def __init__(self):
        super().__init__()
        challenge_description = get_object_file_description()
        task_description = description(f"""
            Now we have learned about some of the most important sections in the ELF file format and 
            how functions and variables in the source code are mapped to the ELF. However, the compiler 
            has even more powerful capabilities. It allows you to place functions or variables into the 
            sections you customized.
                                       
            ** Your task **:
            1. define 3 functions `foo`, `bar`, `main` in the `.ucastext` section.
            2. define a global variable `uninitialized_global` in the `.ucasbss` section.
            3. define a global variable `global_var` with value `0xdeadbeef` in the `.ucasdata` section
            4. define a global variable `uninitialized_global_2` in the `.bss` section
            5. You should submit the `.o` file to finish this challenge.
        """)
        hint = description(f"""
        Hint:
             1. use `objdump -x <ELF_file>` to check the sections of the ELF file.
        """)

        self.description = challenge_description + task_description + hint
        print(self.description)

    def check(self):
        self.run()
        
        if not (self.binary_type == lief.ELF.E_TYPE.RELOCATABLE):
            print("The type of the binary should be relocatable object file!")
            sys.exit(1)

        if not all([
            self.check_function("main", ".ucastext"),
            self.check_function("foo", ".ucastext"),
            self.check_function("bar", ".ucastext"),
            self.check_bss("uninitialized_global_2"),
            self.check_section_data(".ucasbss", "uninitialized_global", 0x00000000),
            self.check_section_data(".ucasdata", "global_var", 0xdeadbeef)
        ]):
            sys.exit(1)

        else:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()


class IntroLevel29(ELFBase):
    def __init__(self):
        super().__init__()
        challenge_description = get_elf_structure_description()
        task_description = description(f"""
            Time to explore the ELF Header. The ELF Header structure is defined in `/usr/include/elf.h`.
            Due to the ELF file has both 32-bit and 64-bit versions, the structure of the ELF Header 
            has also been defined in two versions, which are `Elf32_Ehdr` and `Elf64_Ehdr`. `Elf64_Ehdr`
            has the same structure as `Elf32_Ehdr`, but the size of some fields is different. We use 
            `Elf64_Ehdr` as an example to introduce the structure of the ELF Header:
            ```
            typedef struct
            {{
                unsigned char e_ident[EI_NIDENT];     /* Magic number and other info */
                Elf64_Half    e_type;                 /* Object file type */
                Elf64_Half    e_machine;              /* Architecture */
                Elf64_Word    e_version;              /* Object file version */
                Elf64_Addr    e_entry;                /* Entry point virtual address */
                Elf64_Off     e_phoff;                /* Program header table file offset */
                Elf64_Off     e_shoff;                /* Section header table file offset */
                Elf64_Word    e_flags;                /* Processor-specific flags */
                Elf64_Half    e_ehsize;               /* ELF header size in bytes */
                Elf64_Half    e_phentsize;            /* Program header table entry size */
                Elf64_Half    e_phnum;                /* Program header table entry count */
                Elf64_Half    e_shentsize;            /* Section header table entry size */
                Elf64_Half    e_shnum;                /* Section header table entry count */
                Elf64_Half    e_shstrndx;             /* Section header string table index */
            }} Elf64_Ehdr;                      
            ```
            We recommend you to explore the structure of the ELF Header by yourself. You can use
            `readelf -h <ELF_file>` to check the ELF Header of relocatable object files, and then 
            compare the output with the structure of the ELF Header.
            
            In this challenge, you will know what the `e_ident` and `e_type` fields are used for.
                                       
            ** Your task **:
            1. I accidentally patched a few bytes in the ELF Header of given object file, and now 
               my tools can't recognize it. Can you help me fix it? I remember I only changed 3 bytes. 
               Please Fix the `level{level}.o` we provided, make it pass the check.
            2. You should submit the `.o` file to finish this challenge.
        """)
        hint = description(f"""
        Hint:
             1. use `readelf -h <ELF_file>` to check the ELF Header of the ELF file.
             2. You can use some hex editor tools to patch bytes in the ELF Header.
        """)

        self.description = challenge_description + task_description + hint
        print(self.description)

    def check(self):
        self.run()

        if not (self.binary_type == lief.ELF.E_TYPE.RELOCATABLE):
            print("The type of the binary should be relocatable object file!")
            sys.exit(1)

        if not all([
            self.check_function("main", ".text"),
            self.check_function("bar", ".text"),
            self.check_bss("uninitialized_global"),
            self.check_data("global_var", 0xdeadbeef)
        ]):
            sys.exit(1)
        
        if not self.check_hash("3542f053022283ffe994b03adf88cfbee1f4e50b3bc7b9d587b75b177681eb9d"):
            print("The hash of the binary is not correct! Maybe you have patched the wrong bytes?")
            sys.exit(1)

        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()


class IntroLevel30(ELFBase):
    def __init__(self):
        super().__init__()
        challenge_description = get_elf_structure_description()
        task_description = description(f"""
            In the previous challenge, we learned about the `e_ident` and `e_type` fields. 
            Now, we will try to explore the `e_shoff` field and the ** Section Header Table **. 
            We've already known that an ELF file has multiple sections, like `.text`, `.data`, `.bss`, etc.
            How ELF describes these sections? The answer is the ** Section Header Table **. 
            The Section Header Table is a crucial component of an object file. It contains 
            information about ELF file's sections, like section's name, offset, size, r/w/x permissions, etc.
            Essentially, ELF file's section structure is defined by the Section Header Table.
            
            The design of the Section Header Table is straightforward, It's essentially an array of 
            `Elf64_Shdr` structures, which are defined in `/usr/include/elf.h` as shown below:
                                       
            ```
            typedef struct
            {{
                Elf64_Word    sh_name;                /* Section name (string tbl index) */
                Elf64_Word    sh_type;                /* Section type */
                Elf64_Xword   sh_flags;               /* Section flags */
                Elf64_Addr    sh_addr;                /* Section virtual addr at execution */
                Elf64_Off     sh_offset;              /* Section file offset */
                Elf64_Xword   sh_size;                /* Section size in bytes */
                Elf64_Word    sh_link;                /* Link to another section */
                Elf64_Word    sh_info;                /* Additional section information */
                Elf64_Xword   sh_addralign;           /* Section alignment */
                Elf64_Xword   sh_entsize;             /* Entry size if section holds table */
            }} Elf64_Shdr;
            ```
                                       
            Each `Elf64_Shdr` structure describes a section in the ELF file, so `Elf64_Shdr` is 
            also called ** Section Descriptor **. The Section Header Table begins with a `NULL` entry, 
            meaning that the 1st section in the ELF file is described by the 2nd entry in the 
            Section Header Table.
                                       
            The location of the Section Header Table within the ELF file is given by the `e_shoff` 
            field in the ELF Header. The fields `e_shentsize` and `e_shnum` provide the size of 
            each entry (or element) in the Section Header Table and the total count of entries in the 
            Section Header Table, respectively. Here's how it looks:
            ```
            typedef struct
            {{
                unsigned char e_ident[EI_NIDENT];     /* Magic number and other info */
                Elf64_Half    e_type;                 /* Object file type */
                Elf64_Half    e_machine;              /* Architecture */
                Elf64_Word    e_version;              /* Object file version */
                Elf64_Addr    e_entry;                /* Entry point virtual address */
                Elf64_Off     e_phoff;                /* Program header table file offset */
                Elf64_Off     e_shoff;                /* Section header table file offset */
                Elf64_Word    e_flags;                /* Processor-specific flags */
                Elf64_Half    e_ehsize;               /* ELF header size in bytes */
                Elf64_Half    e_phentsize;            /* Program header table entry size */
                Elf64_Half    e_phnum;                /* Program header table entry count */
                Elf64_Half    e_shentsize;            /* Section header table entry size */
                Elf64_Half    e_shnum;                /* Section header table entry count */
                Elf64_Half    e_shstrndx;             /* Section header string table index */
            }} Elf64_Ehdr;                      
            ```
            
            In this challenge, you will know what the `e_shoff` and `e_shnum` fields are used for.
                                       
            ** Your task **:
            1. I accidentally patched only 1 byte in the ELF Header of given object file, 
               and now my tools can't recognize it. Can you help me fix it? Please Fix the 
               `level{level}.o` we provided, make it pass the check.
            2. You should submit the `.o` file to finish this challenge.
        """)
        hint = description(f"""
        Hint:
             1. use `readelf -h <ELF_file>` to check the ELF Header of the ELF file.
             2. use `readelf -S <ELF_file>` to check the Section Header Table of the ELF file.
             3. You can use some hex editor tools to patch bytes in the ELF Header.
        """)

        self.description = challenge_description + task_description + hint
        print(self.description)

    def check(self):
        self.run()

        if not (self.binary_type == lief.ELF.E_TYPE.RELOCATABLE):
            print("The type of the binary should be relocatable object file!")
            sys.exit(1)

        if not all([
            self.check_function("main", ".text"),
            self.check_function("bar", ".text"),
            self.check_bss("uninitialized_global"),
            self.check_data("global_var", 0xdeadbeef)
        ]):
            sys.exit(1)
        
        if not self.check_hash("3542f053022283ffe994b03adf88cfbee1f4e50b3bc7b9d587b75b177681eb9d"):
            print("The hash of the binary is not correct! Maybe you have patched the wrong bytes?")
            sys.exit(1)

        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()


class IntroLevel31(ELFBase):
    def __init__(self):
        super().__init__()
        challenge_description = get_elf_structure_description()
        task_description = description(f"""
            In the previous challenge, we learned about How ELF Header find the Section Header Table 
            in ELF. Now, we will try to explore the details in the ** Section Header Table **. 
            The design of the Section Header Table is straightforward, It's essentially an array of
            `Elf64_Shdr` structures, which are defined in `/usr/include/elf.h` as shown below:
            ```
            typedef struct
            {{
                Elf64_Word    sh_name;                /* Section name (string tbl index) */
                Elf64_Word    sh_type;                /* Section type */
                Elf64_Xword   sh_flags;               /* Section flags */
                Elf64_Addr    sh_addr;                /* Section virtual addr at execution */
                Elf64_Off     sh_offset;              /* Section file offset */
                Elf64_Xword   sh_size;                /* Section size in bytes */
                Elf64_Word    sh_link;                /* Link to another section */
                Elf64_Word    sh_info;                /* Additional section information */
                Elf64_Xword   sh_addralign;           /* Section alignment */
                Elf64_Xword   sh_entsize;             /* Entry size if section holds table */
            }} Elf64_Shdr;
            ```
            Here we introduce some key fields in the `Elf64_Shdr` structure.
            - `sh_name`: The name of the section, its value is section name string's offset in 
                         the section header's string table. But where is this string table? 
                         Remember the `e_shstrndx` in `Elf64_Ehdr`? Its value is the index of string table
                         in all sections in an ELF. So, we can find the section header's string table 
                         by `e_shstrndx`, then find section's name by `sh_name`.
            - `sh_type`: SHT_NULL:0 -> Unused section
                         SHT_PROGBITS:1 -> section with code, data, etc.
                         SHT_SYMTAB:2 -> symbol table
                         SHT_STRTAB:3 -> string table
                         SHT_RELA:4 -> relocation tables, we will talk about it later.
                         SHT_NOBITS:8 -> section with no data in the file, like .bss section.
            - `sh_flags`: SHF_WRITE:0x1 -> section is writable
                          SHF_ALLOC:0x2 -> section must be allocated memory in the process's virtual address space
                          SHF_EXECINSTR:0x4 -> section contains executable machine instructions
            - `sh_addr`: The virtual address of the section in the process's virtual address space, in object files, it's 0.
            
            In this challenge, you will try to recover the name and flags of `.text` section and `.data` section. 
                                       
            ** Your task **:
            1. I can not found `.text` and `.data` section in the given object file, 
               can you help me recover them? Please Fix the `level{level}.o` we provided, make it pass the check.
            2. The flag of above two sections seems weired, can you help me fix it?
            3. You should submit the `.o` file to finish this challenge.
        """)
        hint = description(f"""
        Hint:
             1. use `readelf -h <ELF_file>` to check the ELF Header of the ELF file.
             2. use `readelf -S <ELF_file>` to check the Section Header Table of the ELF file.
             3. You can use some hex editor tools to patch bytes in the ELF Header.
             4. By default, the permission of `.text` section is A(alloc) and X(execute), the permission of `.data` section is W(write) and A(alloc).
        """)

        self.description = challenge_description + task_description + hint
        print(self.description)

    def check(self):
        self.run()

        if not (self.binary_type == lief.ELF.E_TYPE.RELOCATABLE):
            print("The type of the binary should be relocatable object file!")
            sys.exit(1)

        if not all([
            self.check_function("main", ".text"),
            self.check_function("bar", ".text"),
            self.check_bss("uninitialized_global"),
            self.check_data("global_var", 0xdeadbeef)
        ]):
            sys.exit(1)
        
        if not self.check_hash("3542f053022283ffe994b03adf88cfbee1f4e50b3bc7b9d587b75b177681eb9d"):
            print("The hash of the binary is not correct! Maybe you have patched the wrong bytes?")
            sys.exit(1)

        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()

class IntroLevel32(ELFBase):
    def __init__(self):
        super().__init__()
        challenge_description = get_elf_structure_description()
        task_description = description(f"""
            In this challenge, we will continue to explore other details in the ** Section Header Table **.
            ```
            typedef struct
            {{
                Elf64_Word    sh_name;                /* Section name (string tbl index) */
                Elf64_Word    sh_type;                /* Section type */
                Elf64_Xword   sh_flags;               /* Section flags */
                Elf64_Addr    sh_addr;                /* Section virtual addr at execution */
                Elf64_Off     sh_offset;              /* Section file offset */
                Elf64_Xword   sh_size;                /* Section size in bytes */
                Elf64_Word    sh_link;                /* Link to another section */
                Elf64_Word    sh_info;                /* Additional section information */
                Elf64_Xword   sh_addralign;           /* Section alignment */
                Elf64_Xword   sh_entsize;             /* Entry size if section holds table */
            }} Elf64_Shdr;
            ```
            Here we introduce some other key fields in the `Elf64_Shdr` structure.
            - `sh_offset`: The section's offset in the ELF file.
            - `sh_size`: The section's size.
            - `sh_link`, `sh_info`: If the section is related to linking, `sh_link` and `sh_info` have 
                                    special meanings, which will be talked about later.
            - `sh_addralign`: The section's alignment in the process's virtual address space.
            - `sh_entsize`: If the section holds a table, like symbol table, relocation table, 
                            `sh_entsize` is the size of each entry in the table.
            
            In this challenge, you will try to recover the correct offset of `.text` section and `.data` section.
                                       
            ** Your task **:
            1. I found function and data in the given object file seems weired, can you help me recover them?
            2. I remember the correct value of `global_var` is 0xdeadbeef.
            3. You just need to patch 2 bytes in Section Header Tables to pass the check.
            4. You should submit the `.o` file to finish this challenge.
        """)
        hint = description(f"""
        Hint:
             1. use `readelf -h <ELF_file>` to check the ELF Header of the ELF file.
             2. use `readelf -S <ELF_file>` to check the Section Header Table of the ELF file.
             3. You can use some hex editor tools to patch bytes in the ELF Header.
        """)

        self.description = challenge_description + task_description + hint
        print(self.description)

    def check(self):
        self.run()

        if not (self.binary_type == lief.ELF.E_TYPE.RELOCATABLE):
            print("The type of the binary should be relocatable object file!")
            sys.exit(1)

        if not all([
            self.check_function("main", ".text"),
            self.check_function("bar", ".text"),
            self.check_bss("uninitialized_global"),
            self.check_data("global_var", 0xdeadbeef),
            # 55 48 89 e5:  push rbp; mov rbp, rsp, which is function prologue
            self.check_section_data(".text", "bar", b"\x55\x48\x89\xe5")
        ]):
            sys.exit(1)
        
        if not self.check_hash("3542f053022283ffe994b03adf88cfbee1f4e50b3bc7b9d587b75b177681eb9d"):
            print("The hash of the binary is not correct! Maybe you have patched the wrong bytes?")
            sys.exit(1)

        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()

class IntroLevel33(ELFBase):
    def __init__(self):
        super().__init__()
        task_description = description(f"""
            Before we introduce the next linking stage, let's talk about the **Symbol**. 
            In ELF (Executable and Linkable Format) files, symbols play a significant role. 
            A symbol in this context is essentially a named entity. It could be a variable, a function, 
            or any other identifiable piece of code within a program. The primary roles of symbols 
            in ELF files include:
            1. Linking: Symbols allow the linker to resolve references. When you want to build a program 
                        with several source files, each .c file is compiled into a separate relocatable object file. 
                        If one object file references a function or a variable defined in another object file, 
                        it does so through a symbol. During the linking stage, the linker will resolve these symbols,
                        replacing each reference to a symbol with the actual address of the entity referred to.
            2. Analysis: Symbols are essential for analysis tools like objdump/gdb/ghidra. A program with no symbols
                         is much harder to analyze than one with symbols.
            3. Dynamic linking: Symbols are also used in dynamic linking, where they allow a program to determine at 
                                runtime which functions to call or variables to use from a dynamically loaded library. 
            etc.
            
            Each object file has its own symbol table (.symtab), which contains a list of symbols defined in the 
            object file. The symbols in the symbol table could be one of the following types:
            1. global symbols: These symbols are visible to other object files and libraries, such as functions (`main`, `foo`) and global variables.
            2. external symbols: These symbols are defined in other object files or libraries, such as `printf` in libc.
            3. section name: These symbols are always generated by the compiler and assembler, used to mark the beginning of section.
            4. local symbols: These symbols are only visible to the object file itself, such as static functions and static variables.
            5. debug symbols: These symbols are generated by the compiler and assembler, used for debugging, usually in `DWARF` format.
            
            For us (and linkers), the most important symbols are ** global symbols ** and ** external symbols **. 

            In this challenge, you need to give me an object file with symbols we want.
                                       
            ** Your task **:
            1. Define a global function symbol `foo` and `main`.
            2. Define a local function symbol `bar`
            3. Define a local variable symbol `global_var` which in `.bss` section
            4. Define a global variable symbol `global_var_2` with value `0xdeadbeef` which in `.data` section
            5. Define an extern function symbol `myprintf`
            6. You should submit the `.o` file to finish this challenge.
        """)
        hint = description(f"""
        Hint:
             1. use `readelf -s <ELF_file>` to check the Symbol Table of the ELF file.
        """)

        self.description = task_description + hint
        print(self.description)

    def check(self):
        self.run()

        if not (self.binary_type == lief.ELF.E_TYPE.RELOCATABLE):
            print("The type of the binary should be relocatable object file!")
            sys.exit(1)

        if not all([
            self.check_symbol("foo", symbol_type = lief.ELF.SYMBOL_TYPES.FUNC, symbol_bind = lief.ELF.SYMBOL_BINDINGS.GLOBAL),
            self.check_symbol("main", symbol_type = lief.ELF.SYMBOL_TYPES.FUNC, symbol_bind = lief.ELF.SYMBOL_BINDINGS.GLOBAL),
            self.check_symbol("bar", symbol_type = lief.ELF.SYMBOL_TYPES.FUNC, symbol_bind = lief.ELF.SYMBOL_BINDINGS.LOCAL),
            self.check_symbol("global_var", symbol_type = lief.ELF.SYMBOL_TYPES.OBJECT, symbol_bind = lief.ELF.SYMBOL_BINDINGS.LOCAL),
            self.check_bss("global_var"),
            self.check_symbol("global_var_2", symbol_type = lief.ELF.SYMBOL_TYPES.OBJECT, symbol_bind = lief.ELF.SYMBOL_BINDINGS.GLOBAL),
            self.check_data("global_var_2", 0xdeadbeef),
            self.check_symbol("myprintf", symbol_bind = lief.ELF.SYMBOL_BINDINGS.GLOBAL, external = True)
        ]):
            sys.exit(1)

        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()

class IntroLevel34(ELFBase):
    def __init__(self):
        super().__init__()
        task_description = description(f"""
            The symbol table in ELF object files is a section of the file, with the section 
            name `.symtab`, just like the Section Header Table, the symbol table is also an 
            array composed of `Elf64_Sym` structures. Each such structure defines a symbol, 
            and the 0th element is an invalid undefined symbol, the structure `Elf64_Sym` is 
            defined as follows:
            
            ```
            typedef struct
            {{
                Elf64_Word    st_name;                /* Symbol name (string tbl index) */
                unsigned char st_info;                /* Symbol type and binding */
                unsigned char st_other;               /* Symbol visibility */
                Elf64_Section st_shndx;               /* Section index */
                Elf64_Addr    st_value;               /* Symbol value */
                Elf64_Xword   st_size;                /* Symbol size */
            }} Elf64_Sym;
            ```
            
            I will introduce some key fields in the `Elf64_Sym` structure.
            - st_name: The name of the symbol, its value is symbol name string's offset in 
                       the string table (Remember section's name?)
            - st_info: Symbol's type and binding
                       symbol's binding including: STB_LOCAL, STB_GLOBAL, STB_WEAK
                       symbol's type including: STT_NOTYPE, STT_OBJECT, STT_FUNC, STT_SECTION, STT_FILE
            - st_shndx: The section index of the symbol, if the symbol is not defined in 
                        any section, its value is SHN_UNDEF (external symbol)
            
            We did not tell you the meanings of `st_value` and `st_size`, so in this challenge, 
            you need to dig out the meanings of these two fields by yourself. But do not worry, 
            their meanings are actually simple.

            ** Your task **:
            1. Fix the `level{level}.o` we provided, make it pass the check. You just need to patch 2 bytes in the symbol table.
            2. You should submit the `.o` file to finish this challenge.
        """)
        hint = description(f"""
        Hint:
             1. use `readelf -s <ELF_file>` to check the Symbol Table of the ELF file.
        """)

        self.description = task_description + hint
        print(self.description)

    def check(self):
        self.run()

        if not (self.binary_type == lief.ELF.E_TYPE.RELOCATABLE):
            print("The type of the binary should be relocatable object file!")
            sys.exit(1)

        if not all([
            self.check_section_data(".text", "bar", b"\x55\x48\x89\xe5"),
            self.check_data("global_var", 0xdeadbeef),
        ]):
            sys.exit(1)

        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()


class IntroLevel35(ELFBase):
    def __init__(self):
        super().__init__()
        task_description = description(f"""
            Through the previous challenges, I believe you has gained a certain understanding
            of the outline and some details of ELF object files. In the following challenges, 
            we will talk about ** linking **. 
            What is Linking ? 
            Assuming our program consists of the following two source codes. 

            ``` a.c
            extern int global_var_b;
            extern void swap(int *a, int *b);
            extern int printf(const char *format, ...);

            int main() 
            {{
                int var_a = 100;
                printf("var_a = %d\\n", var_a);
                printf("global_var_b = %d\\n", global_var_b);

                printf("Swap the values of var_a and global_var_b\\n");

                swap(&var_a, &global_var_b);
                return 0;
            }}
            ```

            ``` b.c
            int global_var_b = 10;

            void swap(int *a, int *b) {{
                int temp = *a;
                *a = *b;
                *b = temp;
                return;
            }}
            ```                       

            Then we compile them into ELF object files separately. The next step is to "combine" 
            these two .o files together to create an ELF exeutable. This is what the linker should do.
                                       
            In this challenge, you need to use `ld` to link the given object files into an executable.
            Two given object files are `level35_a.o` and `level35_b.o`, which are compiled from above.
                                       
            ** Your task **:
            1. Using `ld` to link the given object files into an executable.
            2. Your submitted executable file should only contain symbols from object files and symbols generated by the linker.
            3. To avoid the ld's warning, set the executable's entry point to `main`.
            4. You should submit the executable file to finish this challenge.

        """)
        hint = description(f"""
        Hint:
             1. Think about how to find symbol of `printf` in libc when linking.
        """)

        self.description = task_description + hint
        print(self.description)

    def check(self):
        self.run()

        if not (self.binary_type == lief.ELF.E_TYPE.EXECUTABLE or self.binary_type == lief.ELF.E_TYPE.DYNAMIC):
            print("The type of the binary should be ELF executable file!")
            sys.exit(1)

        if not all([
            self.check_symbol("main", symbol_type = lief.ELF.SYMBOL_TYPES.FUNC),
            self.check_symbol("global_var_b", symbol_type = lief.ELF.SYMBOL_TYPES.OBJECT),
            self.check_symbol("swap", symbol_type = lief.ELF.SYMBOL_TYPES.FUNC),
            self.check_symbol("printf@", symbol_type = lief.ELF.SYMBOL_TYPES.FUNC, check_prefix = True),
            self.check_symbol("_start", symbol_type = lief.ELF.SYMBOL_TYPES.FUNC, check_not_exist = True),
            self.check_symbol("__libc_start_main@", check_prefix = True, check_not_exist = True)
        ]):
            sys.exit(1)
        
        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()


class IntroLevel36(ELFBase):
    def __init__(self):
        super().__init__()
        task_description = description(f"""
            You have learned how to use `ld` to link two .o files into an ELF executable file,
            now let's talk about how linkers like `ld` actually works. In other words, how does 
            the linker merge the various sections of .o files into the ELF executable file. 
            To minimize disk and memory space usage, the linker follows a practice of merging 
            sections with the same property together. For example, it merges the `.text` 
            sections of all .o files into the `.text` section of the output executable file, 
            then merges the `.data` sections, the `.bss` sections, and so on.
            
            Linkers that use above method generally adopt a two-pass linking approach, which 
            divides the entire linking process into two steps:
            1. Space and address allocation: Scan all input object files to get the offset, 
               length, and attributes of each section, as well as all symbol information in 
               the object files. Collect them and calculate the merged length and offset of 
               each section in the output file. Additionally, virtual address space needs to 
               be allocated for each section. (You can use `readelf -S <ELF_file>` to check 
               `Address` field of executable and object file)
            2. Symbol resolution and relocation: Based on the information collected in the first
               step, perform symbol resolution and relocation, adjusting the addresses in the code.
               Which is the core of linking process.
            
            In this challenge, we give you a linked ELF executable file, but I can't find the 
            `main` function in `objdump -d <ELF_file>` or IDA, can you help me fix it?

            ** Your task **:
            1. Explore the similarities and differences, as well as the meanings, of various fields 
               in the symbol table of ELF executable files and ELF object files.
            2. Fix the symbol table of the given executable file, make it pass the check. 
            3. You should submit the executable file to finish this challenge.

        """)
        hint = description(f"""
        Hint:
             1. Using `objdump -h --wide <ELF_file>` or `readelf -S --wide <ELF_file>` to check the section header table of the ELF file.
             2. Using `readelf -s <ELF_file>` to check the symbol table of the ELF file.
             3. `main` function is at the beginning of `.text` section.
        """)

        self.description = task_description + hint
        print(self.description)

    def check(self):
        self.run()

        if not (self.binary_type == lief.ELF.E_TYPE.EXECUTABLE or self.binary_type == lief.ELF.E_TYPE.DYNAMIC):
            print("The type of the binary should be ELF executable file!")
            sys.exit(1)

        if not all([
            self.check_symbol("main", symbol_type = lief.ELF.SYMBOL_TYPES.FUNC),
            self.check_section_data(".text", "main", b"\x55\x48\x89\xe5"),
            self.check_symbol("global_var_b", symbol_type = lief.ELF.SYMBOL_TYPES.OBJECT),
            self.check_symbol("swap", symbol_type = lief.ELF.SYMBOL_TYPES.FUNC),
            self.check_symbol("printf@", symbol_type = lief.ELF.SYMBOL_TYPES.FUNC, check_prefix = True),
            self.check_symbol("_start", symbol_type = lief.ELF.SYMBOL_TYPES.FUNC, check_not_exist = True),
            self.check_symbol("__libc_start_main@", check_prefix = True, check_not_exist = True)
        ]):
            sys.exit(1)
        
        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()

class IntroLevel37(ELFBase):
    def __init__(self):
        super().__init__()
        task_description = description(f"""
            Overall, the tasks performed by the linker include address and space allocation, 
            symbol resolution, and instruction fixing, which containing many details, such as
            space allocation strategies and how to fix instructions based on the relocation table, etc. 
            However, our goal is to understand the linking process in general, so we will 
            temporarily skip these details here. 
                                       
            Now, I would like you to take a look at the complete static linking process.
            
            In this challenge, Two object files `level37_a.o` and `level37_b.o` are given,
            I want you to link them into an executable file, make it execute normally.

            ** Your task **:
            1. Link the given object files into an executable file, and make it execute normally. 
            2. Find at least 4 `.o`(object file) or `.a`(static library) files used by the linker.
            3. You should submit a file containing the names of the `.o` or `.a` files used by the linker, and split them with ` `.
                for example `a.o b.o c.a d.a` 

        """)
        hint = description(f"""
        Hint:
             1. `--verbose` or `-v` option may help you.
        """)

        self.description = task_description + hint
        print(self.description)

    def check(self):
        self.get_submitted_file()
        with open(self.submitted_file_path, "r") as f:
            content = f.read().strip()
        
        candidate_pools = [
            "crt1.o", "crti.o", "crtbegin.o", "crtend.o", "crtn.o", "libc.a", "libm.a", "libgcc.a", "libpthread.a",
            "crtbeginS.o", "crtendS.o", "crtbeginT.o", "crtendT.o", "crtbegin.oS", "crtend.oS", "crtbeginT.oS", "crtendT.oS",
            "libgcc_eh.a"
        ]
        results = content.split(" ")

        if len(results) < 4:
            print(results)
            print("You should submit at least 4 files!")
            sys.exit(1)

        if not all([result in candidate_pools for result in results]):
            print("You have submitted some invalid files!")
            sys.exit(1)
        
        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()

class IntroLevel38(ELFBase):
    def __init__(self):
        task_description = description(f"""
            We have learned about how a program is generated from source code to executable file,
            and now we will talk about how a program is executed. Program is a group of instructions, 
            and data, which is stored in the file system, it's a static entity, but when we execute 
            it, operating system will load it into memory, and create a `process`, which is a instance
            of program, and it's a dynamic entity.
            
            Every process has its own independent virtual address space, its size is determined by computer's
            architecture, for example, in 32-bit system, the virtual address space is 4GB, in 64-bit system,
            the theoretical maximum size of virtual address space is 2^64 bytes, but in practice, it's much smaller.
            
            You may find that your computer only has 16GB or 32GB of memory, which seems like it would quickly 
            be consumed by just a few processes. So why hasn't this situation occurred? The answer is that 
            the operating system uses many techniques to reduce the memory consumption of processes, such as
            `paging`, `copy-on-write`, `shared memory`, etc. We will not discuss these techniques in detail here.
                                       
            In this challenge, you will explore the memory layout of a process.
            
            ** Your task **:
            1. find the virtual memory address range where the `.text` section is loaded, the `.data` section is loaded,
               the virtual address range of the stack, and the virtual address range of the heap.
            2. You should submit a file containing the above 4 virtual address ranges
                for example:
                ```
                0x400000-0x401000
                0x401000-0x402000
                0x7ffffffde000-0x7ffffffff000
                0x555555554000-0x555555555000
                ```
        """)
        hint = description(f"""
        Hint:
             1. `/proc/<pid>/maps` will help you to finish this challenge.
        """)

        self.description = task_description + hint
        print(self.description)
    
    def ground_truth(self, pid):
        res = subprocess.check_output(f"cat /proc/{pid}/maps", shell=True).decode().strip()
        entries = res.split("\n")

        result = { }

        for entry in entries:
            ranges = entry.split(" ")[0]
            range_start, range_end = ranges.split("-")
            range_start = int(range_start, 16)
            range_end = int(range_end, 16)
            if 0x4017c0 >= range_start and 0x4017c0 <= range_end:
                result["code"] = (range_start, range_end)
            if 0x5040b0 >= range_start and 0x5040b0 <= range_end:
                result["data"] = (range_start, range_end)
            if "[stack]" in entry:
                result["stack"] = (range_start, range_end)
            if "[heap]" in entry:
                result["heap"] = (range_start, range_end)
        
        return result

    def error(self, submit, ground_truth):
        print("The virtual address range is not correct!")
        print(f"Your range: {submit}")
        print(f"Ground truth: {hex(ground_truth[0])}-{hex(ground_truth[1])}")
        sys.exit(1)

    def check(self):
        self.child_pid = os.fork()

        if self.child_pid == 0:
            print_split_line()
            os.execve("./level38", ["./level38"], {})
        else:
            time.sleep(0.5)
            ground_truth = self.ground_truth(self.child_pid)

            self.get_submitted_file()
            with open(self.submitted_file_path, "r") as f:
                content = f.read().strip()
            
            ranges = content.split("\n")
            if len(ranges) != 4:
                print("You should submit 4 virtual address ranges!")
                sys.exit(1)
            
            for i in range(len(ranges)):
                r = ranges[i]
                range_start = int(r.split("-")[0], 16)
                range_end = int(r.split("-")[1], 16)

                if i == 0:
                    if not (range_start == ground_truth["code"][0] and range_end == ground_truth["code"][1]):
                        self.error(r, ground_truth["code"])
                    else:
                        continue
                if i == 1:
                    if not (range_start == ground_truth["data"][0] and range_end == ground_truth["data"][1]):
                        self.error(r, ground_truth["data"])
                    else:
                        continue
                if i == 2:
                    if not (range_start == ground_truth["stack"][0] and range_end == ground_truth["stack"][1]):
                        self.error(r, ground_truth["stack"])
                    else:
                        continue
                if i == 3:
                    if not (range_start == ground_truth["heap"][0] and range_end == ground_truth["heap"][1]):
                        self.error(r, ground_truth["heap"])
                    else:
                        continue
            
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
            
    def __del__(self):
        if self.child_pid == 0:
            os._exit(0)
        else:
            os.kill(self.child_pid, signal.SIGTERM)

class IntroLevel39(ELFBase):
    def __init__(self):
        task_description = description(f"""
            In the previous challenge, we have explored the basic memory layout of a process, but how
            does an ELF executable file get loaded into memory? In this challenge, we will explore 
            the ELF program header table, which is used to describe the memory layout of an ELF executable file.
            
            Operating system actually does not care about the detailed data in ELF sections, it mainly 
            cares about the privileges of each section, such as whether the section is readable, writable, or executable.
            So some ELF sections with the same privileges can be merged into one `Segment`. 
            
            `Segment` is created by the linker, and the structure used to describe `Segment` is `Program Header`. 
            Only ELF executable files and shared libraries have `Program Header Tables`, which is an array of 
            `Elf64_Phdr` structures, each such structure defines a `Segment`.
            
            ```
            typedef struct {{
                Elf64_Word    p_type;   /* Segment type : LOAD / DYNAMIC / INTERP / ... */
                Elf64_Word    p_flags;  /* Segment flags : R / W / X  */
                Elf64_Off     p_offset; /* Segment file offset : Segment's offset in the ELF file */
                Elf64_Addr    p_vaddr;  /* Segment virtual address : Segment's virtual address in the process's virtual address space */
                Elf64_Addr    p_paddr;  /* Segment physical address : same as virtual address in most cases */
                Elf64_Xword   p_filesz; /* Segment size in file : Segment's size in the ELF file */
                Elf64_Xword   p_memsz;  /* Segment size in memory : Segment's size in the process's virtual address space */
                Elf64_Xword   p_align;  /* Segment alignment : Segment's alignment attribute, it p_align is 10, then the 
                                           segment's address should be 2^10 aligned */
            }} Elf64_Phdr;                          
            ```
                                       
            In this challenge, we provide you with an ELF executable file, but I modified 1 byte in the ELF file, and I found this
            ELF file can not be executed normally, can you help me fix it?
                                       
            ** Your task **:
            1. Fix the `level{level}` we provided, make it pass the check. You just need to patch 1 byte in the program header table.
        """)
        hint = description(f"""
        Hint:
             1. use `readelf -l <ELF_file>` to check the Program Header Table of the ELF file.
             2. use `readelf -h <ELF_file>` to check the ELF Header of the ELF file.
        """)

        self.description = task_description + hint
        print(self.description)

    def check(self):
        self.run()

        if not (self.binary_type == lief.ELF.E_TYPE.EXECUTABLE or self.binary_type == lief.ELF.E_TYPE.DYNAMIC):
            print("The type of the binary should be ELF executable file!")
            sys.exit(1)

        if not all([
            self.check_hash("4228c8043f79c624e6c71af887eb372d8c89d6446453cef5d740038dcb5b28df")
        ]):
            print("The hash of the binary is not correct! Maybe you have patched the wrong bytes?")
            sys.exit(1)
        
        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()


class IntroLevel40(ELFBase):
    def __init__(self):
        task_description = description(f"""
            In this challenge, we will explore the basic knowledge of dynamic linking. In your computer,
            most of the programs are dynamically linked, because dynamic linking can reduce the size of
            executable files, and it can also reduce the memory consumption of processes.
            
            For a dynamically linked ELF executable file, the dynamic linker (maybe `ld-linux-xxx.so.2`)
            is needed to load the executable, and the dynamic linker will also load the shared libraries
            (`.so` files, like libc.so) needed by the executable file into the process's virtual address space.
            You can use `ldd <ELF_file>` to check the shared libraries needed by the executable file.
                                       
            In this challenge, we provide you with a dynamically linked ELF executable file (`level40`) and 
            a shared library (`liblevel40.so`)
            
            ** Your task **:
            1. Run the `level40` executable file, and give me the PID of the process.
            2. You should submit a file containing the virtual address ranges where `printf` function and 
                `my_swap` function are loaded.
                for example:
                ```
                0x400000-0x401000
                0x401000-0x402000
                ```
        """)
        hint = description(f"""
        Hint:
             1. `LD_LIBRARY_PATH` is your friend :)
        """)

        self.description = task_description + hint
        print(self.description)

    def ground_truth(self, pid):
        res = subprocess.check_output(f"cat /proc/{pid}/maps", shell=True).decode().strip()
        entries = res.split("\n")

        result = { }

        for entry in entries:
            ranges = entry.split(" ")[0]
            range_start, range_end = ranges.split("-")
            range_start = int(range_start, 16)
            range_end = int(range_end, 16)
            if "libc.so.6" in entry and "r-xp" in entry:
                result["libc"] = (range_start, range_end)
            if "liblevel40.so" in entry and "r-xp" in entry:
                result["liblevel40"] = (range_start, range_end)
        
        return result

    def error(self, submit, ground_truth):
        print("The virtual address range is not correct!")
        print(f"Your range: {submit}")
        print(f"Ground truth: {hex(ground_truth[0])}-{hex(ground_truth[1])}")
        sys.exit(1)

    def check(self):
        pid = input("PID > ")
        if not pid.isdigit():
            print("PID should be a number!")
            sys.exit(1)

        ground_truth = self.ground_truth(pid)
        
        self.get_submitted_file()
        with open(self.submitted_file_path, "r") as f:
            content = f.read().strip()
        
        ranges = content.split("\n")
        if len(ranges) != 2:
            print("You should submit 2 virtual address ranges!")
            sys.exit(1)

        for i in range(len(ranges)):
            r = ranges[i]
            range_start = int(r.split("-")[0], 16)
            range_end = int(r.split("-")[1], 16)

            if i == 0:
                if not (range_start == ground_truth["libc"][0] and range_end == ground_truth["libc"][1]):
                    self.error(r, ground_truth["libc"])
                else:
                    continue
            if i == 1:
                if not (range_start == ground_truth["liblevel40"][0] and range_end == ground_truth["liblevel40"][1]):
                    self.error(r, ground_truth["liblevel40"])
                else:
                    continue
        
        print("Congratulations! You have passed this challenge! Following is your sesame:")
        get_sesame()


class IntroLevel41(ELFBase):
    def __init__(self):
        task_description = description(f"""
            In Linux ELF, PLT(Procedure Linkage Table) and GOT(Global Offset Table) are two ** important ** 
            concepts, which are used to implement dynamic linking. 
            
            PLT is a series of code blocks in ELF used to implement external function jumps. When a program
            calls a function in a shared library, the program actually calls the corresponding PLT entry first.
            The main purpose of PLT is to implement lazy binding, which means that the function address will 
            be resolved when the function is called for ** the first time **, and the resolved address will be cached
            in GOT. This will reduce the time spent on dynamic linking.
                                       
            GOT is a series of data blocks in ELF used to store the addresses of external functions. Initially,
            the value in a GOT entry is the address of the 2nd instruction of the corresponding PLT entry, which
            can be used to resolve the address of the external function. After the function is called for the first
            time, the true address of the external function will be cached in GOT.

            Following is a simple ascii flow graph to show how PLT and GOT work together:
            ```
                      +-------------------------------------------------+
                      |                                                 |
                      |  +--------------------------------------------+ |
                      |  | .text                                      | |
                      |  |                                            | |
                      |  |      ...                                   | |
                      |  |      ...                                   | |
            +-----------------+ 400637: jmp 400480 <memcmp@plt>       | |
            |         |  |      ...                                   | |
            |         |  |      ...                                   | |
            |         |  +--------------------------------------------+ |
            | 1st step|                                                 |
            |         |                                                 |
            |         |  +--------------------------------------------+ |
            |         |  | .plt                                       | |
            |         |  |                                            | |
            |         |  |      ...                                   | |
            +-----------------> 400480: jmp 601028 <memcmp@got> +---------------+
            +-----------------> 400486: push 0x2                      | |       |
            |         |  |      40048b: jmp 400450 <.plt>             | |       |
            |         |  |      ...                                   | |       |
            |         |  |                                            | |       |
            |         |  |                                            | |       |
            |         |  +--------------------------------------------+ |       |
            | 3rd step|                                                 | 2nd step
            |         |                                                 |       |
            |         |  +--------------------------------------------+ |       |
            |         |  |                                            | |       |
            |         |  | .got                                       | |       |
            |         |  |      ...                                   | |       |
            +----------------+  601028: 0x400486      <-------------------------+
                      |  |      ...                                   | |
                      |  |                                            | |
                      |  +--------------------------------------------- |
                      |                                                 |
                      +-------------------------------------------------+
                                call memcmp function 1st time
                                       

                      +-------------------------------------------------+
                      |                                                 |
                      |  +--------------------------------------------+ |
                      |  | .text                                      | |
                      |  |                                            | |
                      |  |      ...                                   | |
                      |  |      ...                                   | |
            +-----------------+ 400637: jmp 400480 <memcmp@plt>       | |
            |         |  |      ...                                   | |
            |         |  |      ...                                   | |
            |         |  +--------------------------------------------+ |
            | 1st step|                                                 |
            |         |                                                 |
            |         |  +--------------------------------------------+ |
            |         |  | .plt                                       | |
            |         |  |                                            | |
            |         |  |      ...                                   | |
            +-----------------> 400480: jmp 601028 <memcmp@got> +---------------+
                      |  |      400486: push 0x2                      | |       |
                      |  |      40048b: jmp 400450 <.plt>             | |       |
                      |  |      ...                                   | |       |
                      |  |                                            | |       |
                      |  |                                            | |       |
                      |  +--------------------------------------------+ |       +
                      |                                                 | 2nd step
                      |                                                 |       +
                      |  +--------------------------------------------+ |       |
                      |  |                                            | |       |
                      |  | .got                                       | |       |
                      |  |      ...                                   | |       |
                      |  |      601028: <memcmp@libc.so>   <--------------------+
                      |  |      ...                                   | |
                      |  |                                            | |
                      |  +--------------------------------------------+ |
                      |                                                 |
                      +-------------------------------------------------+
                                call memcmp function 2nd time
           
            ```

            In this challenge, you will explore the PLT and GOT of a dynamically linked ELF executable file.
            and try to finish a baby GOT hijacking to pass the check.

            ** Your task **:
            1. Using gdb to debug the given `level41` ELF executable file, explore how PLT and GOT work together.
            2. You have one chance to modify the process's memory, try to pass the check.
                                       
        """)
        hint = description(f"""
        Hint:
             1. No hint :)
        """)

        self.description = task_description + hint
        print(self.description)
    
    def check(self):
        process = subprocess.Popen("./level41", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        outputs = ""
        while True:
            output_line = process.stdout.readline()
            outputs += output_line
            if not output_line:
                break
            print(output_line.strip())

            if "Please input the target memory address you want to hijack:" in output_line:
                target_addr = input("target address > ")
                process.stdin.write(target_addr + "\n")
                process.stdin.flush()
            
            if "Please input the value you want to write:" in output_line:
                value = input("value > ")
                process.stdin.write(value + "\n")
                process.stdin.flush()

        remaining_output, errors = process.communicate()
        outputs += remaining_output
        
        if errors:
            print("Program errors:", errors.strip())
            sys.exit(1)
        
        if "Congratulation!" in outputs:
            print("Congratulations! You have passed this challenge! Following is your sesame:")
            get_sesame()
        else:
            print("You failed to pass this challenge!")
            sys.exit(1)

# TODO: introduce the program memory space, using variable and asserts to teaching the growth of stack (call and stack variables) and heap. For example, for 4 stack variables and 3 call-chains to demonstrate the stack is growing from high address to low address. 

# TODO: introduce the calling convention and stack frame in a function, using assert and argc/argv (get offset) for students to understand stack frame

# TODO: get the target memory of variable in the source code, also using assert and argc/argv(get range/offset) for students to understand stack frame

if __name__ == "__main__":
    challenge = globals()[f"IntroLevel{level}"]
    challenge().check()