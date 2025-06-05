import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QTextEdit, QFileDialog, QLabel,
                           QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from 词法分析器 import WordAnalysis
from 语法分析器 import analyze_code
from 语义1 import perform_semantic_analysis
from 中间代码 import generate_intermediate_code
from 目标代码 import generate_target_code
from 代码优化 import optimize_code

class LexerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.source_file = None
        self.word_analyzer = None
        self.parser = None

    def initUI(self):
        self.setWindowTitle('编译器')
        self.setGeometry(100, 100, 1800, 1000)

        # 创建中心部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建按钮布局
        button_layout = QHBoxLayout()

        # 创建按钮
        self.open_source_btn = QPushButton('打开源文件', self)
        self.lexer_btn = QPushButton('词法分析', self)
        self.parser_btn = QPushButton('语法分析', self)
        self.semantic_btn = QPushButton('语义分析', self)
        self.intermediate_btn = QPushButton('中间代码', self)
        self.optimize_btn = QPushButton('代码优化', self)
        self.target_btn = QPushButton('目标代码', self)
        self.clear_btn = QPushButton('清除结果', self)

        # 初始状态下禁用所有分析按钮
        self.lexer_btn.setEnabled(False)
        self.parser_btn.setEnabled(False)
        self.semantic_btn.setEnabled(False)
        self.intermediate_btn.setEnabled(False)
        self.optimize_btn.setEnabled(False)
        self.target_btn.setEnabled(False)

        # 添加按钮到布局
        button_layout.addWidget(self.open_source_btn)
        button_layout.addWidget(self.lexer_btn)
        button_layout.addWidget(self.parser_btn)
        button_layout.addWidget(self.semantic_btn)
        button_layout.addWidget(self.intermediate_btn)
        button_layout.addWidget(self.optimize_btn)
        button_layout.addWidget(self.target_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()

        # 创建主分割器
        main_splitter = QSplitter(Qt.Horizontal)

        # 左侧面板（源代码和错误信息）
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 源代码显示区
        source_label = QLabel('源代码:')
        source_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.source_text = QTextEdit()
        self.source_text.setReadOnly(True)
        self.source_text.setFont(QFont('Consolas', 10))
        left_layout.addWidget(source_label)
        left_layout.addWidget(self.source_text)

        # 错误信息显示区
        error_label = QLabel('错误信息:')
        error_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setFont(QFont('Consolas', 10))
        self.error_text.setTextColor(QColor('red'))
        left_layout.addWidget(error_label)
        left_layout.addWidget(self.error_text)

        # 右侧面板（分析结果）
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 分析结果显示区
        result_label = QLabel('分析结果:')
        result_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont('Consolas', 10))
        right_layout.addWidget(result_label)
        right_layout.addWidget(self.result_text)

        # 将左右面板添加到主分割器
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([600, 1200])  # 设置初始分割比例

        # 将所有布局添加到主布局
        layout.addLayout(button_layout)
        layout.addWidget(main_splitter)

        # 连接信号和槽
        self.open_source_btn.clicked.connect(self.open_source_file)
        self.lexer_btn.clicked.connect(self.perform_lexical_analysis)
        self.parser_btn.clicked.connect(self.perform_syntax_analysis)
        self.semantic_btn.clicked.connect(self.perform_semantic_analysis)
        self.intermediate_btn.clicked.connect(self.generate_intermediate)
        self.optimize_btn.clicked.connect(self.optimize_code)
        self.target_btn.clicked.connect(self.generate_target)
        self.clear_btn.clicked.connect(self.clear_results)

    def open_source_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '打开源文件', '', 'Text Files (*.txt);;All Files (*)')
        if file_name:
            self.source_file = file_name
            with open(file_name, 'r', encoding='utf-8') as file:
                content = file.read()
                self.source_text.setText(content)
            # 启用所有分析按钮
            self.lexer_btn.setEnabled(True)
            self.parser_btn.setEnabled(True)
            self.semantic_btn.setEnabled(True)
            self.intermediate_btn.setEnabled(True)
            self.optimize_btn.setEnabled(True)
            self.target_btn.setEnabled(True)

    def perform_lexical_analysis(self):
        """执行词法分析"""
        try:
            source_code = self.source_text.toPlainText()
            with open("output_tokens.txt", "r", encoding="utf-8") as f:
                token_text = f.read()
            self.result_text.setText("=== 词法分析结果 ===\n\n" + token_text)
        except Exception as e:
            self.error_text.setText(f"词法分析错误: {str(e)}")

    def perform_syntax_analysis(self):
        """执行语法分析"""
        try:
            source_code = self.source_text.toPlainText()
            result = analyze_code(source_code)
            
            if result['success']:
                # 将AST转换为文本形式
                ast_text = self.ast_to_text(result['ast'])
                self.result_text.setText("=== 语法分析结果 (AST) ===\n\n" + ast_text)
            else:
                self.error_text.setText(f"语法分析失败: {result['error']}")

            if result.get('errors'):
                error_text = "语法错误:\n"
                for error in result['errors']:
                    error_text += f"{error}\n"
                self.error_text.setText(error_text)
        except Exception as e:
            self.error_text.setText(f"语法分析错误: {str(e)}")

    def ast_to_text(self, ast_node, level=0):
        """将AST转换为文本形式"""
        if isinstance(ast_node, list):
            return '\n'.join(self.ast_to_text(node, level) for node in ast_node)
        
        if isinstance(ast_node, dict):
            indent = '  ' * level
            node_type = ast_node.get('type', 'Unknown')
            result = f"{indent}{node_type}"
            
            # 添加节点特定信息
            if node_type == 'declaration':
                result += f": {ast_node.get('data_type', '')} {ast_node.get('name', '')}"
            elif node_type == 'assignment':
                result += f": {ast_node.get('left', '')} = ..."
            elif node_type == 'if_statement':
                result += ": if (...) { ... }"
            elif node_type == 'binary_operation':
                result += f": {ast_node.get('op', '')}"
            elif node_type in ['integer', 'float']:
                result += f": {ast_node.get('value', '')}"
            elif node_type == 'variable':
                result += f": {ast_node.get('name', '')}"
            
            # 递归处理子节点
            if 'body' in ast_node:
                result += '\n' + self.ast_to_text(ast_node['body'], level + 1)
            if 'condition' in ast_node:
                result += '\n' + self.ast_to_text(ast_node['condition'], level + 1)
            if 'left' in ast_node:
                result += '\n' + self.ast_to_text(ast_node['left'], level + 1)
            if 'right' in ast_node:
                result += '\n' + self.ast_to_text(ast_node['right'], level + 1)
            
            return result
        
        return str(ast_node)

    def perform_semantic_analysis(self):
        """执行语义分析"""
        try:
            source_code = self.source_text.toPlainText()
            result = analyze_code(source_code)
            
            if result['success']:
                semantic_result = perform_semantic_analysis(result['ast'])
                self.result_text.setText("=== 语义分析结果 ===\n\n" + semantic_result['formatted_symbol_table'])
                
                if semantic_result['errors']:
                    error_text = self.error_text.toPlainText()
                    error_text += "\n语义错误:\n"
                    for error in semantic_result['errors']:
                        error_text += f"{error}\n"
                    self.error_text.setText(error_text)
        except Exception as e:
            self.error_text.setText(f"语义分析错误: {str(e)}")

    def generate_intermediate(self):
        """生成中间代码"""
        try:
            source_code = self.source_text.toPlainText()
            result = analyze_code(source_code)
            
            if result['success']:
                intermediate_result = generate_intermediate_code(result['ast'])
                if intermediate_result['success']:
                    intermediate_text = "=== 中间代码结果 ===\n\n"
                    for i, quad in enumerate(intermediate_result['quads']):
                        intermediate_text += f"{i:3d}: {quad}\n"
                    self.result_text.setText(intermediate_text)
        except Exception as e:
            self.error_text.setText(f"中间代码生成错误: {str(e)}")

    def generate_target(self):
        """生成目标代码"""
        try:
            source_code = self.source_text.toPlainText()
            result = analyze_code(source_code)
            
            if result['success']:
                intermediate_result = generate_intermediate_code(result['ast'])
                if intermediate_result['success']:
                    target_result = generate_target_code(intermediate_result['quads'])
                    if target_result['success']:
                        try:
                            with open("output.txt", "r", encoding="utf-8") as f:
                                asm_code = f.read()
                            self.result_text.setText("=== 目标代码结果 ===\n\n" + asm_code)
                        except Exception as e:
                            self.result_text.setText(f"无法读取目标代码: {str(e)}")
        except Exception as e:
            self.error_text.setText(f"目标代码生成错误: {str(e)}")

    def optimize_code(self):
        """执行代码优化"""
        try:
            source_code = self.source_text.toPlainText()
            result = analyze_code(source_code)
            
            if result['success']:
                intermediate_result = generate_intermediate_code(result['ast'])
                if intermediate_result['success']:
                    # 执行代码优化
                    optimized_result = optimize_code(intermediate_result['quads'])
                    if optimized_result['success']:
                        optimized_text = "=== 优化后的中间代码 ===\n\n"
                        for i, quad in enumerate(optimized_result['optimized_quads']):
                            optimized_text += f"{i:3d}: {quad}\n"
                        self.result_text.setText(optimized_text)
        except Exception as e:
            self.error_text.setText(f"代码优化错误: {str(e)}")

    def clear_results(self):
        """清除所有分析结果"""
        self.result_text.clear()
        self.error_text.clear()
        # 禁用所有分析按钮
        self.lexer_btn.setEnabled(False)
        self.parser_btn.setEnabled(False)
        self.semantic_btn.setEnabled(False)
        self.intermediate_btn.setEnabled(False)
        self.optimize_btn.setEnabled(False)
        self.target_btn.setEnabled(False)

def main():
    app = QApplication(sys.argv)
    gui = LexerGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 