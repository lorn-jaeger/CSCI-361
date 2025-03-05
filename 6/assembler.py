from enum import Enum, auto
import sys


class Parser:
    class CommandType(Enum):
        A_COMMAND = auto()
        C_COMMAND = auto()
        L_COMMAND = auto()
        INVALID_COMMAND = auto()

    def __init__(self, filepath):
        self.filepath = filepath
        self.file = open(filepath, "r")
        self.command = None
        self.ctype = None

    def hasMoreCommands(self):
        pos = self.file.tell()
        line = self.file.readline()

        if not line:
            return False
        else:
            self.file.seek(pos)
            return True

    def advance(self):
        line = self.strip(self.file.readline())
        self.command = line

    def commandType(self):
        ctype = None

        if not self.command:
            ctype = self.CommandType.INVALID_COMMAND
        elif self.command[0] == "@":
            ctype = self.CommandType.A_COMMAND
        elif self.command[0] == "(" and self.command[-1] == ")":
            ctype = self.CommandType.L_COMMAND
        else:
            ctype = self.CommandType.C_COMMAND

        self.ctype = ctype
        return ctype

    def symbol(self):
        command = None

        if self.ctype == self.CommandType.A_COMMAND:
            command = self.command[1:]
        elif self.ctype == self.CommandType.L_COMMAND:
            command = self.command[1:-1]

        return command

    def dest(self):
        i = self.command.find("=")
        return self.command[:i] if i != -1 else ""

    def comp(self):
        command = None

        i = self.command.find("=")
        j = self.command.find(";")

        if i != -1 and j != -1:
            command = self.command[i + 1 : j]
        elif i != -1:
            command = self.command[i + 1 :]
        elif j != -1:
            command = self.command[:j]
        else:
            command = self.command

        return command

    def jump(self):
        i = self.command.find(";")
        return self.command[i + 1 :] if i != -1 else ""

    def strip(self, line):
        line = line.split("//", 1)[0].strip()
        return line


class Code:
    def __init__(self):
        self.comp_table = {
            "0": "0101010",
            "1": "0111111",
            "-1": "0111010",
            "D": "0001100",
            "A": "0110000",
            "!D": "0001101",
            "!A": "0110001",
            "-D": "0001111",
            "-A": "0110011",
            "D+1": "0011111",
            "A+1": "0110111",
            "D-1": "0001110",
            "A-1": "0110010",
            "D+A": "0000010",
            "D-A": "0010011",
            "A-D": "0000111",
            "D&A": "0000000",
            "D|A": "0010101",
            "M": "1110000",
            "!M": "1110001",
            "-M": "1110011",
            "M+1": "1110111",
            "M-1": "1110010",
            "D+M": "1000010",
            "D-M": "1010011",
            "M-D": "1000111",
            "D&M": "1000000",
            "D|M": "1010101",
            "": "0000000",
        }

        self.jump_table = {
            "": "000",
            "JGT": "001",
            "JEQ": "010",
            "JGE": "011",
            "JLT": "100",
            "JNE": "101",
            "JLE": "110",
            "JMP": "111",
        }

    def dest(self, dest_m):
        dest = ["0", "0", "0"]
        if "M" in dest_m:
            dest[2] = "1"
        if "D" in dest_m:
            dest[1] = "1"
        if "A" in dest_m:
            dest[0] = "1"

        return "".join(dest)

    def comp(self, comp_m):
        return self.comp_table[comp_m]

    def jump(self, jump_m):
        return self.jump_table[jump_m]


class Assembler:
    def __init__(self, filepath, writepath):
        self.parser = Parser(filepath)
        self.code = Code()
        self.writepath = writepath

    def assemble(self):
        with open(self.writepath, "a") as file:
            while self.parser.hasMoreCommands():
                self.parser.advance()
                type = self.parser.commandType()
                line = None
                if type == self.parser.CommandType.A_COMMAND:
                    symbol = self.parser.symbol()
                    line = bin(int(symbol))[2:].zfill(16)

                elif type == self.parser.CommandType.C_COMMAND:
                    dest = self.parser.dest()
                    comp = self.parser.comp()
                    jump = self.parser.jump()

                    dest = self.code.dest(dest)
                    comp = self.code.comp(comp)
                    jump = self.code.jump(jump)

                    line = "111" + comp + dest + jump

                elif type == self.parser.CommandType.L_COMMAND:
                    symbol = self.parser.symbol()
                    line = bin(int(symbol))[2:]

                if line:
                    file.write(line + "\n")
                else:
                    continue


def main():
    filepath = sys.argv[1]
    writepath = sys.argv[2]

    assembler = Assembler(filepath, writepath)
    assembler.assemble()


if __name__ == "__main__":
    main()
