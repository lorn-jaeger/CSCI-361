def getPushD():
    asm = [
        "@SP",
        "A=M",
        "M=D",
        "@SP",
        "M=M+1",
    ]

    return ",".join(asm) + ","


def getPopD():
    asm = [
        "@SP",
        "AM=M-1",
        "D=M",
    ]

    return ",".join(asm) + ","


def setDtoPointer(base, i):
    asm = [
        f"@{base}",  # access pointer, A is pointer index in memory and M is the offset stored in the pointer
        "D=M",  # store the pointer
        f"@{i}",  # store the offset in A and add it to D
        "A=D+A",
        "D=M",  # store the value at base + i in D
    ]

    return ",".join(asm) + ","


def setPointerToD(base, i):
    asm = [f"@{base}", "D=D+M", f"@{i}", "D=D+A", "@SP", "A=M", "A=M", "A=D-A", "M=D-A"]

    return ",".join(asm) + ","


def pointerSeg(pushpop, seg, index):
    """This function returns Hack ML code to push a memory location to
    to the stack, or pop the stack to a memory location.

    INPUTS:
        pushpop = a text string 'pop' means pop to memory location, 'push'
                  is push memory location onto stack
        seg     = the name of the segment that will be be the base address
                  in the form of a text string
        index   = an integer that specifies the offset from the base
                  address specified by seg

    RETURN:
        The memory address is speficied by segment's pointer (SEGLABEL[seg]) + index (index))
        if pushpop is 'push', push the address contents to the stack
        if pushpop is 'pop' then pop the stack to the memory address.
        The string returned accomplishes this. ML commands are seperated by commas (,).

    NOTE: This function will only be called if the seg is one of:
    "local", "argument", "this", "that"
    """

    """
    if we are pushing put the seg + index into D
    if we are popping, pop a value off the stack and take D and set the seg + 
    index
    """
    assert seg in ["local", "argument", "this", "that"] and pushpop in ["push", "pop"]

    seg_map = {"local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}

    pointer = seg_map[seg]

    if pushpop == "push":
        asm = setDtoPointer(pointer, index) + getPushD()
    if pushpop == "pop":
        asm = getPopD() + setPointerToD(pointer, index)

    return asm


print(pointerSeg("push", "this", 5))
print(pointerSeg("pop", "this", 5))
