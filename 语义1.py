class SemanticAnalyzer:
    """语义分析器，检查AST的语义正确性"""

    def __init__(self):
        self.symbol_table = {}  # 符号表，存储变量和函数信息
        self.current_scope = "global"  # 当前作用域
        self.errors = []  # 存储语义错误
        self.function_return_type = None  # 当前函数的返回类型
        self.in_loop = False  # 是否在循环结构中

    def log_error(self, message, line=None):
        """记录语义错误"""
        error_msg = f"语义错误: {message}"
        if line is not None:
            error_msg += f" (第 {line} 行)"
        self.errors.append(error_msg)
        print(error_msg)

    def analyze(self, ast):
        """分析整个AST"""
        self.errors = []  # 重置错误列表
        self.symbol_table = {}  # 重置符号表
        self.current_scope = "global"

        if not ast:
            self.log_error("空的AST")
            return

        # 遍历AST中的每个节点
        for node in ast:
            if node['type'] == 'function_definition':       #函数定义
                self.analyze_function_definition(node)
            elif node['type'] in ('variable_declaration', 'const_declaration'):
                self.analyze_declaration(node)
            else:
                self.log_error(f"全局作用域中不允许的语句类型: {node['type']}")

    def analyze_function_definition(self, node):
        """分析函数定义"""
        # 检查函数名
        if node['name'] != 'main':
            self.log_error("只允许定义main函数", node.get('line'))
            return

        # 设置当前作用域和返回类型
        self.current_scope = "main"
        self.function_return_type = node['return_type']

        # 检查返回类型
        if node['return_type'] != 'void':
            self.log_error(f"main函数应返回void，而不是{node['return_type']}", node.get('line'))

        # 分析函数体
        for stmt in node['body']:
            self.analyze_statement(stmt)

        # 恢复作用域
        self.current_scope = "global"
        self.function_return_type = None

    def analyze_statement(self, node):
        """分析语句"""
        if node is None:
            return

        try:
            if node['type'] == 'assignment':        #赋值
                self.analyze_assignment(node)
            elif node['type'] in ('variable_declaration', 'const_declaration'): #声明
                self.analyze_declaration(node)
            elif node['type'] == 'if_statement':
                self.analyze_if_statement(node)
            elif node['type'] == 'while_statement':
                self.analyze_while_statement(node)
            elif node['type'] == 'do_while_statement':
                self.analyze_do_while_statement(node)
            elif node['type'] == 'for_statement':
                self.analyze_for_statement(node)
            else:
                self.log_error(f"未知的语句类型: {node['type']}", node.get('line'))
        except KeyError as e:
            self.log_error(f"语句节点缺少必要字段: {str(e)}", node.get('line'))

    def analyze_declaration(self, node):
        """分析变量声明"""
        var_name = node['name']
        var_type = node['data_type']

        # 检查变量是否已声明
        if self.is_declared(var_name):
            self.log_error(f"变量 '{var_name}' 已声明", node.get('line'))
            return

        # 检查初始化表达式，检查其类型是否匹配声明类型
        if 'value' in node and node['value'] is not None:
            expr_type = self.analyze_expression(node['value'])
            if expr_type != var_type:
                self.log_error(f"类型不匹配: 不能将 {expr_type} 赋值给 {var_type} 变量 '{var_name}'", node.get('line'))

        # 添加到符号表
        self.symbol_table[(var_name, self.current_scope)] = {
            'type': var_type,
            'is_const': node['type'] == 'const_declaration',
            'line': node.get('line')
        }

    def analyze_assignment(self, node):
        """分析赋值语句"""
        var_name = node['left']

        # 检查变量是否已声明
        if not self.is_declared(var_name):
            self.log_error(f"变量 '{var_name}' 未声明", node.get('line'))
            return

        # 检查是否为常量
        symbol_info = self.get_symbol_info(var_name)
        if symbol_info['is_const']:
            self.log_error(f"不能修改常量 '{var_name}'", node.get('line'))
            return

        # 检查类型匹配
        var_type = symbol_info['type']
        expr_type = self.analyze_expression(node['right'])

        if expr_type != var_type:
            self.log_error(f"类型不匹配: 不能将 {expr_type} 赋值给 {var_type} 变量 '{var_name}'", node.get('line'))

    def analyze_if_statement(self, node):
        """分析if语句"""
        # 检查条件表达式是否为布尔类型
        condition_type = self.analyze_expression(node['condition'])
        if condition_type != 'bool':
            self.log_error(f"if条件应为布尔类型，而不是 {condition_type}", node.get('line'))

        # 分析语句块
        for stmt in node['body']:
            self.analyze_statement(stmt)

    def analyze_while_statement(self, node):
        """分析while语句"""
        # 检查条件表达式是否为布尔类型
        condition_type = self.analyze_expression(node['condition'])
        if condition_type != 'bool':
            self.log_error(f"while条件应为布尔类型，而不是 {condition_type}", node.get('line'))

        # 分析语句块
        prev_in_loop = self.in_loop
        self.in_loop = True
        for stmt in node['body']:
            self.analyze_statement(stmt)
        self.in_loop = prev_in_loop

    def analyze_do_while_statement(self, node):
        """分析do-while语句"""
        # 分析语句块
        prev_in_loop = self.in_loop
        self.in_loop = True
        for stmt in node['body']:
            self.analyze_statement(stmt)
        self.in_loop = prev_in_loop

        # 检查条件表达式是否为布尔类型
        condition_type = self.analyze_expression(node['condition'])
        if condition_type != 'bool':
            self.log_error(f"do-while条件应为布尔类型，而不是 {condition_type}", node.get('line'))

    def analyze_for_statement(self, node):
        """分析for语句"""
        # 分析初始化部分
        if node['init'] is not None:
            self.analyze_statement(node['init'])

        # 检查条件表达式是否为布尔类型
        if node['condition'] is not None:
            condition_type = self.analyze_expression(node['condition'])
            if condition_type != 'bool':
                self.log_error(f"for条件应为布尔类型，而不是 {condition_type}", node.get('line'))

        # 分析更新部分
        if node['update'] is not None:
            self.analyze_statement(node['update'])

        # 分析循环体
        prev_in_loop = self.in_loop
        self.in_loop = True
        for stmt in node['body']:
            self.analyze_statement(stmt)
        self.in_loop = prev_in_loop

    def analyze_expression(self, node):
        """分析表达式并返回其类型"""
        if node is None:
            return 'void'

        try:
            if node['type'] == 'binary_operation':
                return self.analyze_binary_operation(node)
            elif node['type'] == 'integer':
                return 'int'
            elif node['type'] == 'float':
                return 'float'
            elif node['type'] == 'variable':
                return self.analyze_variable(node)
            else:
                self.log_error(f"未知的表达式类型: {node['type']}", node.get('line'))
                return 'error'
        except KeyError as e:
            self.log_error(f"表达式节点缺少必要字段: {str(e)}", node.get('line'))
            return 'error'

    def analyze_binary_operation(self, node):
        """分析二元操作"""
        left_type = self.analyze_expression(node['left'])
        right_type = self.analyze_expression(node['right'])

        # 检查操作符
        op = node['op']

        # 比较操作符返回布尔类型
        if op in ('LT', 'LEQ', 'GT', 'GEQ', 'EQ', 'NEQ'):
            if left_type != right_type:
                self.log_error(f"比较操作类型不匹配: {left_type} 和 {right_type}", node.get('line'))
            return 'bool'
        # 逻辑操作符
        elif op in ('AND', 'OR'):
            if left_type != 'bool' or right_type != 'bool':
                self.log_error(f"逻辑操作要求布尔类型", node.get('line'))
            return 'bool'
        # 算术操作符
        elif op in ('PLUS', 'MINUS', 'MUL', 'DIV'):
            if left_type != right_type:
                self.log_error(f"算术操作类型不匹配: {left_type} 和 {right_type}", node.get('line'))
            return left_type  # 返回操作数的类型
        else:
            self.log_error(f"未知的操作符: {op}", node.get('line'))
            return 'error'

    def analyze_variable(self, node):
        """分析变量引用"""
        var_name = node['name']

        if not self.is_declared(var_name):
            self.log_error(f"变量 '{var_name}' 未声明", node.get('line'))
            return 'error'

        return self.get_symbol_info(var_name)['type']

    def is_declared(self, var_name):
        """检查变量是否已声明"""
        # 先在当前作用域查找
        if (var_name, self.current_scope) in self.symbol_table:
            return True
        # 然后在全局作用域查找
        if (var_name, 'global') in self.symbol_table:
            return True
        return False

    def get_symbol_info(self, var_name):
        """获取变量的符号信息"""
        # 先在当前作用域查找
        if (var_name, self.current_scope) in self.symbol_table:
            return self.symbol_table[(var_name, self.current_scope)]
        # 然后在全局作用域查找
        if (var_name, 'global') in self.symbol_table:
            return self.symbol_table[(var_name, 'global')]
        return None

    def get_formatted_symbol_table(self):
        """格式化符号表以便输出"""
        if not self.symbol_table:
            return "符号表为空"

        # 按作用域分组
        scopes = {}
        for (name, scope), info in self.symbol_table.items():
            if scope not in scopes:
                scopes[scope] = []
            scopes[scope].append((name, info))

        # 格式化输出
        output = []
        for scope, symbols in scopes.items():
            output.append(f"\n作用域: {scope}")
            output.append("-" * 50)
            output.append("{:<15} {:<10} {:<10} {:<10}".format(
                "变量名", "类型", "是否常量", "声明位置"))
            output.append("-" * 50)

            for name, info in sorted(symbols, key=lambda x: x[0]):
                output.append("{:<15} {:<10} {:<10} {:<10}".format(
                    name,
                    info['type'],
                    "是" if info['is_const'] else "否",
                    f"第{info['line']}行" if 'line' in info else "未知"
                ))

        return "\n".join(output)

def perform_semantic_analysis(ast):
    """执行语义分析"""
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    return {
        'success': len(analyzer.errors) == 0,
        'errors': analyzer.errors,
        'symbol_table': analyzer.symbol_table,
        'formatted_symbol_table': analyzer.get_formatted_symbol_table()
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
         'type': 'function_definition'}]

    result = perform_semantic_analysis(test_ast)

    print("\n符号表信息:")
    print(result['formatted_symbol_table'])

    if not result['success']:
        print("\n语义分析发现错误:")
        for error in result['errors']:
            print(error)
    else:
        print("\n语义分析成功完成！")