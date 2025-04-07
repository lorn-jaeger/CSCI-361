#!/usr/bin/python3
import os
import sys

# The following dictionaries are used to translate VM language commands to machine language.

# This contains the binary operations add, sub, and, or as values. The keys are the Hack ML code to do them.
# Assume a getPopD() has been called prior to this lookup.
ARITH_BINARY = {}

# As above, but now the keys are unary operations neg, not
# Values are sequences of Hack ML code, seperated by commas.
# In this case do not assume a getPopD() has been called prior to the lookup
ARITH_UNARY = {}

# Now, the code for operations gt, lt, eq as values.
# These are assumed to be preceded by getPopD()
# The ML code corresponds very nicely to the jump conditions in
# Hack assembly
ARITH_TEST = {}

# Boring, but needed - translate the long VM names argument, local, this, that
# to the shorthand forms of these found in symbol table used for Hack assembly
SEGLABEL = {}

# Here are the segments
SEGMENTS = {}


# This will be used to generate unique labels when they are needed.
LABEL_NUMBER = 0


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

    assert seg in ["local", "argument", "this", "that"] and pushpop in ["push", "pop"]

    seg_map = {"local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}

    pointer = seg_map[seg]

    if pushpop == "push":
        asm = setDtoPointer(pointer, index) + getPushD()
    if pushpop == "pop":
        asm = getPopD() + setPointerToD(pointer, index)

    return asm


def fixedSeg(push, seg, index):
    """
    For pointer and temp segments
    """
    pass


def constantSeg(push, seg, index):
    """
    This will do constant and static segments
    """
    pass


def line2Command(line):
    """This just returns a cleaned up line, removing unneeded spaces and comments"""
    pass


def uniqueLabel():
    """Uses LABEL_NUMBER to generate and return a unique label"""
    pass


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


def ParseFile(f):
    outString = ""
    for line in f:
        command = line2Command(line)
        if command:
            args = [
                x.strip() for x in command.split()
            ]  # Break command into list of arguments, no return characters
            if args[0] in ARITH_BINARY.keys():
                """
                Code that will deal with any of the binary operations (add, sub, and, or)
                do so by doing the things all have in common, then do what is specific
                to each by pulling a key from the appropriate dictionary.
                Remember, it's always about putting together strings of Hack ML code.
                """

            elif args[0] in ARITH_UNARY.keys():
                """
                As above, but now for the unary operators (neg, not)
                """

            elif args[0] in ARITH_TEST.keys():
                """
                Deals with the three simple operators (lt,gt,eq), but likely the hardest
                section because you'll have to write assembly to jump to a different part
                of the code, depending on the result.
                To define where to jump to, use the uniqueLabel() function to get labels.
                The result should be true (0xFFFF) or false (0x0000) depending on the test.
                That goes back onto the stack.
                HINT: Review the quiz for this unit!
                """

            elif args[1] in SEGMENTS.keys():
                """
                Here we deal with code that's like push/pop segment index.
                You've written the functions, the code in here selects the right 
                function by picking a function handle from a dictionary. 
                """

            else:
                print("Unknown command!")
                print(args)
                sys.exit(-1)

    label = uniqueLabel()
    outString += "(%s)" % (label) + ",@%s,0;JMP" % label  # Final endless loop
    return outString.replace(" ", "").replace(",", "\n")


filename = sys.argv[1].strip()

# This is ugly - add some error checking on file open.
f = open(filename)
print(ParseFile(f))
f.close()
