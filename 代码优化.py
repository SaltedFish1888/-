from 中间代码 import IntermediateCodeGenerator


class CodeOptimizer:
    """代码优化器，对四元式进行优化"""

    def __init__(self):
        self.optimized_quads = []

    def optimize(self, quads):
        """执行所有优化步骤"""
        self.optimized_quads = quads.copy()

        # 执行各种优化
        self.remove_redundant_code()
        self.constant_folding()
        self.constant_propagation()
        self.algebraic_simplification()
        self.remove_unused_temp_vars()

        return self.optimized_quads

    def remove_redundant_code(self):
        """删除冗余代码"""
        new_quads = []
        i = 0
        n = len(self.optimized_quads)

        while i < n:
            quad = self.optimized_quads[i]
            op, arg1, arg2, result = quad

            # 删除连续的相同标签
            if op == 'LABEL' and i > 0 and self.optimized_quads[i - 1][0] == 'LABEL':
                i += 1
                continue

            # 删除无条件跳转到下一行的指令
            if op == 'GOTO' and i < n - 1 and self.optimized_quads[i + 1][0] == 'LABEL' and result == \
                    self.optimized_quads[i + 1][3]:
                i += 1
                continue

            new_quads.append(quad)
            i += 1

        self.optimized_quads = new_quads

    def constant_folding(self):
        """常量折叠"""
        new_quads = []
        const_values = {}

        for quad in self.optimized_quads:
            op, arg1, arg2, result = quad

            # 检查是否可以执行常量折叠
            if op in ('+', '-', '*', '/', '<', '<=', '>', '>=', '==', '!=', '&&', '||'):
                # 检查两个操作数是否都是常量
                if arg1.isdigit() and arg2.isdigit():
                    val1 = int(arg1)
                    val2 = int(arg2)
                    folded_value = self.evaluate_constant_expression(op, val1, val2)
                    const_values[result] = str(folded_value)
                    continue
                # 检查一个操作数是否是常量
                elif arg1.isdigit() or arg2.isdigit():
                    # 可以进行一些特殊情况的优化，如 x+0, x*1 等
                    if op == '+' and arg1 == '0':
                        const_values[result] = arg2
                        continue
                    elif op == '+' and arg2 == '0':
                        const_values[result] = arg1
                        continue
                    elif op == '*' and arg1 == '1':
                        const_values[result] = arg2
                        continue
                    elif op == '*' and arg2 == '1':
                        const_values[result] = arg1
                        continue
                    elif op == '*' and (arg1 == '0' or arg2 == '0'):
                        const_values[result] = '0'
                        continue

            # 如果结果已经被常量替换，则替换为赋值语句
            if result in const_values:
                new_quads.append(('=', const_values[result], '_', result))
            else:
                new_quads.append(quad)

        self.optimized_quads = new_quads

    def evaluate_constant_expression(self, op, val1, val2):
        """计算常量表达式的值"""
        if op == '+':
            return val1 + val2
        elif op == '-':
            return val1 - val2
        elif op == '*':
            return val1 * val2
        elif op == '/':
            return val1 // val2
        elif op == '<':
            return int(val1 < val2)
        elif op == '<=':
            return int(val1 <= val2)
        elif op == '>':
            return int(val1 > val2)
        elif op == '>=':
            return int(val1 >= val2)
        elif op == '==':
            return int(val1 == val2)
        elif op == '!=':
            return int(val1 != val2)
        elif op == '&&':
            return int(val1 and val2)
        elif op == '||':
            return int(val1 or val2)
        return 0

    def constant_propagation(self):
        """常量传播"""
        const_values = {}
        new_quads = []

        for quad in self.optimized_quads:
            op, arg1, arg2, result = quad

            # 替换已知常量
            new_arg1 = const_values.get(arg1, arg1)
            new_arg2 = const_values.get(arg2, arg2)

            # 如果是赋值语句且右边是常量，记录常量值
            if op == '=' and new_arg1.isdigit():
                const_values[result] = new_arg1
            else:
                # 如果变量被重新赋值，从常量表中删除
                if result in const_values:
                    del const_values[result]

            # 创建新的四元式
            new_quad = (op, new_arg1, new_arg2, result)
            new_quads.append(new_quad)

        self.optimized_quads = new_quads

    def algebraic_simplification(self):
        """代数化简"""
        new_quads = []

        for quad in self.optimized_quads:
            op, arg1, arg2, result = quad

            # 检查可以简化的代数表达式
            if op == '+' and arg1 == '0':
                new_quads.append(('=', arg2, '_', result))
            elif op == '+' and arg2 == '0':
                new_quads.append(('=', arg1, '_', result))
            elif op == '*' and arg1 == '1':
                new_quads.append(('=', arg2, '_', result))
            elif op == '*' and arg2 == '1':
                new_quads.append(('=', arg1, '_', result))
            elif op == '*' and (arg1 == '0' or arg2 == '0'):
                new_quads.append(('=', '0', '_', result))
            elif op == '-' and arg2 == '0':
                new_quads.append(('=', arg1, '_', result))
            elif op == '/' and arg2 == '1':
                new_quads.append(('=', arg1, '_', result))
            else:
                new_quads.append(quad)

        self.optimized_quads = new_quads

    def remove_unused_temp_vars(self):
        """删除未使用的临时变量"""
        used_vars = set()
        # 第一次遍历：收集所有被使用的变量
        for quad in self.optimized_quads:
            _, arg1, arg2, result = quad
            if arg1 and (arg1.startswith('t') and arg1[1:].isdigit()):
                used_vars.add(arg1)
            if arg2 and (arg2.startswith('t') and arg2[1:].isdigit()):
                used_vars.add(arg2)

        # 第二次遍历：删除定义但未使用的临时变量
        new_quads = []
        temp_defs = {}

        for i, quad in enumerate(self.optimized_quads):
            op, arg1, arg2, result = quad

            # 如果是临时变量的定义
            if result and result.startswith('t') and result[1:].isdigit():
                if result in used_vars:
                    new_quads.append(quad)
                # 否则跳过这个定义
            else:
                new_quads.append(quad)

        self.optimized_quads = new_quads


def optimize_code(quads):
    """优化中间代码"""
    optimizer = CodeOptimizer()
    optimized_quads = optimizer.optimize(quads)

    return {
        'success': True,
        'optimized_quads': optimized_quads
    }


if __name__ == "__main__":
    # 测试代码
    test_ast = [
        {'body': [{'data_type': 'int',
                   'name': 'x',
                   'type': 'variable_declaration',
                   'value': {'left': {'type': 'integer', 'value': 3},
                             'op': 'PLUS',
                             'right': {'type': 'integer', 'value': 1},
                             'type': 'binary_operation'}},
                  {'data_type': 'int',
                   'name': 'y',
                   'type': 'variable_declaration',
                   'value': {'left': {'name': 'x', 'type': 'variable'},
                             'op': 'PLUS',
                             'right': {'type': 'integer', 'value': 2},
                             'type': 'binary_operation'}}],
         'name': 'main',
         'return_type': 'void',
         'type': 'function_definition'}
    ]

    # 生成中间代码
    generator = IntermediateCodeGenerator()
    quads = generator.generate(test_ast)

    print("优化前的中间代码:")
    for i, quad in enumerate(quads):
        print(f"{i:3d}: {quad}")

    # 优化代码
    optimized_result = optimize_code(quads)

    print("\n优化后的中间代码:")
    for i, quad in enumerate(optimized_result['optimized_quads']):
        print(f"{i:3d}: {quad}")