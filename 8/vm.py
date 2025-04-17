import os
import sys

ARITH_BINARY = {
    "add": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=D+M"],
    "sub": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=M-D"],
    "and": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=D&M"],
    "or": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=D|M"],
}

ARITH_UNARY = {
    "neg": ["@SP", "A=M-1", "M=-M"],
    "not": ["@SP", "A=M-1", "M=!M"],
}

ARITH_TEST = {
    "eq": "JEQ",
    "gt": "JGT",
    "lt": "JLT",
}

SEGLABEL = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
}

SEGMENTS = {
    "local": "pointer",
    "argument": "pointer",
    "this": "pointer",
    "that": "pointer",
    "temp": "fixed",
    "pointer": "fixed",
    "static": "constant",
    "constant": "constant",
}

LABEL_NUMBER = 0


def getPushD():
    return ["@SP", "A=M", "M=D", "@SP", "M=M+1"]


def getPopD():
    return ["@SP", "AM=M-1", "D=M"]


def _getPushMem(src):
    """
    Helper function to push memory to location src to stack
    """
    return [
        f"@{src}",
        "D=M",
        *getPushD(),
    ]


def _getPushLabel(src):
    """
    Helper function to push the ROM address of a label to the
    stack.
    """
    return [
        f"@{src}",
        "D=A",
        *getPushD(),
    ]


def _getPopMem(dest):
    """
    Helper function to pop the stack to the memory address dest.
    """
    return [
        *getPopD(),
        f"@{dest}",
        "M=D",
    ]


def _getMoveMem(src, dest):
    """
    Helper function to move the contents of src to memory location dest.
    """
    return [
        f"@{src}",
        "D=M",
        f"@{dest}",
        "M=D",
    ]


def setDtoPointer(base, i):
    return [f"@{base}", "D=M", f"@{i}", "A=D+A", "D=M"]


def setPointerToD(base, i):
    return [
        "@R13",
        "M=D",
        f"@{base}",
        "D=M",
        f"@{i}",
        "D=D+A",
        "@R14",
        "M=D",
        "@R13",
        "D=M",
        "@R14",
        "A=M",
        "M=D",
    ]


def pointerSeg(pushpop, seg, index):
    base = SEGLABEL[seg]
    if pushpop == "push":
        asm = setDtoPointer(base, index) + getPushD()
    elif pushpop == "pop":
        asm = getPopD() + setPointerToD(base, index)
    return asm


def fixedSeg(pushpop, seg, index):
    base = 5 if seg == "temp" else 3
    if pushpop == "push":
        asm = [f"@{base}", "D=A", f"@{index}", "A=D+A", "D=M"] + getPushD()
    else:
        asm = getPopD() + [
            f"@{base}",
            "D=A",
            f"@{index}",
            "D=D+A",
            "@R13",
            "M=D",
            "@SP",
            "A=M",
            "D=M",
            "@R13",
            "A=M",
            "M=D",
        ]

    return asm


def constantSeg(pushpop, seg, index):
    if seg == "constant":
        return [f"@{index}", "D=A"] + getPushD()
    else:
        filename = os.path.splitext(os.path.basename(sys.argv[1]))[0]
        symbol = f"{filename}.{index}"
        if pushpop == "push":
            return [f"@{symbol}", "D=M"] + getPushD()
        else:
            return getPopD() + [f"@{symbol}", "M=D"]


def generateComparison(op):
    true_label = uniqueLabel()
    end_label = uniqueLabel()
    jump_cond = ARITH_TEST[op]
    return [
        *getPopD(),
        "@SP",
        "A=M-1",
        "D=M-D",
        f"@{true_label}",
        f"D;{jump_cond}",
        "@SP",
        "A=M-1",
        "M=0",
        f"@{end_label}",
        "0;JMP",
        f"({true_label})",
        "@SP",
        "A=M-1",
        "M=-1",
        f"({end_label})",
    ]


def uniqueLabel():
    global LABEL_NUMBER
    label = f"LABEL_{LABEL_NUMBER}"
    LABEL_NUMBER += 1
    return label


def line2Command(line):
    return line.split("//")[0].strip()


def ParseFile(f):
    out = []
    for line in f:
        command = line2Command(line)
        if not command:
            continue

        args = command.split()
        if args[0] in ARITH_BINARY:
            out.extend(ARITH_BINARY[args[0]])
        elif args[0] in ARITH_UNARY:
            out.extend(ARITH_UNARY[args[0]])
        elif args[0] in ARITH_TEST:
            out.extend(generateComparison(args[0]))
        elif args[0] in ["push", "pop"]:
            seg_type = SEGMENTS.get(args[1], None)
            if seg_type == "pointer":
                out.extend(pointerSeg(args[0], args[1], int(args[2])))
            elif seg_type == "fixed":
                out.extend(fixedSeg(args[0], args[1], int(args[2])))
            elif seg_type == "constant":
                out.extend(constantSeg(args[0], args[1], int(args[2])))
            else:
                print(f"Unknown segment: {args[1]}")
                sys.exit(1)
        else:
            print(f"Unknown command: {args[0]}")
            sys.exit(1)

    end_label = uniqueLabel()
    out.extend([f"({end_label})", f"@{end_label}", "0;JMP"])

    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("wrong!")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        print(ParseFile(f))
