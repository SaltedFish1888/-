"""
目标代码生成器 - 将四元式转换为8086汇编代码
优化版本，删除冗余代码
"""

import re
from typing import List, Dict, Set, Optional


class TargetCodeGenerator:
    """优化后的目标代码生成器，生成MASM/TASM风格的汇编程序结构"""

    def __init__(self):
        self.asm_code = []
        self.data_section = []
        self.variables = set()
        self.temp_vars = set()
        self.symbol_table: Dict[str, str] = {}
        self.user_variables: Set[str] = set()
        self.assembly_label_counter: int = 0

    def generate(self, quads, output_asm='output/output.asm', output_txt='output/output.txt'):
        """生成目标代码并保存到文件"""
        self._reset()
        self._analyze_symbols(quads)
        self._generate_complete_program(quads)
        return self._save_files(output_asm, output_txt)

    def _reset(self):
        """重置所有状态"""
        self.asm_code = []
        self.data_section = []
        self.variables = set()
        self.temp_vars = set()
        self.symbol_table.clear()
        self.user_variables.clear()
        self.assembly_label_counter = 0

    def _analyze_symbols(self, quads) -> None:
        """分析符号表，识别变量和临时变量"""
        for quad in quads:
            op, arg1, arg2, result = quad

            if op == "DECLARE":
                var_name = result
                var_type = arg1
                if not self._is_reserved_word(var_name):
                    self.symbol_table[var_name] = var_type
                    self.user_variables.add(var_name)
                    self.variables.add(var_name)

            # 收集所有标识符
            for identifier in [arg1, arg2, result]:
                self._collect_identifier(identifier)

    def _collect_identifier(self, identifier: Optional[str]) -> None:
        """收集标识符，区分变量和临时变量"""
        if (not identifier or identifier == "" or identifier == "_" or
                self._is_immediate(identifier)):
            return

        if identifier.startswith("t") and identifier[1:].isdigit():
            # 临时变量
            self.temp_vars.add(identifier)
        elif (re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier) and
              identifier not in self.symbol_table and
              not self._is_reserved_word(identifier)):
            # 普通变量
            self.symbol_table[identifier] = "int"
            self.user_variables.add(identifier)
            self.variables.add(identifier)

    def _generate_complete_program(self, quads):
        """生成完整的汇编程序"""
        # 生成头部
        self.asm_code.extend([
            'START:',
            '    MOV AX, DATAS',
            '    MOV DS, AX',
            ''
        ])

        # 生成代码段
        self._generate_code_section(quads)

        # 生成输出和结束代码
        self._generate_output_and_exit()

    def _generate_data_section(self):
        """生成数据段"""
        # 声明用户变量
        for var_name in self.symbol_table:
            safe_name = self._get_safe_name(var_name)
            self.data_section.append(f"    {safe_name} DW 0")

        # 声明临时变量
        for temp_var in self.temp_vars:
            safe_name = self._get_safe_name(temp_var)
            self.data_section.append(f"    {safe_name} DW 0")

        # 添加输出相关字符串
        self.data_section.extend([
            "",
            "    msg_header DB 'Program Results:', 0Dh, 0Ah, '$'",
            "    msg_equals DB ' = ', '$'",
            "    msg_newline DB 0Dh, 0Ah, '$'",
            "    msg_exit DB 'Press any key...', '$'"
        ])

    def _generate_code_section(self, quads):
        """生成代码段"""
        for quad in quads:
            op, arg1, arg2, result = quad

            if op == 'LABEL':
                self.asm_code.append(f'{result}:')
            elif op == 'DECLARE':
                pass  # 已在数据段处理
            elif op == '=':
                self._generate_assignment(arg1, result)
            elif op in ('+', '-', '*', '/'):
                self._generate_arithmetic(op, arg1, arg2, result)
            elif op in ('<', '<=', '>', '>=', '==', '!='):
                self._generate_comparison(op, arg1, arg2, result)
            elif op == 'IF':
                self._generate_if(arg1, result)
            elif op == 'GOTO':
                self.asm_code.append(f'    JMP {result}')
            elif op == 'RET':
                pass  # 在程序结束统一处理

    def _generate_assignment(self, src, dest):
        """生成赋值指令"""
        self.asm_code.append(f"    ; {dest} = {src}")

        if self._is_immediate(src):
            self.asm_code.append(f"    MOV AX, {src}")
        else:
            safe_src = self._get_safe_name(src)
            self.asm_code.append(f"    MOV AX, [{safe_src}]")

        safe_dest = self._get_safe_name(dest)
        self.asm_code.extend([
            f"    MOV [{safe_dest}], AX",
            ""
        ])

    def _generate_arithmetic(self, op, arg1, arg2, result):
        """生成算术运算指令"""
        self.asm_code.append(f"    ; {result} = {arg1} {op} {arg2}")

        # 加载第一个操作数
        if self._is_immediate(arg1):
            self.asm_code.append(f"    MOV AX, {arg1}")
        else:
            safe_arg1 = self._get_safe_name(arg1)
            self.asm_code.append(f"    MOV AX, [{safe_arg1}]")

        # 执行运算
        if op == "+":
            if self._is_immediate(arg2):
                self.asm_code.append(f"    ADD AX, {arg2}")
            else:
                safe_arg2 = self._get_safe_name(arg2)
                self.asm_code.append(f"    ADD AX, [{safe_arg2}]")
        elif op == "-":
            if self._is_immediate(arg2):
                self.asm_code.append(f"    SUB AX, {arg2}")
            else:
                safe_arg2 = self._get_safe_name(arg2)
                self.asm_code.append(f"    SUB AX, [{safe_arg2}]")
        elif op == "*":
            if self._is_immediate(arg2):
                self.asm_code.append(f"    MOV BX, {arg2}")
            else:
                safe_arg2 = self._get_safe_name(arg2)
                self.asm_code.append(f"    MOV BX, [{safe_arg2}]")
            self.asm_code.append("    MUL BX")
        elif op == "/":
            if self._is_immediate(arg2):
                self.asm_code.append(f"    MOV BX, {arg2}")
            else:
                safe_arg2 = self._get_safe_name(arg2)
                self.asm_code.append(f"    MOV BX, [{safe_arg2}]")
            self.asm_code.extend([
                "    XOR DX, DX",
                "    DIV BX"
            ])

        # 存储结果
        safe_result = self._get_safe_name(result)
        self.asm_code.extend([
            f"    MOV [{safe_result}], AX",
            ""
        ])

    def _generate_comparison(self, op, arg1, arg2, result):
        """生成比较指令"""
        self.asm_code.append(f"    ; {result} = {arg1} {op} {arg2}")

        true_label = f"TRUE_{self.assembly_label_counter}"
        end_label = f"END_{self.assembly_label_counter}"
        self.assembly_label_counter += 1

        # 加载并比较操作数
        if self._is_immediate(arg1):
            self.asm_code.append(f"    MOV AX, {arg1}")
        else:
            safe_arg1 = self._get_safe_name(arg1)
            self.asm_code.append(f"    MOV AX, [{safe_arg1}]")

        if self._is_immediate(arg2):
            self.asm_code.append(f"    CMP AX, {arg2}")
        else:
            safe_arg2 = self._get_safe_name(arg2)
            self.asm_code.append(f"    CMP AX, [{safe_arg2}]")

        # 条件跳转
        jump_map = {"<": "JL", ">": "JG", "<=": "JLE", ">=": "JGE", "==": "JE", "!=": "JNE"}
        jump_instr = jump_map.get(op, "JMP")

        safe_result = self._get_safe_name(result)
        self.asm_code.extend([
            f"    {jump_instr} {true_label}",
            f"    MOV [{safe_result}], 0",
            f"    JMP {end_label}",
            f"{true_label}:",
            f"    MOV [{safe_result}], 1",
            f"{end_label}:",
            ""
        ])

    def _generate_if(self, condition, label):
        """生成IF指令"""
        if self._is_immediate(condition):
            self.asm_code.extend([
                f'    MOV AX, {condition}',
                '    CMP AX, 1'
            ])
        else:
            safe_cond = self._get_safe_name(condition)
            self.asm_code.append(f'    CMP [{safe_cond}], 1')
        self.asm_code.append(f'    JE {label}')

    def _generate_output_and_exit(self):
        """生成输出结果和程序退出代码"""
        self.asm_code.extend([
            "    ; 输出结果",
            "    LEA DX, msg_header",
            "    MOV AH, 09h",
            "    INT 21h",
            ""
        ])

        # 输出用户变量
        for var_name in sorted(self.user_variables):
            self._generate_variable_output(var_name)

        # 程序退出
        self.asm_code.extend([
            "    LEA DX, msg_exit",
            "    MOV AH, 09h",
            "    INT 21h",
            "",
            "    MOV AH, 01h",
            "    INT 21h",
            "",
            "    MOV AH, 4Ch",
            "    INT 21h"
        ])

        # 添加数字输出函数
        self._add_print_number_function()

    def _generate_variable_output(self, var_name: str) -> None:
        """生成变量输出代码"""
        safe_name = self._get_safe_name(var_name)

        # 输出变量名
        for c in var_name:
            self.asm_code.extend([
                f"    MOV DL, '{c}'",
                "    MOV AH, 02h",
                "    INT 21h"
            ])

        self.asm_code.extend([
            "    LEA DX, msg_equals",
            "    MOV AH, 09h",
            "    INT 21h",
            "",
            f"    MOV AX, [{safe_name}]",
            "    CALL PrintNumber",
            "",
            "    LEA DX, msg_newline",
            "    MOV AH, 09h",
            "    INT 21h",
            ""
        ])

    def _add_print_number_function(self):
        """添加数字输出函数"""
        self.asm_code.extend([
            "",
            "PrintNumber PROC",
            "    PUSH BX",
            "    PUSH CX",
            "    PUSH DX",
            "",
            "    MOV CX, 0",
            "    MOV BX, 10",
            "    CMP AX, 0",
            "    JGE PositiveNumber",
            "",
            "    PUSH AX",
            "    MOV DL, '-'",
            "    MOV AH, 02h",
            "    INT 21h",
            "    POP AX",
            "    NEG AX",
            "",
            "PositiveNumber:",
            "    CMP AX, 0",
            "    JNE ConvertLoop",
            "    MOV DL, '0'",
            "    MOV AH, 02h",
            "    INT 21h",
            "    JMP PrintEnd",
            "",
            "ConvertLoop:",
            "    CMP AX, 0",
            "    JE PrintLoop",
            "    XOR DX, DX",
            "    DIV BX",
            "    ADD DL, '0'",
            "    PUSH DX",
            "    INC CX",
            "    JMP ConvertLoop",
            "",
            "PrintLoop:",
            "    CMP CX, 0",
            "    JE PrintEnd",
            "    POP DX",
            "    MOV AH, 02h",
            "    INT 21h",
            "    DEC CX",
            "    JMP PrintLoop",
            "",
            "PrintEnd:",
            "    POP DX",
            "    POP CX",
            "    POP BX",
            "    RET",
            "PrintNumber ENDP"
        ])

    def _save_files(self, output_asm, output_txt):
        """保存文件"""
        # 生成数据段
        self._generate_data_section()

        # 构建完整汇编程序
        full_asm = []
        full_asm.append('DATAS SEGMENT')
        full_asm.extend(self.data_section)
        full_asm.append('DATAS ENDS')
        full_asm.append('')
        full_asm.append('STACKS SEGMENT')
        full_asm.append('    DB 128 DUP (?)')
        full_asm.append('STACKS ENDS')
        full_asm.append('')
        full_asm.append('CODES SEGMENT')
        full_asm.append('    ASSUME CS:CODES, DS:DATAS, SS:STACKS')
        full_asm.extend(self.asm_code)
        full_asm.append('CODES ENDS')
        full_asm.append('    END START')

        # 保存.asm文件
        with open(output_asm, 'w') as f:
            f.write('\n'.join(full_asm))

        # 保存.txt文件
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write("=== 汇编代码 ===\n\n")
            f.write('\n'.join(full_asm))

        return {
            'success': True,
            'message': f'汇编代码已生成到 {output_asm} 和 {output_txt}'
        }

    def _is_immediate(self, operand: Optional[str]) -> bool:
        """判断是否为立即数"""
        if not operand:
            return False
        return bool(re.match(r'^-?\d+$', operand)) or operand in ["true", "false"]

    def _is_reserved_word(self, word: str) -> bool:
        """判断是否为保留字"""
        return (word.startswith("L") or word.startswith("FUNC_") or
                word in ["main", "true", "false"])

    def _get_safe_name(self, name: str) -> str:
        """获取安全的变量名"""
        asm_reserved = {
            "AX", "BX", "CX", "DX", "SI", "DI", "BP", "SP", "AL", "AH", "BL", "BH",
            "CL", "CH", "DL", "DH", "CS", "DS", "ES", "SS", "MOV", "ADD", "SUB",
            "MUL", "DIV", "CMP", "JMP", "JE", "JNE", "JL", "JG", "PUSH", "POP"
        }
        return f"var_{name}" if name.upper() in asm_reserved else name


def generate_target_code(quads, output_asm='output.asm', output_txt='output.txt'):
    """生成目标代码"""
    generator = TargetCodeGenerator()
    return generator.generate(quads, output_asm, output_txt)


if __name__ == "__main__":
    # 测试代码
    quads = [
        ('LABEL', '_', '_', 'FUNC_main'),
        ('=', '1', '_', 'x'),
        ('GOTO', '_', '_', 'L2'),
        ('LABEL', '_', '_', 'L1'),
        ('+', 'a', '1', 't1'),
        ('=', 't1', '_', 'a'),
        ('+', 'x', '1', 't2'),
        ('=', 't2', '_', 'x'),
        ('LABEL', '_', '_', 'L2'),
        ('<', 'x', '5', 't3'),
        ('IF', 't3', '_', 'L1'),
        ('LABEL', '_', '_', 'L3'),
        ('RET', '_', '_', '_')
    ]

    result = generate_target_code(quads)
    print(result['message'])