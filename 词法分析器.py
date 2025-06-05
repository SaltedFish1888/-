import json
import os


class WordAnalysis:
    # 初始化实例
    def __init__(self, c_filepath, t_filepath, output_filepath):
        self.c_filepath = c_filepath  # 测试用例文件路径
        self.t_filepath = t_filepath  # json文件路径
        self.tokens = self.read_tokens()  # 读取json文件内容
        self.code_str = self.read_code()  # 读取测试用例代码
        self.errors = []  # 错误列表，用于存储分析过程中发现的错误
        self.token_list = []  # 存储 token 的列表，作为文法分析的输入
        self.index = 0  # 指针，指向字符列表中当前位置的字符
        self.line_num = 1  # 当前行号
        self.column = 0  # 当前列号
        self.output_filepath = output_filepath  # 输出文件路径


    # 读取示例文件中的测试代码
    def read_code(self):
        file = open(self.c_filepath, "r", encoding='utf-8-sig')
        return file.read()

    # 读取Tokens.json 文件中的词法规则
    def read_tokens(self):
        if not os.path.exists(self.t_filepath):
            raise FileNotFoundError(f"Token文件不存在：{self.t_filepath}")
        with open(self.t_filepath, 'r', encoding='utf-8') as file:
            tokens_data = json.load(file)

        processed_tokens = {
            '关键字': {},
            '运算符': {},
            '界符': {},
            '单词类别': {}
        }

        for item in tokens_data:
            token_type = item['type']  # 获取token类型
            value = item['value']      # 获取token值

            if token_type in ['char', 'int', 'float', 'break', 'const', 'return',
                              'void', 'continue', 'do', 'while', 'if', 'else', 'for']:
                processed_tokens['关键字'][token_type] = value
            elif token_type in ['!', '*', '/', '%', '+', '-', '<', '<=', '>', '>=',
                                '==', '!=', '&&', '||', '=', '.']:
                processed_tokens['运算符'][token_type] = value
            elif token_type in ['{', '}', ';', ',', '(', ')', '[', ']']:
                processed_tokens['界符'][token_type] = value
            elif token_type in ['整数', '字符', '字符串', '标识符', '实数', '八进制数', '十六进制数']:
                processed_tokens['单词类别'][token_type] = value

        return processed_tokens

    # 获取当前字符
    def get_char(self, offset=0):
        pos = self.index + offset  # 计算目标位置：当前索引位置加上偏移量
        if 0 <= pos < len(self.code_str):  # 检查位置是否在有效范围内（0到字符串长度之间）
            return self.code_str[pos]  # 如果位置有效，返回该位置的字符
        return None  # 如果位置无效（超出范围），返回None表示没有字符

    # 跳过当前字符并移动到下一个字符
    def _consume_char(self):
        char = self.get_char()  # 获取当前字符
        self.index += 1  # 移动索引到下一个位置
        self.column += 1  # 增加列号
        if char == '\n':  # 如果遇到换行符
            self.line_num += 1  # 增加行号
            self.column = 0  # 重置列号
        return char  # 返回被跳过的字符
    
    # 检查字符是否为数字
    @staticmethod
    def _is_digit(char):
        return char is not None and char.isdigit()
    
    # 检查字符是否为十六进制数字
    @staticmethod
    def _is_hex_digit(char):
        return char is not None and (char.isdigit() or char.lower() in 'abcdef')

    # 检查当前字符是否为字母或下划线
    @staticmethod
    def _is_alpha(char):
        return char is not None and (char.isalpha() or char == '_')

    # 十六进制匹配
    def hexadecimal(self):
        """匹配十六进制数
        Returns:
            tuple: (value, is_valid) 其中value是匹配的字符串，is_valid表示是否有效
        """
        value = ''  # 存储匹配的十六进制数
        is_valid = True  # 标记是否有效
        if self.get_char() == '0':  # 检查是否以0开头
            value += self._consume_char()  # 跳过0
            if self.get_char() in ['x', 'X']:  # 检查是否跟着x或X
                value += self._consume_char()  # 消费x或X
                hex_digits = []  # 存储十六进制数字
                while self._is_hex_digit(self.get_char()):  # 收集所有十六进制数字
                    hex_digits.append(self._consume_char())

                if not hex_digits:  # 如果没有十六进制数字
                    self.error(value, "Invalid hexadecimal")  # 报告错误
                    is_valid = False
                else:
                    value += ''.join(hex_digits)  # 将数字添加到结果中

                # 检查后续非法字符
                next_char = self.get_char()
                if next_char and (next_char.isalnum() or next_char == '_'):
                    invalid_part = [self._consume_char()]
                    while (nc := self.get_char()) and (nc.isalnum() or nc == '_'):
                        invalid_part.append(self._consume_char())
                    self.error(value + ''.join(invalid_part), "Invalid hexadecimal format")
                    is_valid = False
        return value, is_valid

    # 八进制匹配
    def octal(self):
        """匹配八进制数
        Returns:
            tuple: (value, is_valid) 其中value是匹配的字符串，is_valid表示是否有效
        """
        value = ''  # 存储匹配的八进制数
        is_valid = True  # 标记是否有效
        
        # 检查前导零
        if self.get_char() == '0':
            value += self._consume_char()  # 消费0
            
            # 检查是否有后续数字
            if self._is_digit(self.get_char()):
                octal_digits = []  # 存储八进制数字
                while self._is_digit(self.get_char()):  # 收集所有数字
                    octal_digits.append(self._consume_char())
                
                value += ''.join(octal_digits)  # 将数字添加到结果中
                
                # 检查无效的八进制数字（8或9）
                if any(d in '89' for d in octal_digits):
                    self.error(value, "Invalid octal")
                    is_valid = False
                # 检查多个前导零
                elif len(octal_digits) > 0 and value[0] == '0' and value[1] == '0':
                    self.error(value, "Invalid octal")
                    is_valid = False
            else:
                # 单个0是有效的八进制数
                return value, True
            
            # 检查后续非法字符
            next_char = self.get_char()
            if next_char and (next_char.isalnum() or next_char == '_'):
                invalid_part = [self._consume_char()]
                while (nc := self.get_char()) and (nc.isalnum() or nc == '_'):
                    invalid_part.append(self._consume_char())
                self.error(value + ''.join(invalid_part), "Invalid octal format")
                is_valid = False
                
        return value, is_valid

    # 十进制匹配
    def decimal(self, prefix):
        """匹配十进制数
        Args:
            prefix (str): 已经匹配的前缀
        Returns:
            tuple: (value, is_valid) 其中value是匹配的字符串，is_valid表示是否有效
        """
        value = prefix  # 使用传入的前缀
        is_valid = True  # 标记是否有效
        decimal_digits = []  # 存储十进制数字
        while self._is_digit(self.get_char()):  # 收集所有数字
            decimal_digits.append(self._consume_char())
        value += ''.join(decimal_digits)  # 将数字添加到结果中

        # 检查前导零
        if len(value) > 1 and value[0] == '0':
            self.error(value, "Invalid decimal")
            is_valid = False

        # 检查后续非法字符
        next_char = self.get_char()
        if next_char and (next_char.isalnum() or next_char == '_'):
            invalid_part = [self._consume_char()]
            while (nc := self.get_char()) and (nc.isalnum() or nc == '_'):
                invalid_part.append(self._consume_char())
            self.error(value + ''.join(invalid_part), "Invalid decimal format")
            is_valid = False

        return value, is_valid

    # 标识符和关键字匹配
    def identifier(self):
        """匹配标识符
        Returns:
            tuple: (value, is_valid) 其中value是匹配的字符串，is_valid表示是否有效
        """
        value = ''  # 存储匹配的标识符
        is_valid = False  # 标记是否有效
        while self._is_alpha(self.get_char()) or self._is_digit(self.get_char()):  # 收集所有字母、数字和下划线
            value += self._consume_char()
            is_valid = True  # 至少有一个字符才有效
        return value, is_valid

    # 注释匹配
    def comment(self):
        """匹配注释
        Returns:
            tuple: (value, is_valid) 其中value是匹配的字符串，is_valid表示是否有效
        """
        value = self._consume_char()  # 消费第一个'/'
        next_char = self.get_char()
        if next_char == '/':  # 单行注释
            value += self._consume_char()  # 消费第二个'/'
            while (char := self.get_char()) and char != '\n':  # 收集直到行尾的所有字符
                value += self._consume_char()
            return value, True
        elif next_char == '*':  # 多行注释
            value += self._consume_char()  # 消费'*'
            while True:
                if self.get_char() is None:  # 文件结束
                    self.error(value, "Invalid comment format")
                    return value, False
                if self.get_char() == '*' and self.get_char(1) == '/':  # 检查注释结束
                    value += self._consume_char()  # 消费'*'
                    value += self._consume_char()  # 消费'/'
                    return value, True
                value += self._consume_char()  # 收集注释内容
        else:  # 无效注释
            self.error(value, "Invalid comment format")
            return value, False

    # 运算符匹配
    def operator(self):
        """匹配运算符
        Returns:
            tuple: (value, is_valid) 其中value是匹配的字符串，is_valid表示是否有效
        """
        value = ''  # 存储匹配的运算符
        is_valid = True  # 标记是否有效
        while self.get_char() in '%!*/+-<>=&|.':  # 收集所有可能的运算符字符
            value += self._consume_char()
        if value not in self.tokens.get('运算符', {}):  # 检查是否是有效的运算符
            is_valid = False
            self.error(value, "Invalid operator")
        return value, is_valid

    # 字符匹配
    def character(self):
        """匹配字符字面量
        Returns:
            tuple: (value, is_valid) 其中value是匹配的字符串，is_valid表示是否有效
        """
        value = self._consume_char()  # 跳过单引号
        escape_mode = False  # 标记是否在转义模式
        while self.get_char() != '\'':  # 收集直到下一个单引号的所有字符
            if self.get_char() == '\n' or self.get_char().isspace():  # 检查非法换行或空白
                self.error(value, "Invalid character")
                return value, False
            if self.get_char() == '\\' and self.get_char(1) in 'tnr\\\'\"':  # 检查转义字符
                escape_mode = True
            value += self._consume_char()
        value += self._consume_char()  # 跳过闭合单引号
        if escape_mode:  # 检查转义字符格式
            if len(value) != 4:  # 转义字符应该是4个字符长
                self.error(value, "Invalid character")
                return value, False
        else:
            if len(value) != 3:  # 普通字符应该是3个字符长
                self.error(value, "Invalid character")
                return value, False
        return value, True

    # 字符串匹配
    def string(self):
        """匹配字符串字面量
        Returns:
            tuple: (value, is_valid) 其中value是匹配的字符串，is_valid表示是否有效
        """
        value = self._consume_char()  # 跳过双引号
        while (char := self.get_char()) and char != '"':  # 收集直到下一个双引号的所有字符
            if char is None or char == '\n':  # 检查非法结束或换行
                self.error(value, "Invalid string")
                return value, False
            value += self._consume_char()
        value += self._consume_char()  # 跳过闭合双引号
        return value, True

    # 界符匹配
    def delimiter(self):
        """匹配界符
        Returns:
            str: 匹配的界符
        """
        value = self._consume_char()  # 消费界符
        return value

    def real(self, prefix):
        """匹配实数（浮点数或科学计数法）"""
        value = prefix  # 跳过第一个数字
        has_decimal = '.' in prefix
        is_valid = True
        # 先导零
        if len(value) > 2 and value[0] == '0':
            is_valid = False
        # 处理整数部分和小数部分
        while True:
            if self.get_char() == '.' and not has_decimal:
                value += self._consume_char()  # 跳过小数点
                has_decimal = True
                # 必须至少有一个小数数字
                if not self._is_digit(self.get_char()):
                    is_valid = False

            elif self.get_char() in ['e', 'E']:
                value += self._consume_char()  # 跳过e/E
                # 处理可选符号
                if self.get_char() in ['+', '-']:
                    value += self._consume_char()
                # 必须至少一个指数数字
                if not self._is_digit(self.get_char()):
                    is_valid = False
            elif self._is_digit(self.get_char()):
                value += self._consume_char()

            elif self._is_alpha(self.get_char()) or self.get_char() == '.':
                value += self._consume_char()
                is_valid = False
            else:
                break

        if not is_valid:
            self.error(value, "Invalid Real")
            return value, is_valid
        return value, is_valid

    # 单词匹配
    def process_token(self):
        char = self.get_char()
        if char is None:  # 文件末尾
            return False
        if char.isdigit():
            if char == '0':
                # First check if it's a standalone zero (decimal)
                next_char = self.get_char(1)
                if next_char is None or not (next_char.isdigit() or next_char.lower() == 'x' or next_char == '.'):
                    value = self._consume_char()  # Consume the '0'
                    token_info = f"{value}\t\t{self.tokens['单词类别']['整数']}"
                    self.token_list.append(token_info)
                    print(token_info)
                    return True

                # 0x匹配十六进制
                if next_char in ['x', 'X']:
                    value, is_valid = self.hexadecimal()
                    if is_valid:
                        token_info = f"{value}\t\t{self.tokens['单词类别']['十六进制数']}"
                        self.token_list.append(token_info)
                        print(token_info)
                # 0.匹配浮点数和科学计数
                elif next_char == '.':
                    value = self._consume_char()  # 跳过0
                    value += self._consume_char()  # 跳过.
                    real_part, is_valid = self.real(value)
                    if is_valid:
                        token_info = f"{real_part}\t\t{self.tokens['单词类别']['实数']}"
                        self.token_list.append(token_info)
                        print(token_info)
                # 其他情况视为八进制
                else:
                    pos = self.index
                    value = self._consume_char()  # 跳过第一个数字
                    while self._is_digit(self.get_char()) or self._is_alpha(self.get_char()):
                        value += self._consume_char()  # 跳过剩余数字
                    next_char = self.get_char()
                    if next_char is not None and next_char in '.eE':
                        real_part, is_valid = self.real(value)
                        if is_valid:
                            token_info = f"{real_part}\t\t{self.tokens['单词类别']['实数']}"
                            self.token_list.append(token_info)
                            print(token_info)
                    else:
                        self.index = pos
                        value, is_valid = self.octal()
                        if is_valid:
                            token_info = f"{value}\t\t{self.tokens['单词类别']['八进制数']}"
                            self.token_list.append(token_info)
                            print(token_info)
                # 不是0，整数、科学计数、浮点数
            else:
                value = self._consume_char()  # 跳过第一个数字
                while self._is_digit(self.get_char()):
                    value += self._consume_char()  # 跳过剩余数字
                next_char = self.get_char()
                if next_char is not None and next_char in '.eE':
                    real_part, is_valid = self.real(value)
                    if is_valid:
                        token_info = f"{real_part}\t\t{self.tokens['单词类别']['实数']}"
                        self.token_list.append(token_info)
                        print(token_info)
                else:
                    real_part, is_valid = self.decimal(value)
                    if is_valid:
                        token_info = f"{value}\t\t{self.tokens['单词类别']['整数']}"
                        self.token_list.append(token_info)
                        print(token_info)
            return True
        elif char == '.':
            if self.get_char(1).isdigit():
                value = self._consume_char()  # 跳过字符.
                while self.get_char().isdigit():
                    value += self._consume_char()
                self.error(value, "Invalid Real")
            else:
                value, is_valid = self.operator()
                if is_valid:
                    token_info = f"{value}\t\t{self.tokens['运算符'][value]}"
                    self.token_list.append(token_info)
                    print(token_info)

            return True
        # 标识符和关键字匹配
        elif ('a' <= char <= 'z') or ('A' <= char <= 'Z') or (char == '_'):
            value, is_valid = self.identifier()
            if is_valid:
                if value in self.tokens.get('关键字', {}):
                    token_info = f"{value}\t\t{self.tokens['关键字'][value]}"
                else:
                    token_info = f"{value}\t\t{self.tokens['单词类别'].get('标识符', '700')}"
                self.token_list.append(token_info)
                print(token_info)
            return True
        # 注释匹配
        elif char == '/':
            next_char = self.get_char(1)
            if next_char in ['/', '*']:  # 只有//或/*才进入注释匹配
                self.comment()
                return True
            else:  # 单独/是运算符
                value, is_valid = self.operator()
                if is_valid:
                    token_info = f"{value}\t\t{self.tokens['运算符'][value]}"
                    self.token_list.append(token_info)
                    print(token_info)
                return True
        # 运算符匹配
        elif char in '%!*/+-<>=&|.':
            value, is_valid = self.operator()
            if is_valid:
                token_info = f"{value}\t\t{self.tokens['运算符'][value]}"
                self.token_list.append(token_info)
                print(token_info)
            return True

        # 字符匹配
        elif char == '\'':
            value, is_valid = self.character()
            if is_valid:
                token_info = f"{value}\t\t{self.tokens['单词类别']['字符']}"
                self.token_list.append(token_info)
                print(token_info)
            return True

        # 字符串匹配
        elif char == '"':
            value, is_valid = self.string()
            if is_valid:
                token_info = f"{value}\t\t{self.tokens['单词类别']['字符串']}"
                self.token_list.append(token_info)
                print(token_info)
            return True

        # 空白字符
        elif char.isspace():
            self._consume_char()
            return True

        # 界符匹配
        elif char in '{};,\[\]\(\).':
            value = self.delimiter()
            token_type = self.tokens['界符'].get(value, 'UNKNOWN')
            token_info = f"{value}\t\t{token_type}"
            self.token_list.append(token_info)
            print(token_info)
            return True

        # 未知字符
        else:
            self.error(char, "Unexpected character")
            self._consume_char()
            return True

    # 记录错误信息
    def error(self, value, error_type):
        """记录错误信息
        Args:
            value (str): 导致错误的字符串
            error_type (str): 错误类型描述
        """
        error_message = f"{value}\t{error_type}"  # 构建错误消息
        self.errors.append((value, self.line_num, self.column, error_message))  # 添加到错误列表

    # 保存 token 到文件
    def _save_tokens_to_file(self):
        with open(self.output_filepath, "w", encoding="utf-8") as file:
            for token in self.token_list:
                file.write(token + "\n")
        print(f"Tokens 保存至： {self.output_filepath}")

    # 词法分析
    def analyze(self):
        """执行词法分析的主方法
        遍历源代码，识别并处理所有token
        """
        while self.process_token():  # 持续处理token直到文件结束
            pass
        self._report_errors()  # 报告所有发现的错误
        self._save_tokens_to_file()  # 调用保存 token 的方法

    # 错误汇总输出
    def _report_errors(self):
        if self.errors:  # 如果有错误
            print("\n错误信息:")
            for error in self.errors:
                print(error[3])  # 输出错误信息


if __name__ == "__main__":
    code_filepath = "1.txt"
    token_filepath = "Tokens.json"
    out_filepath = "output_tokens.txt"  # 指定输出文件路径
    analyzer = WordAnalysis(code_filepath, token_filepath, out_filepath)
    analyzer.analyze()