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
    name: str


@dataclass
class Jump(Instruction):
    target: int


@dataclass
class JumpCond(Instruction):
    cond_code: str
    label: str


@dataclass
class Mov(Instruction):
    t: str
    src: str
    dest: str


@dataclass
class Push(Instruction):
    t: str
    reg: str


@dataclass
class Pop(Instruction):
    t: str
    reg: str


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
class Cmp(Operator):
    pass


@dataclass
class Set(Operator):
    code: str


@dataclass
class Test(Operator):
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
class Call(Instruction):
    t: str
    name: str


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
class Div(Operator):
    pass


@dataclass
class AllocateStack(Instruction):
    num: int


@dataclass
class Stack(Operand):
    num: int


@dataclass
class Cqo(Instruction):
    pass


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
            return "negq"
        case Not():
            return "notq"
        case Add():
            return "addq"
        case Sub():
            return "subq"
        case Mul():
            return "imulq"
        case Div():
            return "idivq"
        case Cmp():
            return "cmpq"
        case Set(code):
            return f"set{code}"
        case Test():
            return "testq"


def format_instruction(construct):
    assert isinstance(construct, Instruction)
    match construct:
        case Mov(t, src, dest):
            return [f"mov{t} {src}, {dest}"]
        case Push(t, reg):
            return [f"push{t} {reg}"]
        case Pop(t, reg):
            return [f"pop{t} {reg}"]
        case Ret():
            # return ["movq %rbp, %rsp", "popq %rbp", "retq"]
            return ["retq"]
        case Unary(operator, operand):
            return [f"{format_operator(operator)} {operand}"]
        case Binary(operator, src, dest):
            return [f"{format_operator(operator)} {src}, {dest}"]
        case AllocateStack(num):
            return [f"subq ${num}, %rsp"]
        case Call(t, name):
            if name == "main":
                name = "main_main"
            return [f"call{t} _{name}"]
        case Label(name):
            name = "_" + name.replace(".", "_")
            return [f"{name}:"]
        case Jump(label):
            label = "_" + label.replace(".", "_")
            return [f"jmp {label}"]
        case JumpCond(cond_code, label):
            label = "_" + label.replace(".", "_")
            return [f"j{cond_code} {label}"]
        case Cqo():
            return ["cqo"]

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
    ]
    for instruction in f.instructions:
        output.extend(format_instruction(instruction))

    output.append("movq %rbp, %rsp")
    output.append("xorq %rax, %rax")
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
        output.extend(
            [
                ".section	__TEXT,__text,regular,pure_instructions",
                ".build_version macos, 15, 0	sdk_version 15, 2",
            ]
        )

    for f in prog.functions:
        output.extend(format_function(f))

    output.append(".subsections_via_symbols")
    return output


def fake_main_to_assembly(func):
    lines = []
    lines.append(Push("q", "%rbp"))
    lines.append(Mov("q", "%rsp", "%rbp"))

    if "args" in func and len(func["args"]) > 0:

        arg_regs = ["%rdi", "%rsi", "%rdx", "%rcx", "%r8", "%r9"]

        if func.get("args", []):
            args = func["args"]
            var_count = len(args)

            stack_bytes = (var_count + 1) * 8
            if stack_bytes > 0:
                lines.append(AllocateStack(stack_bytes))
                lines.append(Mov("q", "%rbx", f"{var_count * 8}(%rsp)"))
                lines.append(Mov("q", "%rsi", "%rbx"))

            for i, arg in enumerate(args):
                name = arg["name"]

                offset = 8 * i
                lines.append(Mov("q", "%rbx", "%rdi"))
                lines.append(Mov("q", f"${i + 1}", "%rsi"))
                if arg["type"] == "int":
                    lines.append(Call("q", "_bril_parse_int"))
                else:
                    lines.append(Call("q", "_bril_parse_bool"))
                lines.append(Mov("q", "%rax", f"{offset}(%rsp)"))

            for i, arg in enumerate(args):
                off = i * 8
                if i < len(arg_regs):
                    lines.append(Mov("q", f"{off}(%rsp)", arg_regs[i]))
                else:
                    raise NotImplementedError(">6 args")
            lines.append(Mov("q", f"{var_count * 8}(%rsp)", "%rbx"))

    lines.append(Call("q", "main_main"))
    # lines.append(Jump("main_main"))

    lines.extend([Mov("q", "%rbp", "%rsp"), Pop("q", "%rbp"), Ret()])

    return Function(func["name"], lines)


def func_to_assembly(func):

    lines = []
    lines.append(Push("q", "%rbp"))
    lines.append(Mov("q", "%rsp", "%rbp"))

    var_types = {}
    var_slots = {}
    var_count = 0

    arg_regs = ["%rdi", "%rsi", "%rdx", "%rcx", "%r8", "%r9"]
    for i, arg in enumerate(func.get("args", [])):
        if i < len(arg_regs):
            var_slots[arg["name"]] = var_count
            var_types[arg["name"]] = arg["type"]
            assert var_count == i
            var_count += 1
            # lines.append(Mov("q", arg_regs[i], f"{off}(%rsp)"))
        else:
            raise NotImplementedError(">6")

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
        if i < len(arg_regs):
            off = i * 8
            lines.append(Mov("q", arg_regs[i], f"{off}(%rsp)"))
        else:
            raise NotImplementedError(">6")

    for instr in func["instrs"]:
        if debug_mode:
            print(instr)
        if "label" in instr:
            if debug_mode:
                print(instr["label"])

            lines.append(Label(func["name"] + instr["label"]))
            continue

        if "op" in instr:
            op = instr["op"]

            if op == "const":
                dest = instr["dest"]
                val = instr["value"]
                off = var_slots[dest] * 8

                if instr["type"] == "int":
                    lines.append(Mov("q", f"${val}", f"{off}(%rsp)"))
                else:
                    if val:
                        lines.append(Mov("q", f"$1", f"{off}(%rsp)"))
                    else:
                        lines.append(Mov("q", f"$0", f"{off}(%rsp)"))

            elif op in ("add", "sub", "mul"):
                arg1, arg2 = instr["args"]
                dest = instr["dest"]
                off1 = var_slots[arg1] * 8
                off2 = var_slots[arg2] * 8
                lines.append(Mov("q", f"{off1}(%rsp)", "%rax"))

                temp = {"add": Add(), "sub": Sub(), "mul": Mul()}
                lines.append(Binary(temp[op], f"{off2}(%rsp)", "%rax"))

                off_dest = var_slots[dest] * 8
                lines.append(Mov("q", "%rax", f"{off_dest}(%rsp)"))

            elif op in ("lt", "gt", "le", "ge", "eq"):
                arg1, arg2 = instr["args"]
                dest = instr["dest"]
                off1 = var_slots[arg1] * 8
                off2 = var_slots[arg2] * 8
                off_dest = var_slots[dest] * 8

                cmp_map = {
                    "lt": "l",
                    "gt": "g",
                    "le": "le",
                    "ge": "ge",
                    "eq": "e",
                }

                lines.append(Mov("q", f"{off1}(%rsp)", "%rax"))
                lines.append(Binary(Cmp(), f"{off2}(%rsp)", "%rax"))
                lines.append(Unary(Set(cmp_map[op]), "%al"))
                lines.append(Mov("zbq", "%al", "%rax"))
                lines.append(Mov("q", "%rax", f"{off_dest}(%rsp)"))

            elif op == "div":
                arg1, arg2 = instr["args"]
                dest = instr["dest"]
                off1 = var_slots[arg1] * 8
                off2 = var_slots[arg2] * 8
                off_dest = var_slots[dest] * 8

                lines.append(Mov("q", f"{off1}(%rsp)", "%rax"))
                lines.append(Cqo())
                lines.append(Unary(Div(), f"{off2}(%rsp)"))
                lines.append(Mov("q", "%rax", f"{off_dest}(%rsp)"))

            elif op == "ret":
                if "args" in instr and len(instr["args"]) > 0:
                    ret_var = instr["args"][0]
                    off = var_slots[ret_var] * 8
                    lines.append(Mov("q", f"{off}(%rsp)", "%rax"))
                lines.extend([Mov("q", "%rbp", "%rsp"), Pop("q", "%rbp"), Ret()])

            elif op == "print":
                args = [f"{8 * var_slots[x]}(%rsp)" for x in instr["args"]]
                types = [var_types[x] for x in instr["args"]]

                n = len(args)

                for i in range(n):
                    lines.append(Mov("q", args[i], "%rdi"))
                    if types[i] == "int":
                        lines.append(Call("q", "_bril_print_int"))
                    else:
                        lines.append(Call("q", "_bril_print_bool"))

                    if i < n - 1:
                        lines.append(Call("q", "_bril_print_sep"))
                    else:
                        lines.append(Call("q", "_bril_print_end"))

            elif op == "id":
                dest = instr["dest"]
                src = instr["args"][0]
                off_src = var_slots[src] * 8
                off_dest = var_slots[dest] * 8

                lines.append(Mov("q", f"{off_src}(%rsp)", "%rax"))
                lines.append(Mov("q", "%rax", f"{off_dest}(%rsp)"))

            elif op == "br":
                true_label, false_label = instr["labels"]
                cond_var = instr["args"][0]
                off = var_slots[cond_var] * 8

                lines.append(Mov("q", f"{off}(%rsp)", "%rax"))
                lines.append(Binary(Test(), "%rax", "%rax"))
                lines.append(JumpCond("ne", func["name"] + true_label))
                lines.append(Jump(func["name"] + false_label))

            elif op == "jmp":
                target = instr["labels"][0]
                lines.append(Jump(func["name"] + target))

            elif op == "call":
                # print(instr)
                func_name = instr["funcs"][0]
                args = instr.get("args", [])
                dest = instr.get("dest", None)

                for i, a in enumerate(args):
                    off = var_slots[a] * 8
                    if i < len(arg_regs):
                        lines.append(Mov("q", f"{off}(%rsp)", arg_regs[i]))
                    else:
                        raise NotImplementedError(">6 args")

                lines.append(Call("q", func_name))

                if dest is not None:
                    off_d = var_slots[dest] * 8
                    lines.append(Mov("q", "%rax", f"{off_d}(%rsp)"))

            else:
                raise NotImplementedError(f"not supported op: {op}")

    lines.extend([Mov("q", "%rbp", "%rsp"), Pop("q", "%rbp"), Ret()])

    return Function(func["name"], lines)


def bril_to_assembly(prog):
    functions = []
    for func in prog["functions"]:
        name = func["name"]
        if name == "main":
            functions.append(fake_main_to_assembly(func))
            func["name"] = "main_main"
            functions.append(func_to_assembly(func))
        else:
            functions.append(func_to_assembly(func))
        # functions.append(func_to_assembly(func))

    return Program(functions)


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
