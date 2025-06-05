import json
import os
import pprint
from 词法分析器 import WordAnalysis


class Token:
    """Token类表示词法单元，包含类型和可选的值"""

    def __init__(self, type, value=None, line=None, column=None):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        pos_info = f" at line {self.line}, column {self.column}" if self.line is not None else ""
        value_info = f", {self.value}" if self.value is not None else ""
        return f"Token({self.type}{value_info}{pos_info})"


class Lexer:
    """词法分析器，使用外部词法分析器生成Token序列"""

    def __init__(self, text):
        self.code_filepath = "temp_code.txt"
        self.token_filepath = self.create_token_file()
        self.output_filepath = "output_tokens.txt"

        with open(self.code_filepath, "w", encoding="utf-8") as f:
            f.write(text)

        self.analyzer = WordAnalysis(self.code_filepath, self.token_filepath, self.output_filepath)
        self.analyzer.analyze()
        self.tokens = self.convert_word_analysis_output_to_tokens(self.output_filepath)
        self.pos = 0
        self.current_token = self.tokens[self.pos] if self.tokens else None

    def create_token_file(self):
        """创建Tokens.json文件"""
        token_data = [
            {"type": "int", "value": "101"},
            {"type": "float", "value": "102"},
            {"type": "char", "value": "103"},
            {"type": "const", "value": "105"},
            {"type": "void", "value": "107"},
            {"type": "do", "value": "109"},
            {"type": "while", "value": "110"},
            {"type": "if", "value": "111"},
            {"type": "else", "value": "112"},
            {"type": "for", "value": "113"},
            {"type": "*", "value": "202"},
            {"type": "/", "value": "203"},
            {"type": "+", "value": "205"},
            {"type": "-", "value": "206"},
            {"type": "<", "value": "207"},
            {"type": "<=", "value": "208"},
            {"type": ">", "value": "209"},
            {"type": ">=", "value": "210"},
            {"type": "==", "value": "211"},
            {"type": "!=", "value": "212"},
            {"type": "&&", "value": "213"},
            {"type": "||", "value": "214"},
            {"type": "=", "value": "215"},
            {"type": "{", "value": "301"},
            {"type": "}", "value": "302"},
            {"type": ";", "value": "303"},
            {"type": ",", "value": "304"},
            {"type": "(", "value": "305"},
            {"type": ")", "value": "306"},
            {"type": "整数", "value": "400"},
            {"type": "实数", "value": "800"},
            {"type": "标识符", "value": "700"}
        ]

        token_filepath = "Tokens.json"
        with open(token_filepath, "w", encoding="utf-8") as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)
        return token_filepath

    def convert_word_analysis_output_to_tokens(self, output_filepath):
        """将词法分析器的输出转换为Token对象列表"""
        tokens = []
        token_mapping = {
            '101': 'INT_TYPE', '102': 'FLOAT_TYPE', '103': 'CHAR_TYPE',
            '105': 'CONST', '107': 'VOID', '109': 'DO', '110': 'WHILE',
            '111': 'IF', '112': 'ELSE', '113': 'FOR', '202': 'MUL',
            '203': 'DIV', '205': 'PLUS', '206': 'MINUS', '207': 'LT',
            '208': 'LEQ', '209': 'GT', '210': 'GEQ', '211': 'EQ',
            '212': 'NEQ', '213': 'AND', '214': 'OR', '215': 'ASSIGN',
            '301': 'LBRACE', '302': 'RBRACE', '303': 'SEMI',
            '304': 'COMMA', '305': 'LPAREN', '306': 'RPAREN',
            '400': 'INTEGER', '800': 'FLOAT', '700': 'ID'
        }

        with open(output_filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split("\t\t")
                if len(parts) != 2:
                    continue

                value = parts[0].strip()
                token_type_code = parts[1].strip()

                if token_type_code == '400':  # 整数
                    tokens.append(Token('INTEGER', int(value), line_num, 0))
                elif token_type_code == '800':  # 实数
                    tokens.append(Token('FLOAT', float(value), line_num, 0))
                elif token_type_code in token_mapping:
                    token_type = token_mapping[token_type_code]
                    if token_type in ('INT_TYPE', 'FLOAT_TYPE', 'CHAR_TYPE', 'VOID', 'CONST',
                                      'DO', 'WHILE', 'IF', 'ELSE', 'FOR', 'MUL', 'DIV',
                                      'PLUS', 'MINUS', 'LT', 'LEQ', 'GT', 'GEQ', 'EQ',
                                      'NEQ', 'AND', 'OR', 'ASSIGN', 'LBRACE', 'RBRACE',
                                      'SEMI', 'COMMA', 'LPAREN', 'RPAREN'):
                        tokens.append(Token(token_type, None, line_num, 0))
                    else:
                        tokens.append(Token(token_type, value, line_num, 0))

        tokens.append(Token('EOF', None, line_num + 1 if 'line_num' in locals() else 1, 0))
        return tokens

    def get_next_token(self):
        """获取下一个Token"""
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            self.pos += 1
            return token
        return Token('EOF')


class Parser:
    """语法分析器，将Token序列转换为抽象语法树(AST)"""

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
        self.prev_token = None
        self.errors = []

    def log_error(self, message="语法错误"):
        """记录语法错误并输出清晰的位置信息"""
        line = self.current_token.line
        column = self.current_token.column

        if line is not None and column is not None:
            pos_info = f"第 {line} 行, 第 {column} 列"
        elif line is not None:
            pos_info = f"第 {line} 行, 列号未知"
        else:
            pos_info = "未知位置"

        token_val = self.current_token.value if self.current_token.value is not None else self.current_token.type
        token_type = self.current_token.type

        error_msg = f"{message}（{pos_info}：发现 '{token_val}'）"
        self.errors.append(error_msg)
        print(f"Error: {error_msg}")

    def eat(self, token_type):
        """消费当前Token，并获取下一个Token"""
        self.prev_token = self.current_token
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            expected = {
                'SEMI': "缺少分号';'",
                'LPAREN': "缺少左括号'('",
                'RPAREN': "缺少右括号')'",
                'LBRACE': "缺少左大括号'{'",
                'RBRACE': "缺少右大括号'}'",
                'INT_TYPE': "缺少类型声明",
                'ID': "缺少标识符",
            }.get(token_type, f"期望 {token_type}")

            self.log_error(expected)
            # 不自动跳过token，让调用者决定如何处理

    def program(self):
        """程序 → { 声明 } { 函数定义 } { 语句 } EOF"""
        nodes = []

        while self.current_token.type in ('INT_TYPE', 'FLOAT_TYPE', 'CHAR_TYPE', 'CONST'):
            nodes.append(self.declaration())

        while self.current_token.type in ('INT_TYPE', 'FLOAT_TYPE', 'CHAR_TYPE', 'VOID'):
            func_def = self.function_definition()
            if func_def:
                nodes.append(func_def)

        while self.current_token.type != 'EOF':
            stmt = self.statement()
            if stmt:
                nodes.append(stmt)

        return nodes

    def declaration(self):
        """声明 → 类型 标识符 ['=' 表达式] ';' | 'const' 类型 标识符 '=' 表达式 ';'"""
        is_const = self.current_token.type == 'CONST'
        if is_const:
            self.eat('CONST')

        var_type = self.type_spec()
        var_name = self.current_token.value
        self.eat('ID')

        expr = None
        if is_const or self.current_token.type == 'ASSIGN':
            self.eat('ASSIGN')
            expr = self.expression()

        try:
            self.eat('SEMI')
        except:
            # 如果缺少分号，尝试恢复
            while self.current_token.type not in ('SEMI', 'EOF'):
                self.current_token = self.lexer.get_next_token()
            if self.current_token.type == 'SEMI':
                self.eat('SEMI')

        return {
            'type': 'const_declaration' if is_const else 'variable_declaration',
            'data_type': var_type,
            'name': var_name,
            'value': expr
        }

    def function_definition(self):
        """函数定义 → 类型 'main' '(' ')' '{' {语句} '}'"""
        return_type = self.type_spec()

        # 检查是否是main函数
        if self.current_token.type != 'ID' or self.current_token.value != 'main':
            self.log_error("只允许定义main函数")
            # 跳过非main函数定义
            while self.current_token.type not in ('LBRACE', 'EOF'):
                self.current_token = self.lexer.get_next_token()
            if self.current_token.type == 'LBRACE':
                self.eat('LBRACE')
                while self.current_token.type != 'RBRACE' and self.current_token.type != 'EOF':
                    self.current_token = self.lexer.get_next_token()
                if self.current_token.type == 'RBRACE':
                    self.eat('RBRACE')
            return None

        self.eat('ID')
        self.eat('LPAREN')
        self.eat('RPAREN')
        self.eat('LBRACE')

        body = []
        while self.current_token.type not in ('RBRACE', 'EOF'):
            stmt = self.statement()
            if stmt:
                body.append(stmt)

        if self.current_token.type == 'EOF':
            self.log_error("main函数体未闭合，缺少'}'")
            return None
            # return {
            #     'type': 'function_definition',
            #     'name': 'main',
            #     'return_type': return_type,
            #     'body': body,
            #     'error': 'unclosed_function_body'
            # }

        self.eat('RBRACE')
        return {
            'type': 'function_definition',
            'name': 'main',
            'return_type': return_type,
            'body': body
        }

    def statement(self):
        """语句 → 赋值语句 | 分支语句 | 循环语句 | 声明"""
        if self.current_token.type == 'EOF':
            return None

        try:
            if self.current_token.type == 'IF':
                return self.if_statement()
            elif self.current_token.type == 'DO':
                return self.do_while_statement()
            elif self.current_token.type == 'WHILE':
                return self.while_statement()
            elif self.current_token.type == 'FOR':
                return self.for_statement()
            elif self.current_token.type in ('INT_TYPE', 'FLOAT_TYPE', 'CHAR_TYPE', 'CONST'):
                return self.declaration()
            elif self.current_token.type == 'ID':
                next_token = self.lexer.tokens[self.lexer.pos] if self.lexer.pos < len(self.lexer.tokens) else None
                if next_token and next_token.type == 'LPAREN':
                    return self.function_call()
                return self.assignment_statement()
            elif self.current_token.type in ('LBRACE', 'RBRACE', 'LPAREN', 'RPAREN'):
                # 跳过这些token，不报告为错误
                self.current_token = self.lexer.get_next_token()
                return None
            else:
                self.log_error("无效语句")
                self.current_token = self.lexer.get_next_token()
                return None
        except Exception as e:
            self.log_error(f"解析语句时出错: {str(e)}")
            self.synchronize()
            return None

    def assignment_statement(self):
        """赋值语句 → 标识符 '=' 表达式 ';'"""
        var_name = self.current_token.value
        self.eat('ID')
        self.eat('ASSIGN')
        expr = self.expression()
        self.eat('SEMI')
        return {
            'type': 'assignment',
            'left': var_name,
            'right': expr
        }

    def if_statement(self):
        """分支语句 → 'if' '(' 布尔表达式 ')' '{' {语句} '}'"""
        self.eat('IF')
        self.eat('LPAREN')
        condition = self.boolean_expression()
        self.eat('RPAREN')
        self.eat('LBRACE')

        statements = []
        while self.current_token.type not in ('RBRACE', 'EOF'):
            stmt = self.statement()
            if stmt:
                statements.append(stmt)

        if self.current_token.type == 'EOF':
            self.log_error("if语句块未闭合，缺少'}'")
        else:
            self.eat('RBRACE')

        return {
            'type': 'if_statement',
            'condition': condition,
            'body': statements
        }

    def while_statement(self):
        """while语句 → 'while' '(' 布尔表达式 ')' '{' {语句} '}'"""
        self.eat('WHILE')
        self.eat('LPAREN')
        condition = self.boolean_expression()
        self.eat('RPAREN')
        self.eat('LBRACE')

        statements = []
        while self.current_token.type != 'RBRACE':
            if self.current_token.type == 'EOF':
                self.log_error("while块未闭合，缺少'}'")
                break
            statements.append(self.statement())

        self.eat('RBRACE')
        return {
            'type': 'while_statement',
            'condition': condition,
            'body': statements
        }

    def do_while_statement(self):
        """doWhile语句 → 'do' '{' {语句} '}' 'while' '(' 布尔表达式 ')' ';'"""
        self.eat('DO')
        self.eat('LBRACE')

        statements = []
        while self.current_token.type != 'RBRACE':
            if self.current_token.type == 'EOF':
                self.log_error("do-while块未闭合，缺少'}'")
                break
            statements.append(self.statement())

        self.eat('RBRACE')
        self.eat('WHILE')
        self.eat('LPAREN')
        condition = self.boolean_expression()
        self.eat('RPAREN')
        self.eat('SEMI')
        return {
            'type': 'do_while_statement',
            'condition': condition,
            'body': statements
        }

    def for_statement(self):
        """for语句 → 'for' '(' 赋值语句|声明 布尔表达式 ';' 赋值表达式 ')' '{' {语句} '}'"""
        start_line = self.current_token.line  # 记录for语句开始行号
        self.eat('FOR')
        self.eat('LPAREN')

        # 1. 解析初始化部分（赋值语句或声明）
        init = None
        try:
            if self.current_token.type in ('INT_TYPE', 'FLOAT_TYPE', 'CHAR_TYPE'):
                init = self.declaration()  # 变量声明（如 int i = 0;）
            elif self.current_token.type == 'ID':
                # 检查是否是赋值语句（如 i = 0;）
                next_token = self.lexer.tokens[self.lexer.pos] if self.lexer.pos < len(self.lexer.tokens) else None
                if next_token and next_token.type == 'ASSIGN':
                    init = self.assignment_statement()
                else:
                    self.log_error("for循环初始化部分必须是声明或赋值语句")
                    # 尝试跳过直到分号
                    while self.current_token.type not in ('SEMI', 'RPAREN', 'EOF'):
                        self.current_token = self.lexer.get_next_token()
            else:
                self.log_error("for循环初始化部分不能为空")
                # 尝试跳过直到分号
                while self.current_token.type not in ('SEMI', 'RPAREN', 'EOF'):
                    self.current_token = self.lexer.get_next_token()
        except Exception as e:
            self.log_error(f"解析初始化部分出错: {str(e)}")
            # 尝试恢复
            while self.current_token.type not in ('SEMI', 'RPAREN', 'EOF'):
                self.current_token = self.lexer.get_next_token()

        # 2. 解析条件部分（布尔表达式）
        condition = None
        try:
            if self.current_token.type == 'SEMI':
                self.log_error("for循环条件部分不能为空")
            else:
                condition = self.boolean_expression()
        except Exception as e:
            self.log_error(f"解析条件部分出错: {str(e)}")

        # 吃掉分号（条件部分结束）
        if self.current_token.type == 'SEMI':
            self.eat('SEMI')
        else:
            self.log_error("缺少分号';'")
            # 尝试跳过直到找到分号或右括号
            while self.current_token.type not in ('SEMI', 'RPAREN', 'EOF'):
                self.current_token = self.lexer.get_next_token()
            if self.current_token.type == 'SEMI':
                self.eat('SEMI')

        # 3. 解析更新部分（必须是赋值表达式，不能有分号）
        update = None
        try:
            if self.current_token.type == 'RPAREN':
                self.log_error("for循环更新部分不能为空")
            else:
                # 检查是否是赋值表达式（如 x = x + 1）
                if self.current_token.type == 'ID':
                    next_token = self.lexer.tokens[self.lexer.pos] if self.lexer.pos < len(self.lexer.tokens) else None
                    if next_token and next_token.type == 'ASSIGN':
                        var_name = self.current_token.value
                        self.eat('ID')
                        self.eat('ASSIGN')
                        expr = self.expression()
                        update = {
                            'type': 'assignment',
                            'left': var_name,
                            'right': expr
                        }
                    else:
                        self.log_error("更新部分必须是赋值表达式")
                else:
                    self.log_error("更新部分必须是赋值表达式")
        except Exception as e:
            self.log_error(f"解析更新部分出错: {str(e)}")
            # 尝试跳过直到右括号
            while self.current_token.type not in ('RPAREN', 'EOF'):
                self.current_token = self.lexer.get_next_token()

        # 检查右括号
        if self.current_token.type == 'RPAREN':
            self.eat('RPAREN')
        else:
            self.log_error(f"缺少右括号')' (for语句开始于第{start_line}行)")
            # 尝试跳过直到左大括号
            while self.current_token.type not in ('LBRACE', 'EOF'):
                self.current_token = self.lexer.get_next_token()

        # 检查左大括号
        if self.current_token.type == 'LBRACE':
            self.eat('LBRACE')
        else:
            self.log_error(f"缺少左大括号'{{' (for语句开始于第{start_line}行)")
            # 尝试继续解析语句
            pass

        # 解析循环体
        body = []
        while self.current_token.type != 'RBRACE' and self.current_token.type != 'EOF':
            try:
                stmt = self.statement()
                if stmt:
                    body.append(stmt)
            except Exception as e:
                self.log_error(f"解析循环体语句出错: {str(e)}")
                self.synchronize()

        # 检查右大括号
        if self.current_token.type == 'RBRACE':
            self.eat('RBRACE')
        else:
            self.log_error(f"缺少右大括号'}}' (for语句开始于第{start_line}行)")

        return {
            'type': 'for_statement',
            'init': init,
            'condition': condition,
            'update': update,
            'body': body
        }

    def type_spec(self):
        """类型 → 'int' | 'float' | 'char' | 'void'"""
        token = self.current_token
        if token.type == 'INT_TYPE':
            self.eat('INT_TYPE')
            return 'int'
        elif token.type == 'FLOAT_TYPE':
            self.eat('FLOAT_TYPE')
            return 'float'
        elif token.type == 'CHAR_TYPE':
            self.eat('CHAR_TYPE')
            return 'char'
        elif token.type == 'VOID':
            self.eat('VOID')
            return 'void'
        else:
            self.log_error("缺少类型声明")
            return 'int'

    def boolean_expression(self):
        """布尔表达式 → 逻辑或表达式"""
        return self.logical_or_expression()

    def logical_or_expression(self):
        """逻辑或表达式 → 逻辑与表达式 { '||' 逻辑与表达式 }"""
        node = self.logical_and_expression()

        while self.current_token.type == 'OR':
            token = self.current_token
            self.eat('OR')
            node = {
                'type': 'binary_operation',
                'left': node,
                'op': token.type,
                'right': self.logical_and_expression()
            }

        return node

    def logical_and_expression(self):
        """逻辑与表达式 → 相等表达式 { '&&' 相等表达式 }"""
        node = self.equality_expression()

        while self.current_token.type == 'AND':
            token = self.current_token
            self.eat('AND')
            node = {
                'type': 'binary_operation',
                'left': node,
                'op': token.type,
                'right': self.equality_expression()
            }

        return node

    def equality_expression(self):
        """相等表达式 → 关系表达式 [ ('==' | '!=') 关系表达式 ]"""
        node = self.relational_expression()

        if self.current_token.type in ('EQ', 'NEQ'):
            token = self.current_token
            self.eat(token.type)
            node = {
                'type': 'binary_operation',
                'left': node,
                'op': token.type,
                'right': self.relational_expression()
            }

        return node

    def relational_expression(self):
        """关系表达式 → 表达式 [ ('<' | '<=' | '>' | '>=') 表达式 ]"""
        node = self.expression()

        if self.current_token.type in ('LT', 'LEQ', 'GT', 'GEQ'):
            token = self.current_token
            self.eat(token.type)
            node = {
                'type': 'binary_operation',
                'left': node,
                'op': token.type,
                'right': self.expression()
            }

        return node

    def expression(self):
        """表达式 → 项 { ('+' | '-') 项 }"""
        node = self.term()

        while self.current_token.type in ('PLUS', 'MINUS'):
            token = self.current_token
            self.eat(token.type)
            node = {
                'type': 'binary_operation',
                'left': node,
                'op': token.type,
                'right': self.term()
            }

        return node

    def term(self):
        """项 → 因子 { ('*' | '/') 因子 }"""
        node = self.factor()

        while self.current_token.type in ('MUL', 'DIV'):
            token = self.current_token
            self.eat(token.type)
            node = {
                'type': 'binary_operation',
                'left': node,
                'op': token.type,
                'right': self.factor()
            }

        return node

    def factor(self):
        """因子 → '(' 表达式 ')' | 数字 | 标识符"""
        token = self.current_token

        if token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.expression()
            self.eat('RPAREN')
            return node
        elif token.type == 'INTEGER':
            self.eat('INTEGER')
            return {'type': 'integer', 'value': token.value}
        elif token.type == 'FLOAT':
            self.eat('FLOAT')
            return {'type': 'float', 'value': token.value}
        elif token.type == 'ID':
            self.eat('ID')
            return {'type': 'variable', 'name': token.value}
        else:
            self.log_error("缺少表达式")
            return {'type': 'error'}

    def synchronize(self):
        """错误恢复：跳过token直到找到语句开始"""
        while self.current_token.type != 'EOF':
            if self.current_token.type in ('IF', 'INT_TYPE', 'FLOAT_TYPE', 'CHAR_TYPE', 'ID', 'DO', 'WHILE', 'FOR'):
                return
            self.current_token = self.lexer.get_next_token()


def analyze_code(code_str):
    """分析用户输入的代码"""
    try:
        lexer = Lexer(code_str)
        parser = Parser(lexer)
        ast = parser.program()

        return {
            'success': True,
            'ast': ast,
            'errors': parser.errors,
            'tokens': lexer.tokens
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'tokens': lexer.tokens if 'lexer' in locals() else []
        }


if __name__ == "__main__":
    test_code = """
    void main(){
        int x = 3+1;
        int y = x+2;
    }

    """

    result = analyze_code(test_code)

    if result['success']:
        print("\n语法分析成功！生成的AST:")
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(result['ast'])

        if result['errors']:
            print("\n警告信息:")
            for error in result['errors']:
                print(error)
    else:
        print(f"\n分析失败: {result['error']}")