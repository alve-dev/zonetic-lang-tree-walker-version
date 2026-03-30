from zonc.scanner import *
from zonc.ast import *
from zonc.zonc_errors import DiagnosticEngine, ErrorCode
from zonc.enviroment import Enviroment
from zonc.location_file import Span, FileMap
from typing import List, Union


class Parser:
    COMPOUND_TO_OPERATOR = {
        TokenType.OPERATOR_PLUS_ASSIGN : Operator.ADD,
        TokenType.OPERATOR_MINUS_ASSIGN : Operator.SUB,
        TokenType.OPERATOR_MULT_ASSIGN : Operator.MUL,
        TokenType.OPERATOR_DIV_ASSIGN : Operator.DIV,
        TokenType.OPERATOR_MOD_ASSIGN : Operator.MOD,
        TokenType.OPERATOR_POW_ASSIGN : Operator.POW
    }
    
    TOKEN_TO_OPERATOR = {
        TokenType.OPERATOR_PLUS : Operator.ADD,
        TokenType.OPERATOR_MINUS : Operator.SUB,
        TokenType.OPERATOR_MULT : Operator.MUL,
        TokenType.OPERATOR_DIV : Operator.DIV,
        TokenType.OPERATOR_MOD : Operator.MOD,
        TokenType.OPERATOR_GREATER : Operator.GT,
        TokenType.OPERATOR_GREATER_EQUAL : Operator.GE,
        TokenType.OPERATOR_LESS : Operator.LT,
        TokenType.OPERATOR_LESS_EQUAL : Operator.LE,
        TokenType.OPERATOR_EQUAL : Operator.EQ,
        TokenType.OPERATOR_NOT_EQUAL : Operator.NE,
        TokenType.GATE_OR : Operator.OR,
        TokenType.GATE_AND : Operator.AND,
        TokenType.OPERATOR_POW : Operator.POW
    }
    
    def __init__(self, tokens: ListTokens, diag: DiagnosticEngine, file_map: FileMap) -> None:
        self.tokens = tokens
        self.position = 0
        self.length_list = self.tokens._len()
        self.diag = diag
        self.file_map = file_map

    def at_end(self) -> bool:
        return self.tokens._peek(self.position)._type == TokenType.EOF

    def advance(self) -> bool:
        if self.at_end(): return False
        self.position += 1
        return True
    
    def get_error_span(self, token) -> Span:
        if token._type == TokenType.SEMICOLON:
            return Span(token._span.end - 2, token._span.end - 1, self.file_map)
        elif token._type == TokenType.EOF:
            return Span(token._span.end - 1, token._span.end, self.file_map)
        return token._span
    
    def synchronize(self, block: bool, stop: list[TokenType] = None):
        while not self.at_end():
            if stop is None:
                if self.match_token_type(
                    TokenType.KEYWORD_MUT, TokenType.KEYWORD_INMUT, TokenType.KEYWORD_IF,
                    TokenType.KEYWORD_WHILE, TokenType.KEYWORD_INFINITY, TokenType.LITERAL_IDENT,
                    TokenType.KEYWORD_FUNC, TokenType.KEYWORD_RETURN, TokenType.KEYWORD_GIVE,
                    TokenType.KEYWORD_CONTINUE, TokenType.KEYWORD_BREAK
                ): return
                elif block and self.check(TokenType.RBRACE): return
                else: self.advance()
            else:
                if self.match_token_type(*stop): return
                else: self.advance()
    
    def check(self, type: TokenType) -> bool:
        if self.at_end(): return False
        return self.tokens._peek(self.position)._type == type

    def match_token_type(self, *types) -> bool:
        for type in types:
            if self.check(type): return True
        return False
        
    
    def _add_node_to_list(self, stmt_list: list[Node], node: Union[Node, list[Node], ErrorNode]):
        if isinstance(node, list):
            stmt_list.extend(n for n in node if not isinstance(n, ErrorNode))
        elif not isinstance(node, ErrorNode):
            stmt_list.append(node)
            
    def _consume_block(self, scope: Enviroment, expects_value: bool, start: int, block: bool, aux_r: str = '{') -> BlockExpr | ErrorNode:
        token = self.tokens._peek(self.position)
        if token._type != TokenType.LBRACE:
            self.diag.emit(
                ErrorCode.E2009, { "aux_r" : aux_r, "token": token._value},
                [Span(start, token._span.end, self.file_map)],
                [(token._span, "`{aux_r}` was expected here to open the block")]
            )
            self.synchronize(block, [TokenType.LBRACE])
            return ErrorNode(Span(0, 0, self.file_map))
        
        self.advance()
        return self.parse_block_expr(expects_value, token._span.start, scope, block)

    def _parse_binary_expr(self, next_parser, token_types: list[TokenType], scope: Enviroment, block: bool) -> Node:
        node = next_parser(scope, block)
        if isinstance(node, ErrorNode): return node
        start = node.span.start
        
        while self.match_token_type(*token_types):
            token = self.tokens._peek(self.position)
            operator = self.TOKEN_TO_OPERATOR[token._type]
            self.advance()
            
            right = next_parser(scope, block)
            if isinstance(right, ErrorNode): return right
            
            node = BinaryExpr(node, operator, right, Span(start, right.span.end, self.file_map))
            
        return node
    
    def parse_program(self) -> Program:
        statements: list[Node] = []
        scope = Enviroment()
        
        while not self.at_end():
            if self.check(TokenType.SEMICOLON):
                self.advance()
                continue
            
            node = self.parse_statement(scope, False)
            self._add_node_to_list(statements, node)
            
        return Program(statements, scope)
    
    def parse_statement(self, scope: Enviroment, block: bool) -> Node:
        if self.match_token_type(TokenType.KEYWORD_MUT, TokenType.KEYWORD_INMUT):
            mut = self.check(TokenType.KEYWORD_MUT)
            start = self.tokens._peek(self.position)._span.start
            self.advance()
            return self.parse_declaration(mut, scope, start, block)
        
        elif self.check(TokenType.LITERAL_IDENT):
            token = self.tokens._peek(self.position)
            self.advance()
            if self.check(TokenType.LPAREN):
                self.advance()
                return self.parse_call_func(token, token._span.start, scope, block)
            return self.parse_assignment(scope, token._value, token._span, token._span.start, block)
            
        elif self.check(TokenType.LBRACE):
            token = self.tokens._peek(self.position)
            self.advance()
            return self.parse_block_expr(False, token._span.start, scope, block)
        
        elif self.check(TokenType.KEYWORD_GIVE):
            token = self.tokens._peek(self.position)
            self.advance()
            if not block:
                self.diag.emit(ErrorCode.E2012, None, [token._span], [(token._span, "`give` is not inside a block expression")])
                self.synchronize(block)
                return ErrorNode(Span(0, 0, self.file_map))
            value = self.expression(scope, block)
            return GiveStmt(value, Span(token._span.start, value.span.end, self.file_map))
            
        elif self.check(TokenType.KEYWORD_IF):
            start = self.tokens._peek(self.position)._span.start
            self.advance()
            return self.parse_if_form(scope, False, start, block)
        
        elif self.match_token_type(TokenType.KEYWORD_ELIF, TokenType.KEYWORD_ELSE):
            token_err = self.tokens._peek(self.position)
            self.diag.emit(ErrorCode.E2011, { "keyword" : token_err._value }, [token_err._span], [(token_err._span, "`if` was expected before this `{keyword}`")])
            self.synchronize(block, [TokenType.LBRACE])
            return ErrorNode(Span(0, 0, self.file_map))
        
        elif self.check(TokenType.KEYWORD_WHILE):
            start = self.tokens._peek(self.position)._span.start
            self.advance()
            return self.parse_while_form(scope, start, False, block)
        
        elif self.check(TokenType.KEYWORD_INFINITY):
            start = self.tokens._peek(self.position)._span.start
            self.advance()
            return self.parse_while_form(scope, start, True, block)
        
        elif self.check(TokenType.KEYWORD_BREAK):
            token = self.tokens._peek(self.position)
            self.advance()
            return BreakStmt(token._span)
        
        elif self.check(TokenType.KEYWORD_CONTINUE):
            token = self.tokens._peek(self.position)
            self.advance()
            return ContinueStmt(token._span)

        elif self.check(TokenType.KEYWORD_FUNC):
            start = self.tokens._peek(self.position)._span.start
            self.advance()
            return self.parse_func_form(scope, start, block)
        
        elif self.check(TokenType.KEYWORD_RETURN):
            token = self.tokens._peek(self.position)
            self.advance()
            if not block:
                span = self.get_error_span(token)
                self.diag.emit(ErrorCode.E2026, None, [span], [(span, "`return` is not inside any block")])
                self.synchronize(block)
                return ErrorNode(Span(0, 0, self.file_map))
            
            value: NodeExpr | None = None 
            span: Span
            if not self.check(TokenType.SEMICOLON):
                value = self.expression(scope, block)
                span = Span(token._span.start, value.span.end, self.file_map)
            else:
                span = token._span
                self.advance()
            
            return ReturnStmt(value, span)
        
        else:
            token_err = self.tokens._peek(self.position)
            self.diag.emit(ErrorCode.E2010, { "token" : token_err._value }, [token_err._span], [(token_err._span, "this is not a valid way to start a statement")])
            self.synchronize(block)
            return ErrorNode(Span(0, 0, self.file_map))
        
    def parse_declaration(self, mutable: bool, scope: Enviroment, start: int, block: bool) -> List[Union[DeclarationStmt, AssignmentStmt]]:
        node = self.parse_single_declaration(mutable, scope, start, block)
        declarations = []
        
        if isinstance(node, list):
            if not isinstance(node[0], ErrorNode) and not isinstance(node[1], ErrorNode): declarations.extend(node)
            else: return node
        elif isinstance(node, ErrorNode): return node
        else: declarations.append(node)
        
        if self.check(TokenType.COMMA):
            self.advance()
            for declaration in self.parse_declaration(mutable, scope, start, block):
                declarations.append(declaration)
            return declarations
                
        elif self.check(TokenType.SEMICOLON):
            return declarations
        else:
            token = self.tokens._peek(self.position)
            if token._type == TokenType.EOF:
                return ErrorNode(Span(0, 0, self.file_map))
            
            self.diag.emit(ErrorCode.E2004, { "token" : token._value }, [Span(start, token._span.end, self.file_map)], [(token._span, "expected `;` or `,` here to end or continue the declaration")])
            self.advance()
            self.synchronize(block, [TokenType.SEMICOLON])
            return ErrorNode(Span(0, 0, self.file_map))
        
    def parse_single_declaration(self, mutable: bool, scope: Enviroment, start: int, block: bool) -> DeclarationStmt | List[Union[DeclarationStmt, AssignmentStmt]]:
        name_mut = "mutable" if mutable else "inmutable"
        ident = self.tokens._peek(self.position)
        
        if self.check(TokenType.LITERAL_IDENT):
            self.advance()
            var_name = ident._value
            var_type: ZonType
                
            if self.check(TokenType.COLON):
                self.advance()
                zon_type = self.tokens._peek(self.position)
                current_span = zon_type._span
                       
                match zon_type._type:
                    case TokenType.KEYWORD_INT: var_type = ZonType.INT
                    case TokenType.KEYWORD_FLOAT: var_type = ZonType.FLOAT
                    case TokenType.KEYWORD_BOOL: var_type = ZonType.BOOL
                    case TokenType.KEYWORD_STRING: var_type = ZonType.STRING
                    case TokenType.KEYWORD_VOID:
                        self.diag.emit(ErrorCode.E2018, None, [zon_type._span], [(zon_type._span, "`void` cannot be used as a type here")])
                        self.synchronize(block)
                        return ErrorNode(Span(0, 0, self.file_map))
                    case _:
                        span_end = self.get_error_span(zon_type)
                        self.diag.emit(ErrorCode.E2002, { "type" : zon_type._value }, [Span(start, span_end.end, self.file_map)], [(span_end, "is not a valid type in Zonetic")])
                        self.advance()
                        self.synchronize(block)
                        return ErrorNode(Span(0, 0, self.file_map))
                
                end_offset = current_span.end
                self.advance()
            else:
                var_type = ZonType.UNKNOWN
                end_offset = self.tokens._peek(self.position)._span.end
            
            if self.check(TokenType.OPERATOR_ASSIGN):
                return [
                    DeclarationStmt(var_name, mutable, var_type, ident._span, Span(start, end_offset, self.file_map)),
                    self.parse_assignment(scope, var_name, ident._span, start, block)
                ]
            else:
                return DeclarationStmt(var_name, mutable, var_type, ident._span, Span(start, end_offset, self.file_map))
        else:
            span_end = self.get_error_span(ident)
            self.diag.emit(ErrorCode.E2001, { "name_mut" : name_mut }, [Span(start, span_end.end, self.file_map)], [(span_end, "an identifier was expected here")])
            self.synchronize(block)
            return ErrorNode(Span(0, 0, self.file_map))
        
    def parse_assignment(self, scope: Enviroment, name: str, span_name: Span, start: int, block: bool) -> AssignmentStmt:
        token = self.tokens._peek(self.position)
        self.advance()
        
        if token._type == TokenType.OPERATOR_ASSIGN:
            expr = self.expression(scope, block)
            return AssignmentStmt(name, expr, Span(start, expr.span.end, self.file_map), span_name)
            
        elif token._type in self.COMPOUND_TO_OPERATOR:
            var = VariableExpr(name, Span(token._span.start, token._span.end, self.file_map))
            right_expr = self.expression(scope, block)
            expr = BinaryExpr(var, self.COMPOUND_TO_OPERATOR[token._type], right_expr, Span(var.span.start, right_expr.span.end, self.file_map))
            return AssignmentStmt(name, expr, Span(start, expr.span.end, self.file_map), span_name)
            
        else:
            span_end = self.get_error_span(token)
            
            self.diag.emit(ErrorCode.E2006, { "token" : token._value , "name" : name }, [Span(start, span_end.end, self.file_map)], [(span_end, "expected an assignment operator here")])
            self.synchronize(block)
            return ErrorNode(Span(0, 0, self.file_map))
    
    def parse_block_expr(self, expects_value: bool, start: int, scope_back: Enviroment, block: bool) -> BlockExpr:
        statements: list[Node] = []
        give_value: GiveStmt = None
        is_value_give = False
        end: int = 0
        
        scope = Enviroment(scope_back)
        
        while True:
            if self.check(TokenType.SEMICOLON):
                self.advance()
                continue
            
            if self.at_end():
                token_eof = self.tokens._peek(self.position)
                self.diag.emit(ErrorCode.E2008, {"aux_l": '}', "aux_r" : '{'}, [Span(start, token_eof._span.end-1, self.file_map)], [(Span(token_eof._span.end-2, token_eof._span.end-1, self.file_map), "`{aux_l}` was expected here to close the block")])
                return ErrorNode(Span(0, 0, self.file_map))
            
            if self.check(TokenType.RBRACE):
                end = self.tokens._peek(self.position)._span.end
                self.advance()
                break
            
            node = self.parse_statement(scope, True)
            
            if isinstance(node, GiveStmt):
                give_value = node
                statements.append(node)
                is_value_give = True
            else:
                self._add_node_to_list(statements, node)
        
        span_block = Span(start, end, self.file_map)
        
        if is_value_give:
            if not expects_value:
                self.diag.emit(ErrorCode.W2001, None, [Span(start, give_value.span.end, self.file_map)], [(give_value.span, "this `give` is unreachable, no value is expected from this block")])
            return BlockExpr(statements, statements.index(give_value), scope, span_block)
        else:
            if expects_value:
                end_stmt = statements[-1] if statements else ErrorNode(Span(start, start, self.file_map))
                self.diag.emit(ErrorCode.E2007, None, [Span(start, end_stmt.span.end, self.file_map)], [(end_stmt.span, "`give` with a value was expected here")])
                self.synchronize(block)
                return ErrorNode(Span(0, 0, self.file_map))
        
        return BlockExpr(statements, None, scope, span_block)   
                
    def parse_if_form(self, scope_back: Enviroment, expects_value: bool, start: int, block: bool) -> IfForm:
        elif_branches = []
        else_branch = None
        len_branch = 1
        
        cond = self.expression(scope_back, block)
        block_expr = self._consume_block(scope_back, expects_value, start, block)
        if isinstance(block_expr, ErrorNode): return block_expr
        
        if_branch = IfBranch(cond, Span(start, block_expr.span.end, self.file_map), block_expr)
        
        while self.check(TokenType.KEYWORD_ELIF):
            token_elif = self.tokens._peek(self.position)
            self.advance()
            cond_elif = self.expression(scope_back, block)
            block_elif = self._consume_block(scope_back, expects_value, start, block)
            if isinstance(block_elif, ErrorNode): return block_elif
            
            elif_branches.append(IfBranch(cond_elif, Span(token_elif._span.start, block_elif.span.end, self.file_map), block_elif))
            len_branch += 1
                
        if self.check(TokenType.KEYWORD_ELSE):
            token_else = self.tokens._peek(self.position)
            self.advance()
            block_else = self._consume_block(scope_back, expects_value, start, block)
            if isinstance(block_else, ErrorNode): return block_else
            
            else_branch = IfBranch(BoolLiteral(1, Span(0, 0, self.file_map)), Span(token_else._span.start, block_else.span.end, self.file_map), block_else)
            len_branch += 1
            
        span_end = else_branch.span.end if else_branch else (elif_branches[-1].span.end if elif_branches else if_branch.span.end)
        span_if_form = Span(start, span_end, self.file_map)
        
        if len(elif_branches) < 1: elif_branches = None
        
        return IfForm(if_branch, elif_branches, else_branch, len_branch, span_if_form)
    
    def parse_while_form(self, scope_back: Enviroment, start: int, infinity: bool, block: bool) -> WhileForm:
        cond = BoolLiteral(1, Span(0, 0, self.file_map)) if infinity else self.expression(scope_back, block)
        block_expr = self._consume_block(scope_back, False, start, block)
        if isinstance(block_expr, ErrorNode): return block_expr
        
        return WhileForm(cond, block_expr, Span(start, block_expr.span.end, self.file_map))
            
    def parse_func_form(self, scope: Enviroment, start: int, block: bool) -> FuncForm:
        name: Token
        params: list[Param] = []
        
        if self.check(TokenType.LITERAL_IDENT):
            name = self.tokens._peek(self.position)
            self.advance()
        else:
            token = self.tokens._peek(self.position)
            span = self.get_error_span(token)
            self.diag.emit(ErrorCode.E2013, { "token" : token._value }, [span], [(span, "a valid function name was expected here")])
            self.synchronize(block, [TokenType.LBRACE])
            return ErrorNode(Span(0, 0, self.file_map))
            
        if self.check(TokenType.LPAREN):
            self.advance()
            while not(self.check(TokenType.RPAREN)):
                mut: bool
                if self.check(TokenType.KEYWORD_MUT): mut = True
                elif self.check(TokenType.KEYWORD_INMUT): mut = False
                else:
                    token = self.tokens._peek(self.position)
                    span = self.get_error_span(token)
                    self.diag.emit(ErrorCode.E2016, { "token" : token._value}, [span], [(span, "`mut` or `inmut` was expected here to start a parameter")])
                    self.synchronize(block, [TokenType.COMMA, TokenType.RPAREN])
                    if self.check(TokenType.COMMA):
                        self.advance()
                        continue
                    elif self.check(TokenType.RPAREN): break
                    else: return ErrorNode(Span(0, 0, self.file_map))
                    
                param_start = self.tokens._peek(self.position)._span.start
                self.advance()
                
                name_param: Token
                if self.check(TokenType.LITERAL_IDENT):
                    name_param = self.tokens._peek(self.position)
                else:
                    mut_keyword = "mut" if mut else "inmut"
                    token = self.tokens._peek(self.position)
                    span = self.get_error_span(token)
                    self.diag.emit(ErrorCode.E2017, { "mut_keyword" : mut_keyword, "token" : token._value }, [span], [(span, "a valid parameter name was expected here")])
                    self.synchronize(block, [TokenType.RPAREN, TokenType.COMMA])
                    if self.check(TokenType.COMMA):
                        self.advance()
                        continue
                    elif self.check(TokenType.RPAREN): break
                    else: return ErrorNode(Span(0, 0, self.file_map))
                
                self.advance()
                
                zontype: ZonType
                if self.check(TokenType.COLON):
                    self.advance()
                    zontype_token = self.tokens._peek(self.position)
                    match zontype_token._type:
                        case TokenType.KEYWORD_INT: zontype = ZonType.INT
                        case TokenType.KEYWORD_FLOAT: zontype = ZonType.FLOAT
                        case TokenType.KEYWORD_BOOL: zontype = ZonType.BOOL
                        case TokenType.KEYWORD_STRING: zontype = ZonType.STRING
                        case TokenType.KEYWORD_VOID:
                            self.diag.emit(ErrorCode.E2018, None, [zontype_token._span], [(zontype_token._span, "`void` cannot be used as a type here")])
                            self.synchronize(block, [TokenType.RPAREN, TokenType.COMMA])
                            if self.check(TokenType.COMMA):
                                self.advance()
                                continue
                            else: break
                        case _:
                            span = self.get_error_span(zontype_token)
                            self.diag.emit(ErrorCode.E2019, { "type" : zontype_token._value }, [span], [(span, "`{type}` is not a valid parameter type")])
                            self.advance()
                            self.synchronize(block, [TokenType.COMMA, TokenType.RPAREN])
                            if self.check(TokenType.COMMA):
                                self.advance()
                                continue
                            elif self.check(TokenType.RPAREN): break
                            else: return ErrorNode(Span(0, 0, self.file_map))
                else:
                    token = self.tokens._peek(self.position)
                    span = self.get_error_span(token)
                    self.diag.emit(ErrorCode.E2020, { "name" : token._value }, [span], [(span, "`:` and a valid type were expected here")])
                    self.synchronize(block, [TokenType.COMMA, TokenType.RPAREN])
                    if self.check(TokenType.COMMA):
                        self.advance()
                        continue
                    elif self.check(TokenType.RPAREN): break
                    else: return ErrorNode(Span(0, 0, self.file_map))
                    
                param_end = self.tokens._peek(self.position)._span.end
                self.advance()
                
                default = None
                if self.check(TokenType.OPERATOR_ASSIGN):
                    self.advance()
                    default = self.expression(scope, False)
                    param_end = default.span.end
                    
                params.append(Param(mut, name_param._value, zontype, default, Span(param_start, param_end, self.file_map), name_param._span))
                
                if self.check(TokenType.COMMA): self.advance()
                elif self.check(TokenType.RPAREN): break
                else:
                    token = self.tokens._peek(self.position)
                    span = self.get_error_span(token)
                    self.diag.emit(ErrorCode.E2025, { "token" : token._value}, [span], [(span, "`,` or `)` was expected here")])
                    self.synchronize(block, [TokenType.KEYWORD_FUNC])
                    return ErrorNode(Span(0, 0, self.file_map))
        else:
            token = self.tokens._peek(self.position)
            span = self.get_error_span(token)
            self.diag.emit(ErrorCode.E2014, { "token" : token._value, "name" : name._value }, [span], [(span, "`(` was expected here to open the parameter list")])
            self.synchronize(block, [TokenType.LBRACE])
            return ErrorNode(Span(0, 0, self.file_map))
        
        self.advance()
        
        return_type: ZonType
        if self.check(TokenType.ARROW):
            self.advance()
            zontype_token = self.tokens._peek(self.position)
            match zontype_token._type:
                case TokenType.KEYWORD_INT: return_type = ZonType.INT
                case TokenType.KEYWORD_FLOAT: return_type = ZonType.FLOAT
                case TokenType.KEYWORD_BOOL: return_type = ZonType.BOOL
                case TokenType.KEYWORD_STRING: return_type = ZonType.STRING
                case TokenType.KEYWORD_VOID: return_type = ZonType.VOID
                case _:
                    span = self.get_error_span(zontype_token)
                    self.diag.emit(ErrorCode.E2022, { "token" : zontype_token._value }, [span], [(span, "a valid return type or `void` was expected here")])
                    self.synchronize(block, [TokenType.LBRACE])
                    return ErrorNode(Span(0, 0, self.file_map))
        else:
            token = self.tokens._peek(self.position)
            span = self.get_error_span(token)
            self.diag.emit(ErrorCode.E2021, { "token" : token._value }, [span], [(span, "`->` was expected here to declare the return type")])
            self.synchronize(block, [TokenType.LBRACE])
            return ErrorNode(Span(0, 0, self.file_map))
        
        self.advance()
        
        block_expr = self._consume_block(scope, False, start, block)
        if isinstance(block_expr, ErrorNode): return block_expr
            
        if len(params) < 1: params = None
            
        return FuncForm(name._value, params, return_type, block_expr, name._span, Span(start, block_expr.span.end, self.file_map))
    
    def parse_call_func(self, name: Token, start: int, scope: Enviroment, block: bool) -> CallFunc:
        mode_keyparam = False
        keyparams = {}
        params = []
        
        while not self.check(TokenType.RPAREN):        
            if self.check(TokenType.LITERAL_IDENT) and self.tokens._peek(self.position + 1)._type == TokenType.OPERATOR_ASSIGN:
                mode_keyparam = True
                name_param = self.tokens._peek(self.position)
                
                if name_param._value in keyparams:
                    span_keyparam = keyparams[name_param._value][1]
                    self.diag.emit(ErrorCode.E2023, { "name" : name_param._value }, [name_param._span, span_keyparam], [(name_param._span, "`{name}` is passed again here"), (span_keyparam, "`{name}` was already passed here")])
                    self.synchronize(block, [TokenType.RPAREN, TokenType.COMMA])
                    if self.check(TokenType.COMMA):
                        self.advance()
                        continue
                    else: break
                
                self.advance()
                self.advance()
                expr_param = self.expression(scope, block)
                keyparams.update({name_param._value: (expr_param, Span(name_param._span.start, expr_param.span.end, self.file_map), name_param._span)})
                    
            else:
                if self.check(TokenType.RPAREN): break
                elif not mode_keyparam: params.append(self.expression(scope, block))
                else:
                    token = self.tokens._peek(self.position)
                    self.diag.emit(ErrorCode.E2024, None, [token._span], [(token._span, "positional parameter not allowed here, use `name=value` instead")])
                    self.synchronize(block, [TokenType.RPAREN, TokenType.COMMA])
                    if self.check(TokenType.COMMA):
                        self.advance()
                        continue
                    else: break
            
            if self.check(TokenType.COMMA):
                self.advance()
                continue
            elif self.check(TokenType.RPAREN): break
            else:
                token = self.tokens._peek(self.position)
                span = self.get_error_span(token)
                self.diag.emit(ErrorCode.E2025, { "token" : token._value }, [span], [(span, "`,` or `)` was expected here")])
                self.synchronize(block)
                return ErrorNode(Span(0, 0, self.file_map))
                
        end = self.tokens._peek(self.position)._span.end
        self.advance()
            
        if len(params) < 1: params = None
        if len(keyparams) < 1: keyparams = None
                    
        return CallFunc(name._value, params, keyparams, Span(start, end, self.file_map), name._span)

    def expression(self, scope: Enviroment, block: bool) -> Node:
        return self.logic_or_expr(scope, block)

    def logic_or_expr(self, scope: Enviroment, block: bool) -> Node:
        return self._parse_binary_expr(self.logic_and_expr, [TokenType.GATE_OR], scope, block)
    
    def logic_and_expr(self, scope: Enviroment, block: bool) -> Node:
        return self._parse_binary_expr(self.logic_not_expr, [TokenType.GATE_AND], scope, block)
    
    def logic_not_expr(self, scope: Enviroment, block: bool) -> Node:
        if self.check(TokenType.GATE_NOT):
            start = self.tokens._peek(self.position)._span.start
            self.advance()
            value: Node = self.logic_not_expr(scope, block)
            if isinstance(value, UnaryExpr) and value.operator == Operator.NOT:
                return value.value # Optimización: elimina doble negación
            return UnaryExpr(Operator.NOT, value, Span(start, value.span.end, self.file_map))
        return self.comparison_expr(scope, block)
    
    def comparison_expr(self, scope: Enviroment, block: bool) -> Node:
        return self._parse_binary_expr(
            self.term_expr,
            [TokenType.OPERATOR_GREATER, TokenType.OPERATOR_LESS, TokenType.OPERATOR_GREATER_EQUAL, 
             TokenType.OPERATOR_LESS_EQUAL, TokenType.OPERATOR_EQUAL, TokenType.OPERATOR_NOT_EQUAL],
            scope, block
        )
        
    def term_expr(self, scope: Enviroment, block: bool) -> Node:
        return self._parse_binary_expr(self.factor_expr, [TokenType.OPERATOR_PLUS, TokenType.OPERATOR_MINUS], scope, block)
    
    def factor_expr(self, scope: Enviroment, block: bool) -> Node:
        return self._parse_binary_expr(self.unary_expr, [TokenType.OPERATOR_MULT, TokenType.OPERATOR_DIV, TokenType.OPERATOR_MOD], scope, block)
    
    def unary_expr(self, scope: Enviroment, block: bool) -> Node:    
        if self.check(TokenType.OPERATOR_MINUS):
            start = self.tokens._peek(self.position)._span.start
            self.advance()
            value: Node = self.unary_expr(scope, block)
            if isinstance(value, UnaryExpr) and value.operator == Operator.NEG:
                return value.value
            return UnaryExpr(Operator.NEG, value, Span(start, value.span.end, self.file_map))
        elif self.check(TokenType.OPERATOR_PLUS):
            self.advance()
            return self.unary_expr(scope, block)
        else:
            return self.exponentiation_expr(scope, block)
    
    def exponentiation_expr(self, scope: Enviroment, block: bool) -> Node:
        node = self.primitive(scope, block)
        if isinstance(node, ErrorNode): return node
        
        start = node.span.start

        while self.check(TokenType.OPERATOR_POW):
            self.advance()
            right = self.exponentiation_expr(scope, block)
            if isinstance(right, ErrorNode): return node
            
            end = right.span.end
            node = BinaryExpr(node, Operator.POW, right, Span(start, end, self.file_map))
            
        return node
    
    def primitive(self, scope: Enviroment, block: bool) -> Node:
        if self.check(TokenType.LITERAL_NUMBER):
            current_token = self.tokens._peek(self.position)
            node = FloatLiteral(current_token._value, current_token._span) if isinstance(current_token._value, float) else IntLiteral(current_token._value, current_token._span)
            self.advance()
            return node

        elif self.check(TokenType.LITERAL_STRING):
            current_token = self.tokens._peek(self.position)
            self.advance()
            return StringLiteral(current_token._value, current_token._span)
                        
        elif self.check(TokenType.LITERAL_TRUE):
            span = self.tokens._peek(self.position)._span
            self.advance()
            return BoolLiteral(1, span)
        
        elif self.check(TokenType.LITERAL_FALSE):
            span = self. tokens._peek(self.position)._span
            self.advance()
            return BoolLiteral(0, span)
        
        elif self.check(TokenType.LPAREN):
            span_lparen = self.tokens._peek(self.position)._span
            self.advance()
            node = self.expression(scope, block)
            
            if self.check(TokenType.RPAREN):
                self.advance()
                return node
            else:
                token = self.tokens._peek(self.position)
                self.diag.emit(ErrorCode.E2003, None, [Span(span_lparen.start, node.span.end, self.file_map)], [(Span(node.span.end-1, node.span.end, self.file_map), "`)` was expected here to close the expression")])
                self.synchronize(block)
                return ErrorNode(Span(0, 0, self.file_map))
        
        elif self.check(TokenType.LITERAL_IDENT):
            var_ident = self.tokens._peek(self.position)
            self.advance()
            if self.check(TokenType.LPAREN):
                self.advance()
                return self.parse_call_func(var_ident, var_ident._span.start, scope, block)
            return VariableExpr(var_ident._value, Span(var_ident._span.start, var_ident._span.end, self.file_map))
        
        elif self.check(TokenType.LBRACE):
            start = self.tokens._peek(self.position)._span.start
            self.advance()
            return self.parse_block_expr(True, start, scope, block)
        
        elif self.check(TokenType.KEYWORD_IF):
            start = self.tokens._peek(self.position)._span.start
            self.advance()
            return self.parse_if_form(scope, True, start, block)
        
        else:
            token = self.tokens._peek(self.position)
            span = self.get_error_span(token)
            
            self.diag.emit(ErrorCode.E2005, { "token" : token._value}, [span], [(span, "cannot start an expression")])
            self.synchronize(block)
            return ErrorNode(Span(0, 0, self.file_map))