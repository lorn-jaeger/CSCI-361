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
        pass

    def dest(self, dest_m):
        dest = 0b00
        if "M" in dest_m:
            dest ^= 1 << 0
        if "D" in dest_m:
            dest ^= 1 << 1
        if "A" in dest_m:
            dest ^= 1 << 2

        return dest

    def comp(self, comp_m):
        comp = None

        match comp_m:
            case "0":
                comp = 0b101010
            case "1":
                comp = 0b111111
            case "-1":
                comp = 0b111010
            case "D":
                comp = 0b001100
            case "A":
                comp = 0b1100
            case "!D":
                comp = 0b0101010
            case "!A":
                comp = 0b0101010
            case "D+1":
                comp = 0b0101010
            case "A+1":
                comp = 0b0101010
            case "D-1":
                comp = 0b0101010
            case "A-1":
                comp = 0b0101010
            case "D+A":
                comp = 0b0101010
            case "D-A":
                comp = 0b0101010
            case "A-D":
                comp = 0b0101010
            case "D&A":
                comp = 0b0101010
            case "D|A":
                comp = 0b0101010
            case "M":
                comp = 0b0101010
            case "!M":
                comp = 0b0101010
            case "-M":
                comp = 0b0101010
            case "M+1":
                comp = 0b0101010
            case "M-1":
                comp = 0b0101010
            case "D+M":
                comp = 0b0101010
            case "D-M":
                comp = 0b0101010
            case "M-D":
                comp = 0b0101010
            case "D&M":
                comp = 0b0101010
            case "D|M":
                comp = 0b0101010

    def jump(self, jump_m):
        pass
