from enum import Enum, auto


class Parser:
    class CommandType(Enum):
        A_COMMAND = auto()
        C_COMMAND = auto()
        L_COMMAND = auto()
        INVALID_COMMAND = auto()

    def __init__(self, filepath):
        self.filepath = filepath
        self.file = open(filepath, "r")
        self.command
        self.ctype

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
        self.currentCommand = line

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

        i = command.find("=")
        j = command.find(";")

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
            "0": 0b0101010,
            "1": 0b0111111,
            "-1": 0b0111010,
            "D": 0b0001100,
            "A": 0b0110000,
            "!D": 0b0001101,
            "!A": 0b0110001,
            "-D": 0b0001111,
            "-A": 0b0110011,
            "D+1": 0b0011111,
            "A+1": 0b0110111,
            "D-1": 0b0001110,
            "A-1": 0b0110010,
            "D+A": 0b0000010,
            "D-A": 0b0010011,
            "A-D": 0b0000111,
            "D&A": 0b0000000,
            "D|A": 0b0010101,
            "M": 0b1110000,
            "!M": 0b1110001,
            "-M": 0b1110011,
            "M+1": 0b1110111,
            "M-1": 0b1110010,
            "D+M": 0b1000010,
            "D-M": 0b1010011,
            "M-D": 0b1000111,
            "D&M": 0b1000000,
            "D|M": 0b1010101,
        }

        self.jump = {
            "null": 0b000,
            "JGT": 0b001,
            "JEQ": 0b010,
            "JGE": 0b011,
            "JLT": 0b100,
            "JNE": 0b101,
            "JLE": 0b110,
            "JMP": 0b111,
        }

    def dest(self, dest_m):
        dest = 0b000
        if "M" in dest_m:
            dest ^= 1 << 0
        if "D" in dest_m:
            dest ^= 1 << 1
        if "A" in dest_m:
            dest ^= 1 << 2

        return dest

    def comp(self, comp_m):
        return self.comp_table[comp_m]

    def jump(self, jump_m):
        return self.jump[jump_m]


class Assembler:
    def __init__(self, filepath, writepath):
        self.parser = Parser(filepath)
        self.code = Code()
        self.writepath = writepath

    def assemble(self):
        with open("output.bin", "w") as file:
            while self.parser.hasMoreCommands:
                self.parser.advance()
                type = self.parser.commandType()

                if type == self.parser.CommandType.A_COMMAND:
                    symbol = self.parser.symbol()
                    line = bin(symbol)

                elif type == self.parser.CommandType.C_COMMAND:
                    dest = self.parser.dest()
                    comp = self.parser.comp()
                    jump = self.parser.jump()

                    line = self.code.dest(dest)
                    line += self.code.comp(comp)
                    line += self.code.jump(jump)

                elif type == self.parser.CommandType.L_COMMAND:
                    symbol = self.parser.symbol()
                    line = bin(symbol)

                file.write(line)
