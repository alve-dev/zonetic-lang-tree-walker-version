from zonc.ast import *
from zonc.zonc_errors import DiagnosticEngine
from zonc.enviroment import *
from zonc.zonc_errors import ErrorCode
from zonc.location_file import Span, FileMap
from dataclasses import dataclass, field

@dataclass
class DictTemp:
    dict_temp: dict


@dataclass
class FlowResult:
    has_global_returned: bool = False
    has_returned: bool = False
    return_type: ZonType | None = None
    possible_not_return: list[dict] = field(default_factory=list)
    has_given: bool = False
    give_type: ZonType | None = None
    give_span: Span | None = None
    has_broken: bool = False
    has_continued: bool = False


class Semantic:
    def __init__(self, diag: DiagnosticEngine, file_map: FileMap) -> None:
        self.diag = diag
        self.file_map = file_map
        self.current_func: FuncSymbol | None = None
        self.loop_depth: int = 0
        
    def insert_std(self, scope: Enviroment):
        span_aux = Span(0, 0, self.file_map)
        scope.define("print", FuncSymbol([], span_aux, span_aux, ZonType.VOID, True, True))
        scope.define("readInt", FuncSymbol(
            [Param(False, "prompt", ZonType.STRING, StringLiteral(" ", span_aux), span_aux, span_aux)],
            span_aux, span_aux, ZonType.INT, True, True))
        scope.define("readFloat", FuncSymbol(
            [Param(False, "prompt", ZonType.STRING, StringLiteral(" ", span_aux), span_aux, span_aux)],
            span_aux, span_aux, ZonType.FLOAT, True, True))
        scope.define("readString", FuncSymbol(
            [Param(False, "prompt", ZonType.STRING, StringLiteral(" ", span_aux), span_aux, span_aux)],
            span_aux, span_aux, ZonType.STRING, True, True))
        
    
    def pre_scan(self, ast: Node, scope: Enviroment):
        self.insert_std(scope)
        for node in ast.stmts:
            if isinstance(node, FuncForm):
                get: FuncSymbol = scope.get_symbol(node.name)
                if not(get is None):
                    if get.is_native:
                        self.diag.emit(
                            ErrorCode.E3013,
                            { "name" : node.name, "kind" : "function" },
                            [node.span_name],
                            [(node.span_name, "this name is already in use for a native function")]
                        )
                        continue
                    
                    self.diag.emit(
                        ErrorCode.E3013,
                        { "name" : node.name, "kind" : "function" },
                        [node.span_name, get.name_span],
                        [(node.span_name, "this name is already in use"), (get.name_span, "first defined as a function here")]
                    )
                    continue
                
                scope.define(
                    node.name,
                    FuncSymbol(node.params, node.span, node.span_name, node.return_type)
                )

    def check_ast(self, ast: Node, is_expr: bool) -> None | ZonType:
        scope: Enviroment = ast.scope
        self.pre_scan(ast, scope)
        self.evaluate_statements(ast.stmts, scope, is_expr=is_expr)
        return None

    def evaluate_statements(
        self,
        stmts: list[Node],
        scope: Enviroment,
        is_expr: bool = False,
        is_func_body: bool = False,
        sym_empty_count: DictTemp = None,
    ) -> FlowResult:
        flow = FlowResult()
        len_stmts = len(stmts)
        
        for i, stmt in enumerate(stmts):
            if isinstance(stmt, DeclarationStmt):    
                self.check_declaration_stmt(stmt, scope)
                
            elif isinstance(stmt, AssignmentStmt):
                symbol = scope.get_symbol(stmt.name)
                
                if isinstance(symbol, FuncSymbol): continue
                if symbol is None:
                    self.diag.emit(ErrorCode.E3001, { "name" : stmt.name }, [stmt.span], [(stmt.span_name, "does not exist in this scope")])
                    continue
                    
                is_empty = symbol.is_empty
                self.check_assignment_stmt(stmt, scope, True)
                if not(sym_empty_count is None) and not(scope.exist_here(stmt.name)):
                    if stmt.name in sym_empty_count.dict_temp:
                        sym_empty_count.dict_temp[stmt.name][0] += 1
                    else:
                        if not scope.exist_here(stmt.name):
                            if not(symbol is None) and is_empty:
                                sym_empty_count.dict_temp.update({stmt.name : [1, symbol.decl_span]})
                    
                    symbol.is_empty = True
            
            elif isinstance(stmt, BlockExpr):
                block_flow = self.evaluate_statements(stmt.stmts, stmt.scope, is_expr=False)
                if block_flow.has_returned:
                    flow.has_returned = True
                    flow.possible_not_return.extend(block_flow.possible_not_return)
                
            elif isinstance(stmt, GiveStmt):
                if is_func_body:
                    self.diag.emit(
                        ErrorCode.E3018, None, [stmt.span],
                        [(stmt.span, "`give` is only for block expressions, not function bodies")]
                    )
                else:
                    flow.has_given = True
                    flow.give_type = self.infer_expr(stmt.value, scope)
                    flow.give_span = stmt.span
                    
            elif isinstance(stmt, IfForm):
                if_flow = self.check_if_form(stmt, scope, is_expr=False)
                if if_flow.has_returned:
                    flow.has_returned = True
                    flow.possible_not_return.extend(if_flow.possible_not_return)
            
            elif isinstance(stmt, WhileForm):
                self.loop_depth += 1
                while_flow = self.check_while_form(scope, stmt)
                self.loop_depth -= 1
                
                if while_flow.has_returned:
                    flow.possible_not_return.extend(while_flow.possible_not_return)
            
            elif isinstance(stmt, BreakStmt):
                if self.loop_depth == 0:
                    self.diag.emit( ErrorCode.E3012, {"keyword" : "break" }, [stmt.span], 
                    [(stmt.span, "can only be used in loops")])
                else:
                    flow.has_broken = True
            
            elif isinstance(stmt, ContinueStmt):
                if self.loop_depth == 0:
                    self.diag.emit( ErrorCode.E3012, {"keyword" : "break" }, [stmt.span], 
                    [(stmt.span, "can only be used in loops")])
                else:
                    flow.has_continued = True
                    
            elif isinstance(stmt, FuncForm):
                if is_func_body:
                    self.diag.emit(
                        ErrorCode.E3017, { "inner_name" : stmt.name }, [stmt.span_name],
                        [[stmt.span_name, "nested functions are forbidden"]]
                    )
                else:
                    self.check_func_form(stmt, scope)
                
            elif isinstance(stmt, ReturnStmt):
                if is_func_body:
                    flow.has_global_returned = True

                flow.has_returned = True
                flow.return_type = self.check_return_stmt(stmt, scope)
                
            elif isinstance(stmt, CallFunc):
                self.check_call_func(stmt, scope)
                
            if flow.has_returned or flow.has_given or flow.has_broken or flow.has_continued:
                if i < len_stmts - 1:
                    
                    if isinstance(stmt, GiveStmt):
                        self.diag.emit(
                            ErrorCode.W3001, None, [stmt.span, stmts[-1].span],
                            [(stmt.span, "this `give` exits the current block expr"), (stmts[-1].span, "...so this code will never be executed.")]
                        )
                        break
                    
                    if isinstance(stmt, ReturnStmt) and is_func_body:
                        self.diag.emit(
                            ErrorCode.W3005, { "aux" : '}'}, [stmt.span, stmts[-1].span],
                            [(stmt.span, "this `return` exits the current function"), (stmts[-1].span, "...so this code will never be executed.")]
                        )
                        break
                    
                    if isinstance(stmt, (BreakStmt, ContinueStmt)):
                        keyword = "break" if isinstance(stmt, BreakStmt) else "continue"
                        self.diag.emit(
                            ErrorCode.W3006, { "keyword" : keyword }, [stmt.span, stmts[-1].span],
                            [(stmt.span, "this `{keyword}` exits the current loop"), (stmts[-1].span, "...so this code will never be executed.")]
                        )
                        break

        return flow

    def check_return_stmt(self, node: ReturnStmt, scope: Enviroment) -> ZonType:
        if self.current_func is None:
            self.diag.emit(
                ErrorCode.E3014, None, [node.span],
                [(node.span, "this `return` is not inside a function scope")]
            )
            return ZonType.UNKNOWN
                
        type_expr = ZonType.VOID if node.value is None else self.infer_expr(node.value, scope)
        
        if type_expr != self.current_func.return_type:
            self.diag.emit(
                ErrorCode.E3015,
                { "func_name" : self.current_func.name_span.to_string(),
                  "found" : type_expr.name.lower(),
                  "expected" : self.current_func.return_type.name.lower()},
                [node.span],
                [(node.span, "expected `{expected}`, found `{found}`")]
            )
        return type_expr
        
    def check_func_form(self, node: FuncForm, scope: Enviroment):
        prev_func = self.current_func
        self.current_func = scope.get_symbol(node.name)
        # llenar el scope con variables de los parametros
        if not node.params is None:
            for param in node.params:
                param_to_decl = DeclarationStmt(
                    param.name,
                    param.mut,
                    param.zontype,
                    param.span_name,
                    param.span
                )
                self.check_declaration_stmt(param_to_decl, node.block_expr.scope, (param.default is None))
                
                if not param.default is None:
                    param_to_assign = AssignmentStmt(
                        param.name,
                        param.default,
                        param.span,
                        param.span_name
                    )
                    self.check_assignment_stmt(param_to_assign, node.block_expr.scope, True, True)
        
        
        flow = self.evaluate_statements(node.block_expr.stmts, node.block_expr.scope, is_func_body=True)
        
        if not flow.has_global_returned and len(flow.possible_not_return) > 0 and node.return_type != ZonType.VOID:
            for error_span in flow.possible_not_return:
                self.diag.emit(
                    ErrorCode.E3019, { "func_name" : node.name }, [error_span["span"]],
                    [(Span(error_span["span"].end-1, error_span["span"].end, self.file_map), "missing 'else' or a global 'return' after this if form")]
                )
                
        self.current_func = prev_func
    
    def check_call_func(self, node: CallFunc, scope: Enviroment):
        func_symbol: FuncSymbol = scope.get_symbol(node.name)
        there_is_error = False
        
        if func_symbol.is_native and func_symbol.is_varidic:
            for expr in node.params:
                self.infer_expr(expr, scope)
            return
        
        if func_symbol is None or isinstance(func_symbol, Symbol):
            self.diag.emit(ErrorCode.E3020, { "name" : node.name }, [node.span], [(node.span, "cannot call `{name}` because it has not been defined")])
            if not there_is_error: there_is_error = True
            return
        
        func_params = {}
        if not func_symbol.params is None:
            for param in func_symbol.params:
                is_default = False if param.default is None else True
                func_params.update({param.name: [False, 0, is_default]})
        
        if not node.params is None:
            if len(func_params) == 0:
                self.diag.emit(ErrorCode.E3021, None, [node.span, func_symbol.name_span],
                [(node.span, "these parameters are not expected here"), (func_symbol.name_span, "this function is defined with no parameters")])
                if not there_is_error: there_is_error = True
                return
            
            for i, param in enumerate(node.params):
                zontype_param = self.infer_expr(param, scope)
                if zontype_param == ZonType.UNKNOWN: continue
                func_param = func_symbol.params[i]
                
                if zontype_param != func_param.zontype:
                    self.diag.emit(ErrorCode.E3022, { "found" : zontype_param.name.lower(), "expect" : func_param.zontype.name.lower()},
                    [param.span], [(param.span, "this expression is `{found}` but the parameter expects `{expect}`")])
                    if not there_is_error: there_is_error = True
                    continue
                
                func_params[func_param.name][0] = True
                func_params[func_param.name][1] = i
                
        if not node.keyparams is None:
            if len(func_params) == 0:
                self.diag.emit(ErrorCode.E3021, None, [func_symbol.name_span, node.span],
                [(func_symbol.name_span, "this function is defined with no parameters"), (node.span, "these parameters are not expected here")])
                if not there_is_error: there_is_error = True
                return
                        
            for key, value in node.keyparams.items():
                zontype_param = self.infer_expr(value[0], scope)
                if zontype_param == ZonType.UNKNOWN: return
                
                func_param = None
                for i in range(len(func_symbol.params)):
                    if key == func_symbol.params[i].name:
                        func_param = func_symbol.params[i]
                
                if func_param is None:
                    self.diag.emit(ErrorCode.E3023, { "name" : node.name, "name_param" : key },
                    [value[1]], [(value[2], "this parameter does not exist in `{name}`")])
                    if not there_is_error: there_is_error = True
                    continue
                
                if func_params[func_param.name][0]:
                    self.diag.emit(ErrorCode.E3024, { "name_func" : node.name, "name_param" : key, "param_pos" : func_params[func_param.name][1] },
                    [value[1]], [(value[1], "this parameter already received a value")])
                    if not there_is_error: there_is_error = True
                    continue
                
                if zontype_param != func_param.zontype:
                    self.diag.emit(ErrorCode.E3022, { "found" : zontype_param.name.lower(), "expect" : func_param.zontype.name.lower()},
                    [param.span], [(param.span, "this expression is `{found}` but the parameter expects `{expect}`")])
                    if not there_is_error: there_is_error = True
                    continue
                
                func_params[func_param.name][0] = True
        
        missing_params = 0
        for key, value in func_params.items():
            if not value[0] and not value[2]:
                missing_params += 1
        
        if missing_params > 0 and not there_is_error:
            self.diag.emit(ErrorCode.E3025, { "name_func" : node.name, "num" : missing_params }, [node.span_name],
            [(node.span_name, "missing {num} required parameter(s)")])
            
    def check_declaration_stmt(self, node: DeclarationStmt, scope: Enviroment, is_param = False):
        get = scope.get_symbol(node.name)
        if not(get is None) and isinstance(get, FuncSymbol):
            self.diag.emit(
                ErrorCode.E3013, { "name": node.name, "kind": "variable"},
                [node.span_name, get.name_span],
                [(node.span_name, "this name is already in use"), (get.name_span, "first defined as a function here")]
            )
            return
        
        scope.define(node.name, Symbol(node.mut, node.type, not is_param, node.span))
            
    def check_assignment_stmt(self, node: AssignmentStmt, scope: Enviroment, not_empty: bool, is_param = False):
        value_type = self.infer_expr(node.value, scope)
        if value_type == ZonType.UNKNOWN: return
        
        symbol = scope.get_symbol(node.name)
        if symbol is None:
            self.diag.emit(ErrorCode.E3001, { "name" : node.name }, [node.span], [(node.span_name, "does not exist in this scope")])
            return
        
        if isinstance(symbol, FuncSymbol): return
        
        if not symbol.mutability and not symbol.is_empty:
            self.diag.emit(ErrorCode.E3005, { "name" : node.name }, [node.span, symbol.decl_span],
            [(node.span_name, "is immutable, it was already assigned a value"), (symbol.decl_span, "was first defined as immutable here")])
            return
        
        
        if self.loop_depth > 0 and not(scope.exist_here(node.name)) and not(symbol.mutability) and symbol.is_empty:
            self.diag.emit(ErrorCode.E3016, None, [node.span], [(node.span_name, "cannot initialize an outer `inmut` variable here")])
            return
        
        if symbol.zontype == ZonType.UNKNOWN:
            symbol.zontype = value_type
            
        elif symbol.zontype != value_type:
            err_span = node.value.stmts[node.value.give_address].value.span if isinstance(node.value, BlockExpr) else node.value.span
            self.diag.emit(
                ErrorCode.E3006,
                { "name" : node.name, "expected_type" : symbol.zontype.name.lower(), "found_type" : value_type.name.lower()},
                [node.span],
                [(err_span, "this expression returns '{found_type}', but '{name}' expects '{expected_type}'")]
            )
            return
    
        if symbol.is_empty and not_empty and not is_param:
            symbol.is_empty = False
                
    def check_if_form(self, if_node: IfForm, scope: Enviroment, is_expr: bool) -> FlowResult | list:
        sym_empty_count = DictTemp({})
        values_give = []
        flow = FlowResult()

        def eval_branch(branch, is_expr_branch, is_else) -> FlowResult:
            if isinstance(branch.cond, BoolLiteral) and not is_else:
                has_unreachable = (if_node.elif_branches or if_node.else_branch)
                if branch.cond.value == 1 and has_unreachable:
                    self.diag.emit(ErrorCode.W3002, None, [branch.cond.span], [(branch.cond.span, "this condition is always `true`")])
                elif branch.cond.value == 0:
                    self.diag.emit(ErrorCode.W3003, None, [branch.cond.span], [(branch.cond.span, "this condition is always `false`")])
            
            check_cond = True
            if is_else:
                check_cond = False
            
            return self.check_if_branch(branch, scope, sym_empty_count, check_cond, is_expr_branch)

        if_branch_flow = eval_branch(if_node.if_branch, is_expr, False)
        if is_expr and if_branch_flow.has_given: values_give.append((if_branch_flow.give_type, if_branch_flow.give_span))
        if if_branch_flow.has_returned: flow.has_returned = True
        
        if if_node.else_branch is None:
            if flow.has_returned:
                flow.possible_not_return.append({"span" : if_node.span})
            
            if len(sym_empty_count.dict_temp) > 0:
                last_branch_span = if_node.elif_branches[-1].span if if_node.elif_branches else if_node.if_branch.span
                self.diag.emit(ErrorCode.E3008, None, [last_branch_span], [(Span(last_branch_span.end-1, last_branch_span.end, self.file_map), "an `else` branch was expected here")])
                return flow
                
        if if_node.elif_branches:
            for elif_node in if_node.elif_branches:
                elif_flow = eval_branch(elif_node, is_expr, False)
                if is_expr and elif_flow.has_given: values_give.append((elif_flow.give_type, elif_flow.give_span))
                if elif_flow.has_returned and flow.has_returned and elif_flow.return_type != if_branch_flow.return_type:
                    flow.possible_not_return.append({"span": if_node.span})

        if if_node.else_branch:
            else_flow = eval_branch(if_node.else_branch, is_expr, True)
            if is_expr and else_flow.has_given: values_give.append((else_flow.give_type, else_flow.give_span))

        if len(sym_empty_count.dict_temp) > 0:
            for symbol, branches_span in sym_empty_count.dict_temp.items():
                if branches_span[0] < if_node.len_branch:
                    self.diag.emit(
                        ErrorCode.E3009, { "name" : symbol }, [if_node.span, branches_span[1]],
                        [(Span(if_node.span.end-1, if_node.span.end, self.file_map), "`{name}` is first assigned inside this if form, but not in every branch"),
                         (branches_span[1], "`{name}` is declared empty here and may still be empty after the if form")]
                    )
                else:
                    scope.get_symbol(symbol).is_empty = False
        
        return values_give if is_expr else flow
                
    def check_if_branch(self, if_branch: IfBranch, scope_back: Enviroment, sym_empty_count: DictTemp, check_cond: bool, is_expr: bool) -> FlowResult:
        if check_cond:
            type_condition = self.infer_expr(if_branch.cond, scope_back)
            if type_condition != ZonType.UNKNOWN and type_condition != ZonType.BOOL:
                self.diag.emit(
                    ErrorCode.E3007, { "found_type" : type_condition.name.lower() },
                    [Span(if_branch.span.start, if_branch.cond.span.end, self.file_map)],
                    [(if_branch.cond.span, "this expression returns `{found_type}`, but a condition field expects `bool`")]
                )

        return self.evaluate_statements(if_branch.block.stmts, if_branch.block.scope, is_expr=is_expr, sym_empty_count=sym_empty_count)
                
    def check_while_form(self, scope: Enviroment, while_node: WhileForm) -> FlowResult:
        type_condition = self.infer_expr(while_node.condition_field, scope)
        if type_condition != ZonType.UNKNOWN and type_condition != ZonType.BOOL:
            self.diag.emit(
                ErrorCode.E3007, { "found_type" : type_condition.name.lower() },
                [Span(while_node.span.start, while_node.condition_field.span.end, self.file_map)],
                [(while_node.condition_field.span, "this expression returns `{found_type}`, but a condition field expects `bool`")]
            )
            
        flow = self.evaluate_statements(while_node.block_expr.stmts, while_node.block_expr.scope)
        
        if isinstance(while_node.condition_field, BoolLiteral):
            if while_node.condition_field.value == 1:
                if not flow.has_broken:
                    self.diag.emit(
                        ErrorCode.W3004, None, [while_node.span],
                        [(Span(while_node.span.end - 1, while_node.span.end, self.file_map), "this loop has no exit point")]
                    )
            else:
                self.diag.emit(
                    ErrorCode.W3003, None, [while_node.condition_field.span],
                    [(while_node.condition_field.span, "this condition is always `false`")]
                )
        return flow
            
    def check_operands_type(self, operands_type: tuple, return_type: ZonType, equal: bool, operator: str, *zontypes):    
        len_types = len(zontypes)
        for i in range(len(operands_type)):
            no_match = sum(1 for j in range(len_types) if operands_type[i][0] != zontypes[j])
            
            if no_match == len_types:
                valid_types = ", ".join(t.name.lower() for t in zontypes[:-1])
                if len_types > 1: valid_types += f" or {zontypes[-1].name.lower()}"
                else: valid_types = zontypes[0].name.lower()
                
                self.diag.emit(
                    ErrorCode.E3003,
                    { "operator": operator, "valid_types": valid_types, "found_type": operands_type[i][0].name.lower()},
                    [operands_type[i][1]],
                    [(operands_type[i][1], "this operand is `{found_type}`, but `{operator}` expects {valid_types}")]
                )
                return ZonType.UNKNOWN
                
        if equal and operands_type[0][0] != operands_type[1][0]:
            self.diag.emit(
                ErrorCode.E3004,
                { "operator": operator, "right_type": operands_type[1][0].name.lower(), "left_type": operands_type[0][0].name.lower()},
                [operands_type[1][1]],
                [(operands_type[1][1], "this is `{right_type}`, but `{operator}` expects `{left_type}` to match the left operand")]
            )
            return ZonType.UNKNOWN
            
        return return_type
                
    def infer_expr(self, expr: NodeExpr, scope: Enviroment) -> ZonType:
        if isinstance(expr, IntLiteral): return ZonType.INT
        elif isinstance(expr, FloatLiteral): return ZonType.FLOAT
        elif isinstance(expr, BoolLiteral): return ZonType.BOOL
        elif isinstance(expr, StringLiteral): return ZonType.STRING
        
        elif isinstance(expr, BinaryExpr):
            op = expr.operator
            left_type = self.infer_expr(expr.left, scope)
            right_type = self.infer_expr(expr.right, scope)
            
            if left_type == ZonType.UNKNOWN or right_type == ZonType.UNKNOWN: return ZonType.UNKNOWN
            
            if op in (Operator.ADD, Operator.SUB, Operator.MUL, Operator.POW, Operator.MOD, Operator.DIV):
                op_str = {Operator.ADD: '+', Operator.SUB: '-', Operator.MUL: '*', Operator.DIV: '/', Operator.MOD: '%', Operator.POW: "**"}[op]
                return self.check_operands_type(((left_type, expr.left.span), (right_type, expr.right.span)), left_type, True, op_str, ZonType.INT, ZonType.FLOAT)
            
            elif op in (Operator.LT, Operator.GT, Operator.LE, Operator.GE):
                op_str = {Operator.LT: '<', Operator.GT: '>', Operator.LE: '<=', Operator.GE: '>='}[op]
                return self.check_operands_type(((left_type, expr.left.span), (right_type, expr.right.span)), ZonType.BOOL, True, op_str, ZonType.INT, ZonType.FLOAT)
            
            elif op in (Operator.AND, Operator.OR):
                op_str = {Operator.AND: 'and/&&', Operator.OR: 'or/||'}[op]
                return self.check_operands_type(((left_type, expr.left.span), (right_type, expr.right.span)), left_type, False, op_str, ZonType.BOOL)
            
            elif op in (Operator.EQ, Operator.NE):
                op_str = {Operator.EQ: '==', Operator.NE: '!='}[op]
                return self.check_operands_type(((left_type, expr.left.span), (right_type, expr.right.span)), ZonType.BOOL, True, op_str, ZonType.INT, ZonType.FLOAT, ZonType.BOOL, ZonType.STRING)
                
        elif isinstance(expr, UnaryExpr):
            op = expr.operator
            value_type = self.infer_expr(expr.value, scope)
            if value_type == ZonType.UNKNOWN: return ZonType.UNKNOWN
            
            if op == Operator.NEG:
                return self.check_operands_type(((value_type, expr.value.span),), value_type, False, '-', ZonType.INT, ZonType.FLOAT)
            else:
                return self.check_operands_type(((value_type, expr.value.span),), value_type, False, 'not/!', ZonType.BOOL)
        
        elif isinstance(expr, VariableExpr):
            symbol = scope.get_symbol(expr.name)
            if symbol is None:
                self.diag.emit(ErrorCode.E3001, { "name" : expr.name }, [expr.span], [(expr.span, "does not exist in this scope")])
                return ZonType.UNKNOWN
            elif symbol.is_empty:
                self.diag.emit(ErrorCode.E3002, { "name" : expr.name }, [expr.span], [(expr.span, "has no value at this point")])
                return ZonType.UNKNOWN
            return symbol.zontype
        
        elif isinstance(expr, BlockExpr):
            self.evaluate_statements(expr.stmts, expr.scope, is_expr=True)
            return self.infer_expr(expr.stmts[expr.give_address].value, expr.scope)

        elif isinstance(expr, IfForm):
            if expr.else_branch is None:
                last_branch_span = expr.elif_branches[-1].span if expr.elif_branches else expr.if_branch.span
                self.diag.emit(ErrorCode.E3010, None, [last_branch_span], [(Span(last_branch_span.end - 1, last_branch_span.end, self.file_map), "an `else` branch is required here when the if form is used as an expression")])
                return ZonType.UNKNOWN
            
            give_values = self.check_if_form(expr, scope, is_expr=True)
            type_first, errors_span, codes_span = None, [], []
            
            for i, val in enumerate(give_values):
                if i == 0:
                    type_first = val[0]
                    continue
                if val[0] != type_first:
                    errors_span.append((val[1], f"this `give` returns `{val[0].name.lower()}`, but the if form expects `{type_first.name.lower()}`"))
                    codes_span.append(val[1])
            
            if codes_span:
                self.diag.emit(ErrorCode.E3011, None, codes_span, errors_span)
                return ZonType.UNKNOWN
            return type_first

        elif isinstance(expr, CallFunc):
            self.check_call_func(expr, scope)
            func_symbol = scope.get_symbol(expr.name)
            if func_symbol is None: return ZonType.UNKNOWN
            if func_symbol.return_type == ZonType.VOID:
                self.diag.emit(ErrorCode.E3026, { "name" : expr.name }, [expr.span_name], [(expr.span_name, "this call returns `void`")])
                return ZonType.UNKNOWN
            return func_symbol.return_type
            
        return ZonType.UNKNOWN