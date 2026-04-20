from zonc.zonast import *
import struct
from .opcode import OpCode, Funct3, Funct7
from .register_manager import RegisterManager

class Emitter:
    def __init__(self):
        self.code = bytearray()
        self.reg_manager = RegisterManager()
        self.variables = {}
    
    def emit_r_type(self, opcode, funct3, funct7, rd, rs1, rs2):
        rd &= 0x1F
        rs1 &= 0x1F
        rs2 &= 0x1F
        funct3 &= 0x7
        funct7 &= 0x7F
        opcode &= 0x7F
        instruction = (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode
        self.code.extend(struct.pack('<I', instruction))
        print(struct.pack('<I', instruction))
        
    def emit_i_type(self, opcode, funct3, rd, rs1, imm):
        rd &= 0x1F
        rs1 &= 0x1F
        funct3 &= 0x7
        imm &= 0xFFF
        opcode &= 0x7F
        instruction = (imm << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode
        self.code.extend(struct.pack('<I', instruction))
        print(struct.pack('<I', instruction))
        
    def emit_halt(self):
        self.code.extend(struct.pack('<I', 0x00000000))
        print("HALT")
        
    def save(self, filename):
        with open(f"{filename}", "wb") as f:
            f.write(struct.pack('<I', 0x5A4F4E21))
            f.write(self.code)
        
    def generate_literal_num(self, imm, reg):
        self.emit_i_type(OpCode.OP_IMM, Funct3.ADDI, reg, 0x0, imm)
        
    def generate_stmt(self, node):
        match node:
            case DeclarationStmt():
                reg = self.reg_manager.alloc_variable(node.name)
                self.emit_i_type(OpCode.OP_IMM, Funct3.ADDI, reg, 0x0, 0)
                
            case AssignmentStmt():
                reg = self.reg_manager.get_var_reg(node.name)
                if isinstance(node.value, IntLiteral):
                    self.generate_literal_num(node.value.value, reg)
                    return
                
                reg_value = self.generate_expr(node.value)
                self.emit_i_type(OpCode.OP_IMM, Funct3.ADDI, reg, reg_value, 0)
                self.reg_manager.free_temp(reg_value)
                
            case InitializationStmt():
                reg = 0
                temp = False
                if node.decl_stmt.name in self.reg_manager.used_saved:
                    reg = self.reg_manager.get_var_reg(node.decl_stmt.name)
                else:
                    reg = self.reg_manager.alloc_temp()
                    temp = True
                
                if isinstance(node.assign_stmt.value, IntLiteral):
                    self.generate_literal_num(node.assign_stmt.value.value, reg)
                
                else:
                    reg_value = self.generate_expr(node.assign_stmt.value)
                    self.emit_i_type(OpCode.OP_IMM, Funct3.ADDI, reg, reg_value, 0)
                    self.reg_manager.free_temp(reg_value)
                    
                if temp:
                    real_reg = self.reg_manager.alloc_variable(node.decl_stmt.name)
                    self.emit_i_type(OpCode.OP_IMM, Funct3.ADDI, real_reg, reg, 0)
                    self.reg_manager.free_temp(reg)

    def generate_expr(self, node):
        match node:
            case IntLiteral():
                reg = self.reg_manager.alloc_temp()
                self.generate_literal_num(node.value, reg)
                return reg
                
            case BinaryExpr():
                match node.operator:
                    case Operator.ADD:
                        if isinstance(node.left, IntLiteral) and isinstance(node.right, IntLiteral):
                            reg = self.reg_manager.alloc_temp()
                            self.generate_literal_num(node.left.value + node.right.value, reg)
                            return reg

                        if isinstance(node.right, IntLiteral):
                            reg_left = self.generate_expr(node.left)
                            reg = self.reg_manager.alloc_temp()
                            self.emit_i_type(OpCode.OP_IMM, Funct3.ADDI, reg, reg_left, node.right.value)
                            self.reg_manager.free_temp(reg_left)
                            return reg

                        if isinstance(node.left, IntLiteral):
                            reg_right = self.generate_expr(node.right)
                            reg = self.reg_manager.alloc_temp()
                            self.emit_i_type(OpCode.OP_IMM, Funct3.ADDI, reg, reg_right, node.left.value)
                            self.reg_manager.free_temp(reg_right)
                            return reg

                        reg_left = self.generate_expr(node.left)
                        reg_right = self.generate_expr(node.right)
                        reg = self.reg_manager.alloc_temp()
                        self.emit_r_type(OpCode.OP, Funct3.ADD_SUB, Funct7.ADD, reg, reg_left, reg_right)
                        self.reg_manager.free_temp(reg_left)
                        self.reg_manager.free_temp(reg_right)
                        return reg

                    
                    case Operator.SUB:
                        reg_left = self.generate_expr(node.left)
                        reg_right = self.generate_expr(node.right)
                        reg = self.reg_manager.alloc_temp()
                        self.emit_r_type(OpCode.OP, Funct3.ADD_SUB, Funct7.SUB, reg, reg_left, reg_right)
                        self.reg_manager.free_temp(reg_left)
                        self.reg_manager.free_temp(reg_right)
                        return reg
                    
                    case Operator.MUL:
                        reg_left = self.generate_expr(node.left)
                        reg_right = self.generate_expr(node.right)
                        reg = self.reg_manager.alloc_temp()
                        self.emit_r_type(OpCode.OP, Funct3.MUL, Funct7.M_EXT, reg, reg_left, reg_right)
                        self.reg_manager.free_temp(reg_left)
                        self.reg_manager.free_temp(reg_right)
                        return reg
                    
                    case Operator.DIV:
                        reg_left = self.generate_expr(node.left)
                        reg_right = self.generate_expr(node.right)
                        reg = self.reg_manager.alloc_temp()
                        self.emit_r_type(OpCode.OP, Funct3.DIV, Funct7.M_EXT, reg, reg_left, reg_right)
                        self.reg_manager.free_temp(reg_left)
                        self.reg_manager.free_temp(reg_right)
                        return reg
                    
                    case Operator.MOD:
                        reg_left = self.generate_expr(node.left)
                        reg_right = self.generate_expr(node.right)
                        reg = self.reg_manager.alloc_temp()
                        self.emit_r_type(OpCode.OP, Funct3.REM, Funct7.M_EXT, reg, reg_left, reg_right)
                        self.reg_manager.free_temp(reg_left)
                        self.reg_manager.free_temp(reg_right)
                        return reg
                    
            case UnaryExpr():
                match node.operator:
                    case Operator.NEG:
                        reg_value = self.generate_expr(node.value)
                        reg = self.reg_manager.alloc_temp()
                        self.emit_r_type(OpCode.OP, Funct3.ADD_SUB, Funct7.SUB, reg, 0x0, reg_value)
                        self.reg_manager.free_temp(reg_value)
                        return reg
            
            case VariableExpr():
                return self.reg_manager.get_var_reg(node.name)
                
                
        