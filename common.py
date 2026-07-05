# -*- coding: utf-8 -*-
"""共通部品

日付ヘルパー・全画面の基底ウィジェット・共用ダイアログ。"""
from PyQt5.QtWidgets import (
    QWidget,
    QDialog,
    QMessageBox,
    QPushButton,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QCalendarWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout
)
from PyQt5.QtCore import Qt, QDate
import sqlite3
from db_utils import get_categories


# 年月処理の共通クラス
class DateHelper:
    @staticmethod
    def get_current_year_month():
        """現在の年月を取得"""
        current_date = QDate.currentDate()
        return current_date.year(), current_date.month()
    
    @staticmethod
    def format_year_month(year, month):
        """年月を表示用にフォーマット"""
        return f'{year}年{month}月'
    
    @staticmethod
    def get_prev_month(year, month):
        """前月の年月を取得"""
        if month == 1:
            return year - 1, 12
        else:
            return year, month - 1
    
    @staticmethod
    def get_next_month(year, month):
        """次月の年月を取得"""
        if month == 12:
            return year + 1, 1
        else:
            return year, month + 1
    
    @staticmethod
    def get_month_range(year, month):
        """指定した月の開始日と終了日を取得"""
        start_date = QDate(year, month, 1)
        end_date = QDate(year, month, start_date.daysInMonth())
        return start_date, end_date
    
    @staticmethod
    def get_month_range_str(year, month):
        """指定した月の日付範囲をSQLクエリ用に取得"""
        start_date, end_date = DateHelper.get_month_range(year, month)
        return start_date.toString('yyyy-MM-dd'), end_date.toString('yyyy-MM-dd')
    
    @staticmethod
    def get_months_between(start_year, start_month, end_year, end_month):
        """指定した範囲の年月リストを取得"""
        months = []
        current_date = QDate(start_year, start_month, 1)
        end_date = QDate(end_year, end_month, 1)
        
        while current_date <= end_date:
            months.append((current_date.year(), current_date.month()))
            current_date = current_date.addMonths(1)
        
        return months
    
    @staticmethod
    def get_last_n_months(n, end_year=None, end_month=None):
        """直近n月分の年月リストを取得"""
        if end_year is None or end_month is None:
            end_year, end_month = DateHelper.get_current_year_month()
        
        end_date = QDate(end_year, end_month, 1)
        start_date = end_date.addMonths(-(n-1))  # n-1ヶ月前
        
        return DateHelper.get_months_between(
            start_date.year(), start_date.month(),
            end_date.year(), end_date.month()
        )


class BaseWidget(QWidget):
    """共通機能を持つ基底ウィジェット"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_navigation_buttons()
        
    def setup_navigation_buttons(self):
        """ナビゲーションボタンを設定"""
        self.button_layout = QHBoxLayout()
        
        # ボタンの作成
        self.income_expense_button = QPushButton('入出金')
        self.breakdown_button = QPushButton('収支内訳')
        self.monthly_report_button = QPushButton('月次収支')
        self.goal_management_button = QPushButton('目標管理')
        self.diagnostic_report_button = QPushButton('診断レポート')
        self.comprehensive_analysis_button = QPushButton('全データ分析')  # ←追加
        self.asset_management_button = QPushButton('資産管理')  # ←追加
        
        # ボタンをレイアウトに追加
        buttons = [
            self.income_expense_button,
            self.breakdown_button,
            self.monthly_report_button,
            self.goal_management_button,
            self.diagnostic_report_button,
            self.comprehensive_analysis_button,
            self.asset_management_button
        ]
        
        for button in buttons:
            self.button_layout.addWidget(button)
            


class YearMonthDialog(QDialog):
    """年月選択ダイアログ"""
    def __init__(self, parent=None):
        """YearMonthDialogの初期化メソッド。
        ウィンドウタイトルを設定し、UIを構築します。
        Args:
            parent (QWidget, optional): 親ウィジェット。デフォルトはNone。"""
        super().__init__(parent)
        self.setWindowTitle('年月選択')
        self.initUI()
        
    def initUI(self):
        """
        ダイアログのUI要素（カレンダーとボタン）を配置します。
        """
        layout = QVBoxLayout()
        
        # 1. カレンダーウィジェットを配置
        self.calendar = QCalendarWidget()
        layout.addWidget(self.calendar)
        
        # 2. OK/キャンセルボタンのレイアウト
        button_layout = QHBoxLayout()
        ok_button = QPushButton('OK')
        cancel_button = QPushButton('キャンセル')
        
        # OKボタンがクリックされたらダイアログを accept (結果を返す)
        ok_button.clicked.connect(self.accept)

        # キャンセルボタンがクリックされたらダイアログを reject (キャンセル)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)


class EditableTableItem(QTableWidgetItem):
    def __init__(self, text, editable=True):
        super().__init__(text)
        if not editable:
            self.setFlags(self.flags() & ~Qt.ItemIsEditable)  


class RecurringExpenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('定期支払い管理')
        self.setModal(True)
        self.initUI()
        self.load_recurring_expenses()

    def initUI(self):
        layout = QVBoxLayout()

        # 定期支払い一覧
        self.expense_table = QTableWidget(0, 5)
        self.expense_table.setHorizontalHeaderLabels(['カテゴリ', '金額', '説明', '支払日', '状態'])
        self.expense_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.expense_table)

        # 入力フォーム
        form_layout = QFormLayout()
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(get_categories())

        self.amount_input = QLineEdit()
        self.description_input = QLineEdit()
        self.payment_day_input = QSpinBox()
        self.payment_day_input.setRange(1, 31)
        
        form_layout.addRow('カテゴリ:', self.category_combo)
        form_layout.addRow('金額:', self.amount_input)
        form_layout.addRow('説明:', self.description_input)
        form_layout.addRow('支払日:', self.payment_day_input)
        
        layout.addLayout(form_layout)

        # ボタン
        button_layout = QHBoxLayout()
        add_button = QPushButton('追加')
        add_button.clicked.connect(self.add_recurring_expense)
        delete_button = QPushButton('削除')
        delete_button.clicked.connect(self.delete_recurring_expense)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_recurring_expenses(self):
        """定期支払いの一覧を読み込む"""
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        c.execute('SELECT id, category, amount, description, payment_day, is_active FROM recurring_expenses')
        expenses = c.fetchall()
        conn.close()

        self.expense_table.setRowCount(len(expenses))
        for row, expense in enumerate(expenses):
            _, category, amount, description, payment_day, is_active = expense
            
            self.expense_table.setItem(row, 0, QTableWidgetItem(category))
            self.expense_table.setItem(row, 1, QTableWidgetItem(f"{amount:,.0f}"))
            self.expense_table.setItem(row, 2, QTableWidgetItem(description))
            self.expense_table.setItem(row, 3, QTableWidgetItem(str(payment_day)))
            self.expense_table.setItem(row, 4, QTableWidgetItem('有効' if is_active else '無効'))

    def add_recurring_expense(self):
        """定期支払いを追加"""
        try:
            amount = float(self.amount_input.text().replace(',', ''))
            if amount <= 0:
                raise ValueError("金額は正の数を入力してください")
            
            category = self.category_combo.currentText()
            description = self.description_input.text()
            payment_day = self.payment_day_input.value()
            
            conn = sqlite3.connect('budget.db')
            try:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO recurring_expenses
                    (category, amount, description, payment_day)
                    VALUES (?, ?, ?, ?)
                ''', (category, amount, description, payment_day))
                conn.commit()
            except Exception:
                conn.rollback()  # 保存に失敗したら書きかけを取り消す
                raise            # 下のexceptでユーザーに通知する
            finally:
                conn.close()     # 成功・失敗にかかわらず必ず接続を閉じる

            self.load_recurring_expenses()
            self.amount_input.clear()
            self.description_input.clear()

        except ValueError as e:
            QMessageBox.warning(self, '警告', str(e))
        except Exception as e:
            # DBエラーなど入力ミス以外の失敗もユーザーに知らせる
            QMessageBox.critical(self, 'エラー', f'定期支払いの保存に失敗しました: {e}')
            
    def delete_recurring_expense(self):
        """選択された定期支払いを削除"""
        selected_rows = self.expense_table.selectedItems()
        if not selected_rows:
            return
            
        reply = QMessageBox.question(
            self, '確認', 
            '選択した定期支払いを削除してもよろしいですか？',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            row = selected_rows[0].row()
            category = self.expense_table.item(row, 0).text()
            amount = float(self.expense_table.item(row, 1).text().replace(',', ''))
            payment_day = int(self.expense_table.item(row, 3).text())
            
            conn = sqlite3.connect('budget.db')
            try:
                c = conn.cursor()
                c.execute('''
                    DELETE FROM recurring_expenses
                    WHERE category = ? AND amount = ? AND payment_day = ?
                ''', (category, amount, payment_day))
                conn.commit()
            except Exception as e:
                conn.rollback()  # 削除に失敗したら取り消す
                QMessageBox.critical(self, 'エラー', f'定期支払いの削除に失敗しました: {e}')
                return
            finally:
                conn.close()     # 必ず接続を閉じる

            self.load_recurring_expenses()
