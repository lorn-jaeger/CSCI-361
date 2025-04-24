import os
import sys
import glob

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
    return [
        f"@{src}",
        "D=M",
        *getPushD(),
    ]

def _getPushLabel(src):
    return [
        f"@{src}",
        "D=A",
        *getPushD(),
    ]

def _getPopMem(dest):
    return [
        *getPopD(),
        f"@{dest}",
        "M=D",
    ]

def _getMoveMem(src, dest):
    return [
        f"@{src}",
        "D=M",
        f"@{dest}",
        "M=D",
    ]

def getIf_goto(label):
    return [
        *getPopD(),
        f"@{label}",
        "D;JNE",  # Jump if D != 0 (true)
    ]

def getGoto(label):
    return [f"@{label}", "0;JMP"]

def getLabel(label):
    """Returns Hack ML for a label, eg (label)"""
    return [
        f"({label})",
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
    if seg == "pointer":
        reg = "THIS" if index == 0 else "THAT"
        if pushpop == "push":
            return [f"@{reg}", "D=M"] + getPushD()
        else:
            return getPopD() + [f"@{reg}", "M=D"]
    else:  # temp segment
        base = 5
        if pushpop == "push":
            return [f"@{base+index}", "D=M"] + getPushD()
        else:
            return getPopD() + [f"@{base+index}", "M=D"]

def constantSeg(pushpop, seg, index, vm_name):
    if seg == "constant":
        return [f"@{index}", "D=A"] + getPushD()
    else:
        symbol = f"{vm_name}.{index}"
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

def cleanLine(line):
    return line.split("//")[0].strip()

def parseFile(f, vm_name):
    out = []
    for line in f:
        command = cleanLine(line)
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
                out.extend(constantSeg(args[0], args[1], int(args[2]), vm_name))
            else:
                raise ValueError(f"Unknown segment: {args[1]}")
            
        elif args[0] == "label":
            out.extend(getLabel(args[1]))
        elif args[0] == "goto":
            out.extend(getGoto(args[1]))
        elif args[0] == "if-goto":
            out.extend(getIf_goto(args[1]))
        elif args[0] == "function":
            out.extend(getFunction(args[1], int(args[2])))
        elif args[0] == "call":
            out.extend(getCall(args[1], int(args[2])))
        elif args[0] == "return":
            out.extend(getReturn())
        else:
            raise ValueError(f"Unknown command: {args[0]}")

    end_label = uniqueLabel()
    out.extend([f"({end_label})", f"@{end_label}", "0;JMP"])

    return out

def getCall(function, nargs):
    return_label = uniqueLabel()
    
    return [
        *_getPushLabel(return_label),
        *_getPushMem("LCL"),
        *_getPushMem("ARG"),
        *_getPushMem("THIS"),
        *_getPushMem("THAT"),
        "@SP",
        "D=M",
        f"@{nargs}",
        "D=D-A",
        "@5",
        "D=D-A",
        "@ARG",
        "M=D",
        "@SP",
        "D=M",
        "@LCL",
        "M=D",
        *getGoto(function),
        *getLabel(return_label),
    ]

def getFunction(function, nlocal):
    asm = [
        f"({function})",  
    ]
    
    for _ in range(nlocal):
        asm.extend([
            "@0",
            "D=A",
            *getPushD(),
        ])
    
    return asm

def getReturn():
    return [
        "@LCL",
        "D=M",
        "@FRAME",
        "M=D",
        "@5",
        "A=D-A",
        "D=M",
        "@RET",
        "M=D",
        *getPopD(),
        "@ARG",
        "A=M",
        "M=D",
        "@ARG",
        "D=M+1",
        "@SP",
        "M=D",
        "@FRAME",
        "D=M",
        "@1",
        "A=D-A",
        "D=M",
        "@THAT",
        "M=D",
        "@FRAME",
        "D=M",
        "@2",
        "A=D-A",
        "D=M",
        "@THIS",
        "M=D",
        "@FRAME",
        "D=M",
        "@3",
        "A=D-A",
        "D=M",
        "@ARG",
        "M=D",
        "@FRAME",
        "D=M",
        "@4",
        "A=D-A",
        "D=M",
        "@LCL",
        "M=D",
        "@RET",
        "A=M",
        "0;JMP",
    ]

def getInit(sysinit=True):
    asm = ["@256", "D=A", "@SP", "M=D"]
    if sysinit:
        label = uniqueLabel()
        ext = [
                "A=A+1",
                "M=-1",
                "A=A+1",
                "M=-1",
                "A=A+1",
                "M=-1",
                "A=A+1",
                "M=-1",
                *getCall("Sys.init", 0),
                f"@{label}",
                *getLabel(label),
                "0;JMP"
        ]
        asm.extend(ext)
    return asm

if __name__ == "__main__":
    source = sys.argv[1].strip()
    out = []
    if os.path.isdir(source):
        f = glob.glob(os.path.join(source, "*.vm"))
        sys_vm = None
        for file_path in f:
            if os.path.basename(file_path) == 'Sys.vm':
                sys_vm = file_path
                break
        if sys_vm:
            f.remove(sys_vm)
            f.insert(0, sys_vm)
        out.extend(getInit())
        for filename in f:
            current_vm_name = os.path.splitext(os.path.basename(filename))[0]
            with open(filename, 'r') as f:
                out.extend(parseFile(f, current_vm_name))
    else:
        current_vm_name = os.path.splitext(os.path.basename(source))[0]
        with open(source, 'r') as f:
            out.extend(getInit(sysinit=False))
            out.extend(parseFile(f, current_vm_name))

    print("\n".join(out))