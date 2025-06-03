import os
import sys
import subprocess
import platform
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QFileDialog, 
                             QLabel, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

class VimDirectoryCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('icon.ico'))
        self.initUI()
        
    def initUI(self):
        # 设置窗口属性
        self.setWindowTitle('DirCreate')
        self.setGeometry(110, 110, 1200, 1000)
        self.setFont(QFont('Ariel', 12))
        
        # 创建中心部件和布局
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # 说明标签
        instructions = QLabel("Enter Vim-style directory structure below. \nExample:\n\n"
                             "Project/\n"
                             "├── src/\n"
                             "│   ├── main.py\n"
                             "│   └── utils.py\n"
                             "├── tests/\n"
                             "│   └── test_main.py\n"
                             "└── README.md"
                             "\n\nThen select the target directory and click 'Create Directory Structure'.")
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)
        
        # 添加创建项目子文件夹的复选框
        self.subfolder_checkbox = QCheckBox("Create project subfolder")
        self.subfolder_checkbox.setChecked(True)
        main_layout.addWidget(self.subfolder_checkbox)
        
        # 目录结构输入的文本区域
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter directory structure here...")
        self.text_edit.setFont(QFont('Monospace', 12))
        self.text_edit.setAcceptRichText(False)
        main_layout.addWidget(self.text_edit)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 选择目录按钮
        self.select_dir_button = QPushButton("Select Target Directory")
        self.select_dir_button.clicked.connect(self.select_directory)
        button_layout.addWidget(self.select_dir_button)
        
        # 创建结构按钮
        self.create_button = QPushButton("Create Directory Structure")
        self.create_button.clicked.connect(self.create_structure)
        self.create_button.setEnabled(False)  # Disabled until directory is selected
        button_layout.addWidget(self.create_button)
        
        main_layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("No directory selected")
        main_layout.addWidget(self.status_label)
        
        self.setCentralWidget(central_widget)
        
        # 存储选定的目录
        self.target_directory = None
        
    def select_directory(self): # 选择目录
        directory = QFileDialog.getExistingDirectory(self, "Select Target Directory")
        if directory:
            self.target_directory = directory
            self.status_label.setText(f"Selected directory: {directory}")
            self.create_button.setEnabled(True)
    
    def create_structure(self): # 创建结构
        if not self.target_directory:
            QMessageBox.warning(self, "Error", "Please select a target directory first.")
            return
            
        structure_text = self.text_edit.toPlainText().strip()
        if not structure_text:
            QMessageBox.warning(self, "Error", "Please enter a directory structure.")
            return
            
        try:
            created_path = self.parse_and_create(structure_text)
            self.show_success_dialog(created_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create directory structure: {str(e)}")
    
    def show_success_dialog(self, created_path):
        """显示成功对话框，提供关闭或打开文件夹的选项"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Success")
        msg_box.setText("Directory structure created successfully!")
        msg_box.setInformativeText(f"Created at: {created_path}")
        
        # 添加自定义按钮
        close_button = msg_box.addButton("关闭", QMessageBox.RejectRole)
        open_button = msg_box.addButton("打开文件夹", QMessageBox.AcceptRole)
        
        msg_box.setDefaultButton(open_button)
        msg_box.exec_()
        
        # 检查用户点击的按钮
        if msg_box.clickedButton() == open_button:
            self.open_folder(created_path)
    
    def open_folder(self, folder_path):
        """根据操作系统打开文件夹"""
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(folder_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            elif system == "Linux":
                subprocess.run(["xdg-open", folder_path])
            else:
                QMessageBox.information(self, "Info", f"Please manually open: {folder_path}")
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not open folder: {str(e)}")
    
    def parse_and_create(self, structure_text): # 解析并创建
        lines = structure_text.split('\n')  # 按行分割
        
        # 提取项目名称(第一行)
        project_name = lines[0].strip().split('#')[0].strip()
        if project_name.endswith('/'):
            project_name = project_name[:-1]
            
        # 确定基础目录
        if self.subfolder_checkbox.isChecked():
            base_dir = os.path.join(self.target_directory, project_name)
        else:
            base_dir = self.target_directory
        
        # 使用栈来管理目录层级
        path_stack = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue  # 跳过空行和注释
                
            # 移除行内注释(井号后的所有内容)
            line = line.split('#')[0].strip()
            if not line:
                continue
            
            # 计算层级深度
            level = 0
            name = ""
            
            if line.strip() == project_name or line.strip() == project_name + '/':
                # 根目录
                level = 0
                name = project_name
                # 只有在勾选了创建项目子文件夹时才创建根目录
                if self.subfolder_checkbox.isChecked():
                    os.makedirs(base_dir, exist_ok=True)
                path_stack = []
                continue
            elif '├──' in line or '└──' in line:
                # 计算层级（通过 │ 字符的数量）
                level = line.count('│')
                # 提取文件/目录名
                if '├──' in line:
                    name = line.split('├──')[1].strip()
                else:
                    name = line.split('└──')[1].strip()
            elif '│' in line and not ('├──' in line or '└──' in line):
                # 只有 │ 字符的行，跳过
                continue
            else:
                # 简单的缩进格式
                leading_spaces = len(line) - len(line.lstrip())
                level = leading_spaces // 4  # 假设每级缩进4个空格
                name = line.strip()
            
            if not name:
                continue
            
            # 调整路径栈以匹配当前层级
            while len(path_stack) > level:
                path_stack.pop()
            
            # 处理名称中包含路径分隔符的情况
            if '/' in name:
                path_components = [comp for comp in name.split('/') if comp]
                for i, component in enumerate(path_components):
                    current_level = level + i
                    # 调整栈深度
                    while len(path_stack) > current_level:
                        path_stack.pop()
                    
                    path_stack.append(component)
                    full_path = os.path.join(base_dir, *path_stack)
                    
                    # 创建目录
                    os.makedirs(full_path, exist_ok=True)
            else:
                # 添加到路径栈
                path_stack.append(name)
                
                # 构建完整路径
                full_path = os.path.join(base_dir, *path_stack)
                
                if name.endswith('/'):
                    # 这是一个目录
                    clean_name = name.rstrip('/')
                    path_stack[-1] = clean_name
                    full_path = os.path.join(base_dir, *path_stack)
                    os.makedirs(full_path, exist_ok=True)
                else:
                    # 没有扩展名的按普通文件处理
                    directory = os.path.dirname(full_path)
                    if directory and not os.path.exists(directory):
                        os.makedirs(directory, exist_ok=True)
                    # 创建空文件
                    with open(full_path, 'w') as f:
                        pass
                    # 从栈中移除文件名，因为它不是目录
                    path_stack.pop()
        
        # 如果没有勾选创建项目子文件夹，返回选定的目录
        # 如果勾选了，返回创建的项目目录
        return base_dir if self.subfolder_checkbox.isChecked() else self.target_directory

def main():
    app = QApplication(sys.argv)
    window = VimDirectoryCreator()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()