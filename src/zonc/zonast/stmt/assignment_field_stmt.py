from .node_stmt import NodeStmt
from zonc.location_file import Span
from .assignment_stmt import AssignmentStmt
from ..expr.field_expr import FieldExpr
from ..expr.variable_expr import VariableExpr

class AssignmentFieldStmt(NodeStmt):
    def __init__(
        self,
        object_name: 'FieldExpr | VariableExpr',
        field_assign: AssignmentStmt,
        span: Span
    ):
        self.object_name = object_name
        self.field_assign = field_assign
        self.span = span

    def get_details(self):
        detail = [self.field_assign.name, '=', 'expr']
        current = self.object_name
        while isinstance(current, FieldExpr):
            detail.insert(0, '.')
            detail.insert(0, current.field)
            
        detail.insert(0, '.')
        detail.insert(0, current.name)
        
        return "".join(detail)
    
    def get_children(self):
        return [self.field_assign]