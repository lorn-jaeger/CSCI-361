import os
import sys

# Constants
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

# Global counter for unique labels
LABEL_NUMBER = 0

def getPushD():
    """Push D register onto the stack and increment SP"""
    return ["@SP", "A=M", "M=D", "@SP", "M=M+1"]

def getPopD():
    """Pop from stack into D register and decrement SP"""
    return ["@SP", "AM=M-1", "D=M"]

def _getPushMem(src):
    """Helper function to push memory to location src to stack"""
    return [
        f"@{src}",
        "D=M",
        *getPushD(),
    ]

def _getPushLabel(src):
    """Helper function to push the ROM address of a label to the stack."""
    return [
        f"@{src}",
        "D=A",
        *getPushD(),
    ]

def _getPopMem(dest):
    """Helper function to pop the stack to the memory address dest."""
    return [
        *getPopD(),
        f"@{dest}",
        "M=D",
    ]

def _getMoveMem(src, dest):
    """Helper function to move the contents of src to memory location dest."""
    return [
        f"@{src}",
        "D=M",
        f"@{dest}",
        "M=D",
    ]

def getIf_goto(label):
    """Returns Hack ML to goto label if top of stack is true"""
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

def getCall(function, nargs):
    """
    Returns Hack ML code to call a function with nargs arguments.
    Saves return address and caller's state before jumping to function.
    """
    return_label = uniqueLabel()
    
    return [
        # Push return address
        *_getPushLabel(return_label),
        # Save caller's segment pointers
        *_getPushMem("LCL"),
        *_getPushMem("ARG"),
        *_getPushMem("THIS"),
        *_getPushMem("THAT"),
        # Reposition ARG (ARG = SP - 5 - nargs)
        "@SP",
        "D=M",
        f"@{nargs}",
        "D=D-A",
        "@5",
        "D=D-A",
        "@ARG",
        "M=D",
        # LCL = SP
        "@SP",
        "D=M",
        "@LCL",
        "M=D",
        # Jump to function
        *getGoto(function),
        # Return address label
        *getLabel(return_label),
    ]

def getFunction(function, nlocal):
    """
    Returns Hack ML code to define a function with nlocal local variables.
    Initializes local variables to 0.
    """
    asm = [
        f"({function})",  # Function label
    ]
    
    # Initialize nlocal local variables to 0
    for _ in range(nlocal):
        asm.extend([
            "@0",
            "D=A",
            *getPushD(),
        ])
    
    return asm

def getReturn():
    """
    Returns Hack ML code to return from a function.
    Restores caller's state and jumps to return address.
    """
    return [
        # FRAME = LCL (temporary variable)
        "@LCL",
        "D=M",
        "@FRAME",
        "M=D",
        # RET = *(FRAME - 5) (return address)
        "@5",
        "A=D-A",
        "D=M",
        "@RET",
        "M=D",
        # *ARG = pop() (return value)
        *getPopD(),
        "@ARG",
        "A=M",
        "M=D",
        # SP = ARG + 1 (restore SP)
        "@ARG",
        "D=M+1",
        "@SP",
        "M=D",
        # THAT = *(FRAME - 1)
        "@FRAME",
        "D=M",
        "@1",
        "A=D-A",
        "D=M",
        "@THAT",
        "M=D",
        # THIS = *(FRAME - 2)
        "@FRAME",
        "D=M",
        "@2",
        "A=D-A",
        "D=M",
        "@THIS",
        "M=D",
        # ARG = *(FRAME - 3)
        "@FRAME",
        "D=M",
        "@3",
        "A=D-A",
        "D=M",
        "@ARG",
        "M=D",
        # LCL = *(FRAME - 4)
        "@FRAME",
        "D=M",
        "@4",
        "A=D-A",
        "D=M",
        "@LCL",
        "M=D",
        # goto RET
        "@RET",
        "A=M",
        "0;JMP",
    ]

def setDtoPointer(base, i):
    """Helper to set D to pointer value"""
    return [f"@{base}", "D=M", f"@{i}", "A=D+A", "D=M"]

def setPointerToD(base, i):
    """Helper to set pointer value from D"""
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
    """Handles push/pop for pointer segments (local, argument, this, that)"""
    base = SEGLABEL[seg]
    if pushpop == "push":
        asm = setDtoPointer(base, index) + getPushD()
    elif pushpop == "pop":
        asm = getPopD() + setPointerToD(base, index)
    return asm

def fixedSeg(pushpop, seg, index):
    """Handles push/pop for fixed segments (temp, pointer)"""
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

def constantSeg(pushpop, seg, index):
    """Handles push/pop for constant/static segments"""
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
    """Generates assembly for comparison operations (eq, gt, lt)"""
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
    """Generates a unique label using global counter"""
    global LABEL_NUMBER
    label = f"LABEL_{LABEL_NUMBER}"
    LABEL_NUMBER += 1
    return label

def cleanLine(line):
    """Removes comments and whitespace from line"""
    return line.split("//")[0].strip()

def parseFile(f):
    """Main parser that converts VM commands to Hack assembly"""
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
                out.extend(constantSeg(args[0], args[1], int(args[2])))
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

    # Add infinite loop at end to prevent execution from continuing
    end_label = uniqueLabel()
    out.extend([f"({end_label})", f"@{end_label}", "0;JMP"])

    return "\n".join(out)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python vm_translator.py <input.vm>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        print(parseFile(f))