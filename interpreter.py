from parser import (
    Program, FunctionDef, Return, If, While, Assign,
    ExprStatement, BinaryOp, UnaryOp, Call, Identifier,
    NumberLiteral, StringLiteral
)


class LangRuntimeError(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise LangRuntimeError(f"Undefined variable '{name}'")

    def set(self, name, value):
        env = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        self.vars[name] = value

    def define(self, name, value):
        self.vars[name] = value


class Function:
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure


class BuiltinFunction:
    def __init__(self, name, fn):
        self.name = name
        self.fn = fn


class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.globals.define('print', BuiltinFunction('print', self.builtin_print))
        self.globals.define('put', BuiltinFunction('put', self.builtin_put))
        self.globals.define('input', BuiltinFunction('input', self.builtin_input))

    def builtin_print(self, args):
        print(*[self.stringify(a) for a in args])
        return None

    def builtin_put(self, args):
        print(*[self.stringify(a) for a in args], end='', sep='')
        return None

    def builtin_input(self, args):
        value = input()
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    def stringify(self, value):
        if value is None:
            return 'nil'
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    def run(self, program):
        self.execute_block(program.statements, self.globals)

    def execute_block(self, statements, env):
        for stmt in statements:
            self.execute(stmt, env)

    def execute(self, node, env):
        method = getattr(self, f'exec_{type(node).__name__}', None)
        if method is None:
            raise LangRuntimeError(f"No executor for {type(node).__name__}")
        return method(node, env)

    def exec_FunctionDef(self, node, env):
        func = Function(node.name, node.params, node.body, env)
        env.define(node.name, func)

    def exec_Return(self, node, env):
        value = self.evaluate(node.value, env) if node.value is not None else None
        raise ReturnSignal(value)

    def exec_If(self, node, env):
        condition = self.evaluate(node.condition, env)
        if self.is_truthy(condition):
            self.execute_block(node.then_body, env)
        else:
            self.execute_block(node.else_body, env)

    def exec_While(self, node, env):
        while self.is_truthy(self.evaluate(node.condition, env)):
            self.execute_block(node.body, env)

    def exec_Assign(self, node, env):
        value = self.evaluate(node.value, env)
        if node.op == '=':
            env.set(node.name, value)
        elif node.op == '+=':
            current = env.get(node.name)
            env.set(node.name, self.apply_binary('+', current, value))
        elif node.op == '-=':
            current = env.get(node.name)
            env.set(node.name, self.apply_binary('-', current, value))
        else:
            raise LangRuntimeError(f"Unknown assignment operator {node.op}")

    def exec_ExprStatement(self, node, env):
        self.evaluate(node.expr, env)

    def evaluate(self, node, env):
        method = getattr(self, f'eval_{type(node).__name__}', None)
        if method is None:
            raise LangRuntimeError(f"No evaluator for {type(node).__name__}")
        return method(node, env)

    def eval_NumberLiteral(self, node, env):
        return node.value

    def eval_StringLiteral(self, node, env):
        return node.value

    def eval_Identifier(self, node, env):
        return env.get(node.name)

    def eval_UnaryOp(self, node, env):
        value = self.evaluate(node.operand, env)
        if node.op == '-':
            if not self.is_number(value):
                raise LangRuntimeError("Unary '-' requires a number operand")
            return -value
        if node.op == 'not':
            return not self.is_truthy(value)
        raise LangRuntimeError(f"Unknown unary operator {node.op}")

    def eval_BinaryOp(self, node, env):
        if node.op == 'and':
            left = self.evaluate(node.left, env)
            if not self.is_truthy(left):
                return left
            return self.evaluate(node.right, env)
        if node.op == 'or':
            left = self.evaluate(node.left, env)
            if self.is_truthy(left):
                return left
            return self.evaluate(node.right, env)
        left = self.evaluate(node.left, env)
        right = self.evaluate(node.right, env)
        return self.apply_binary(node.op, left, right)

    def eval_Call(self, node, env):
        callee = env.get(node.callee)
        args = [self.evaluate(arg, env) for arg in node.args]
        return self.call_function(callee, args)

    def call_function(self, callee, args):
        if isinstance(callee, BuiltinFunction):
            return callee.fn(args)
        if isinstance(callee, Function):
            if len(args) != len(callee.params):
                raise LangRuntimeError(
                    f"Function '{callee.name}' expects {len(callee.params)} arguments but got {len(args)}"
                )
            call_env = Environment(parent=callee.closure)
            for param, value in zip(callee.params, args):
                call_env.define(param, value)
            try:
                self.execute_block(callee.body, call_env)
            except ReturnSignal as signal:
                return signal.value
            return None
        raise LangRuntimeError("Attempted to call a non-function value")

    def is_number(self, value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def is_truthy(self, value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if self.is_number(value):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        return True

    def get_type_rank(self, value):
        match value:
            case bool(): return 0
            case int(): return 1
            case float(): return 2
            case str(): return 3
            case _: raise LangRuntimeError(f"Cannot determine type rank for {type(value).__name__}")

    def cast_to_rank(self, value, rank):
        match rank:
            case 0: return bool(value)
            case 1: return int(value)
            case 2: return float(value)
            case 3: return self.stringify(value)
            case _: raise LangRuntimeError(f"Invalid type rank {rank}")
    
    def apply_binary(self, op, left, right):
        if left is None or right is None:
            if op == '==': return left == right
            if op == '!=': return left != right
            raise LangRuntimeError(f"Unsupported operand types for {op} with nil")
        
        rank_left = self.get_type_rank(left)
        rank_right = self.get_type_rank(right)
        target_rank = max(rank_left, rank_right)
        val_left = self.cast_to_rank(left, target_rank)
        val_right = self.cast_to_rank(right, target_rank)

        # strings
        if target_rank == 3: 
            if op == '+': return val_left + val_right
            if op == '==': return val_left == val_right
            if op == '!=': return val_left != val_right
            if op in ('<', '<=', '>', '>='):
                if op == '<': return val_left < val_right
                if op == '<=': return val_left <= val_right
                if op == '>': return val_left > val_right
                if op == '>=': return val_left >= val_right
            raise LangRuntimeError(f"Unsupported operator '{op}' for string types")
        
        else:
            if op == '+': return val_left + val_right
            if op == '-': return val_left - val_right
            if op == '*': return val_left * val_right
            if op == '/':
                if val_right == 0:
                    raise LangRuntimeError("Division by zero")
                return val_left / val_right
            if op == '%':
                if val_right == 0:
                    raise LangRuntimeError("Modulo by zero")
                return val_left % val_right
            if op == '==': return val_left == val_right
            if op == '!=': return val_left != val_right
            if op in ('<', '<=', '>', '>='):
                if op == '<': return val_left < val_right
                if op == '<=': return val_left <= val_right
                if op == '>': return val_left > val_right
                if op == '>=': return val_left >= val_right

        raise LangRuntimeError(f"Unknown operator {op}")
