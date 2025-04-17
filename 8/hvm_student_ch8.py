#!/usr/bin/python3
import os
import sys
import glob

ARITH_BINARY = {'add':'A=A-1, M=M+D,','sub':'A=A-1, M=M-D,','and':'A=A-1, M=M&D,','or':'A=A-1, M=M|D,'}
ARITH_UNARY = {'neg':'@SP, A=M-1, M=-M,','not':'@SP, A=M-1, M=!M,'}
ARITH_TEST  = {'gt':'JGT','lt':'JLT','eq':'JEQ'}
SEGLABEL = {'argument':'ARG','local':'LCL','this':'THIS','that':'THAT'}

LABEL_NUMBER = 0

def pointerSeg(push,seg,index):
    # The following puts the segment's pointer + index in the D
    # register
    instr = '@%s, D=M, @%d, D=D+A,'%(SEGLABEL[seg],int(index))
    if push == 'push':
        return instr + ('A=D, D=M,'+getPushD())
    elif push == 'pop':
        return (instr+'@R15, M=D,' + getPopD() + '@R15, A=M, M=D,')
    else:
        print("Yikes, pointer segment, bet seg not found.")

def fixedSeg(push,seg,index):
    if push == 'push':
        if seg == 'pointer':
            return ('@%d, D=M,'%(3 + int(index)) + getPushD())
        elif seg == 'temp':
            return ('@%d, D=M,'%(5 + int(index)) + getPushD())
    elif push == 'pop':
        if seg == 'pointer':
            return (getPopD() + '@%d, M=D,'%(3 + int(index)))
        elif seg == 'temp':
            return (getPopD() + '@%d, M=D,'%(5 + int(index)))
    else:
        print("Yikes, fixed segment, but seg not found.")

def constantSeg(push,seg,index):
    global filename
    fn_ = filename.split('/')
    fn_ = fn_[-1]
    fn_ = fn_.split('.')
    fn_ = fn_[0]
    if seg == 'constant':
        return '@%d,    D=A,'%(int(index)) + getPushD()
    elif seg == 'static' and push == 'push':
        return '@%s.%d, D=M,'%(fn_,int(index)) + getPushD()
    elif seg == 'static' and push == 'pop':
        return getPopD() + '@%s.%d, M=D,'%(fn_,int(index))

# Yeah this is akward, but needed so that the function handles are known.
SEGMENTS = {'constant':constantSeg,'static':constantSeg,'pointer':fixedSeg,'temp':fixedSeg,\
            'local':pointerSeg,'argument':pointerSeg,'this':pointerSeg,'that':pointerSeg}

def getIf_goto(label):
    """
    Returns Hack ML to goto the label specified as
    an input arguement if the top entry of the stack is
    true.
    """

def getGoto(label):
    """
    Return Hack ML string that will unconditionally 
    jumpt to the input label.
    """

def getLabel(label):
    """
    Returns Hack ML for a label, eg (label)
    """

def getCall(function,nargs):
    """
    This function returns the Hack ML code to 
    invoke the `call function nargs` type command in 
    the Hack virtual machine (VM) language.

    In order for this to work, review slides
    46-58 in the Project 8 presentation available 
    on the nand2tetris.org website.
    """

def getFunction(function,nlocal):
    """
    Return the Hack ML code to represent a function which sets a label
    and initializes local variables to zero.
    See slides 59-63 in the nand2tetris book.
    """

def getReturn():
    """
    Returns Hack ML code to perform a return, one
    of the more complex operations in this unit.
    The code restores all the memory segments to the
    calling function. It also has to restore the 
    instruction pointer (IP) and reset the stack 
    pointer. See slides 64-76 of nand2tetris.org
    project 8.

    """

# More jank, this time to define the function pointers for flow control.
PROG_FLOW  = {'if-goto':getIf_goto,'goto':getGoto,'label':getLabel,'call':getCall,'function':getFunction,'return':getReturn}

def _getPushMem(src):
    """
    Helper function to push memory to location src to stack
    """
    

def _getPushLabel(src):
    """
    Helper function to push the ROM address of a label to the
    stack.
    """
   

def _getPopMem(dest):
    """
    Helper function to pop the stack to the memory address dest.
    """
  

def _getMoveMem(src,dest):
    """
    Helper function to move the contents of src to memory location dest.
    """

def line2Command(l):
            return l[:l.find('//')].strip()

def uniqueLabel():
    global LABEL_NUMBER
    LABEL_NUMBER +=1
    return "UL_"+ str(LABEL_NUMBER)

def getPushD():
     # This method takes no arguments and returns a string with assembly language
     # that will push the contents of the D register to the stack.
     return '@SP, A=M, M=D, @SP, M=M+1,'

def getPopD():
    # This method takes no arguments and returns a string with assembly language
    # that will pop the stack to the D register.
    # SIDE EFFECT: The A register contains the SP.
     return '@SP, AM=M-1, D=M,'

def ParseFile(f):
    outString = ""
    for line in f:
        command = line2Command(line)
        if command:
            args = [x.strip() for x in command.split()] # Break command into list of arguments, no return characters
            if args[0] in ARITH_BINARY.keys():
                outString += getPopD()
                outString += ARITH_BINARY[args[0]]

            elif args[0] in ARITH_UNARY.keys():
                outString += ARITH_UNARY[args[0]]

            elif args[0] in PROG_FLOW.keys():
                if args[0] == 'function' or args[0] == 'call':
                    outString += PROG_FLOW[args[0]](args[1],int(args[2]))
                elif args[0] == 'return':
                    outString += PROG_FLOW[args[0]]()
                elif args[0] == 'label' or args[0] == 'goto' or args[0] == 'if-goto':
                    outString += PROG_FLOW[args[0]](args[1])

            elif args[0] in ARITH_TEST.keys():
                outString += getPopD()
                outString += ARITH_BINARY['sub']
                outString += getPopD()
                l1 = uniqueLabel()
                l2 = uniqueLabel()
                js = \
                  '@%s, D;%s, @%s, D=0;JMP, (%s),D=-1,(%s),'\
                  %(l1,ARITH_TEST[args[0]],l2,l1,l2)
                outString += js
                outString += getPushD()

            elif args[1] in SEGMENTS.keys():
                outString += SEGMENTS[args[1]](args[0],args[1],args[2])

            else:
                print("Unknown command!")
                print(args)
                sys.exit(-1)

    return outString

def getInit(sysinit = True):
    """
    Write the VM initialization code:
        Set the SP to 256.
        Initialize system pointers to -1.
        Call Sys.Init()
        Halt loop
    Passing sysinit = False oly sets the SP.  This allows the simpler
    VM test scripts to run correctly.
    """
    os = ""
    os += '@256,D=A,@SP,M=D,'
    if sysinit:
        os += 'A=A+1,M=-1,A=A+1,M=-1,A=A+1,M=-1,A=A+1,M=-1,'  # initialize ARG, LCL, THIS, THAT
        os += getCall('Sys.init', 0) # release control to init
        halt = uniqueLabel()
        os += '@%s, (%s), 0;JMP,' % (halt, halt)
    return os

source = sys.argv[1].strip()

out_string = ""

if os.path.isdir(source):
    filelist = glob.glob(source+"*.vm")
    out_string += getInit()
    for filename in filelist:
        f = open(filename)
        out_string += ParseFile(f)
        f.close()
else:
    filename = source
    f = open(source)
    out_string += getInit(sysinit=False)
    out_string += ParseFile(f)
    f.close()

print(out_string.replace(" ","").replace(',','\n'))
