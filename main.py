import json
import sys

from dataclasses import dataclass

device = "mac"
assert device in ["mac", "linux"]

debug_mode = False

@dataclass
class Instruction:
    pass

@dataclass
class Label(Instruction):
    pass

@dataclass
class Jump(Instruction):
    target: int

@dataclass
class JumpCond(Instruction):
    cond_code: str
    label: str

@dataclass
class Mov(Instruction):
    src: str
    dest: str

@dataclass
class Ret(Instruction):
    pass

@dataclass
class Operator:
    pass

@dataclass
class Neg(Operator):
    pass

@dataclass
class Not(Operator):
    pass

@dataclass 
class Add(Operator):
    pass

@dataclass
class Sub(Operator):
    pass

@dataclass
class Mul(Operator):
    pass

@dataclass
class Operand:
    pass

@dataclass
class Reg:
    name: str

@dataclass
class Unary(Instruction):
    unary_operator: Operator
    operand: str

@dataclass
class Binary(Instruction):
    binary_operator: str
    src: str
    dest: str

@dataclass
class Print(Instruction):
    args: list[str]
    types: list[str]
    

@dataclass
class Imm(Operand):
    val: int

@dataclass
class Pseudo:
    identifier: str

@dataclass
class Idiv(Instruction):
    pass

@dataclass
class AllocateStack(Instruction):
    num: int

@dataclass
class Stack:
    num: int

@dataclass
class ParseCmdLine(Instruction):
    src: int
    idx: int
    t: str


def format_operand(operand: Operand) -> str:
    match operand:
        case Reg(name):
            reg_mapping = {
                "AX": "%eax",
                "DX": "%edx",
                "R10": "%r10d",
                "R11": "%r11d",
            }
            assert name in reg_mapping
            return reg_mapping[name]
        case Stack(num):
            return f"{num}(%rsp)"
        case Imm(num):
            return f"${num}"


def format_operator(operator):
    match operator:
        case Neg():
            return "negl"
        case Not():
            return "notl"
        case Add():
            return "addl"
        case Sub():
            return "subl"
        case Mul():
            return "imull"

def format_instruction(construct):
    assert isinstance(construct, Instruction)
    match construct:
        case Mov(src, dest):
            return [f"movl {src}, {dest}"]
        case Ret():
            return [
                "movq %rbp, %rsp",
                "popq %rbp",
                "retq"
            ]
        case Unary(operator, operand):
            return [f"{format_operator(operator)} {operand}"]
        case Binary(operator, src, dest):
            return [f"{format_operator(operator)} {src}, {dest}"]
        case AllocateStack(num):
            return [f"subq ${num}, %rsp"]
        
        case Print(args, types):
            lines = []
            first = True
            assert len(args) == len(types)
            n = len(args)
            for i in range(n):
                lines.append(f"movl {args[i]}, %edi")
                if types[i] == "int":
                    lines.append(f"callq __bril_print_int")
                else:
                    lines.append(f"callq __bril_print_bool")

                if i < n - 1:
                    lines.append("callq __bril_print_sep")
                else:
                    lines.append("callq __bril_print_end")
            return lines
        
        case ParseCmdLine(src, idx, t):
            assert t in ["int", "bool"]
            lines = []
            lines.append(f"movq ${idx}, %esi")
            lines.append(f"movl {src}, %rdi")
            if t == "int":
                lines.append("callq __bril_parse_int")
            else:
                lines.append("callq __bril_parse_bool")
            return lines



    raise NotImplementedError(f"Unknown instruction: {construct}")





    
@dataclass
class Function:
    name: str
    instructions: list[Instruction]

def format_function(f: Function) -> list[str]:
    output = [
        f".globl _{f.name}",
        ".p2align	4, 0x90",
        f"_{f.name}:",
        "pushq %rbp",
        "movq %rsp, %rbp"
    ]
    for instruction in f.instructions:
        output.extend(format_instruction(instruction))
    

    output.append("movq %rbp, %rsp")
    output.append("xorl %eax, %eax")
    output.append("popq %rbp")
    output.append("retq")

    return output




@dataclass
class Program:
    functions: list[Function]

def format_program(prog: Program):

    output = []
    if device == "linux":
        output.append('.section .note.GNU-stack,"",@progbits')
    elif device == "mac":
        output.extend([
            ".section	__TEXT,__text,regular,pure_instructions",
            ".build_version macos, 15, 0	sdk_version 15, 2"
        ])
    
    for f in prog.functions:
        output.extend(format_function(f))
    
    output.append(".subsections_via_symbols")
    return output




# def instr_to_assembly(instr):
#     print(instr)
#     output = []
#     if "op" in instr:
#         op = instr["op"]
#         if op == "add":
#             pass
#         elif op == "ret":
#             if "args" in instr:
#                 var = instr["args"][0]
#                 assert len(instr["args"]) == 1
                
#             output.append(Ret())
        


def func_to_assembly(func):

    lines = []

    var_types = {}
    var_slots = {}
    var_count = 0
    
    for i, arg in enumerate(func.get("args", [])):
        if debug_mode:
            print("arg:", arg)
        name = arg["name"]
        var_types[name] = arg["type"]
        var_slots[name] = var_count

        var_count += 1


    for instr in func["instrs"]:
        if "dest" not in instr:
            continue

        dest = instr["dest"]
        if dest not in var_slots:
            var_slots[dest] = var_count
            var_count += 1
            
        if "type" in instr:
            typ = instr["type"]
            if dest in var_types and var_types[dest] != typ:
                raise TypeError()
            var_types[dest] = typ



    stack_bytes = var_count * 8
    if stack_bytes > 0:
        lines.append(AllocateStack(stack_bytes))

    for i, arg in enumerate(func.get("args", [])):
        if debug_mode:
            print(i, arg)
        offset = 8 * var_slots[arg["name"]]
        lines.append(ParseCmdLine(f"{offset}(%ebx)", i, arg["type"]))
        lines.append(Mov("%eax", f"{offset}(%rsp)"))

    for instr in func["instrs"]:
        if debug_mode:
            print(instr)
        if "label" in instr:
            if debug_mode:
                print(instr["label"])
            pass
        if "op" in instr:
            op = instr["op"]

            if op == "const":
                dest = instr["dest"]
                val = instr["value"]
                off = var_slots[dest] * 8
                lines.append(Mov(f"${val}", f"{off}(%rsp)"))

            elif op in ("add", "sub", "mul"):
                arg1, arg2 = instr["args"]
                dest = instr["dest"]
                off1 = var_slots[arg1] * 8
                off2 = var_slots[arg2] * 8
                lines.append(Mov(f"{off1}(%rsp)", "%eax"))

                temp = {
                    "add": Add(),
                    "sub": Sub(),
                    "mul": Mul()
                }
                lines.append(Binary(temp[op], f"{off2}(%rsp)", "%eax"))

                off_dest = var_slots[dest] * 8
                lines.append(Mov("%eax", f"{off_dest}(%rsp)"))
            
            elif op == "lt":
                pass

            elif op == "ret":
                if len(instr["args"]) > 0:
                    ret_var = instr["args"][0]
                    off = var_slots[ret_var] * 8
                    lines.append(Mov(f"{off}(%rsp)", "%eax"))
                lines.append(Ret())

            elif op == "print":
                args = [f"{8 * var_slots[x]}(%rsp)" for x in instr["args"]]
                types = [var_types[x] for x in instr["args"]]
                lines.append(Print(args, types))

            elif op == "id":
                print(instr)
                dest = instr["dest"]
                src = instr["args"][0]
                off_src = var_slots[src] * 8
                off_dest = var_slots[dest] * 8
                lines.append(Mov(f"{off_src}(%rsp)", f"{off_dest}(%rsp)"))

            else:
                raise NotImplementedError(f"not supported op: {op}")
            
    return Function(func["name"], lines)





def bril_to_assembly(prog):
    return Program([func_to_assembly(func) for func in prog["functions"]])


if __name__ == "__main__":
    prog = json.load(sys.stdin)

    # print(Ret().format())
    # print(format_instruction(Ret()))
    # print(format_instruction(Mov("hi", "bye")))
    prog = bril_to_assembly(prog)
    if debug_mode:
        print(prog)

    formatted = format_program(prog)
    [print(i) for i in formatted]





