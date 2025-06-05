class IntermediateCodeGenerator:
    """中间代码生成器，将AST转换为四元式"""

    def __init__(self):
        self.quads = []  # 存储生成的四元式
        self.temp_var_count = 0  # 临时变量计数器
        self.label_count = 0  # 标签计数器

    def generate(self, ast):
        """生成中间代码"""
        self.quads = []

        # 遍历AST中的每个节点
        for node in ast:
            if node['type'] == 'function_definition':
                self.generate_function(node)

        return self.quads

    def generate_function(self, node):
        """生成函数定义的中间代码"""
        # 函数开始标签
        func_label = f"FUNC_{node['name']}"
        self.emit('LABEL', '_', '_', func_label)

        # 生成函数体代码
        for stmt in node['body']:
            self.generate_statement(stmt)

        # 函数结束
        if node['return_type'] == 'void':
            self.emit('RET', '_', '_', '_')

    def generate_statement(self, node):
        """生成语句的中间代码"""
        if node is None:
            return

        if node['type'] == 'assignment':
            self.generate_assignment(node)
        elif node['type'] in ('variable_declaration', 'const_declaration'):
            self.generate_declaration(node)
        elif node['type'] == 'if_statement':
            self.generate_if_statement(node)
        elif node['type'] == 'while_statement':
            self.generate_while_statement(node)
        elif node['type'] == 'do_while_statement':
            self.generate_do_while_statement(node)
        elif node['type'] == 'for_statement':
            self.generate_for_statement(node)

    def generate_declaration(self, node):
        """生成变量声明的中间代码"""
        if 'value' in node and node['value'] is not None:
            # 带初始化的声明，转换为赋值语句
            result = node['name']
            value = self.generate_expression(node['value'])
            self.emit('=', value, '_', result)

    def generate_assignment(self, node):
        """生成赋值语句的中间代码"""
        result = node['left']
        value = self.generate_expression(node['right'])
        self.emit('=', value, '_', result)

    def generate_if_statement(self, node):
        """生成if语句的中间代码"""
        # 生成条件表达式
        condition = self.generate_expression(node['condition'])
        # 创建标签
        false_label = f"L{self.new_label()}"
        end_label = f"L{self.new_label()}"
        # 条件跳转
        self.emit('IF_NOT', condition, '_', false_label)
        # 生成then部分
        for stmt in node['body']:
            self.generate_statement(stmt)
        # 跳转到结束
        self.emit('GOTO', '_', '_', end_label)
        # else部分标签
        self.emit('LABEL', '_', '_', false_label)
        # 结束标签
        self.emit('LABEL', '_', '_', end_label)

    def generate_while_statement(self, node):
        """生成while语句的中间代码"""
        start_label = f"L{self.new_label()}"
        condition_label = f"L{self.new_label()}"
        end_label = f"L{self.new_label()}"

        # 跳转到条件判断
        self.emit('GOTO', '_', '_', condition_label)

        # 循环体开始
        self.emit('LABEL', '_', '_', start_label)

        # 生成循环体
        for stmt in node['body']:
            self.generate_statement(stmt)

        # 条件判断标签
        self.emit('LABEL', '_', '_', condition_label)

        # 生成条件表达式
        condition = self.generate_expression(node['condition'])

        # 条件为真则跳回循环体
        self.emit('IF', condition, '_', start_label)

        # 结束标签
        self.emit('LABEL', '_', '_', end_label)

    def generate_do_while_statement(self, node):
        """生成do-while语句的中间代码"""
        start_label = f"L{self.new_label()}"
        end_label = f"L{self.new_label()}"

        # 循环体开始
        self.emit('LABEL', '_', '_', start_label)

        # 生成循环体
        for stmt in node['body']:
            self.generate_statement(stmt)

        # 生成条件表达式
        condition = self.generate_expression(node['condition'])

        # 条件为真则跳回循环体
        self.emit('IF', condition, '_', start_label)

        # 结束标签
        self.emit('LABEL', '_', '_', end_label)

    def generate_for_statement(self, node):
        """生成for语句的中间代码"""
        # 生成初始化部分
        if node['init'] is not None:
            self.generate_statement(node['init'])

        start_label = f"L{self.new_label()}"
        condition_label = f"L{self.new_label()}"
        end_label = f"L{self.new_label()}"

        # 跳转到条件判断
        self.emit('GOTO', '_', '_', condition_label)

        # 循环体开始
        self.emit('LABEL', '_', '_', start_label)

        # 生成循环体
        for stmt in node['body']:
            self.generate_statement(stmt)

        # 生成更新部分
        if node['update'] is not None:
            self.generate_statement(node['update'])

        # 条件判断标签
        self.emit('LABEL', '_', '_', condition_label)

        # 生成条件表达式
        if node['condition'] is not None:
            condition = self.generate_expression(node['condition'])
            # 条件为真则跳回循环体
            self.emit('IF', condition, '_', start_label)
        else:
            # 无条件跳转
            self.emit('GOTO', '_', '_', start_label)

        # 结束标签
        self.emit('LABEL', '_', '_', end_label)

    def generate_expression(self, node):
        """生成表达式的中间代码，返回结果变量名"""
        if node['type'] == 'binary_operation':
            return self.generate_binary_operation(node)
        elif node['type'] in ('integer', 'float'):
            return str(node['value'])
        elif node['type'] == 'variable':
            return node['name']

    def generate_binary_operation(self, node):
        """生成二元运算的中间代码"""
        left = self.generate_expression(node['left'])
        right = self.generate_expression(node['right'])
        # 生成临时变量存储结果
        temp_var = self.new_temp()
        # 根据操作符生成四元式
        op = self.get_quad_operator(node['op'])
        self.emit(op, left, right, temp_var)
        return temp_var

    def get_quad_operator(self, token_op):
        """将词法分析器的操作符转换为四元式操作符"""
        op_map = {
            'PLUS': '+',
            'MINUS': '-',
            'MUL': '*',
            'DIV': '/',
            'LT': '<',
            'LEQ': '<=',
            'GT': '>',
            'GEQ': '>=',
            'EQ': '==',
            'NEQ': '!=',
            'AND': '&&',
            'OR': '||'
        }
        return op_map.get(token_op, token_op)

    def new_temp(self):
        """生成新的临时变量"""
        self.temp_var_count += 1
        return f"t{self.temp_var_count}"

    def new_label(self):
        """生成新的标签"""
        self.label_count += 1
        return self.label_count

    def emit(self, op, arg1, arg2, result):
        """生成一个四元式"""
        self.quads.append((op, arg1, arg2, result))


def generate_intermediate_code(ast):
    """生成中间代码"""
    generator = IntermediateCodeGenerator()
    quads = generator.generate(ast)

    return {
        'success': True,
        'quads': quads
    }


if __name__ == "__main__":
    # 测试代码
    test_ast = [
        {'data_type': 'int',
         'name': 'a',
         'type': 'variable_declaration',
         'value': {'type': 'integer', 'value': 1}},
        {'body': [{'data_type': 'int',
                   'name': 'N',
                   'type': 'variable_declaration',
                   'value': {'type': 'integer', 'value': 1}},
                  {'data_type': 'int',
                   'name': 'M',
                   'type': 'variable_declaration',
                   'value': {'type': 'integer', 'value': 2}},
                  {'left': 'a',
                   'right': {'left': {'name': 'M', 'type': 'variable'},
                             'op': 'PLUS',
                             'right': {'name': 'N', 'type': 'variable'},
                             'type': 'binary_operation'},
                   'type': 'assignment'}],
         'name': 'main',
         'return_type': 'void',
         'type': 'function_definition'}
    ]

    result = generate_intermediate_code(test_ast)

    print("\n生成的中间代码（四元式）:")
    for i, quad in enumerate(result['quads']):
        print(f"{i:3d}: {quad}")