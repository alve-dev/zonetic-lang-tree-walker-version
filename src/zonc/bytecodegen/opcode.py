from enum import IntEnum

class OpCode(IntEnum):
    OP_IMM = 0x13
    OP = 0x33
    HALT = 0x00
    
class Funct3(IntEnum):
    ADD_SUB = 0x00
    MUL = 0x00
    ADDI = 0x01
    DIV = 0x04
    REM = 0x06

class Funct7(IntEnum):
    ADD = 0x00
    M_EXT = 0x01
    SUB = 0x20
    