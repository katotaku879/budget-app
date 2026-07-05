# -*- coding: utf-8 -*-
"""カテゴリ管理ダイアログ

カテゴリの追加・編集・削除・並び替え。"""
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QMessageBox,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox,
    QDateEdit, QCalendarWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QFrame,
    QScrollArea, QStackedWidget, QTabWidget, QListWidget, QListWidgetItem,
    QAction, QFileDialog, QDialogButtonBox, QProgressBar, QProgressDialog,
    QSizePolicy, QSpacerItem, QInputDialog
)
from PyQt5.QtCore import Qt, QDate, QMargins, QPointF
from PyQt5.QtGui import QFont, QColor, QPen, QBrush
import sqlite3
from db_utils import get_db_connection, execute_query, get_categories, execute_many, fetch_df


class CategoryManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('カテゴリ管理')
        self.setMinimumWidth(400)
        self.initUI()
        self.load_categories()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # カテゴリリスト
        self.category_table = QTableWidget(0, 3)
        self.category_table.setHorizontalHeaderLabels(['カテゴリ名', '表示順', 'デフォルト'])
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.category_table)
        
        # 新規カテゴリ追加エリア
        form_layout = QHBoxLayout()
        self.new_category_input = QLineEdit()
        self.new_category_input.setPlaceholderText('新規カテゴリ名')
        
        add_button = QPushButton('追加')
        add_button.clicked.connect(self.add_category)
        
        form_layout.addWidget(self.new_category_input)
        form_layout.addWidget(add_button)
        layout.addLayout(form_layout)
        
        # ボタン配置
        button_layout = QHBoxLayout()
        
        edit_button = QPushButton('編集')
        edit_button.clicked.connect(self.edit_category)
        
        delete_button = QPushButton('削除')
        delete_button.clicked.connect(self.delete_category)
        
        move_up_button = QPushButton('↑')
        move_up_button.clicked.connect(lambda: self.move_category(-1))
        
        move_down_button = QPushButton('↓')
        move_down_button.clicked.connect(lambda: self.move_category(1))
        
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(move_up_button)
        button_layout.addWidget(move_down_button)
        layout.addLayout(button_layout)
        
        # OKボタン
        close_button = QPushButton('閉じる')
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
    
    def load_categories(self):
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        c.execute('SELECT id, name, sort_order, is_default FROM categories ORDER BY sort_order')
        
        categories = c.fetchall()
        conn.close()
        
        self.category_table.setRowCount(len(categories))
        
        for row, category in enumerate(categories):
            category_id, name, sort_order, is_default = category
            
            # ID情報を非表示データとして保存
            id_item = QTableWidgetItem(str(category_id))
            self.category_table.setItem(row, 0, QTableWidgetItem(name))
            self.category_table.setItem(row, 1, QTableWidgetItem(str(sort_order)))
            
            # デフォルトカテゴリかどうかをチェックボックスで表示
            checkbox = QCheckBox()
            checkbox.setChecked(bool(is_default))
            checkbox.setEnabled(False)  # 編集不可（デフォルトカテゴリは削除不可にする）
            self.category_table.setCellWidget(row, 2, checkbox)
            
            # 非表示の項目にIDを保存
            self.category_table.item(row, 0).setData(Qt.UserRole, category_id)
    
    def add_category(self):
        category_name = self.new_category_input.text().strip()
        if not category_name:
            QMessageBox.warning(self, '警告', 'カテゴリ名を入力してください')
            return
        
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        try:
            # 現在の最大表示順を取得
            c.execute('SELECT MAX(sort_order) FROM categories')
            max_order = c.fetchone()[0]
            if max_order is None:
                max_order = 0
            
            # 新しいカテゴリを追加
            c.execute('INSERT INTO categories (name, sort_order) VALUES (?, ?)', 
                     (category_name, max_order + 1))
            conn.commit()
            
            self.new_category_input.clear()
            self.load_categories()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, '警告', f'カテゴリ「{category_name}」は既に存在します')
        finally:
            conn.close()
    
    def edit_category(self):
        selected_items = self.category_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', 'カテゴリを選択してください')
            return
        
        row = selected_items[0].row()
        current_name = self.category_table.item(row, 0).text()
        category_id = self.category_table.item(row, 0).data(Qt.UserRole)
        
        # デフォルトカテゴリは編集不可
        checkbox = self.category_table.cellWidget(row, 2)
        if checkbox.isChecked():
            QMessageBox.warning(self, '警告', 'デフォルトカテゴリは編集できません')
            return
        
        new_name, ok = QInputDialog.getText(
            self, 'カテゴリ編集', 'カテゴリ名:', text=current_name
        )
        
        if ok and new_name.strip():
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            
            try:
                c.execute('UPDATE categories SET name = ? WHERE id = ?', 
                         (new_name, category_id))
                conn.commit()
                self.load_categories()
                
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, '警告', f'カテゴリ「{new_name}」は既に存在します')
            finally:
                conn.close()
    
    def delete_category(self):
        selected_items = self.category_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', 'カテゴリを選択してください')
            return
        
        row = selected_items[0].row()
        category_name = self.category_table.item(row, 0).text()
        category_id = self.category_table.item(row, 0).data(Qt.UserRole)
        
        # デフォルトカテゴリは削除不可
        checkbox = self.category_table.cellWidget(row, 2)
        if checkbox.isChecked():
            QMessageBox.warning(self, '警告', 'デフォルトカテゴリは削除できません')
            return
        
        # 確認ダイアログ
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        # このカテゴリを使用しているデータがあるか確認
        c.execute('SELECT COUNT(*) FROM expenses WHERE category = ?', (category_name,))
        usage_count = c.fetchone()[0]
        
        if usage_count > 0:
            reply = QMessageBox.question(
                self, '確認', 
                f'このカテゴリは{usage_count}件のデータで使用されています。\n'
                f'削除するとこれらのデータは「その他」カテゴリに変更されます。\n\n'
                f'カテゴリ「{category_name}」を削除しますか？',
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
        else:
            reply = QMessageBox.question(
                self, '確認', 
                f'カテゴリ「{category_name}」を削除しますか？',
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
        
        if reply == QMessageBox.Yes:
            try:
                # 関連データを「その他」カテゴリに変更
                if usage_count > 0:
                    c.execute('UPDATE expenses SET category = "その他" WHERE category = ?',
                             (category_name,))
                
                # カテゴリを削除
                c.execute('DELETE FROM categories WHERE id = ?', (category_id,))
                conn.commit()
                
                self.load_categories()
                
                if usage_count > 0:
                    QMessageBox.information(
                        self, '完了', 
                        f'{usage_count}件のデータが「その他」カテゴリに変更されました。'
                    )
                
            except Exception as e:
                QMessageBox.critical(self, 'エラー', f'削除中にエラーが発生しました: {e}')
            finally:
                conn.close()
    
    def move_category(self, direction):
        selected_items = self.category_table.selectedItems()
        if not selected_items:
            return
            
        row = selected_items[0].row()
        
        # 移動先が範囲外なら何もしない
        if (row == 0 and direction < 0) or (row == self.category_table.rowCount() - 1 and direction > 0):
            return
            
        target_row = row + direction
        
        # 現在の行と移動先の行のIDと順序を取得
        current_id = self.category_table.item(row, 0).data(Qt.UserRole)
        target_id = self.category_table.item(target_row, 0).data(Qt.UserRole)
        
        current_order = int(self.category_table.item(row, 1).text())
        target_order = int(self.category_table.item(target_row, 1).text())
        
        # データベースで順序を入れ替え
        conn = sqlite3.connect('budget.db')
        try:
            c = conn.cursor()

            c.execute('UPDATE categories SET sort_order = ? WHERE id = ?', (target_order, current_id))
            c.execute('UPDATE categories SET sort_order = ? WHERE id = ?', (current_order, target_id))

            # 2つのUPDATEが両方成功したときだけ確定する
            conn.commit()
        except Exception as e:
            conn.rollback()  # 片方だけ入れ替わった中途半端な状態を防ぐ
            QMessageBox.critical(self, 'エラー', f'カテゴリの並び替えに失敗しました: {e}')
            return
        finally:
            conn.close()     # 必ず接続を閉じる

        # テーブル表示を更新
        self.load_categories()
        
        # 選択状態を移動先の行に移す
        self.category_table.selectRow(target_row)
