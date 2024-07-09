import os
import sys
import json
from functools import partial

import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QDialog, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QComboBox, QMenu, QAction, QInputDialog, QListWidgetItem, QToolButton, QListWidget
)
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt
from cryptography.fernet import Fernet
from ui import PasswordManagerUI


class PasswordManagerApp(PasswordManagerUI):
    def __init__(self):
        super().__init__()

        self.entries = {}
        self.categories = {"全部": [],
                           "未分组": []}
        self.key = self.load_key()
        self.cipher = Fernet(self.key)
        self.name_identifiers = {}

        self.load_entries()

        self.add_account_button.clicked.connect(self.add_account)
        self.export_button.clicked.connect(self.export_entries)
        self.search_button.clicked.connect(self.search_entry)
        self.add_category_button.clicked.connect(self.add_category)
        self.category_list.itemClicked.connect(self.show_category_entries)
        # self.category_list.setSelectionMode(QListWidget.MultiSelection)  # 设置为多选模式
        # self.category_list.setSortingEnabled(False)  # 禁用自动排序
        self.category_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.category_list.customContextMenuRequested.connect(self.show_category_menu)

        self.entry_list.itemClicked.connect(self.show_entry_details)
        # self.entry_list.setSelectionMode(QListWidget.MultiSelection)  # 设置为多选模式
        # self.entry_list.setSortingEnabled(False)  # 禁用自动排序
        self.entry_list.itemDoubleClicked.connect(self.edit_entry_dialog)
        self.entry_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.entry_list.customContextMenuRequested.connect(self.show_entry_menu)

        self.setWindowIcon(QIcon('ico/icon.ico'))

        default_category_item = self.category_list.findItems("全部", Qt.MatchExactly)[0]
        self.category_list.setCurrentItem(default_category_item)
        self.show_category_entries(default_category_item)

    def load_key(self):
        try:
            with open(r"secret.key", "rb") as key_file:
                key = key_file.read()
        except FileNotFoundError:
            key = Fernet.generate_key()
            with open(r"secret.key", "wb") as key_file:
                key_file.write(key)
        return key

    def save_entries(self):
        encrypted_entries = {name: self.cipher.encrypt(json.dumps(info).encode()).decode() for name, info in
                             self.entries.items()}
        with open("entries.dat", "w") as f:
            json.dump(encrypted_entries, f)
        with open("categories.dat", "w") as f:
            json.dump(self.categories, f)

    def load_entries(self):
        try:
            with open("entries.dat", "r") as f:
                encrypted_entries = json.load(f)
                self.entries = {name: json.loads(self.cipher.decrypt(info.encode()).decode()) for name, info in
                                encrypted_entries.items()}
        except FileNotFoundError:
            pass
        try:
            with open("categories.dat", "r") as f:
                self.categories = json.load(f)
                for category in self.categories.keys():
                    self.category_list.addItem(category)
        except FileNotFoundError:
            self.category_list.addItem("全部")
            self.category_list.addItem("未分组")

        self.update_all_category()

    def update_all_category(self):
        self.categories["全部"] = list(self.entries.keys())
        # print(self.categories["全部"])
        self.show_category_entries(self.category_list.currentItem())

    def add_account(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('添加账号')
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint | Qt.WindowTitleHint)

        name_label = QLabel('名称:', dialog)
        name_input = QLineEdit(dialog)

        account_label = QLabel('账号:', dialog)
        account_input = QLineEdit(dialog)

        password_label = QLabel('密码:', dialog)
        password_input = QLineEdit(dialog)

        category_label = QLabel('分组:', dialog)
        category_combo = QComboBox(dialog)
        category_combo.addItems(self.categories.keys())
        new_category_input = QLineEdit(dialog)
        new_category_input.setPlaceholderText('添加新的分组')

        save_button = QPushButton('保存', dialog)
        save_button.clicked.connect(lambda: self.save_new_entry(
            name_input.text(), account_input.text(), password_input.text(),
            category_combo.currentText(), new_category_input.text(), dialog))

        category_combo.currentTextChanged.connect(lambda text: new_category_input.clear() if text != "不分组" else None)

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(name_label)
        dialog_layout.addWidget(name_input)
        dialog_layout.addWidget(account_label)
        dialog_layout.addWidget(account_input)
        dialog_layout.addWidget(password_label)
        dialog_layout.addWidget(password_input)
        dialog_layout.addWidget(category_label)
        dialog_layout.addWidget(category_combo)
        dialog_layout.addWidget(new_category_input)
        dialog_layout.addWidget(save_button)

        dialog.setLayout(dialog_layout)
        dialog.exec_()

    def save_new_entry(self, name, account, password, category, new_category, dialog):
        name = self.generate_unique_name(name)

        if name and account and password:
            if new_category:
                category = new_category
                if category not in self.categories:
                    self.categories[category] = []
                    self.category_list.addItem(category)
            elif not category or category == "全部":
                category = "未分组"  # 默认归类为未分类
                if category not in self.categories:
                    self.categories[category] = []
                    self.category_list.addItem(category)

            self.entries[name] = (account, password)
            self.categories[category].append(name)
            self.update_all_category()
            self.save_entries()

            # 切换到新条目所属的分组
            for i in range(self.category_list.count()):
                item = self.category_list.item(i)
                if item.text() == category:
                    if item.text() != "未分组":
                        self.category_list.setCurrentItem(item)
                        self.show_category_entries(item)
                        break
                    else:
                        default_category_item = self.category_list.findItems("全部", Qt.MatchExactly)[0]
                        self.category_list.setCurrentItem(default_category_item)
                        self.show_category_entries(default_category_item)

            dialog.accept()
        else:
            QMessageBox.warning(self, '警告', '请填写所有字段！')

    def generate_unique_name(self, name):
        # Generate a unique identifier for the name
        if name not in self.entries:
            return name

        index = 1
        while f"{name}_{index}" in self.entries:
            index += 1

        return f"{name}_{index}"

    def add_category(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('添加分组')

        category_label = QLabel('分组名:', dialog)
        category_input = QLineEdit(dialog)

        save_button = QPushButton('保存', dialog)
        save_button.clicked.connect(lambda: self.save_new_category(category_input.text(), dialog))

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(category_label)
        dialog_layout.addWidget(category_input)
        dialog_layout.addWidget(save_button)

        dialog.setLayout(dialog_layout)
        dialog.exec_()

    def save_new_category(self, category, dialog):
        if category and category not in self.categories:
            self.categories[category] = []
            self.category_list.addItem(category)
            self.save_entries()
            dialog.accept()
        else:
            QMessageBox.warning(self, '警告', '请填写分组名，且不能重复！')

    def update_category_list(self):
        self.category_list.clear()
        self.category_list.addItem("全部")
        self.category_list.addItem("未分组")
        for category in sorted(self.categories.keys()):
            if category not in ["全部", "未分组"]:
                self.category_list.addItem(category)

    def show_category_entries(self, item):
        self.entry_list.clear()
        if item is None:
            return

        self.entry_list.clear()
        selected_category = item.text()

        if selected_category == "全部":
            entries_to_show = list(self.entries.keys())
        else:
            entries_to_show = self.categories[selected_category]

        for name in entries_to_show:
            if name in self.entries:
                account, password = self.entries[name]
                item = QListWidgetItem(f"{name}  {account}")  # 调整显示格式
                # item = QListWidgetItem(f"名称：{name}  账号：{account}")  # 调整显示格式
                self.entry_list.addItem(item)

    def export_entries(self):
        try:
            path, _ = QFileDialog.getSaveFileName(self, "导出账户信息", "PassWords.xlsx", "Excel Files (*.xlsx)")
            if path:
                # all_data = []
                data = []

                for category, names in self.categories.items():
                    for name in names:
                        account, password = self.entries.get(name, ('', ''))
                        # if category == "全部":
                        #     all_data.append((category, name, account, password))
                        # else:
                        #     other_data.append((category, name, account, password))
                        if category != "全部":
                            data.append((category, name, account, password))
                            # all_data.append((category, name, account, password))

                with pd.ExcelWriter(path) as writer:
                    df_all = pd.DataFrame(data, columns=['分组', '名称', '账号', '密码'])
                    df_all.to_excel(writer, sheet_name='账号列表', index=False)

                    # if all_data:
                        # df_other = pd.DataFrame(all_data, columns=['分组', '名称', '账号', '密码'])
                        # df_other.to_excel(writer, sheet_name='全部账号', index=False)

                QMessageBox.information(self, '导出成功', f'账户信息已成功导出到 {path}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导出过程中出现错误：{str(e)}')

    def search_entry(self):
        query = self.search_input.text().strip()
        if query:
            found_entries = []
            for name, (account, password) in self.entries.items():
                if query.lower() in name.lower() or query.lower() in account.lower():
                    found_entries.append((name, account, password))

            if found_entries:
                self.entry_list.clear()

                # 添加不可点击的“查询结果”项目
                result_item = QListWidgetItem("查询结果")
                result_item.setFlags(result_item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
                result_item.setTextAlignment(Qt.AlignCenter)
                self.entry_list.addItem(result_item)

                for name, account, password in found_entries:
                    category = self.get_key(name)
                    item = QListWidgetItem(f"{category}  {name}  {account}")  # 调整显示格式
                    self.entry_list.addItem(item)
            else:
                QMessageBox.warning(self, '未找到', '未找到包含查询字符串的账户信息')
        else:
            QMessageBox.warning(self, '警告', '请输入查询字符串')

    def copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def get_key(self, value):
        for dic in self.categories:
            if value in self.categories[dic] and dic != "全部":
                return dic
        return "未分组"

    def show_entry_details(self, item):
        try:
            if not (item.flags() & Qt.ItemIsSelectable):
                return
            # 从 item 中提取名称和账号
            name_account = item.text().split('  ')  # 根据两个空格分割
            if len(name_account) == 2:
                name = name_account[0]
            elif len(name_account) == 3:
                name = name_account[1]

            category = self.get_key(name)

            if name in self.entries:
                account, password = self.entries[name]

                dialog = QDialog(self)
                dialog.setWindowTitle(f"{category}：{name}")
                dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)

                container = QVBoxLayout()

                layoutv = QVBoxLayout()
                layouth1 = QHBoxLayout()
                layouth2 = QHBoxLayout()

                account_label = QLabel(f'账号: {account}')
                layouth1.addWidget(account_label)
                # layoutv.addWidget(account_label)

                password_label = QLabel(f'密码: {password}')
                layouth2.addWidget(password_label)
                # layoutv.addWidget(password_label)
                copy_account_button = QToolButton()
                copy_account_button.setIcon(QIcon('ico/copy.ico'))  # 设置复制图标
                copy_account_button.setToolTip('复制账号')
                copy_account_button.setCursor(QCursor(Qt.PointingHandCursor))
                copy_account_button.clicked.connect(lambda: self.copy_to_clipboard(account))
                layouth1.addWidget(copy_account_button)
                layoutv.addLayout(layouth1)

                copy_password_button = QToolButton()
                copy_password_button.setIcon(QIcon('ico/copy.ico'))  # 设置复制图标
                copy_password_button.setToolTip('复制密码')
                copy_password_button.setCursor(QCursor(Qt.PointingHandCursor))
                copy_password_button.clicked.connect(lambda: self.copy_to_clipboard(password))
                layouth2.addWidget(copy_password_button)
                layoutv.addLayout(layouth2)

                layouth = QHBoxLayout()

                edit_button = QPushButton('编辑')
                edit_button.clicked.connect(lambda: self.edit_entry_dialog(name, account, password, dialog))
                layouth.addWidget(edit_button)

                delete_button = QPushButton('删除')
                delete_button.clicked.connect(partial(self.delete_entry, name, dialog))
                layouth.addWidget(delete_button)

                container.addLayout(layoutv)
                container.addLayout(layouth)

                dialog.setLayout(container)
                dialog.exec_()
            else:
                QMessageBox.warning(self, '警告', '信息不存在！')
        except Exception as e:
            print(f"Error displaying entry details: {e}")
            QMessageBox.critical(self, '错误', '显示信息时出错！')

    def edit_entry_dialog(self, name, account, password, parent=None):
        dialog = QDialog(parent)
        dialog.setWindowTitle('编辑账号信息')

        current_category = self.get_key(name)

        name_label = QLabel('名称:', dialog)
        name_input = QLineEdit(name, dialog)

        account_label = QLabel('账号:', dialog)
        account_input = QLineEdit(account, dialog)

        password_label = QLabel('密码:', dialog)
        password_input = QLineEdit(password, dialog)

        category_label = QLabel('分组:', dialog)
        category_combo = QComboBox(dialog)
        category_combo.addItems(self.categories.keys())
        category_combo.setCurrentText(current_category)  # 设置当前分组为默认选项
        new_category_input = QLineEdit(dialog)
        new_category_input.setPlaceholderText('添加新的分组')

        save_button = QPushButton('保存', dialog)
        save_button.clicked.connect(lambda: self.update_entry(
            name, name_input.text(), account_input.text(), password_input.text(),
            category_combo.currentText(), new_category_input.text(), dialog))

        category_combo.currentTextChanged.connect(lambda text: new_category_input.clear() if text != "不分组" else None)

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(name_label)
        dialog_layout.addWidget(name_input)
        dialog_layout.addWidget(account_label)
        dialog_layout.addWidget(account_input)
        dialog_layout.addWidget(password_label)
        dialog_layout.addWidget(password_input)
        dialog_layout.addWidget(category_label)
        dialog_layout.addWidget(category_combo)
        dialog_layout.addWidget(new_category_input)
        dialog_layout.addWidget(save_button)

        dialog.setLayout(dialog_layout)
        dialog.exec_()

    def update_entry(self, original_name, name, account, password, category, new_category, dialog):
        if name and account and password:
            if new_category:
                category = new_category
                if category not in self.categories:
                    self.categories[category] = []
                    self.category_list.addItem(category)
            elif not category or category == "全部":
                category = "未分组"
                if category not in self.categories:
                    self.categories[category] = []
                    self.category_list.addItem(category)

            if original_name != name:
                del self.entries[original_name]
                self.remove_entry_from_categories(original_name)

            self.entries[name] = (account, password)
            old_category = self.get_key(original_name)

            if old_category:
                self.categories[old_category].remove(original_name)

            self.categories[category].append(name)

            self.update_all_category()
            self.save_entries()

            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QDialog) and widget != self and widget.windowTitle() != "添加账号" and widget.windowTitle() != "添加分组":
                    widget.close()

            # 显示更新后的条目详情页
            # if dialog and dialog.isVisible():
            item = QListWidgetItem(f"{category}  {name}  {account}")
            self.show_entry_details(item)

        else:
            QMessageBox.warning(self, '警告', '请填写所有字段！')

    def remove_entry_from_categories(self, name, category):
        if category in self.categories and name in self.categories[category]:
            self.categories[category].remove(name)

    def show_entry_menu(self, pos):
        item = self.entry_list.itemAt(pos)
        if isinstance(item, QListWidgetItem):
            menu = QMenu()
            edit_action = QAction(QIcon(r"ico\edit.ico"), '编辑', self)
            delete_action = QAction(QIcon(r"ico\delete.ico"), '删除', self)

            name = item.text().split(' ')[0]

            edit_action.triggered.connect(lambda: self.edit_entry(item))
            delete_action.triggered.connect(lambda: self.delete_entry(name))

            menu.addAction(edit_action)
            menu.addAction(delete_action)

            menu.exec_(self.entry_list.mapToGlobal(pos))

    def edit_entry(self, item):
        if isinstance(item, QListWidgetItem):
            name = item.text().split(' ')[0]
            account, password = self.entries[name]
            self.edit_entry_dialog(name, account, password)

    def delete_entry(self, name, dialog=None):
        # print(f"Deleting entry: {name}")
        # print("Before deletion:")
        # print("Entries:", self.entries)
        # print("Categories:", self.categories)

        reply = QMessageBox.question(self, '确认', f'确认删除账号信息 "{name}"？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            categories_to_update = []
            for category, entries in self.categories.items():
                while name in entries:
                    entries.remove(name)
                    categories_to_update.append(category)

            for category in categories_to_update:
                self.remove_entry_from_categories(name, category)

            del self.entries[name]  # 删除条目信息

            self.update_all_category()  # 更新所有分类列表
            self.save_entries()  # 保存更新后的条目信息
            if dialog and dialog.isVisible():
                dialog.accept()

    def show_category_menu(self, pos):
        menu = QMenu()
        rename_action = QAction(QIcon(r"ico\rename.ico"), '重命名', self)
        delete_action = QAction(QIcon(r"ico\delete.ico"), '删除', self)

        rename_action.triggered.connect(self.rename_category)
        delete_action.triggered.connect(self.delete_category)

        menu.addAction(rename_action)
        menu.addAction(delete_action)

        menu.exec_(self.category_list.mapToGlobal(pos))

    def rename_category(self):
        current_item = self.category_list.currentItem()
        if current_item is not None:
            current_text = current_item.text()
            new_text, ok = QInputDialog.getText(self, '重命名分组', '添加新的分组名:', QLineEdit.Normal, current_text)
            if ok and new_text:
                if new_text != current_text and new_text not in self.categories:
                    self.categories[new_text] = self.categories.pop(current_text)
                    current_item.setText(new_text)
                    self.save_entries()
                else:
                    QMessageBox.warning(self, '警告', '分组名不能为空且不能重复！')

    def delete_category(self):
        current_item = self.category_list.currentItem()
        if current_item is not None:
            selected_category = current_item.text()
            if selected_category in self.categories and selected_category not in ["全部", "未分组"]:
                reply = QMessageBox.question(self, '删除分组',
                                             f'确定要删除分组 "{selected_category}" 吗？',
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    # 将分组下的所有账户信息移动到 "未分组"
                    for name in self.categories[selected_category]:
                        self.categories["未分组"].append(name)
                    del self.categories[selected_category]
                    self.update_category_list()
                    self.save_entries()
                    self.show_category_entries(self.category_list.currentItem())
            else:
                QMessageBox.warning(self, '警告', '不能删除默认分组或无效的分组。')
        else:
            QMessageBox.warning(self, '警告', '未选择分组。')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PasswordManagerApp()
    ex.show()
    sys.exit(app.exec_())
