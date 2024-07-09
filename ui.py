import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QListWidget, QHBoxLayout, QDesktopWidget, QSplitter, QApplication
)
from PyQt5.QtCore import Qt


class PasswordManagerUI(QWidget):
    def __init__(self):
        super().__init__()

        self.category_list = QListWidget(self)
        self.entry_list = QListWidget(self)
        self.search_input = QLineEdit(self)

        self.add_account_button = QPushButton(QIcon("ico/add.ico"), '添加账号', self)
        self.search_button = QPushButton(QIcon("ico/search.ico"), '搜索', self)
        self.export_button = QPushButton(QIcon("ico/export.ico"), '导出', self)
        self.add_category_button = QPushButton(QIcon("ico/add.ico"), '添加分组', self)

        self.initUI()

    def initUI(self):
        # 顶部按钮布局
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.add_account_button)
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.search_button)
        top_layout.addWidget(self.export_button)

        # 左侧分类栏
        category_layout = QVBoxLayout()
        category_layout.addWidget(self.category_list)
        category_layout.addWidget(self.add_category_button)

        # 右侧账户信息栏
        entry_layout = QVBoxLayout()
        entry_layout.addWidget(self.entry_list)

        # 主布局，使用 QSplitter 实现左右布局
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_widget.setLayout(category_layout)
        right_widget = QWidget()
        right_widget.setLayout(entry_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([150, 350])  # 设置初始大小

        # 整体布局
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)
        self.setWindowTitle('PwManager')
        self.setGeometry(300, 300, 400, 400)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PasswordManagerUI()
    ex.show()
    sys.exit(app.exec_())
