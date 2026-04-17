from enum import Enum, auto

class Operator(Enum):
    # Arithmetic Binary Operators
    ADD = auto()  # `+`
    SUB = auto()  # `-`
    MUL = auto()  # `*`
    DIV = auto()  # `/`
    POW = auto()  # '**`
    MOD = auto()  # `%`
    
    # Arithmetic Unary Operators
    NEG = auto()  # `-` diferente a SUB, es para unarios y convertir un numero a negativo

    # Boolean Binary Operators
    AND = auto()  # `and` | `&`
    OR = auto()   # `or` | `||`
    
    # Boolean Unary Operators
    NOT = auto()  # `not` | `!`
    
    # Binary Comparison Operators
    EQ = auto()  # `==`
    NE = auto()  # `!=`, NEG + EQ = NE
    
    GT = auto()  # `>`, Greater Than
    LT = auto()  # `<`, Less Than
    
    GE = auto()  # `>=`, Greater or Equal
    LE = auto()  # `<=`, Less or Equal
    
    def get_details(self):
        match self.value:
            case 1: return '+'
            case 2: return '-'
            case 3: return '*'
            case 4: return '/'
            case 5: return '**'
            case 6: return '%'
            case 7: return '-'
            case 8: return 'and/&&'
            case 9: return 'or/||'
            case 10: return 'not/!'
            case 11: return '=='
            case 12: return '!='
            case 13: return '>'
            case 14: return '<'
            case 15: return '>='
            case 16: return '<='
    