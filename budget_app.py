# PyQt5 ウィジェット
from PyQt5.QtWidgets import (
    # アプリケーション/ウィンドウの基本クラス
    QApplication, QMainWindow, QWidget, QDialog, QMessageBox,
    
    # 基本的な入力ウィジェット
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox,
    
    # 日付関連ウィジェット
    QDateEdit, QCalendarWidget,
    
    # テーブル関連ウィジェット
    QTableWidget, QTableWidgetItem, QHeaderView,
    
    # レイアウト管理クラス
    QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QFrame,
    
    # コンテナ/ナビゲーションウィジェット
    QScrollArea, QStackedWidget, QTabWidget, QListWidget, QListWidgetItem,
    
    # メニュー/ダイアログ関連
    QAction, QFileDialog, QDialogButtonBox, QProgressBar, QProgressDialog,
    
    # レイアウト調整/その他
    QSizePolicy, QSpacerItem, QColorDialog, QInputDialog
)

# PyQt5 コアとグラフィック
from PyQt5.QtCore import Qt, QDate, QMargins, QPointF
from PyQt5.QtGui import QFont, QColor, QIcon, QPen

# PyQt5 チャート関連
from PyQt5.QtChart import (
    QChart, QChartView, QPieSeries, QPieSlice, QBarSeries, 
    QBarSet, QValueAxis, QBarCategoryAxis, QLineSeries
)

# その他のライブラリ
import sqlite3
import pandas as pd
import numpy as np
import os
import sys
import shutil
import time
from datetime import datetime, timedelta

# データベースユーティリティ関数
def get_db_connection():
    """データベース接続を取得"""
    return sqlite3.connect('budget.db')

def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    """SQLクエリを実行し、必要に応じて結果を取得"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(query, params)
    
    result = None
    if fetch_one:
        result = c.fetchone()
    elif fetch_all:
        result = c.fetchall()
        
    conn.commit()
    conn.close()
    return result

def execute_many(query, param_list):
    """複数のクエリを一括実行"""
    conn = get_db_connection()
    c = conn.cursor()
    c.executemany(query, param_list)
    conn.commit()
    conn.close()

def fetch_df(query, params=()):
    """SQLクエリを実行し、結果をPandasのDataFrameとして取得"""
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

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
        self.savings_goal_button = QPushButton('貯金目標')
        self.ai_advisor_button = QPushButton('AIアドバイザー')
        self.diagnostic_report_button = QPushButton('診断レポート')
        self.comprehensive_analysis_button = QPushButton('全データ分析')  # ←追加
        
        # ボタンをレイアウトに追加
        buttons = [
            self.income_expense_button,
            self.breakdown_button,
            self.monthly_report_button,
            self.goal_management_button,
            self.savings_goal_button,
            self.ai_advisor_button,
            self.diagnostic_report_button,
            self.comprehensive_analysis_button  # ←追加
        ]
        
        for button in buttons:
            self.button_layout.addWidget(button)
            
    def connect_navigation_buttons(self, stacked_widget):
        """ボタンのクリックイベントを接続"""
        widgets = {
            'income_expense': self.income_expense_button,
            'breakdown': self.breakdown_button,
            'monthly_report': self.monthly_report_button,
            'goal_management': self.goal_management_button,
            'savings_goal': self.savings_goal_button,
            'ai_advisor': self.ai_advisor_button,
            'diagnostic_report': self.diagnostic_report_button
        }
        
        for name, button in widgets.items():
            widget = getattr(self.parent, f"{name}_widget", None)
            if widget:
                button.clicked.connect(lambda checked, w=widget: stacked_widget.setCurrentWidget(w))

class YearMonthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('年月選択')
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        self.calendar = QCalendarWidget()
        layout.addWidget(self.calendar)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton('OK')
        cancel_button = QPushButton('キャンセル')
        
        ok_button.clicked.connect(self.accept)
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
        self.category_combo.addItems([
            '食費', '交通費', '娯楽', 'その他', '住宅', 
            '水道光熱費', '美容', '通信費', '日用品', '健康', '教育'
        ])
        
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
            c = conn.cursor()
            c.execute('''
                INSERT INTO recurring_expenses 
                (category, amount, description, payment_day)
                VALUES (?, ?, ?, ?)
            ''', (category, amount, description, payment_day))
            conn.commit()
            conn.close()
            
            self.load_recurring_expenses()
            self.amount_input.clear()
            self.description_input.clear()
            
        except ValueError as e:
            QMessageBox.warning(self, '警告', str(e))
            
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
            c = conn.cursor()
            c.execute('''
                DELETE FROM recurring_expenses 
                WHERE category = ? AND amount = ? AND payment_day = ?
            ''', (category, amount, payment_day))
            conn.commit()
            conn.close()
            
            self.load_recurring_expenses()                  

class BudgetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_database()
        # self.initUI()  # 古いメソッドをコメントアウト
        
        # バックアップマネージャーの初期化
        self.backup_manager = BackupManager()
        
        self.enhanced_init_ui()  # 新しいメソッドを呼び出す
        
        # 定期支払いの処理をアプリケーション起動時にも実行
        widget = self.income_expense_widget
        if hasattr(widget, 'process_recurring_expenses'):
            widget.process_recurring_expenses()

        # 目標データを読み込む（追加）
        if hasattr(self, 'goal_management_widget'):
            self.goal_management_widget.load_goals()    
        
        # アプリ起動時の自動バックアップ
        self.check_auto_backup()

    def closeEvent(self, event):
            """アプリケーション終了時の処理"""
            # 未保存のデータがあれば保存する処理を追加
            if hasattr(self, 'goal_management_widget'):
                # 必要に応じて保存メソッドを呼び出す
                # self.goal_management_widget.save_goals()
                pass
            
            # 親クラスのcloseEventを呼び出す
            super().closeEvent(event)


    def initUI(self):
        self.setWindowTitle('家計簿アプリ')
        self.setGeometry(100, 100, 800, 600)
        
        # メインウィジェットとしてQStackedWidgetを使用
        self.stacked_widget = QStackedWidget()
        
        # 各画面のウィジェットを作成
        self.income_expense_widget = IncomeExpenseWidget(self)
        self.breakdown_widget = BreakdownWidget(self)
        self.monthly_report_widget = MonthlyReportWidget(self)
        
        # StackedWidgetに各画面を追加
        self.stacked_widget.addWidget(self.income_expense_widget)
        self.stacked_widget.addWidget(self.breakdown_widget)
        self.stacked_widget.addWidget(self.monthly_report_widget)
        
        # ボタンのクリックイベントを接続
        self.income_expense_widget.income_expense_button.clicked.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.income_expense_widget)
        )
        self.income_expense_widget.breakdown_button.clicked.connect(
            lambda: self.switch_to_breakdown()
        )
        self.income_expense_widget.monthly_report_button.clicked.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.monthly_report_widget)
        )
        
        self.breakdown_widget.income_expense_button.clicked.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.income_expense_widget)
        )
        self.breakdown_widget.breakdown_button.clicked.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.breakdown_widget)
        )
        self.breakdown_widget.monthly_report_button.clicked.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.monthly_report_widget)
        )
        
        self.monthly_report_widget.income_expense_button.clicked.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.income_expense_widget)
        )
        self.monthly_report_widget.breakdown_button.clicked.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.breakdown_widget)
        )
        self.monthly_report_widget.monthly_report_button.clicked.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.monthly_report_widget)
        )
        
        self.setCentralWidget(self.stacked_widget)

        # メニューバーを追加
        menubar = self.menuBar()
        file_menu = menubar.addMenu('ファイル')
        
        # バックアップメニュー
        backup_menu = file_menu.addMenu('バックアップ')
        
        # 新規バックアップ作成
        create_backup_action = QAction('バックアップを作成', self)
        create_backup_action.triggered.connect(self.create_backup)
        backup_menu.addAction(create_backup_action)
        
        # バックアップ管理
        manage_backup_action = QAction('バックアップを管理', self)
        manage_backup_action.triggered.connect(self.show_backup_manager)
        backup_menu.addAction(manage_backup_action)
        
        # バックアップ設定
        backup_settings_action = QAction('バックアップ設定', self)
        backup_settings_action.triggered.connect(self.show_backup_settings)
        backup_menu.addAction(backup_settings_action)

    def switch_to_breakdown(self):
        self.breakdown_widget.update_display()
        self.stacked_widget.setCurrentWidget(self.breakdown_widget)

    def init_database(self):
        
        # 既存のexpensesテーブル作成
        execute_query('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT
            )
        ''')
        
        # 月次収入テーブルの作成
        execute_query('''
            CREATE TABLE IF NOT EXISTS monthly_income (
                year INTEGER,
                month INTEGER,
                income REAL NOT NULL,
                PRIMARY KEY (year, month)
            )
        ''')
        
        # 定期支払いテーブルの作成
        execute_query('''
            CREATE TABLE IF NOT EXISTS recurring_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                payment_day INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        # 新しいテーブル：カテゴリ別予算目標
        execute_query('''
            CREATE TABLE IF NOT EXISTS category_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                month INTEGER,
                category TEXT NOT NULL,
                goal_amount REAL NOT NULL,
                UNIQUE(year, month, category)
            )
        ''')
    
        # 新しいテーブル：全体目標（貯蓄目標など）
        execute_query('''
            CREATE TABLE IF NOT EXISTS monthly_goals (
                year INTEGER,
                month INTEGER,
                savings_goal REAL NOT NULL DEFAULT 0,
                expense_limit REAL,
                PRIMARY KEY (year, month)
            )
        ''')
        
        # クレジットカード明細のインポート履歴テーブル（オプション）
        execute_query('''
            CREATE TABLE IF NOT EXISTS credit_card_imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_date TEXT NOT NULL,
                file_name TEXT NOT NULL,
                format_name TEXT NOT NULL,
                record_count INTEGER NOT NULL
            )
        ''')

        # カテゴリテーブルの作成
        execute_query('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                sort_order INTEGER DEFAULT 0,
                is_default BOOLEAN DEFAULT 0
            )
        ''')

        # デフォルトカテゴリの追加（まだデータがない場合）
        category_count = execute_query('SELECT COUNT(*) FROM categories', fetch_one=True)
        if category_count[0] == 0:
            default_categories = [
                ('食費', 0, 1), 
                ('交通費', 1, 1), 
                ('娯楽', 2, 1), 
                ('住宅', 3, 1),
                ('水道光熱費', 4, 1), 
                ('美容', 5, 1), 
                ('通信費', 6, 1), 
                ('日用品', 7, 1), 
                ('健康', 8, 1), 
                ('教育', 9, 1),
                ('その他', 10, 1)
            ]
            execute_many(
                'INSERT INTO categories (name, sort_order, is_default) VALUES (?, ?, ?)', 
                default_categories
            )

    # 貯金目標テーブルの作成
        execute_query('''
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                start_date TEXT NOT NULL,
                target_date TEXT,
                description TEXT,
                color TEXT DEFAULT '#4CAF50',
                is_completed BOOLEAN DEFAULT 0
            )
        ''')
        
        # 貯金履歴テーブルの作成
        execute_query('''
            CREATE TABLE IF NOT EXISTS savings_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (goal_id) REFERENCES savings_goals(id)
            )
        ''')

    def enhanced_init_ui(self):
        self.setWindowTitle('家計簿アプリ')
        self.setGeometry(100, 100, 900, 700)
        
        # メインウィジェットとしてQStackedWidgetを使用
        self.stacked_widget = QStackedWidget()
        
        # ウィジェット情報の定義
        widget_classes = {
            'income_expense': IncomeExpenseWidget,
            'breakdown': BreakdownWidget,
            'monthly_report': MonthlyReportWidget,
            'goal_management': GoalManagementWidget,
            'diagnostic_report': DiagnosticReportWidget,
            'savings_goal': SavingsGoalWidget,
            'ai_advisor': AIExpenseAdvisorWidget,
            'comprehensive_analysis': ComprehensiveAnalysisWidget  # ←追加
        }

        # ウィジェットの作成と追加を同時に行う
        for name, widget_class in widget_classes.items():
            widget = widget_class(self)
            setattr(self, f"{name}_widget", widget)  # self.name_widget = widget の動的版
            self.stacked_widget.addWidget(widget)

        self.widgets = {
            'income_expense': self.income_expense_widget,
            'breakdown': self.breakdown_widget,
            'monthly_report': self.monthly_report_widget,
            'goal_management': self.goal_management_widget,
            'diagnostic_report': self.diagnostic_report_widget,
            'savings_goal': self.savings_goal_widget,
            'ai_advisor': self.ai_advisor_widget,
            'comprehensive_analysis': self.comprehensive_analysis_widget  # ←追加
        }

        # ナビゲーションボタンを接続
        self.connect_navigation_buttons()
        
        # 目標達成状況表示を入出金画面に追加
        self.income_expense_widget.add_goal_progress_to_income_expense()
        
        
        # 目標データを読み込む
        if hasattr(self, 'goal_management_widget'):
            self.goal_management_widget.load_goals()
        
        # 入出金画面の目標進捗を更新
        if hasattr(self, 'income_expense_widget') and hasattr(self.income_expense_widget, 'update_goal_progress'):
            self.income_expense_widget.update_goal_progress()
        
        # 収支内訳画面を更新
        if hasattr(self, 'breakdown_widget') and hasattr(self.breakdown_widget, 'update_display'):
            self.breakdown_widget.update_display()
        
        # メニューバーを追加
        menubar = self.menuBar()
        file_menu = menubar.addMenu('ファイル')

        # バックアップメニュー
        backup_menu = file_menu.addMenu('バックアップ')

        category_action = QAction('カテゴリ管理', self)
        category_action.triggered.connect(self.show_category_management)
        file_menu.addAction(category_action)

        # 新規バックアップ作成
        create_backup_action = QAction('バックアップを作成', self)
        create_backup_action.triggered.connect(self.create_backup)
        backup_menu.addAction(create_backup_action)

        # バックアップ管理
        manage_backup_action = QAction('バックアップを管理', self)
        manage_backup_action.triggered.connect(self.show_backup_manager)
        backup_menu.addAction(manage_backup_action)

        # バックアップ設定
        backup_settings_action = QAction('バックアップ設定', self)
        backup_settings_action.triggered.connect(self.show_backup_settings)
        backup_menu.addAction(backup_settings_action)


        self.setCentralWidget(self.stacked_widget)

    def connect_navigation_buttons(self):
        """各ウィジェットのナビゲーションボタンを接続する"""
        # ウィジェットリストの作成
        widget_dict = {
            'income_expense': self.income_expense_widget,
            'breakdown': self.breakdown_widget,
            'monthly_report': self.monthly_report_widget,
            'goal_management': self.goal_management_widget,
            'diagnostic_report': self.diagnostic_report_widget,
            'savings_goal': self.savings_goal_widget,
            'ai_advisor': self.ai_advisor_widget,
            'comprehensive_analysis': self.comprehensive_analysis_widget  # ←追加
        }
        
        # ボタン名とターゲットウィジェットのマッピング
        button_targets = {
            'income_expense_button': self.income_expense_widget,
            'breakdown_button': self.breakdown_widget,
            'monthly_report_button': self.monthly_report_widget,
            'goal_management_button': self.goal_management_widget,
            'diagnostic_report_button': self.diagnostic_report_widget,
            'savings_goal_button': self.savings_goal_widget,
            'ai_advisor_button': self.ai_advisor_widget,
            'comprehensive_analysis_button': self.comprehensive_analysis_widget  # ←追加
        }
        
        # 各ウィジェットについて処理
        for widget in widget_dict.values():
            # 各ボタンについて処理
            for button_name, target_widget in button_targets.items():
                # ウィジェットが対応するボタン属性を持っていれば接続
                if hasattr(widget, button_name):
                    button = getattr(widget, button_name)
                    # 遷移ロジック（lambdaで遅延評価）
                    button.clicked.connect(
                        lambda checked=False, w=target_widget: self.stacked_widget.setCurrentWidget(w)
                    )

        # breakdownウィジェットへの特別な遷移処理（updateが必要な場合）
        if hasattr(self, 'income_expense_widget') and hasattr(self, 'breakdown_widget'):
            self.income_expense_widget.breakdown_button.clicked.connect(
                lambda: self.switch_to_breakdown()
            )

    def add_button_to_layout(self, widget, button):
        """ウィジェットのレイアウトにボタンを安全に追加する"""
        try:
            if hasattr(widget, 'layout') and widget.layout() is not None:
                # まずメインレイアウトを試す
                widget.layout().addWidget(button)
            elif hasattr(widget, 'diagnostic_report_button'):
                # 既存のボタンがあるレイアウトを探す
                try:
                    button_layout = widget.layout().itemAt(0).layout()
                    if button_layout is not None:
                        button_layout.addWidget(button)
                except:
                    # 失敗した場合は警告を出すだけにする
                    print(f"Warning: Could not add button to {type(widget).__name__}")
        except Exception as e:
            print(f"Error adding button to {type(widget).__name__}: {e}")    

    def create_backup(self):
        """バックアップを作成する"""
        try:
            backup_path = self.backup_manager.create_backup()
            QMessageBox.information(self, "成功", f"バックアップが正常に作成されました。\n{backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))

    def show_backup_manager(self):
        """バックアップ管理ダイアログを表示"""
        dialog = BackupManagerDialog(self.backup_manager, self)
        dialog.exec_()

    def show_backup_settings(self):
        """バックアップ設定ダイアログを表示"""
        dialog = BackupSettingsDialog(self)
        dialog.exec_()

    def check_auto_backup(self):
        """自動バックアップの実行"""
        # 実際のアプリケーションでは設定から読み込む
        auto_backup_enabled = True
        max_backups = 5
        
        if auto_backup_enabled:
            try:
                self.backup_manager.auto_backup(max_backups)
                # メッセージを表示しない（完全に自動）
            except Exception as e:
                # エラーログにのみ記録
                print(f"自動バックアップエラー: {e}")

    def show_category_management(self):
        """カテゴリ管理ダイアログを表示"""
        dialog = CategoryManagementDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # カテゴリが更新された場合、各ウィジェットのカテゴリリストを更新
            self.update_all_category_lists()

    def update_all_category_lists(self):
        """全てのウィジェットのカテゴリリストを更新"""
        # データベースから最新のカテゴリリストを取得
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        c.execute('SELECT name FROM categories ORDER BY sort_order')
        categories = [row[0] for row in c.fetchall()]
        conn.close()

    def update_goal_data_across_widgets(self):
        """目標データが更新された際に各ウィジェットの表示を更新する"""
        
        # 1. 入出金画面の目標達成状況を更新
        if hasattr(self, 'income_expense_widget') and hasattr(self.income_expense_widget, 'update_goal_progress'):
            try:
                self.income_expense_widget.update_goal_progress()
            except Exception as e:
                print(f"入出金画面の更新中にエラー: {e}")
        
        # 2. 収支内訳画面の目標関連表示を更新
        if hasattr(self, 'breakdown_widget'):
            try:
                # enhanced_update_displayがあればそれを使用、なければ通常のupdate_displayを使用
                if hasattr(self.breakdown_widget, 'enhanced_update_display'):
                    self.breakdown_widget.enhanced_update_display()
                elif hasattr(self.breakdown_widget, 'update_display'):
                    self.breakdown_widget.update_display()
            except Exception as e:
                print(f"収支内訳画面の更新中にエラー: {e}")
        
        # 3. 月次レポート画面の目標関連表示を更新
        if hasattr(self, 'monthly_report_widget'):
            try:
                # enhanced_update_report_displayがあればそれを使用、なければ通常のupdate_displayを使用
                if hasattr(self.monthly_report_widget, 'enhanced_update_report_display'):
                    self.monthly_report_widget.enhanced_update_report_display()
                elif hasattr(self.monthly_report_widget, 'update_display'):
                    self.monthly_report_widget.update_display()
            except Exception as e:
                print(f"月次レポート画面の更新中にエラー: {e}")
        
        # 4. 診断レポート画面の表示を更新
        if hasattr(self, 'diagnostic_report_widget') and hasattr(self.diagnostic_report_widget, 'generate_report'):
            try:
                self.diagnostic_report_widget.generate_report()
            except Exception as e:
                print(f"診断レポート画面の更新中にエラー: {e}")
        
        # 5. 目標管理画面自体も更新
        if hasattr(self, 'goal_management_widget'):
            try:
                self.goal_management_widget.update_display()
            except Exception as e:
                print(f"目標管理画面の更新中にエラー: {e}")

        # 各ウィジェットのカテゴリコンボボックスを更新
        if hasattr(self, 'income_expense_widget') and hasattr(self.income_expense_widget, 'category_input'):
            current_category = self.income_expense_widget.category_input.currentText()
            self.income_expense_widget.category_input.clear()
            # Retrieve categories from the database
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            c.execute('SELECT name FROM categories ORDER BY sort_order')
            categories = [row[0] for row in c.fetchall()]
            conn.close()

            # Add categories to the combo box
            self.income_expense_widget.category_input.addItems(categories)
            
            # 以前選択されていたカテゴリを再選択（存在する場合）
            index = self.income_expense_widget.category_input.findText(current_category)
            if index >= 0:
                self.income_expense_widget.category_input.setCurrentIndex(index)

class IncomeExpenseWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)  # BaseWidget の初期化
        self.current_year, self.current_month = DateHelper.get_current_year_month()
        self.initUI()
        self.load_monthly_income()      # ←この行を追加
        self.update_monthly_expense()
        self.process_recurring_expenses()

    def initUI(self):
        layout = QVBoxLayout()
        
        # BaseWidgetで作成したボタンレイアウトを追加
        layout.addLayout(self.button_layout)

        # 当月収支表示エリア
        summary_layout = QFormLayout()
        font_large = QFont()
        font_large.setPointSize(14)
        
        self.monthly_income_input = QLineEdit()
        self.monthly_income_input.setFont(font_large)
        self.monthly_expense_label = QLabel('0 円')
        self.monthly_expense_label.setFont(font_large)
        self.monthly_balance_label = QLabel('0 円')
        self.monthly_balance_label.setFont(font_large)
        
        income_label = QLabel('当月収入:')
        expense_label = QLabel('当月支出:')
        balance_label = QLabel('当月収支:')
        income_label.setFont(font_large)
        expense_label.setFont(font_large)
        balance_label.setFont(font_large)
        
        summary_layout.addRow(income_label, self.monthly_income_input)
        summary_layout.addRow(expense_label, self.monthly_expense_label)
        summary_layout.addRow(balance_label, self.monthly_balance_label)
        
        # 収入保存ボタンを追加
        self.save_income_button = QPushButton('収入を保存')
        self.save_income_button.clicked.connect(self.save_monthly_income)
        summary_layout.addRow(self.save_income_button)
        
        self.monthly_income_input.textChanged.connect(self.calculate_monthly_balance)
        layout.addLayout(summary_layout)

        # 年月選択ボタン
        self.year_month_button = QPushButton('年月選択')
        self.year_month_button.clicked.connect(self.show_year_month_dialog)
        layout.addWidget(self.year_month_button)

        # 選択された年月の表示
        self.selected_period_label = QLabel(
            f'{self.current_year}年{self.current_month}月'
        )
        layout.addWidget(self.selected_period_label)

        # 入力フォーム
        form_layout = QFormLayout()

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())
        form_layout.addRow('日付:', self.date_input)

        # 修正後: データベースからカテゴリを動的に取得
        # 正しい修正: categories変数の定義と使用
        self.category_input = QComboBox()
        try:
            # カテゴリをデータベースから取得
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            c.execute('SELECT name FROM categories ORDER BY sort_order')
            db_categories = [row[0] for row in c.fetchall()]
            conn.close()
            
            # 取得したカテゴリをコンボボックスに追加
            self.category_input.addItems(db_categories)
            
        except Exception as e:
            # エラー時はデフォルトカテゴリを使用
            print(f"カテゴリ取得エラー: {e}")
            default_categories = [
                '食費', '交通費', '娯楽', 'その他', '住宅', 
                '水道光熱費', '美容', '通信費', '日用品', '健康', '教育'
            ]
            self.category_input.addItems(default_categories)
        form_layout.addRow('カテゴリ:', self.category_input)

        self.amount_input = QLineEdit()
        form_layout.addRow('金額:', self.amount_input)

        self.description_input = QLineEdit()
        form_layout.addRow('説明:', self.description_input)

        layout.addLayout(form_layout)

        # 追加ボタン
        self.add_button = QPushButton('追加')
        self.add_button.clicked.connect(self.add_expense)
        layout.addWidget(self.add_button)

        # テーブル
        self.expense_table = QTableWidget(0, 5)
        self.expense_table.setHorizontalHeaderLabels(['ID', '日付', 'カテゴリ', '金額', '説明'])
        self.expense_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.expense_table.horizontalHeader().setStretchLastSection(True)
        self.expense_table.setColumnHidden(0, True)
        self.expense_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.expense_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.expense_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 削除ボタン
        self.delete_button = QPushButton('選択した行を削除')
        self.delete_button.clicked.connect(self.delete_selected_rows)
        layout.addWidget(self.delete_button)
        
        layout.addWidget(self.expense_table)
        
        self.expense_table.itemChanged.connect(self.on_table_item_changed)

        self.past_recurring_button = QPushButton('過去の定期支払いを登録')
        self.past_recurring_button.clicked.connect(self.register_past_recurring_expenses)
        layout.addWidget(self.past_recurring_button)

        # 定期支払い管理ボタン
        self.recurring_expense_button = QPushButton('定期支払い管理')
        self.recurring_expense_button.clicked.connect(self.show_recurring_expense_dialog)
        layout.addWidget(self.recurring_expense_button)

        # クレジットカード明細取込ボタン
        self.credit_card_import_button = QPushButton('クレジットカード明細取込')
        self.credit_card_import_button.clicked.connect(self.show_credit_card_import_dialog)
        layout.addWidget(self.credit_card_import_button)

        self.setLayout(layout)
        self.update_table()
        self.load_monthly_income()  # 初期収入データの読み込み
        self.update_monthly_expense()  # 初期支出データの更新

    def add_goal_progress_to_income_expense(self):
        # 月間目標の達成状況表示
        self.goal_progress_frame = QFrame()
        self.goal_progress_frame.setFrameShape(QFrame.StyledPanel)
        goal_progress_layout = QVBoxLayout()
        
        self.goal_progress_frame.setLayout(goal_progress_layout)
        goal_progress_layout.addWidget(QLabel('<b>目標達成状況</b>'))
        
        # 貯蓄目標プログレスバー
        self.savings_goal_label = QLabel('貯蓄目標: 0 円中 0 円 (0%)')
        self.savings_progress = QProgressBar()
        goal_progress_layout.addWidget(self.savings_goal_label)
        goal_progress_layout.addWidget(self.savings_progress)
        
        # 支出上限プログレスバー
        self.expense_limit_label = QLabel('支出上限: 0 円中 0 円 (0%)')
        self.expense_progress = QProgressBar()
        goal_progress_layout.addWidget(self.expense_limit_label)
        goal_progress_layout.addWidget(self.expense_progress)
        
        # レイアウトに追加
        self.layout().addWidget(self.goal_progress_frame)
        
        # update_tableが呼ばれるたびに目標進捗も更新
        self.update_goal_progress()

        # 初期表示時にも目標進捗を更新
        self.update_goal_progress()  # 確実に更新するため2回呼び出し

    
    def update_goal_progress(self):
        """月間目標の達成状況表示を更新（強化版）"""
        try:
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            
            # 月間目標を取得
            c.execute('''
                SELECT savings_goal, expense_limit FROM monthly_goals
                WHERE year = ? AND month = ?
            ''', (self.current_year, self.current_month))
            
            monthly_goal = c.fetchone()
        
            # 現在の収入を取得
            c.execute('''
                SELECT income FROM monthly_income
                WHERE year = ? AND month = ?
            ''', (self.current_year, self.current_month))
            
            income_result = c.fetchone()
            current_income = income_result[0] if income_result else 0
            
            # 現在の支出を取得
            c.execute('''
                SELECT SUM(amount) FROM expenses
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ''', (str(self.current_year), f"{self.current_month:02d}"))
            
            expense_result = c.fetchone()
            current_expense = expense_result[0] if expense_result and expense_result[0] else 0
            
            conn.close()
            
            # 貯蓄額の計算
            current_savings = current_income - current_expense
            
            # プログレスバーと達成状況の更新
            if monthly_goal:
                savings_goal = monthly_goal[0]
                expense_limit = monthly_goal[1]
                
                # 貯蓄目標の達成状況
                if savings_goal > 0:
                    savings_percentage = min(100, (current_savings / savings_goal) * 100)
                    self.savings_progress.setValue(int(savings_percentage))
                    self.savings_goal_label.setText(
                        f'貯蓄目標: {savings_goal:,.0f} 円中 {current_savings:,.0f} 円 ({savings_percentage:.1f}%)'
                    )
                else:
                    self.savings_progress.setValue(0)
                    self.savings_goal_label.setText('貯蓄目標: 設定なし')
                
                # 支出上限の達成状況
                if expense_limit:
                    expense_percentage = min(100, (current_expense / expense_limit) * 100)
                    self.expense_progress.setValue(int(expense_percentage))
                    self.expense_limit_label.setText(
                        f'支出上限: {expense_limit:,.0f} 円中 {current_expense:,.0f} 円 ({expense_percentage:.1f}%)'
                    )
                    
                    # 支出が上限を超えている場合は赤色表示
                    if current_expense > expense_limit:
                        self.expense_progress.setStyleSheet("QProgressBar::chunk { background-color: #FF4B4B; }")
                    else:
                        self.expense_progress.setStyleSheet("")
                    
                else:
                    self.expense_progress.setValue(0)
                    self.expense_limit_label.setText('支出上限: 設定なし')
            else:
                self.savings_progress.setValue(0)
                self.expense_progress.setValue(0)
                self.savings_goal_label.setText('貯蓄目標: 設定なし')
                self.expense_limit_label.setText('支出上限: 設定なし')
            
        except Exception as e:
            print(f"目標進捗表示の更新中にエラー: {e}") 

    def get_expenses_as_dataframe(self):
        """支出データをDataFrameとして取得する"""
        return fetch_df('SELECT * FROM expenses')

    def update_expense_in_db(self, expense_id, date, category, amount, description):
        
        execute_query.execute('''
            UPDATE expenses 
            SET date = ?, category = ?, amount = ?, description = ?
            WHERE id = ?
        ''', (date, category, amount, description, expense_id))

    def delete_expense_from_db(self, expense_id):
        
        execute_query.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))

    def show_year_month_dialog(self):
        dialog = YearMonthDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected_date = dialog.calendar.selectedDate()
            self.current_year = selected_date.year()
            self.current_month = selected_date.month()
            self.selected_period_label.setText(
                f'{self.current_year}年{self.current_month}月'
            )
            
            # ↓ この部分を修正（順序を変更）
            self.load_monthly_income()      # 収入を先に読み込み
            self.update_table()
            self.update_monthly_expense()
            
            # 目標進捗も更新（あれば）
            if hasattr(self, 'update_goal_progress'):
                self.update_goal_progress()

    def add_expense(self):
        try:
            amount = float(self.amount_input.text().replace(',', ''))
            if amount <= 0:
                raise ValueError("金額は正の数を入力してください")
                    
            date = self.date_input.date().toString("yyyy-MM-dd")
            category = self.category_input.currentText()
            description = self.description_input.text()
            
            # データベース操作を共通関数で置き換え
            execute_query('''
                INSERT INTO expenses (date, category, amount, description)
                VALUES (?, ?, ?, ?)
            ''', (date, category, amount, description))
            
            self.amount_input.clear()
            self.description_input.clear()
            
            self.update_table()
            self.update_monthly_expense()
            
        except ValueError as e:
            QMessageBox.warning(self, '警告', str(e))
        except Exception as e:
            QMessageBox.warning(self, '警告', f'エラーが発生しました: {str(e)}')

    def save_monthly_income(self):
        try:
            income_text = self.monthly_income_input.text().replace(',', '')
            if not income_text:
                QMessageBox.warning(self, '警告', '収入を入力してください')
                return
                    
            income = float(income_text)
            if income < 0:
                raise ValueError("収入は正の数を入力してください")
            
            # データベース接続と実行を1行に簡略化
            execute_query('''
                INSERT OR REPLACE INTO monthly_income (year, month, income)
                VALUES (?, ?, ?)
            ''', (self.current_year, self.current_month, income))
            
            QMessageBox.information(self, '成功', '収入を保存しました')
            self.calculate_monthly_balance()
            
        except ValueError as e:
            QMessageBox.warning(self, '警告', str(e))
        except Exception as e:
            QMessageBox.warning(self, '警告', f'エラーが発生しました: {str(e)}')

    def load_monthly_income(self):
        try:
            result = execute_query('''
                SELECT income FROM monthly_income 
                WHERE year = ? AND month = ?
            ''', (self.current_year, self.current_month), fetch_one=True)
            
            if result:
                self.monthly_income_input.setText(f"{result[0]:,.0f}")
            else:
                self.monthly_income_input.clear()

            self.calculate_monthly_balance()    
            
        except Exception as e:
            QMessageBox.warning(self, '警告', f'収入データの読み込みに失敗しました: {str(e)}')

    def calculate_monthly_balance(self):
        try:
            income = float(self.monthly_income_input.text().replace(',', '') or 0)
            expense = float(self.monthly_expense_label.text().replace('円', '').replace(',', ''))
            balance = income - expense
            self.monthly_balance_label.setText(f"{balance:,.0f} 円")
        except ValueError:
            self.monthly_balance_label.setText("0 円")


    # IncomeExpenseWidget クラスの update_table メソッドで、
    # QTableWidgetItem の代わりに QComboBox を使用するように変更

    def update_table(self):
        self.is_updating = True
        df = self.get_expenses_as_dataframe()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            monthly_df = df[
                (df['date'].dt.year == self.current_year) & 
                (df['date'].dt.month == self.current_month)
            ]
            monthly_df = monthly_df.sort_values('date')

            self.expense_table.setRowCount(len(monthly_df))
            
            # データベースからカテゴリリストを取得
            try:
                conn = sqlite3.connect('budget.db')
                c = conn.cursor()
                c.execute('SELECT name FROM categories ORDER BY sort_order')
                categories = [row[0] for row in c.fetchall()]
                conn.close()
            except Exception as e:
                print(f"カテゴリ取得エラー: {e}")
                categories = ['食費', '交通費', '娯楽', 'その他', '住宅', 
                            '水道光熱費', '美容', '通信費', '日用品', '健康', '教育']
            
            for row_idx, (_, row) in enumerate(monthly_df.iterrows()):
                self.expense_table.setItem(
                    row_idx, 0, 
                    EditableTableItem(str(row['id']), editable=False)
                )
                self.expense_table.setItem(
                    row_idx, 1, 
                    EditableTableItem(str(row['date'].strftime('%Y-%m-%d')))
                )
                
                # カテゴリセルにコンボボックスを設定
                category_combo = QComboBox()
                category_combo.addItems(categories)
                current_index = category_combo.findText(str(row['category']))
                if current_index >= 0:
                    category_combo.setCurrentIndex(current_index)
                
                # コンボボックスの変更イベントを接続
                category_combo.currentIndexChanged.connect(
                    lambda idx, r=row_idx: self.on_category_combo_changed(r)
                )
                
                self.expense_table.setCellWidget(row_idx, 2, category_combo)
                
                amount_item = EditableTableItem(f"{row['amount']:,.0f}")
                amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右寄せ
                self.expense_table.setItem(row_idx, 3, amount_item)
                
                self.expense_table.setItem(
                    row_idx, 4, 
                    EditableTableItem(str(row['description']))
                )
        else:
            self.expense_table.setRowCount(0)
            
        self.is_updating = False

    # 新しいメソッドを追加: カテゴリコンボボックスの変更イベントハンドラ
    def on_category_combo_changed(self, row):
        if not hasattr(self, 'is_updating') or not self.is_updating:
            try:
                combo = self.expense_table.cellWidget(row, 2)
                expense_id = int(self.expense_table.item(row, 0).text())
                new_category = combo.currentText()
                
                # データベースを更新
                execute_query('''
                    UPDATE expenses 
                    SET category = ?
                    WHERE id = ?
                ''', (new_category, expense_id))
                
                # 月間支出を更新
                self.update_monthly_expense()
                
            except Exception as e:
                print(f"カテゴリ更新エラー: {e}")
                QMessageBox.warning(self, '警告', f'カテゴリの更新に失敗しました: {str(e)}')

    def on_table_item_changed(self, item):
        if not hasattr(self, 'is_updating') or not self.is_updating:
            row = item.row()
            column = item.column()
            
            try:
                expense_id = int(self.expense_table.item(row, 0).text())
                date = self.expense_table.item(row, 1).text()
                
                # カテゴリの処理（コンボボックスかテキストか判定）
                category_widget = self.expense_table.cellWidget(row, 2)
                if category_widget and isinstance(category_widget, QComboBox):
                    category = category_widget.currentText()
                else:
                    category_item = self.expense_table.item(row, 2)
                    category = category_item.text() if category_item else ''
                
                # 金額の処理を改善
                amount_text = self.expense_table.item(row, 3).text()
                # カンマ、空白、円記号、マイナス記号を処理
                amount_text = amount_text.replace(',', '').replace(' ', '').replace('円', '').replace('−', '-').replace('－', '-')
                
                # 空文字列チェック
                if not amount_text.strip():
                    raise ValueError("金額が入力されていません")
                
                amount = float(amount_text)
                
                # 金額が負数でない場合は絶対値を使用（支出として記録）
                if amount < 0:
                    amount = abs(amount)
                
                description = self.expense_table.item(row, 4).text()
                
                # データベース更新（共通関数を使用）
                execute_query('''
                    UPDATE expenses 
                    SET date = ?, category = ?, amount = ?, description = ?
                    WHERE id = ?
                ''', (date, category, amount, description, expense_id))
                
                print(f"データ更新成功: ID={expense_id}, 金額={amount}")  # デバッグ用
                
                # 表示を更新（金額編集時は少し待つ）
                if column == 3:  # 金額列の場合
                    QApplication.processEvents()  # UI更新を待つ
                
                self.update_monthly_expense()
                self.update_goal_progress()  # 目標進捗も更新
                
            except ValueError as e:
                print(f"値エラー: {e}")
                QMessageBox.warning(self, '警告', f'入力値が正しくありません: {str(e)}\n数値を正しく入力してください。')
                self.update_table()
            except Exception as e:
                print(f"予期しないエラー: {e}")
                QMessageBox.warning(self, '警告', '変更の保存中にエラーが発生しました。')
                self.update_table()

    def delete_selected_rows(self):
        """選択された支出項目を削除"""
        selected_rows = set(item.row() for item in self.expense_table.selectedItems())
        if not selected_rows:
            return

        # 選択された行数に応じてメッセージを変更
        count = len(selected_rows)
        if count == 1:
            message = '選択した項目を削除してもよろしいですか？'
        else:
            message = f'選択した{count}件の項目を削除してもよろしいですか？'

        reply = QMessageBox.question(
            self, '確認', 
            message,
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            expense_ids = []
            # 選択された行のIDを取得
            for row in sorted(selected_rows, reverse=True):
                expense_id = int(self.expense_table.item(row, 0).text())
                expense_ids.append(expense_id)
            
            # 一括でデータベースから削除
            for expense_id in expense_ids:
                execute_query('DELETE FROM expenses WHERE id = ?', (expense_id,))
            
            self.update_table()
            self.update_monthly_expense()

    def show_recurring_expense_dialog(self):
        """定期支払い管理ダイアログを表示"""
        dialog = RecurringExpenseDialog(self)
        dialog.exec_()
        
    def process_recurring_expenses(self):
        """定期支払いの自動記録を処理"""
        today = QDate.currentDate()

        # 定期支払いテーブルが存在するか確認
        table_exists = execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='recurring_expenses'", fetch_one=True)
        if not table_exists:
            print("定期支払いテーブルが存在しません")
            return

        # 有効な定期支払いを取得
        recurring_expenses = execute_query('''
            SELECT id, category, amount, description, payment_day 
            FROM recurring_expenses 
            WHERE is_active = 1
        ''', fetch_all=True)

        # 処理結果を表示
        for expense in recurring_expenses:
            expense_id, category, amount, description, payment_day = expense

        processed = False  # 処理が行われたかフラグ

        for expense in recurring_expenses:
            expense_id, category, amount, description, payment_day = expense
        
            # 今日が支払日かチェック
            if today.day() == payment_day:

                # まだ記録されていないか確認
                existing = execute_query('''
                    SELECT id FROM expenses 
                    WHERE date = ? AND category = ? AND amount = ? AND description LIKE ?
                ''', (today.toString("yyyy-MM-dd"), category, amount, f"定期支払い: {description}%"), fetch_one=True)
            
                if not existing:
                    # 支出を記録
                    try:
                        execute_query('''
                            INSERT INTO expenses (date, category, amount, description)
                            VALUES (?, ?, ?, ?)
                        ''', (today.toString("yyyy-MM-dd"), category, amount, f"定期支払い: {description}"))
                        processed = True
                    except Exception as e:
                        print(f"挿入エラー: {e}")
              
        # 何か処理が行われた場合はテーブルを更新
        if processed:
            try:
                self.update_table()
                self.update_monthly_expense()
                QMessageBox.information(self, "定期支払い", "定期支払いを自動記録しました")
            except Exception as e:
                print(f"更新エラー: {e}")
    
    def register_past_recurring_expenses(self):
        """過去の定期支払いを遡って登録する"""
        # 登録期間の設定ダイアログを表示
        start_date = QDate()
        start_date.setDate(self.current_year, self.current_month, 1)
        start_date = start_date.addMonths(-6)  # デフォルトで半年前から
            
        end_date = QDate.currentDate()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("過去の定期支払い登録")
        
        dialog_layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # ここで日付編集ウィジェットを作成
        start_date_edit = QDateEdit()
        start_date_edit.setDate(start_date)
        start_date_edit.setCalendarPopup(True)
        start_date_edit.setDisplayFormat("yyyy年MM月")
        
        end_date_edit = QDateEdit()
        end_date_edit.setDate(end_date)
        end_date_edit.setCalendarPopup(True)
        end_date_edit.setDisplayFormat("yyyy年MM月")
        
        form_layout.addRow("開始月:", start_date_edit)
        form_layout.addRow("終了月:", end_date_edit)
        
        dialog_layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)
        
        dialog.setLayout(dialog_layout)
        
        # ダイアログ実行
        if dialog.exec_() != QDialog.Accepted:
            return
        
        # ここで日付編集ウィジェットから値を取得
        start_year = start_date_edit.date().year()
        start_month = start_date_edit.date().month()
        end_year = end_date_edit.date().year()
        end_month = end_date_edit.date().month()
        
        # 進捗ダイアログを表示
        progress_dialog = QProgressDialog("過去の定期支払いを登録中...", "キャンセル", 0, 100, self)
        progress_dialog.setWindowTitle("処理中")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.show()
        
        # 定期支払いデータを取得
        recurring_expenses = execute_query(
            'SELECT id, category, amount, description, payment_day FROM recurring_expenses WHERE is_active = 1',
            fetch_all=True
        )
        
        if not recurring_expenses:
            QMessageBox.information(self, "登録", "有効な定期支払いがありません")
            progress_dialog.close()
            return
        
        # 期間内の各月について処理
        current_date = QDate(start_year, start_month, 1)
        end_process_date = QDate(end_year, end_month, 1).addMonths(1).addDays(-1)  # 終了月の末日
        
        total_months = (end_year - start_year) * 12 + (end_month - start_month) + 1  # 正確な月数
        processed_months = 0
        total_processed = 0
        
        while current_date <= end_process_date:
            year = current_date.year()
            month = current_date.month()
            
            # 進捗更新
            progress_percent = int((processed_months / total_months) * 100)
            progress_dialog.setValue(progress_percent)
            if progress_dialog.wasCanceled():
                break
            
            # 各定期支払いについて
            for expense in recurring_expenses:
                expense_id, category, amount, description, payment_day = expense
                
                # 月の最終日を考慮
                days_in_month = current_date.daysInMonth()
                actual_payment_day = min(payment_day, days_in_month)
                
                # 支払日の日付を作成
                payment_date = QDate(year, month, actual_payment_day)
                
                # 将来の日付はスキップ
                today = QDate.currentDate()
                if payment_date > today:
                    continue
                
                # 日付文字列を正確に設定
                date_str = payment_date.toString("yyyy-MM-dd")
                
                # すでに記録されていないか確認 - より詳細な条件付き
                existing = execute_query('''
                    SELECT id FROM expenses 
                    WHERE date = ? AND category = ? AND amount = ? AND description LIKE ?
                ''', (date_str, category, amount, f"%{description}%"), fetch_one=True)
                
                if existing:
                    continue
                    
                # 支出を記録
                try:
                    execute_query('''
                        INSERT INTO expenses (date, category, amount, description)
                        VALUES (?, ?, ?, ?)
                    ''', (date_str, category, amount, f"定期支払い(過去): {description}"))
                    total_processed += 1
                except Exception as e:
                    print(f"登録エラー: {e}")
            
            # 次の月に進む
            current_date = current_date.addMonths(1)
            processed_months += 1
        
        progress_dialog.close()
        
        # テーブルを更新
        self.update_table()
        self.update_monthly_expense()
        
        QMessageBox.information(self, "登録完了", f"{total_processed}件の過去の定期支払いを登録しました")

    def update_monthly_expense(self):
        """月間支出を計算して表示を更新する"""
        df = self.get_expenses_as_dataframe()
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            monthly_df = df[
                (df['date'].dt.year == self.current_year) & 
                (df['date'].dt.month == self.current_month)
            ]
            total_expense = monthly_df['amount'].sum()
            self.monthly_expense_label.setText(f"{total_expense:,.0f} 円")
        else:
            self.monthly_expense_label.setText("0 円")
        
        self.calculate_monthly_balance()

    def calculate_monthly_balance(self):
        """収支バランスを計算して表示を更新する"""
        try:
            income = float(self.monthly_income_input.text().replace(',', '') or 0)
            expense = float(self.monthly_expense_label.text().replace('円', '').replace(',', ''))
            balance = income - expense
            self.monthly_balance_label.setText(f"{balance:,.0f} 円")
        except ValueError:
            self.monthly_balance_label.setText("0 円")

    def get_expenses_as_dataframe(self):
        """支出データをDataFrameとして取得する"""
        conn = sqlite3.connect('budget.db')
        df = pd.read_sql_query('SELECT * FROM expenses', conn)
        conn.close()
        return df     

    def show_credit_card_import_dialog(self):
        """クレジットカード明細取込ダイアログを表示"""
        dialog = CreditCardImportDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_table()
            self.update_monthly_expense()     
    

class BreakdownWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_year, self.current_month = DateHelper.get_current_year_month()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        layout.addLayout(self.button_layout)
        
        # 当月収支表示エリア
        summary_layout = QFormLayout()
        font_large = QFont()
        font_large.setPointSize(14)
        
        self.monthly_income_input = QLineEdit()
        self.monthly_income_input.setFont(font_large)
        self.monthly_income_input.setReadOnly(True)
        self.monthly_expense_label = QLabel('0 円')
        self.monthly_expense_label.setFont(font_large)
        self.monthly_balance_label = QLabel('0 円')
        self.monthly_balance_label.setFont(font_large)
        
        income_label = QLabel('当月収入:')
        expense_label = QLabel('当月支出:')
        balance_label = QLabel('当月収支:')
        income_label.setFont(font_large)
        expense_label.setFont(font_large)
        balance_label.setFont(font_large)
        
        summary_layout.addRow(income_label, self.monthly_income_input)
        summary_layout.addRow(expense_label, self.monthly_expense_label)
        summary_layout.addRow(balance_label, self.monthly_balance_label)
        
        layout.addLayout(summary_layout)

        # 年月選択ボタン
        self.year_month_button = QPushButton('年月選択')
        self.year_month_button.clicked.connect(self.show_year_month_dialog)
        layout.addWidget(self.year_month_button)

        # 選択された年月の表示
        self.selected_period_label = QLabel(
            f'{self.current_year}年{self.current_month}月'
        )
        layout.addWidget(self.selected_period_label)

        # カテゴリ別支出テーブル
        self.category_table = QTableWidget(0, 3)
        self.category_table.setHorizontalHeaderLabels(['カテゴリ', '金額', '割合'])
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("カテゴリ別支出"))
        layout.addWidget(self.category_table)

        # 円グラフ
        self.chart_view = QChartView()
        self.chart_view.setMinimumHeight(300)
        layout.addWidget(self.chart_view)

        self.setLayout(layout)
        self.load_monthly_data()
        self.update_display()

    def show_year_month_dialog(self):
        dialog = YearMonthDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected_date = dialog.calendar.selectedDate()
            self.current_year = selected_date.year()
            self.current_month = selected_date.month()
            self.selected_period_label.setText(
                f'{self.current_year}年{self.current_month}月'
            )
            self.update_display()

    def load_monthly_data(self):
        income_result = execute_query('''
            SELECT income FROM monthly_income 
            WHERE year = ? AND month = ?
        ''', (self.current_year, self.current_month), fetch_one=True)
        
        # 支出データの取得
        df = fetch_df('''
            SELECT category, SUM(amount) as total_amount 
            FROM expenses 
            WHERE strftime('%Y', date) = ? 
            AND strftime('%m', date) = ?
            GROUP BY category
        ''', params=(str(self.current_year), f"{self.current_month:02d}"))
        
        return income_result[0] if income_result else 0, df

    def update_display(self):
        income, expense_df = self.load_monthly_data()
        
        # 収入表示の更新
        self.monthly_income_input.setText(f"{income:,.0f}")
        
        # 総支出の計算と表示
        total_expense = expense_df['total_amount'].sum() if not expense_df.empty else 0
        self.monthly_expense_label.setText(f"{total_expense:,.0f} 円")
        
        # 収支の計算と表示
        balance = income - total_expense
        self.monthly_balance_label.setText(f"{balance:,.0f} 円")
        
        # テーブルの更新
        self.category_table.setRowCount(len(expense_df))
        
        # 見やすい色のリストを定義
        colors = [
            '#FF6B6B',  # 赤
            '#4ECDC4',  # ターコイズ
            '#45B7D1',  # 青
            '#96CEB4',  # 薄緑
            '#FFEEAD',  # クリーム
            '#FFD93D',  # 黄色
            '#6C5B7B',  # 紫
            '#F7A072',  # オレンジ
            '#C06C84',  # ピンク
            '#95A5A6',  # グレー
            '#2ECC71',  # エメラルド
        ]
        
        # 円グラフの作成
        series = QPieSeries()
        
        for idx, row in expense_df.iterrows():
            category = row['category']
            amount = row['total_amount']
            percentage = (amount / total_expense * 100) if total_expense > 0 else 0
            
            # テーブルに行を追加
            self.category_table.setItem(idx, 0, QTableWidgetItem(category))
            self.category_table.setItem(idx, 1, QTableWidgetItem(f"{amount:,.0f}"))
            self.category_table.setItem(idx, 2, QTableWidgetItem(f"{percentage:.1f}%"))
            
            # 円グラフにデータを追加
            slice = series.append(f"{category}", amount)
            slice.setLabel(f"{category}\n{percentage:.1f}%")
            slice.setLabelVisible(True)
            
            # カラーの設定
            color_idx = idx % len(colors)
            slice.setColor(QColor(colors[color_idx]))
            
            # ラベルの位置を調整（スライスの中心に配置）
            slice.setLabelPosition(QPieSlice.LabelInsideHorizontal)

        # 円グラフの更新
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"{self.current_year}年{self.current_month}月 支出内訳")
        chart.legend().hide()  # 凡例を非表示（ラベルで十分な情報を表示するため）
        self.chart_view.setChart(chart)
        
        # グラフの更新
        chart = self.create_pie_chart(expense_df, total_expense)
        self.chart_view.setChart(chart)

    def enhanced_update_display(self):
        income, expense_df = self.load_monthly_data()
        
        # 収入表示の更新
        self.monthly_income_input.setText(f"{income:,.0f}")
        
        # 総支出の計算と表示
        total_expense = expense_df['total_amount'].sum() if not expense_df.empty else 0
        self.monthly_expense_label.setText(f"{total_expense:,.0f} 円")
        
        # 収支の計算と表示
        balance = income - total_expense
        self.monthly_balance_label.setText(f"{balance:,.0f} 円")
        
        # カテゴリ別目標を取得
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        c.execute('''
            SELECT category, goal_amount FROM category_goals
            WHERE year = ? AND month = ?
        ''', (self.current_year, self.current_month))
        
        category_goals = {category: amount for category, amount in c.fetchall()}
        conn.close()
        
        # テーブルを更新（目標情報も含める）
        self.category_table.setRowCount(len(expense_df))
        self.category_table.setColumnCount(5)  # カテゴリ, 金額, 割合, 目標, 達成率
        self.category_table.setHorizontalHeaderLabels(['カテゴリ', '金額', '割合', '目標', '達成率'])
        
        for idx, row in expense_df.iterrows():
            category = row['category']
            amount = row['total_amount']
            percentage = (amount / total_expense * 100) if total_expense > 0 else 0
            
            # 目標金額と達成率
            goal = category_goals.get(category, 0)
            achievement = (amount / goal * 100) if goal > 0 else 0
            
            # テーブルに行を追加
            self.category_table.setItem(idx, 0, QTableWidgetItem(category))
            self.category_table.setItem(idx, 1, QTableWidgetItem(f"{amount:,.0f}"))
            self.category_table.setItem(idx, 2, QTableWidgetItem(f"{percentage:.1f}%"))
            
            goal_item = QTableWidgetItem(f"{goal:,.0f}" if goal > 0 else "未設定")
            self.category_table.setItem(idx, 3, goal_item)
            
            if goal > 0:
                achievement_item = QTableWidgetItem(f"{achievement:.1f}%")
                if amount > goal:
                    achievement_item.setBackground(QColor("#FFE4E1"))  # 超過は薄い赤
                self.category_table.setItem(idx, 4, achievement_item)
            else:
                self.category_table.setItem(idx, 4, QTableWidgetItem("-"))
        
        # グラフの更新
        chart = self.create_enhanced_pie_chart(expense_df, total_expense, category_goals)
        self.chart_view.setChart(chart)

     

    def create_pie_chart(self, expense_df, total_expense):
        """円グラフを作成"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 円グラフのデータを作成
        series = QPieSeries()
        
        # カラーリスト（異なる色を用意）
        colors = [
            '#FF6B6B',  # 赤
            '#4ECDC4',  # ターコイズ
            '#45B7D1',  # 青
            '#96CEB4',  # 薄緑
            '#FFEEAD',  # クリーム
            '#FFD93D',  # 黄色
            '#6C5B7B',  # 紫
            '#F7A072',  # オレンジ
            '#C06C84',  # ピンク
            '#95A5A6',  # グレー
            '#2ECC71',  # エメラルド
        ]
        
        # カテゴリごとのデータを追加
        if not expense_df.empty:
            for idx, row in expense_df.iterrows():
                percentage = (row['total_amount'] / total_expense * 100) if total_expense > 0 else 0
                slice = series.append(
                    f"{row['category']}\n{percentage:.1f}%",
                    row['total_amount']
                )
                # カラーを設定
                color_idx = idx % len(colors)
                slice.setColor(QColor(colors[color_idx]))
                # ラベルを表示
                slice.setLabelVisible(True)
                slice.setLabelPosition(QPieSlice.LabelInsideHorizontal)

        # グラフにデータを追加
        chart.addSeries(series)
        chart.setTitle(f"{self.current_year}年{self.current_month}月 支出内訳")
        
        # 凡例を非表示（ラベルで十分な情報を表示するため）
        chart.legend().hide()
        
        return chart    

    def create_enhanced_pie_chart(self, expense_df, total_expense, category_goals):
        """カテゴリ別支出と目標を表示する円グラフを作成"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 円グラフのデータを作成
        series = QPieSeries()
        
        # カラーリスト
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD',
            '#FFD93D', '#6C5B7B', '#F7A072', '#C06C84', '#95A5A6', '#2ECC71'
        ]
        
        # カテゴリごとのデータを追加
        if not expense_df.empty:
            for idx, row in expense_df.iterrows():
                category = row['category']
                amount = row['total_amount']
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                
                # 目標金額
                goal = category_goals.get(category, 0)
                
                # ラベルに目標との比較を含める
                label = f"{category}\n{percentage:.1f}%"
                if goal > 0:
                    ratio = amount / goal * 100
                    label += f"\n目標比: {ratio:.1f}%"
                
                slice = series.append(label, amount)
                
                # カラーを設定
                color_idx = idx % len(colors)
                slice.setColor(QColor(colors[color_idx]))
                
                # 目標を超過している場合は、スライスを少し引き出す
                if goal > 0 and amount > goal:
                    slice.setExploded(True)
                    slice.setExplodeDistanceFactor(0.1)
                
                # ラベルを表示
                slice.setLabelVisible(True)
                slice.setLabelPosition(QPieSlice.LabelInsideHorizontal)

        # グラフにデータを追加
        chart.addSeries(series)
        chart.setTitle(f"{self.current_year}年{self.current_month}月 支出内訳（目標比）")
        
        # 凡例を非表示（ラベルで十分な情報を表示するため）
        chart.legend().hide()
        
        return chart      

class MonthlyReportWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate.currentDate()
        # display_year/month ではなく current_year/month に変更
        self.current_year = self.current_date.year()
        self.current_month = self.current_date.month()

        self.display_year = self.current_year
        self.display_month = self.current_month
        
        # 選択されたカテゴリグラフを保持するリスト
        self.category_views = []
        
        self.initUI()
        self.update_display()

    def initUI(self):
        layout = QVBoxLayout()

        # BaseWidgetで作成したボタンレイアウトを追加
        layout.addLayout(self.button_layout)
        
        # 月選択ボタンと期間表示
        nav_layout = QHBoxLayout()
        self.prev_month_button = QPushButton('前月')
        self.next_month_button = QPushButton('次月')
        self.period_label = QLabel(f'{self.display_year}年{self.display_month}月')
        
        self.prev_month_button.clicked.connect(self.show_prev_month)
        self.next_month_button.clicked.connect(self.show_next_month)
        
        nav_layout.addWidget(self.prev_month_button)
        nav_layout.addWidget(self.period_label)
        nav_layout.addWidget(self.next_month_button)
        layout.addLayout(nav_layout)

        # カテゴリ選択エリア
        category_select_layout = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            '食費', '交通費', '娯楽', 'その他', '住宅', 
            '水道光熱費', '美容', '通信費', '日用品', '健康', '教育'
        ])
        self.add_category_button = QPushButton('カテゴリグラフ追加')
        self.add_category_button.clicked.connect(self.add_category_graph)
        self.clear_category_button = QPushButton('カテゴリグラフクリア')
        self.clear_category_button.clicked.connect(self.clear_category_graphs)
        
        category_select_layout.addWidget(QLabel('カテゴリ選択:'))
        category_select_layout.addWidget(self.category_combo)
        category_select_layout.addWidget(self.add_category_button)
        category_select_layout.addWidget(self.clear_category_button)
        category_select_layout.addStretch()
        
        layout.addLayout(category_select_layout)

        # グラフ表示エリア用のウィジェット
        self.chart_view = QWidget()
        self.chart_view.setMinimumHeight(500)
        layout.addWidget(self.chart_view)

        # 収支リスト（テーブル）
        self.summary_table = QTableWidget()
        self.summary_table.setMinimumHeight(400)
        layout.addWidget(self.summary_table)

        self.setLayout(layout)

    def update_table(self, months_data):
        # 全期間のカテゴリを取得
        all_categories = set()
        for data in months_data:
            all_categories.update(data['expenses_by_category'].keys())
        all_categories = sorted(list(all_categories))
        
        # テーブルの設定
        self.summary_table.clear()
        row_count = len(all_categories) + 3  # カテゴリ + 収入行 + 支出合計行 + 収支合計行
        col_count = len(months_data)
        self.summary_table.setRowCount(row_count)
        self.summary_table.setColumnCount(col_count)
        
        # ヘッダーの設定
        headers = [f"{data['year']}/{data['month']}" for data in months_data]
        self.summary_table.setHorizontalHeaderLabels(headers)
        
        # データの設定
        for col, data in enumerate(months_data):
            # 収入行
            income_item = QTableWidgetItem(f"{data['income']:,.0f}")
            self.summary_table.setItem(0, col, income_item)
            
            # カテゴリ別支出
            for row, category in enumerate(all_categories, 1):
                amount = data['expenses_by_category'].get(category, 0)
                item = QTableWidgetItem(f"{amount:,.0f}")
                self.summary_table.setItem(row, col, item)
            
            # 支出合計行
            total_expense_item = QTableWidgetItem(f"{data['total_expense']:,.0f}")
            self.summary_table.setItem(row_count-2, col, total_expense_item)
            
            # 収支合計行
            balance_item = QTableWidgetItem(f"{data['balance']:,.0f}")
            balance_item.setBackground(
                QColor("#FFE4E1") if data['balance'] < 0 else QColor("#E0FFFF")
            )
            self.summary_table.setItem(row_count-1, col, balance_item)
        
        # 行ラベルの設定
        row_labels = ['収入'] + list(all_categories) + ['支出合計', '収支合計']
        self.summary_table.setVerticalHeaderLabels(row_labels)
        
        # セルの幅を調整
        self.summary_table.resizeColumnsToContents()
        self.summary_table.resizeRowsToContents()

    def show_prev_month(self):
        self.current_year, self.current_month = DateHelper.get_prev_month(self.current_year, self.current_month)
        self.display_year = self.current_year
        self.display_month = self.current_month
        self.update_display()

    def show_next_month(self):
        self.current_year, self.current_month = DateHelper.get_next_month(self.current_year, self.current_month)
        self.display_year = self.current_year
        self.display_month = self.current_month
        self.update_display()

    def get_6month_data(self):
        """現在の月を含む前後6ヶ月分のデータを取得"""
        conn = sqlite3.connect('budget.db')
        months_data = []
        
        # 開始月と終了月を計算
        start_date = QDate(self.display_year, self.display_month, 1).addMonths(-5)
        end_date = QDate(self.display_year, self.display_month, 1)
        
        current_date = start_date
        while current_date <= end_date:
            year = current_date.year()
            month = current_date.month()
            
            # 収入データの取得
            c = conn.cursor()
            c.execute('''
                SELECT income FROM monthly_income 
                WHERE year = ? AND month = ?
            ''', (year, month))
            income_result = c.fetchone()
            income = income_result[0] if income_result else 0
            
            # 支出データの取得（カテゴリ別）
            df = pd.read_sql_query('''
                SELECT category, SUM(amount) as total_amount 
                FROM expenses 
                WHERE strftime('%Y', date) = ? 
                AND strftime('%m', date) = ?
                GROUP BY category
            ''', conn, params=(str(year), f"{month:02d}"))
            
            # カテゴリ別支出を辞書に変換
            expenses_by_category = {}
            total_expense = 0
            for _, row in df.iterrows():
                expenses_by_category[row['category']] = row['total_amount']
                total_expense += row['total_amount']
            
            months_data.append({
                'year': year,
                'month': month,
                'income': income,
                'total_expense': total_expense,
                'expenses_by_category': expenses_by_category,
                'balance': income - total_expense
            })
            
            current_date = current_date.addMonths(1)
        
        conn.close()
        return months_data

    def update_display(self):
        # 期間表示の更新
        if hasattr(self, 'period_label'):
            self.period_label.setText(f'{self.display_year}年{self.display_month}月')
        
        # データの取得
        try:
            months_data = self.get_6month_data()
            
            # グラフの更新
            self.update_chart(months_data)
            
            # テーブルの更新
            self.update_table(months_data)
        except Exception as e:
            print(f"Error in update_display: {e}")


    def enhanced_update_report_display(self):
        # 期間表示の更新
        self.period_label.setText(f'{self.display_year}年{self.display_month}月')
        
        # データの取得
        months_data = self.get_enhanced_6month_data()
        
        # グラフの更新
        self.update_chart(months_data)
        
        # テーブルの更新
        self.update_enhanced_table(months_data)

    # MonthlyReportWidgetクラスに新しいメソッドを追加
    def get_enhanced_6month_data(self):
        """目標情報を含む6ヶ月分のデータを取得"""
        conn = sqlite3.connect('budget.db')
        months_data = []
        
        # 開始月と終了月を計算
        start_date = QDate(self.display_year, self.display_month, 1).addMonths(-5)
        end_date = QDate(self.display_year, self.display_month, 1)
        
        current_date = start_date
        while current_date <= end_date:
            year = current_date.year()
            month = current_date.month()
            
            # 収入データの取得
            c = conn.cursor()
            c.execute('''
                SELECT income FROM monthly_income 
                WHERE year = ? AND month = ?
            ''', (year, month))
            income_result = c.fetchone()
            income = income_result[0] if income_result else 0
            
            # 支出データの取得（カテゴリ別）
            df = pd.read_sql_query('''
                SELECT category, SUM(amount) as total_amount 
                FROM expenses 
                WHERE strftime('%Y', date) = ? 
                AND strftime('%m', date) = ?
                GROUP BY category
            ''', conn, params=(str(year), f"{month:02d}"))
            
            # カテゴリ別支出を辞書に変換
            expenses_by_category = {}
            total_expense = 0
            for _, row in df.iterrows():
                expenses_by_category[row['category']] = row['total_amount']
                total_expense += row['total_amount']
            
            # 月間目標を取得
            c.execute('''
                SELECT savings_goal, expense_limit FROM monthly_goals
                WHERE year = ? AND month = ?
            ''', (year, month))
            
            monthly_goal = c.fetchone()
            savings_goal = monthly_goal[0] if monthly_goal else 0
            expense_limit = monthly_goal[1] if monthly_goal and monthly_goal[1] else None
            
            # 貯蓄額と目標達成率の計算
            balance = income - total_expense
            savings_achievement = (balance / savings_goal * 100) if savings_goal > 0 else 0
            expense_achievement = (expense_limit / total_expense * 100) if expense_limit and total_expense > 0 else 0
            
            months_data.append({
                'year': year,
                'month': month,
                'income': income,
                'total_expense': total_expense,
                'expenses_by_category': expenses_by_category,
                'balance': balance,
                'savings_goal': savings_goal,
                'expense_limit': expense_limit,
                'savings_achievement': min(100, savings_achievement),
                'expense_achievement': min(100, expense_achievement) if expense_limit else 0
            })
            
            current_date = current_date.addMonths(1)
        
        conn.close()
        return months_data

    def update_enhanced_table(self, months_data):
        # 全期間のカテゴリを取得
        all_categories = set()
        for data in months_data:
            all_categories.update(data['expenses_by_category'].keys())
        all_categories = sorted(list(all_categories))
        
        # テーブルの設定
        self.summary_table.clear()
        row_count = len(all_categories) + 6  # カテゴリ + 収入行 + 支出合計行 + 収支合計行 + 貯蓄目標行 + 目標達成率行
        col_count = len(months_data)
        self.summary_table.setRowCount(row_count)
        self.summary_table.setColumnCount(col_count)
        
        # ヘッダーの設定
        headers = [f"{data['year']}/{data['month']}" for data in months_data]
        self.summary_table.setHorizontalHeaderLabels(headers)
        
        # データの設定
        for col, data in enumerate(months_data):
            row = 0
            
            # 収入行
            income_item = QTableWidgetItem(f"{data['income']:,.0f}")
            self.summary_table.setItem(row, col, income_item)
            row += 1
            
            # カテゴリ別支出
            for category in all_categories:
                amount = data['expenses_by_category'].get(category, 0)
                item = QTableWidgetItem(f"{amount:,.0f}")
                self.summary_table.setItem(row, col, item)
                row += 1
            
            # 支出合計行
            total_expense_item = QTableWidgetItem(f"{data['total_expense']:,.0f}")
            self.summary_table.setItem(row, col, total_expense_item)
            row += 1
            
            # 収支合計行
            balance_item = QTableWidgetItem(f"{data['balance']:,.0f}")
            balance_item.setBackground(
                QColor("#FFE4E1") if data['balance'] < 0 else QColor("#E0FFFF")
            )
            self.summary_table.setItem(row, col, balance_item)
            row += 1
            
            # 貯蓄目標行
            savings_goal_item = QTableWidgetItem(f"{data['savings_goal']:,.0f}")
            self.summary_table.setItem(row, col, savings_goal_item)
            row += 1
            
            # 貯蓄目標達成率行
            achievement_item = QTableWidgetItem(f"{data['savings_achievement']:.1f}%")
            achievement_item.setBackground(
                QColor("#E0FFFF") if data['savings_achievement'] >= 90 else QColor("#FFFACD")
            )
            self.summary_table.setItem(row, col, achievement_item)
        
        # 行ラベルの設定
        row_labels = ['収入'] + list(all_categories) + ['支出合計', '収支合計', '貯蓄目標', '目標達成率']
        self.summary_table.setVerticalHeaderLabels(row_labels)
        
        # セルの幅を調整
        self.summary_table.resizeColumnsToContents()
        self.summary_table.resizeRowsToContents()    


    def create_category_graph(self, category, months_data):
        """指定されたカテゴリの棒グラフとラインチャートを作成"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # カテゴリ（X軸）のラベル
        categories = []
        values = []
        
        # データの設定
        for i, data in enumerate(months_data):
            amount = data['expenses_by_category'].get(category, 0)
            values.append(amount)
            categories.append(f"{data['month']}月")
        
        # 1. 棒グラフの作成
        bar_set = QBarSet(category)
        bar_set.setColor(QColor("#FFD93D"))  # 黄色系の色に設定
        bar_set.append(values)
        
        bar_series = QBarSeries()
        bar_series.append(bar_set)
        bar_series.setBarWidth(0.8)
        
        # 2. ラインチャートの作成
        line_series = QLineSeries()
        line_series.setName(f"{category}の推移")
        for i, value in enumerate(values):
            line_series.append(i, value)
        line_series.setColor(QColor("#FF4B4B"))  # 赤系の色に設定
        
        # シリーズをチャートに追加
        chart.addSeries(bar_series)
        chart.addSeries(line_series)
        
        # X軸の設定
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        bar_series.attachAxis(axis_x)
        line_series.attachAxis(axis_x)
        
        # Y軸の設定
        max_value = max(values) if values else 0
        axis_y = QValueAxis()
        axis_y.setRange(0, max_value * 1.1)
        axis_y.setLabelFormat("%,.0f")
        chart.addAxis(axis_y, Qt.AlignLeft)
        bar_series.attachAxis(axis_y)
        line_series.attachAxis(axis_y)
        
        # チャートの設定
        chart.setTitle(f"{category}の推移")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setMargins(QMargins(10, 10, 10, 10))
        
        # チャートビューの作成
        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(400)  
        
        return chart_view
    
    def create_category_line_chart(self, months_data, category):
        """カテゴリごとの推移ラインチャートを作成"""
        # チャートの作成
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)

        # データポイントの準備
        points = []
        categories = []
        values = []

        # データの設定とデータポイントの追加
        for i, data in enumerate(months_data):
            amount = data['expenses_by_category'].get(category, 0)
            values.append(amount)
            categories.append(f"{data['month']}月")
            points.append(QPointF(i, amount))

        # ラインシリーズの作成と設定
        series = QLineSeries()
        series.setName(category)
        series.append(points)  # ポイントをまとめて追加

        # グラフにシリーズを追加
        chart.addSeries(series)

        # X軸の設定（カテゴリ軸）
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        # Y軸の設定
        axis_y = QValueAxis()
        max_value = max(values) if values else 0
        axis_y.setRange(0, max_value * 1.1)
        axis_y.setLabelFormat("%,.0f")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        # チャートの設定
        chart.setTitle(f"{category}の推移（ライン）")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setMargins(QMargins(10, 10, 10, 10))

        # チャートビューの作成と設定
        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(300)
        chart_view.setMinimumWidth(400)

        return chart_view


    def add_category_graph(self):
        """選択されたカテゴリのグラフを追加"""
        selected_category = self.category_combo.currentText()
        months_data = self.get_6month_data()
        
        # 新しいカテゴリビューを作成して保存
        category_view = self.create_category_graph(selected_category, months_data)
        self.category_views.append((selected_category, category_view))  # タプルとして保存
        
        # 全てのグラフを再表示
        self.update_display()

    def update_chart(self, months_data):
        # 既存のレイアウトとウィジェットをクリーンアップ
        if self.chart_view.layout() is not None:
            old_layout = self.chart_view.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old_layout)

        # 新しいレイアウトを作成
        chart_layout = QVBoxLayout()
        
        # 1. 収支の棒グラフ
        income_expense_chart = QChart()
        income_expense_chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 収入用のバーセット
        income_series = QBarSet("収入")
        income_series.setColor(QColor("#4CAF50"))  # 緑色
        expense_series = QBarSet("支出")
        expense_series.setColor(QColor("#F44336"))  # 赤色
        
        # カテゴリ（X軸）のラベル
        categories = []
        income_values = []
        expense_values = []
        
        # データの設定
        for data in months_data:
            income_values.append(data['income'])
            expense_values.append(data['total_expense'])
            categories.append(f"{data['month']}月")
        
        income_series.append(income_values)
        expense_series.append(expense_values)
        
        # バーシリーズの作成
        series = QBarSeries()
        series.append(income_series)
        series.append(expense_series)
        series.setBarWidth(0.8)
        
        # グラフの設定
        income_expense_chart.addSeries(series)
        income_expense_chart.setTitle("月次収支推移")
        
        # X軸の設定
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        income_expense_chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        # Y軸の設定
        axis_y = QValueAxis()
        max_value = max(max(income_values), max(expense_values))
        axis_y.setRange(0, max_value * 1.1)
        axis_y.setLabelFormat("%,.0f")
        income_expense_chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # 凡例の設定
        income_expense_chart.legend().setVisible(True)
        income_expense_chart.legend().setAlignment(Qt.AlignBottom)
        income_expense_chart.setMargins(QMargins(10, 10, 10, 10))
        
        # 収支チャートビューの作成と設定
        income_expense_view = QChartView(income_expense_chart)
        income_expense_view.setMinimumHeight(200)  # 収支グラフを小さく
        chart_layout.addWidget(income_expense_view)
        
        # カテゴリグラフを追加
        for category, view in self.category_views:
            new_view = self.create_category_graph(category, months_data)
            chart_layout.addWidget(new_view)

        # 新しいレイアウトを設定
        self.chart_view.setLayout(chart_layout)

    
    def clear_category_graphs(self):
        """追加された個別カテゴリグラフをクリア"""
        self.category_views = []
        self.update_display()

class GoalManagementWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)  # BaseWidgetの初期化
        self.current_year, self.current_month = DateHelper.get_current_year_month()
        
        self.initUI()
        self.load_goals()
        
    def initUI(self):
        layout = QVBoxLayout()

        layout.addLayout(self.button_layout)
        
        # 年月選択
        date_layout = QHBoxLayout()
        
        self.prev_month_button = QPushButton('前月')
        self.next_month_button = QPushButton('次月')
        self.period_label = QLabel(f'{self.current_year}年{self.current_month}月')
        
        self.prev_month_button.clicked.connect(self.show_prev_month)
        self.next_month_button.clicked.connect(self.show_next_month)
        
        date_layout.addWidget(self.prev_month_button)
        date_layout.addWidget(self.period_label)
        date_layout.addWidget(self.next_month_button)
        
        layout.addLayout(date_layout)
        
        # タブウィジェットでセクションを分ける
        tab_widget = QTabWidget()
        
        # タブ1: 月間目標設定
        monthly_tab = QWidget()
        monthly_layout = QVBoxLayout()
        
        # 月間目標設定フォーム
        form_layout = QFormLayout()
        
        self.savings_goal_input = QLineEdit()
        self.expense_limit_input = QLineEdit()
        
        form_layout.addRow('貯蓄目標 (円):', self.savings_goal_input)
        form_layout.addRow('支出上限 (円):', self.expense_limit_input)
        
        save_monthly_button = QPushButton('月間目標を保存')
        save_monthly_button.clicked.connect(self.save_monthly_goals)
        
        monthly_layout.addLayout(form_layout)
        monthly_layout.addWidget(save_monthly_button)
        
        # 月間目標の達成状況表示
        self.monthly_progress_frame = QFrame()
        self.monthly_progress_frame.setFrameShape(QFrame.StyledPanel)
        self.monthly_progress_frame.setMinimumHeight(150)
        monthly_progress_layout = QVBoxLayout()
        
        self.savings_goal_label = QLabel('貯蓄目標: 0 円中 0 円 (0%)')
        self.expense_limit_label = QLabel('支出上限: 0 円中 0 円 (0%)')
        
        # プログレスバー
        self.savings_progress = QProgressBar()
        self.expense_progress = QProgressBar()
        
        monthly_progress_layout.addWidget(QLabel('<b>目標達成状況</b>'))
        monthly_progress_layout.addWidget(self.savings_goal_label)
        monthly_progress_layout.addWidget(self.savings_progress)
        monthly_progress_layout.addWidget(self.expense_limit_label)
        monthly_progress_layout.addWidget(self.expense_progress)
        
        self.monthly_progress_frame.setLayout(monthly_progress_layout)
        monthly_layout.addWidget(self.monthly_progress_frame)
        
        monthly_tab.setLayout(monthly_layout)
        
        # タブ2: カテゴリ別目標設定
        category_tab = QWidget()
        category_layout = QVBoxLayout()
        
        # カテゴリ別目標入力フォーム
        category_form_layout = QFormLayout()
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            '食費', '交通費', '娯楽', 'その他', '住宅', 
            '水道光熱費', '美容', '通信費', '日用品', '健康', '教育'
        ])
        
        self.category_goal_input = QLineEdit()
        
        category_form_layout.addRow('カテゴリ:', self.category_combo)
        category_form_layout.addRow('目標金額 (円):', self.category_goal_input)
        
        button_layout = QHBoxLayout()

        save_category_button = QPushButton('カテゴリ目標を保存')
        save_category_button.clicked.connect(self.save_category_goal)

        # 削除ボタンを追加
        delete_category_goal_button = QPushButton('選択した目標を削除')
        delete_category_goal_button.clicked.connect(self.delete_category_goal)
        delete_category_goal_button.setStyleSheet('background-color: #FF6B6B; color: white;')

        button_layout.addWidget(save_category_button)
        button_layout.addWidget(delete_category_goal_button)
        
        category_layout.addLayout(category_form_layout)
        category_layout.addLayout(button_layout)
        category_layout.addWidget(save_category_button)
        
        # カテゴリ別目標と実績の一覧テーブル
        self.category_goal_table = QTableWidget(0, 4)
        self.category_goal_table.setHorizontalHeaderLabels(['カテゴリ', '目標額', '実績', '達成率'])
        self.category_goal_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.category_goal_table.setSelectionBehavior(QTableWidget.SelectRows)  # ←追加
        self.category_goal_table.setSelectionMode(QTableWidget.SingleSelection)  # ←追加
        
        category_layout.addWidget(QLabel('<b>カテゴリ別目標と実績</b>'))
        category_layout.addWidget(self.category_goal_table)
        
        category_tab.setLayout(category_layout)
        
        # タブ3: 目標達成履歴
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        
        # 目標達成履歴のチャート
        self.history_chart_view = QChartView()
        self.history_chart_view.setMinimumHeight(300)
        
        history_layout.addWidget(QLabel('<b>目標達成履歴</b>'))
        history_layout.addWidget(self.history_chart_view)
        
        history_tab.setLayout(history_layout)
        
        # タブをタブウィジェットに追加
        tab_widget.addTab(monthly_tab, "月間目標")
        tab_widget.addTab(category_tab, "カテゴリ別目標")
        tab_widget.addTab(history_tab, "達成履歴")
        
        layout.addWidget(tab_widget)
        
        self.setLayout(layout)
    
    def show_prev_month(self):
        self.current_year, self.current_month = DateHelper.get_prev_month(self.current_year, self.current_month)
        self.update_display()

    def show_next_month(self):
        self.current_year, self.current_month = DateHelper.get_next_month(self.current_year, self.current_month)
        self.update_display()
    
    def update_display(self):
        self.period_label.setText(f'{self.current_year}年{self.current_month}月')
        self.load_goals()
        self.update_progress_display()
        self.update_category_table()
        self.update_history_chart()
    
    def load_goals(self):
        """データベースから目標設定を読み込む"""
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        # 月間目標を取得
        c.execute('''
            SELECT savings_goal, expense_limit FROM monthly_goals
            WHERE year = ? AND month = ?
        ''', (self.current_year, self.current_month))
        
        monthly_goal = c.fetchone()
        if monthly_goal:
            self.savings_goal_input.setText(f"{monthly_goal[0]:,.0f}")
            if monthly_goal[1]:  # expense_limitがNULLでない場合
                self.expense_limit_input.setText(f"{monthly_goal[1]:,.0f}")
            else:
                self.expense_limit_input.clear()
        else:
            self.savings_goal_input.clear()
            self.expense_limit_input.clear()
        
        conn.close()
        
        # 目標達成状況と実績も更新
        self.update_progress_display()
        self.update_category_table()
        
        # 履歴チャートも更新
        if hasattr(self, 'update_history_chart'):
            self.update_history_chart()
    
    def save_monthly_goals(self):
        """月間目標をデータベースに保存"""
        try:
            # 入力値を取得
            savings_goal_text = self.savings_goal_input.text().replace(',', '')
            expense_limit_text = self.expense_limit_input.text().replace(',', '')
            
            if not savings_goal_text:
                savings_goal = 0
            else:
                savings_goal = float(savings_goal_text)
                    
            if not expense_limit_text:
                expense_limit = None
            else:
                expense_limit = float(expense_limit_text)
            
            # データベース操作
            execute_query('''
                INSERT OR REPLACE INTO monthly_goals (year, month, savings_goal, expense_limit)
                VALUES (?, ?, ?, ?)
            ''', (self.current_year, self.current_month, savings_goal, expense_limit))
            
            QMessageBox.information(self, '成功', '月間目標を保存しました')
            
            # 表示の更新
            self.update_progress_display()
            self.update_category_table()
            
            # 月間目標の履歴チャートも更新
            if hasattr(self, 'update_history_chart'):
                self.update_history_chart()
            
            # 入出金画面の更新（シンプルな方法に修正）
            try:
                # メインウィンドウを取得
                main_app = QApplication.instance()
                for widget in main_app.topLevelWidgets():
                    if isinstance(widget, QMainWindow):
                        if hasattr(widget, 'income_expense_widget'):
                            if hasattr(widget.income_expense_widget, 'update_goal_progress'):
                                widget.income_expense_widget.update_goal_progress()
                                break
            except Exception as e:
                print(f"更新処理中にエラー: {e}")
            
        except ValueError:
            QMessageBox.warning(self, '警告', '数値を正しく入力してください')
        except Exception as e:
            print(f"目標保存中にエラー: {e}")
            QMessageBox.warning(self, '警告', f'保存中にエラーが発生しました: {str(e)}')
    
    def save_category_goal(self):
        """カテゴリ別目標をデータベースに保存"""
        try:
            category = self.category_combo.currentText()
            goal_amount_text = self.category_goal_input.text().replace(',', '')
            
            if not goal_amount_text:
                QMessageBox.warning(self, '警告', '目標金額を入力してください')
                return
                    
            goal_amount = float(goal_amount_text)
            
            # データベース操作を共通関数で置き換え
            execute_query('''
                INSERT OR REPLACE INTO category_goals (year, month, category, goal_amount)
                VALUES (?, ?, ?, ?)
            ''', (self.current_year, self.current_month, category, goal_amount))
            
            QMessageBox.information(self, '成功', 'カテゴリ別目標を保存しました')
            self.category_goal_input.clear()
            
            # 自分自身の表示を完全に更新
            self.update_category_table()
            self.update_progress_display()
            
            # 履歴チャートも更新
            if hasattr(self, 'update_history_chart'):
                self.update_history_chart()
            
            # ...その他の処理...
            
        except ValueError:
            QMessageBox.warning(self, '警告', '数値を正しく入力してください')
        except Exception as e:
            print(f"目標保存中にエラー: {e}")
            QMessageBox.warning(self, '警告', f'保存中にエラーが発生しました: {str(e)}')
    
    def update_progress_display(self):
        """月間目標の達成状況表示を更新"""
        
        # 月間目標を取得
        monthly_goal = execute_query('''
            SELECT savings_goal, expense_limit FROM monthly_goals
            WHERE year = ? AND month = ?
        ''', (self.current_year, self.current_month), fetch_one=True)
        
        # 現在の収入を取得
        income_result = execute_query('''
            SELECT income FROM monthly_income
            WHERE year = ? AND month = ?
        ''', (self.current_year, self.current_month), fetch_one=True)
        current_income = income_result[0] if income_result else 0
        
        # 現在の支出を取得
        expense_result = execute_query('''
            SELECT SUM(amount) FROM expenses
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        ''', (str(self.current_year), f"{self.current_month:02d}"), fetch_one=True)
        current_expense = expense_result[0] if expense_result and expense_result[0] else 0
        
        # 貯蓄額の計算
        current_savings = current_income - current_expense
        
        # プログレスバーと達成状況の更新
        if monthly_goal:
            savings_goal = monthly_goal[0]
            expense_limit = monthly_goal[1]
            
            # 貯蓄目標の達成状況
            if savings_goal > 0:
                savings_percentage = min(100, (current_savings / savings_goal) * 100)
                self.savings_progress.setValue(int(savings_percentage))
                self.savings_goal_label.setText(
                    f'貯蓄目標: {savings_goal:,.0f} 円中 {current_savings:,.0f} 円 ({savings_percentage:.1f}%)'
                )
            else:
                self.savings_progress.setValue(0)
                self.savings_goal_label.setText('貯蓄目標: 設定なし')
            
            # 支出上限の達成状況
            if expense_limit:
                expense_percentage = min(100, (current_expense / expense_limit) * 100)
                self.expense_progress.setValue(int(expense_percentage))
                self.expense_limit_label.setText(
                    f'支出上限: {expense_limit:,.0f} 円中 {current_expense:,.0f} 円 ({expense_percentage:.1f}%)'
                )
                
                # 支出が上限を超えている場合は赤色表示
                if current_expense > expense_limit:
                    self.expense_progress.setStyleSheet("QProgressBar::chunk { background-color: #FF4B4B; }")
                else:
                    self.expense_progress.setStyleSheet("")
            else:
                self.expense_progress.setValue(0)
                self.expense_limit_label.setText('支出上限: 設定なし')
        else:
            self.savings_progress.setValue(0)
            self.expense_progress.setValue(0)
            self.savings_goal_label.setText('貯蓄目標: 設定なし')
            self.expense_limit_label.setText('支出上限: 設定なし')

    def update_category_table(self):
        """カテゴリ別目標と実績の表示を更新"""
        
        # カテゴリ別目標を取得
        goals = execute_query('''
            SELECT category, goal_amount FROM category_goals
            WHERE year = ? AND month = ?
        ''', (self.current_year, self.current_month), fetch_all=True)
        
        # カテゴリ別支出を取得
        expenses = execute_query('''
            SELECT category, SUM(amount) as total_amount 
            FROM expenses
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            GROUP BY category
        ''', (str(self.current_year), f"{self.current_month:02d}"), fetch_all=True)
        
        # SQLの結果をディクショナリに変換
        expenses_dict = {category: amount for category, amount in expenses} if expenses else {}
        
        # テーブルを更新
        self.category_goal_table.setRowCount(len(goals))
        
        for row, (category, goal) in enumerate(goals):
            actual = expenses_dict.get(category, 0)
            achievement = (actual / goal * 100) if goal > 0 else 0
            
            self.category_goal_table.setItem(row, 0, QTableWidgetItem(category))
            self.category_goal_table.setItem(row, 1, QTableWidgetItem(f"{goal:,.0f}"))
            self.category_goal_table.setItem(row, 2, QTableWidgetItem(f"{actual:,.0f}"))
            
            achievement_item = QTableWidgetItem(f"{achievement:.1f}%")
            if actual > goal:
                achievement_item.setBackground(QColor("#FFE4E1"))  # 超過は薄い赤
            elif achievement >= 80:
                achievement_item.setBackground(QColor("#E0FFFF"))  # 80%以上は薄い青
            
            self.category_goal_table.setItem(row, 3, achievement_item)
    
    def update_history_chart(self):
        """目標達成履歴のチャートを更新"""
        # 過去6ヶ月分のデータを取得
        # 開始月と終了月を計算
        end_date = QDate(self.current_year, self.current_month, 1)
        start_date = end_date.addMonths(-5)
        
        months_data = []
        current_date = start_date
        
        while current_date <= end_date:
            year = current_date.year()
            month = current_date.month()
            
            # その月の目標と実績を取得
            # 月間目標
            monthly_goal = execute_query('''
                SELECT savings_goal, expense_limit FROM monthly_goals
                WHERE year = ? AND month = ?
            ''', (year, month), fetch_one=True)
            
            savings_goal = monthly_goal[0] if monthly_goal else 0
            expense_limit = monthly_goal[1] if monthly_goal and monthly_goal[1] else 0
            
            # 収入
            income_result = execute_query('''
                SELECT income FROM monthly_income
                WHERE year = ? AND month = ?
            ''', (year, month), fetch_one=True)
            
            income = income_result[0] if income_result else 0
            
            # 支出
            expense_result = execute_query('''
                SELECT SUM(amount) FROM expenses
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ''', (str(year), f"{month:02d}"), fetch_one=True)
            
            expense = expense_result[0] if expense_result and expense_result[0] else 0
            
            # 実際の貯蓄額
            actual_savings = income - expense
            
            # 貯蓄目標達成率
            savings_achievement = min(100, (actual_savings / savings_goal * 100)) if savings_goal > 0 else 0
            
            # 支出目標達成率（支出が上限以下であれば100%、超過していれば下回る割合）
            expense_achievement = min(100, (1 - (max(0, expense - expense_limit) / expense_limit)) * 100) if expense_limit > 0 else 0
            
            months_data.append({
                'year': year,
                'month': month,
                'savings_goal': savings_goal,
                'actual_savings': actual_savings,
                'savings_achievement': savings_achievement,
                'expense_limit': expense_limit,
                'actual_expense': expense,
                'expense_achievement': expense_achievement
            })
            
            current_date = current_date.addMonths(1)
        
        # チャートの作成
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # カテゴリ（X軸）のラベル
        categories = []
        savings_achievements = []
        expense_achievements = []
        
        for data in months_data:
            categories.append(f"{data['month']}月")
            savings_achievements.append(data['savings_achievement'])
            expense_achievements.append(data['expense_achievement'])
        
        # 貯蓄目標達成率のラインシリーズ
        savings_series = QLineSeries()
        savings_series.setName("貯蓄目標達成率")
        for i, value in enumerate(savings_achievements):
            savings_series.append(i, value)
        savings_series.setColor(QColor("#4CAF50"))  # 緑色
        
        # 支出目標達成率のラインシリーズ
        expense_series = QLineSeries()
        expense_series.setName("支出目標達成率")
        for i, value in enumerate(expense_achievements):
            expense_series.append(i, value)
        expense_series.setColor(QColor("#2196F3"))  # 青色
        
        # シリーズをチャートに追加
        chart.addSeries(savings_series)
        chart.addSeries(expense_series)
        
        # X軸の設定
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        savings_series.attachAxis(axis_x)
        expense_series.attachAxis(axis_x)
        
        # Y軸の設定
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setLabelFormat("%.0f%%")
        chart.addAxis(axis_y, Qt.AlignLeft)
        savings_series.attachAxis(axis_y)
        expense_series.attachAxis(axis_y)
        
        # チャートの設定
        chart.setTitle("目標達成率の推移")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        self.history_chart_view.setChart(chart)

    def delete_category_goal(self):
        """選択されたカテゴリ別目標を削除"""
        # 選択された行を取得
        selected_rows = self.category_goal_table.selectedItems()
        
        if not selected_rows:
            QMessageBox.warning(self, '警告', '削除する目標を選択してください')
            return
        
        # 選択された行のカテゴリを取得
        row = selected_rows[0].row()
        category = self.category_goal_table.item(row, 0).text()
        goal_amount = self.category_goal_table.item(row, 1).text()
        
        # 確認ダイアログ
        reply = QMessageBox.question(
            self, '確認', 
            f'{self.current_year}年{self.current_month}月の\n'
            f'「{category}」の目標（{goal_amount}円）を削除してもよろしいですか？',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # データベースから削除
            execute_query('''
                DELETE FROM category_goals
                WHERE year = ? AND month = ? AND category = ?
            ''', (self.current_year, self.current_month, category))
            
            QMessageBox.information(self, '成功', f'「{category}」の目標を削除しました')
            
            # 表示を更新
            self.update_category_table()
            self.update_progress_display()
            
            # 履歴チャートも更新
            if hasattr(self, 'update_history_chart'):
                self.update_history_chart()
            
            # 他のウィジェットも更新
            self.notify_goal_update()
            
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'削除中にエラーが発生しました: {str(e)}')

    def notify_goal_update(self):
        """目標データが更新されたことを他のウィジェットに通知"""
        try:
            # 親ウィジェット（BudgetApp）のメソッドを呼び出す
            if hasattr(self.parent, 'update_goal_data_across_widgets'):
                self.parent.update_goal_data_across_widgets()
        except Exception as e:
            print(f"目標更新通知中にエラー: {e}")    

class DiagnosticReportWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_year, self.current_month = DateHelper.get_current_year_month()
        
        # 健全性スコアの初期値
        self.health_score = 0
        
        # UIの初期化
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        layout.addLayout(self.button_layout)
        
        # 年月選択
        date_layout = QHBoxLayout()
        
        self.prev_month_button = QPushButton('前月')
        self.next_month_button = QPushButton('次月')
        self.period_label = QLabel(f'{self.current_year}年{self.current_month}月')
        
        self.prev_month_button.clicked.connect(self.show_prev_month)
        self.next_month_button.clicked.connect(self.show_next_month)
        
        date_layout.addWidget(self.prev_month_button)
        date_layout.addWidget(self.period_label)
        date_layout.addWidget(self.next_month_button)
        
        layout.addLayout(date_layout)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # タブ1: 概要
        self.summary_tab = QWidget()
        summary_layout = QVBoxLayout()
        self.summary_tab.setLayout(summary_layout)
        
        # 健全性スコア表示
        self.health_score_frame = QFrame()
        self.health_score_frame.setFrameShape(QFrame.StyledPanel)
        self.health_score_frame.setMinimumHeight(100)
        health_score_layout = QVBoxLayout()
        
        self.health_score_label = QLabel('<h2>家計健全性スコア</h2>')
        self.health_score_label.setAlignment(Qt.AlignCenter)
        self.health_score_value = QLabel('計算中...')
        self.health_score_value.setAlignment(Qt.AlignCenter)
        self.health_score_value.setStyleSheet('font-size: 48px; font-weight: bold;')
        
        health_score_layout.addWidget(self.health_score_label)
        health_score_layout.addWidget(self.health_score_value)
        self.health_score_frame.setLayout(health_score_layout)
        summary_layout.addWidget(self.health_score_frame)
        
        # 主要な改善ポイント
        self.improvement_frame = QFrame()
        self.improvement_frame.setFrameShape(QFrame.StyledPanel)
        improvement_layout = QVBoxLayout()
        
        improvement_title = QLabel('<h3>主要な改善ポイント</h3>')
        self.improvement_list = QLabel('データを分析中...')
        self.improvement_list.setWordWrap(True)
        
        improvement_layout.addWidget(improvement_title)
        improvement_layout.addWidget(self.improvement_list)
        self.improvement_frame.setLayout(improvement_layout)
        summary_layout.addWidget(self.improvement_frame)
        
        # タブ2: 詳細分析
        self.analysis_tab = QWidget()
        analysis_layout = QVBoxLayout()
        self.analysis_tab.setLayout(analysis_layout)
        
        # カテゴリ別最適化分析チャート
        self.category_analysis_view = QChartView()
        self.category_analysis_view.setMinimumHeight(300)
        analysis_layout.addWidget(QLabel('<h3>カテゴリ別支出最適化分析</h3>'))
        analysis_layout.addWidget(self.category_analysis_view)
        
        # 収支バランス分析
        self.balance_analysis_view = QChartView()
        self.balance_analysis_view.setMinimumHeight(250)
        analysis_layout.addWidget(QLabel('<h3>収支バランス分析</h3>'))
        analysis_layout.addWidget(self.balance_analysis_view)
        
        # タブ3: 改善提案
        self.improvement_tab = QWidget()
        improvement_layout = QVBoxLayout()
        self.improvement_tab.setLayout(improvement_layout)
        
        # 改善提案テーブル
        self.improvement_table = QTableWidget(0, 3)
        self.improvement_table.setHorizontalHeaderLabels(['改善アクション', '期待効果', '優先度'])
        self.improvement_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        improvement_layout.addWidget(QLabel('<h3>具体的な改善アクションプラン</h3>'))
        improvement_layout.addWidget(self.improvement_table)
        
        # 改善後の予測表示
        self.prediction_frame = QFrame()
        self.prediction_frame.setFrameShape(QFrame.StyledPanel)
        prediction_layout = QVBoxLayout()
        
        prediction_title = QLabel('<h3>改善後の予測</h3>')
        self.prediction_text = QLabel('改善案を実行した場合の予測効果...')
        self.prediction_text.setWordWrap(True)
        
        prediction_layout.addWidget(prediction_title)
        prediction_layout.addWidget(self.prediction_text)
        self.prediction_frame.setLayout(prediction_layout)
        improvement_layout.addWidget(self.prediction_frame)
        
        # タブ4: 将来予測
        self.forecast_tab = QWidget()
        forecast_layout = QVBoxLayout()
        self.forecast_tab.setLayout(forecast_layout)
        
        # 将来予測グラフ
        self.forecast_chart_view = QChartView()
        self.forecast_chart_view.setMinimumHeight(400)
        forecast_layout.addWidget(QLabel('<h3>将来資産推移予測</h3>'))
        forecast_layout.addWidget(self.forecast_chart_view)
        
        # 予測シナリオ選択
        scenario_layout = QHBoxLayout()
        scenario_layout.addWidget(QLabel('予測シナリオ:'))
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems(['現状維持', '改善案適用', '積極的節約'])
        self.scenario_combo.currentIndexChanged.connect(self.update_forecast_chart)
        scenario_layout.addWidget(self.scenario_combo)
        scenario_layout.addStretch()
        forecast_layout.addLayout(scenario_layout)
        
        # タブをタブウィジェットに追加
        self.tab_widget.addTab(self.summary_tab, "概要")
        self.tab_widget.addTab(self.analysis_tab, "詳細分析")
        self.tab_widget.addTab(self.improvement_tab, "改善提案")
        self.tab_widget.addTab(self.forecast_tab, "将来予測")
        
        layout.addWidget(self.tab_widget)
        
        # レポート更新ボタン
        self.refresh_button = QPushButton('レポート更新')
        self.refresh_button.clicked.connect(self.generate_report)
        layout.addWidget(self.refresh_button)
        
        self.setLayout(layout)
    
    def show_prev_month(self):
        self.current_year, self.current_month = DateHelper.get_prev_month(self.current_year, self.current_month)
        self.update_period_label()
        self.generate_report()

    def show_next_month(self):
        self.current_year, self.current_month = DateHelper.get_next_month(self.current_year, self.current_month)
        self.update_period_label()
        self.generate_report()

    def update_display(self):
        """現在選択されている年月に応じた表示を更新する"""
        self.update_period_label()  # 期間表示を更新
        self.generate_report()      # レポートを生成    
    
    def update_period_label(self):
        self.period_label.setText(DateHelper.format_year_month(self.current_year, self.current_month))
        
    def generate_report(self):
        """診断レポートを生成する"""
        # データ取得・分析
        try:
            self.analyze_data()
            
            # 各セクションの更新
            self.update_health_score()
            self.update_improvement_points()
            self.update_category_analysis_chart()
            self.update_balance_analysis_chart()
            self.update_improvement_table()
            self.update_prediction_text()
            self.update_forecast_chart()
        except Exception as e:
            QMessageBox.warning(self, "分析エラー", f"データの分析中にエラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def analyze_data(self):
        """データ分析を行い、結果を保存する"""
        # 収入データ
        income_result = execute_query('''
            SELECT income FROM monthly_income 
            WHERE year = ? AND month = ?
        ''', (self.current_year, self.current_month), fetch_one=True)
        
        self.current_income = income_result[0] if income_result else 0
        
        # 支出データ（カテゴリ別）
        df = fetch_df('''
            SELECT category, SUM(amount) as total_amount 
            FROM expenses 
            WHERE strftime('%Y', date) = ? 
            AND strftime('%m', date) = ?
            GROUP BY category
        ''', params=(str(self.current_year), f"{self.current_month:02d}"))
        
        self.expense_by_category = {}
        self.total_expense = 0
        if not df.empty:
            for _, row in df.iterrows():
                self.expense_by_category[row['category']] = row['total_amount']
                self.total_expense += row['total_amount']
        
        # 目標データ
        monthly_goal = execute_query('''
            SELECT savings_goal, expense_limit FROM monthly_goals
            WHERE year = ? AND month = ?
        ''', (self.current_year, self.current_month), fetch_one=True)
        
        self.savings_goal = monthly_goal[0] if monthly_goal else 0
        self.expense_limit = monthly_goal[1] if monthly_goal and monthly_goal[1] else 0
        
        # カテゴリ別目標
        category_goals_result = execute_query('''
            SELECT category, goal_amount FROM category_goals
            WHERE year = ? AND month = ?
        ''', (self.current_year, self.current_month), fetch_all=True)
        
        self.category_goals = {category: amount for category, amount in category_goals_result} if category_goals_result else {}
        
        # 過去6ヶ月のデータ（トレンド分析用）
        start_date = QDate(self.current_year, self.current_month, 1).addMonths(-5)
        self.historical_data = []
        
        current_date = start_date
        while current_date <= QDate(self.current_year, self.current_month, 1):
            year = current_date.year()
            month = current_date.month()
            
            # 収入
            income_result = execute_query('''
                SELECT income FROM monthly_income 
                WHERE year = ? AND month = ?
            ''', (year, month), fetch_one=True)
            
            month_income = income_result[0] if income_result else 0
            
            # 支出
            expense_result = execute_query('''
                SELECT SUM(amount) FROM expenses
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ''', (str(year), f"{month:02d}"), fetch_one=True)
            
            month_expense = expense_result[0] if expense_result and expense_result[0] else 0
            
            self.historical_data.append({
                'year': year,
                'month': month,
                'income': month_income,
                'expense': month_expense,
                'balance': month_income - month_expense
            })
            
            current_date = current_date.addMonths(1)
        
        # 分析結果の計算
        self.balance = self.current_income - self.total_expense
        self.savings_ratio = (self.balance / self.current_income * 100) if self.current_income > 0 else 0
        
        # 理想的な支出比率（一般的な目安）
        self.ideal_expense_ratios = {
            '住宅': 30,  # 収入の30%
            '食費': 15,  # 収入の15%
            '交通費': 10,  # 収入の10%
            '水道光熱費': 7,  # 収入の7%
            '通信費': 5,  # 収入の5%
            '娯楽': 5,  # 収入の5%
            '美容': 3,  # 収入の3%
            '健康': 5,  # 収入の5%
            '教育': 5,  # 収入の5%
            '日用品': 5,  # 収入の5%
            'その他': 10,  # 収入の10%
        }
        
        # 各カテゴリの実際の支出比率を計算
        self.actual_expense_ratios = {}
        if self.current_income > 0:
            for category, amount in self.expense_by_category.items():
                self.actual_expense_ratios[category] = (amount / self.current_income * 100)
        
        # 改善候補の特定
        self.improvement_candidates = []
        
        # 貯蓄率チェック
        if self.savings_ratio < 20:  # 理想的な貯蓄率は20-30%
            self.improvement_candidates.append({
                'action': '貯蓄率の向上',
                'effect': f'貯蓄率を20%以上に引き上げる（現在: {self.savings_ratio:.1f}%）',
                'priority': '高'
            })
        
        # カテゴリ別の支出チェック
        for category, ratio in self.actual_expense_ratios.items():
            ideal_ratio = self.ideal_expense_ratios.get(category, 5)  # デフォルトは5%
            if ratio > ideal_ratio * 1.2:  # 理想の1.2倍以上なら改善候補
                self.improvement_candidates.append({
                    'action': f'{category}の支出削減',
                    'effect': f'収入の{ideal_ratio}%以内に抑える（現在: {ratio:.1f}%）',
                    'priority': '中' if ratio > ideal_ratio * 1.5 else '低'
                })
        
        # 健全性スコアの計算（100点満点）
        score = 100
        
        # 1. 貯蓄率に基づく減点（理想は20-30%）
        if self.savings_ratio < 0:
            score -= 40  # 赤字は大幅減点
        elif self.savings_ratio < 10:
            score -= 25  # 10%未満は大きく減点
        elif self.savings_ratio < 20:
            score -= 15  # 20%未満は中程度減点
        
        # 2. カテゴリ別の支出超過に基づく減点
        category_penalty = 0
        for category, ratio in self.actual_expense_ratios.items():
            ideal_ratio = self.ideal_expense_ratios.get(category, 5)
            if ratio > ideal_ratio * 1.5:
                category_penalty += 5  # 大幅超過は大きく減点
            elif ratio > ideal_ratio * 1.2:
                category_penalty += 2  # 超過は小さく減点
        
        score = max(0, score - min(30, category_penalty))  # カテゴリ減点は最大30点まで
        
        # 3. 目標達成度に基づく追加減点
        if self.expense_limit > 0 and self.total_expense > self.expense_limit:
            score -= 10  # 支出上限超過で減点
        
        if self.savings_goal > 0 and self.balance < self.savings_goal:
            score -= 10  # 貯蓄目標未達で減点
        
        self.health_score = score
        
    def update_health_score(self):
        """健全性スコアの表示を更新"""
        self.health_score_value.setText(f'{self.health_score}/100')
        
        # スコアに応じて色を変更
        if self.health_score >= 80:
            self.health_score_value.setStyleSheet('font-size: 48px; font-weight: bold; color: #2E8B57;')  # 緑
        elif self.health_score >= 60:
            self.health_score_value.setStyleSheet('font-size: 48px; font-weight: bold; color: #DAA520;')  # 黄金
        else:
            self.health_score_value.setStyleSheet('font-size: 48px; font-weight: bold; color: #B22222;')  # 赤
    
    def update_improvement_points(self):
        """改善ポイントの表示を更新"""
        if not hasattr(self, 'improvement_candidates') or not self.improvement_candidates:
            self.improvement_list.setText("現状では特に大きな改善点は見つかりませんでした。このまま良好な家計管理を続けましょう。")
            return
        
        # 最大3つの改善点を表示
        points = []
        for i, candidate in enumerate(self.improvement_candidates[:3]):
            points.append(f"<b>{i+1}. {candidate['action']}</b>: {candidate['effect']}")
        
        self.improvement_list.setText('<br>'.join(points))
    
    def update_category_analysis_chart(self):
        """カテゴリ別最適化分析チャートを更新"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # カテゴリごとに実際の支出比率と理想比率を表示
        if hasattr(self, 'expense_by_category'):
            categories = list(self.expense_by_category.keys())
            
            # 実際の支出比率（青色のバー）
            actual_set = QBarSet('実際の比率')
            actual_set.setColor(QColor("#4682B4"))  # スティールブルー
            
            # 理想の支出比率（緑色のバー）
            ideal_set = QBarSet('理想的な比率')
            ideal_set.setColor(QColor("#2E8B57"))  # シーグリーン
            
            for category in categories:
                if hasattr(self, 'actual_expense_ratios'):
                    actual_ratio = self.actual_expense_ratios.get(category, 0)
                else:
                    actual_ratio = 0
                
                if hasattr(self, 'ideal_expense_ratios'):
                    ideal_ratio = self.ideal_expense_ratios.get(category, 5)
                else:
                    ideal_ratio = 5
                
                actual_set.append(actual_ratio)
                ideal_set.append(ideal_ratio)
            
            # バーシリーズの作成
            series = QBarSeries()
            series.append(actual_set)
            series.append(ideal_set)
            
            # グラフの設定
            chart.addSeries(series)
            chart.setTitle("カテゴリ別支出比率（収入に対する割合）")
            
            # X軸の設定
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)
            
            # Y軸の設定
            axis_y = QValueAxis()
            if hasattr(self, 'actual_expense_ratios') and self.actual_expense_ratios:
                max_ratio = max(self.actual_expense_ratios.values(), default=5)
            else:
                max_ratio = 5
            axis_y.setRange(0, max(max_ratio, 30) * 1.1)
            axis_y.setLabelFormat("%.1f%%")
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)
            
            # 凡例の設定
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)
        else:
            # データがない場合のダミーグラフ
            series = QBarSeries()
            chart.addSeries(series)
            chart.setTitle("データが不足しています")
        
        # チャートビューに設定
        self.category_analysis_view.setChart(chart)
    
    def update_balance_analysis_chart(self):
        """収支バランス分析チャートを更新"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # データの確認
        if hasattr(self, 'historical_data') and self.historical_data:
            # 過去6ヶ月の収入と支出をグラフ化
            months = [f"{data['month']}月" for data in self.historical_data]
            
            # 収入用のライン
            income_series = QLineSeries()
            income_series.setName("収入")
            
            # 支出用のライン
            expense_series = QLineSeries()
            expense_series.setName("支出")
            
            # 収支用のライン
            balance_series = QLineSeries()
            balance_series.setName("収支")
            
            for i, data in enumerate(self.historical_data):
                income_series.append(i, data['income'])
                expense_series.append(i, data['expense'])
                balance_series.append(i, data['balance'])
            
            # シリーズをチャートに追加
            chart.addSeries(income_series)
            chart.addSeries(expense_series)
            chart.addSeries(balance_series)
            
            # X軸の設定
            axis_x = QBarCategoryAxis()
            axis_x.append(months)
            chart.addAxis(axis_x, Qt.AlignBottom)
            income_series.attachAxis(axis_x)
            expense_series.attachAxis(axis_x)
            balance_series.attachAxis(axis_x)
            
            # Y軸の設定
            all_values = []
            for data in self.historical_data:
                all_values.extend([data['income'], data['expense'], data['balance']])
            
            max_value = max(all_values) if all_values else 100000
            min_value = min(all_values) if all_values else 0
            
            axis_y = QValueAxis()
            axis_y.setRange(min(0, min_value * 1.1), max_value * 1.1)
            axis_y.setLabelFormat("%,.0f")
            chart.addAxis(axis_y, Qt.AlignLeft)
            income_series.attachAxis(axis_y)
            expense_series.attachAxis(axis_y)
            balance_series.attachAxis(axis_y)
            
            # シリーズのカラー設定
            income_series.setColor(QColor("#4CAF50"))  # 緑
            expense_series.setColor(QColor("#F44336"))  # 赤
            balance_series.setColor(QColor("#2196F3"))  # 青
            
            # シリーズの線幅を設定
            pen = income_series.pen()
            pen.setWidth(3)
            income_series.setPen(pen)
            
            pen = expense_series.pen()
            pen.setWidth(3)
            expense_series.setPen(pen)
            
            pen = balance_series.pen()
            pen.setWidth(3)
            balance_series.setPen(pen)
            
            # チャートの設定
            chart.setTitle("月次収支推移")
        else:
            # データがない場合のダミーグラフ
            series = QLineSeries()
            chart.addSeries(series)
            chart.setTitle("十分なデータがありません")
        
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        # チャートビューに設定
        self.balance_analysis_view.setChart(chart)
    
    def update_balance_analysis_chart(self):
        """収支バランス分析チャートを更新"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # データの確認
        if hasattr(self, 'historical_data') and self.historical_data:
            # 過去6ヶ月の収入と支出をグラフ化
            months = [f"{data['month']}月" for data in self.historical_data]
            
            # 収入用のライン
            income_series = QLineSeries()
            income_series.setName("収入")
            
            # 支出用のライン
            expense_series = QLineSeries()
            expense_series.setName("支出")
            
            # 収支用のライン
            balance_series = QLineSeries()
            balance_series.setName("収支")
            
            for i, data in enumerate(self.historical_data):
                income_series.append(i, data['income'])
                expense_series.append(i, data['expense'])
                balance_series.append(i, data['balance'])
            
            # シリーズをチャートに追加
            chart.addSeries(income_series)
            chart.addSeries(expense_series)
            chart.addSeries(balance_series)
            
            # X軸の設定
            axis_x = QBarCategoryAxis()
            axis_x.append(months)
            chart.addAxis(axis_x, Qt.AlignBottom)
            income_series.attachAxis(axis_x)
            expense_series.attachAxis(axis_x)
            balance_series.attachAxis(axis_x)
            
            # Y軸の設定
            all_values = []
            for data in self.historical_data:
                all_values.extend([data['income'], data['expense'], data['balance']])
            
            max_value = max(all_values) if all_values else 100000
            min_value = min(all_values) if all_values else 0
            
            axis_y = QValueAxis()
            axis_y.setRange(min(0, min_value * 1.1), max_value * 1.1)
            axis_y.setLabelFormat("%,.0f")
            chart.addAxis(axis_y, Qt.AlignLeft)
            income_series.attachAxis(axis_y)
            expense_series.attachAxis(axis_y)
            balance_series.attachAxis(axis_y)
            
            # シリーズのカラー設定
            income_series.setColor(QColor("#4CAF50"))  # 緑
            expense_series.setColor(QColor("#F44336"))  # 赤
            balance_series.setColor(QColor("#2196F3"))  # 青
            
            # シリーズの線幅を設定
            pen = income_series.pen()
            pen.setWidth(3)
            income_series.setPen(pen)
            
            pen = expense_series.pen()
            pen.setWidth(3)
            expense_series.setPen(pen)
            
            pen = balance_series.pen()
            pen.setWidth(3)
            balance_series.setPen(pen)
            
            # チャートの設定
            chart.setTitle("月次収支推移")
        else:
            # データがない場合のダミーグラフ
            series = QLineSeries()
            chart.addSeries(series)
            chart.setTitle("十分なデータがありません")
        
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        # チャートビューに設定
        self.balance_analysis_view.setChart(chart)
    
    def update_improvement_table(self):
        """改善提案テーブルを更新"""
        # データの確認
        if not hasattr(self, 'improvement_candidates'):
            self.improvement_candidates = []
            
        self.improvement_table.setRowCount(len(self.improvement_candidates))
        
        # 優先度に応じた背景色を設定
        colors = {
            '高': QColor("#FFEBEE"),  # 薄い赤
            '中': QColor("#FFF8E1"),  # 薄い黄色
            '低': QColor("#E8F5E9")   # 薄い緑
        }
        
        for row, candidate in enumerate(self.improvement_candidates):
            action_item = QTableWidgetItem(candidate['action'])
            effect_item = QTableWidgetItem(candidate['effect'])
            priority_item = QTableWidgetItem(candidate['priority'])
            
            # 優先度に応じた背景色を設定
            priority_color = colors.get(candidate['priority'], QColor("#FFFFFF"))
            action_item.setBackground(priority_color)
            effect_item.setBackground(priority_color)
            priority_item.setBackground(priority_color)
            
            self.improvement_table.setItem(row, 0, action_item)
            self.improvement_table.setItem(row, 1, effect_item)
            self.improvement_table.setItem(row, 2, priority_item)
        
        # 列の幅を調整
        self.improvement_table.resizeColumnsToContents()
    
    def update_prediction_text(self):
        """改善後の予測テキストを更新"""
        if not hasattr(self, 'improvement_candidates') or not self.improvement_candidates:
            self.prediction_text.setText('現在の家計管理は良好です。このまま継続することで、安定した資産形成が期待できます。')
            return
        
        # 改善効果の予測
        if hasattr(self, 'balance'):
            current_savings = self.balance
        else:
            current_savings = 0
            
        potential_savings = current_savings
        
        for candidate in self.improvement_candidates:
            if '支出削減' in candidate['action']:
                category = candidate['action'].split('の')[0]
                
                if hasattr(self, 'ideal_expense_ratios') and hasattr(self, 'expense_by_category') and hasattr(self, 'current_income'):
                    ideal_ratio = self.ideal_expense_ratios.get(category, 5)
                    actual_amount = self.expense_by_category.get(category, 0)
                    ideal_amount = self.current_income * ideal_ratio / 100
                    
                    if actual_amount > ideal_amount:
                        potential_savings += (actual_amount - ideal_amount)
        
        monthly_increase = potential_savings - current_savings
        yearly_increase = monthly_increase * 12
        
        if monthly_increase > 0:
            if hasattr(self, 'current_income') and self.current_income > 0:
                savings_ratio = self.balance / self.current_income * 100 if hasattr(self, 'balance') else 0
                potential_ratio = potential_savings / self.current_income * 100
                ratio_text = f'これにより、貯蓄率は現在の<b>{savings_ratio:.1f}%</b>から<b>{potential_ratio:.1f}%</b>に向上します。'
            else:
                ratio_text = ""
                
            self.prediction_text.setText(
                f'提案した改善策をすべて実行した場合、月間の貯蓄額が<b>約{monthly_increase:,.0f}円増加</b>し、'
                f'年間では<b>約{yearly_increase:,.0f}円の追加貯蓄</b>が期待できます。\n\n'
                f'{ratio_text}'
            )
        else:
            self.prediction_text.setText('現在の家計状況では、大きな改善効果は期待できません。収入を増やすか、支出の内訳を見直すことを検討してください。')
    
    def update_forecast_chart(self):
        """将来予測チャートを更新"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 選択されたシナリオに基づいて予測
        scenario = self.scenario_combo.currentText()
        
        # データの確認
        if hasattr(self, 'balance'):
            # 現在の月間貯蓄額
            monthly_savings = self.balance
            
            # シナリオに応じた貯蓄額の調整
            if scenario == '改善案適用':
                # 改善候補からの追加貯蓄額を計算
                if hasattr(self, 'improvement_candidates'):
                    for candidate in self.improvement_candidates:
                        if '支出削減' in candidate['action']:
                            category = candidate['action'].split('の')[0]
                            
                            if hasattr(self, 'ideal_expense_ratios') and hasattr(self, 'expense_by_category') and hasattr(self, 'current_income'):
                                ideal_ratio = self.ideal_expense_ratios.get(category, 5)
                                actual_amount = self.expense_by_category.get(category, 0)
                                ideal_amount = self.current_income * ideal_ratio / 100
                                
                                if actual_amount > ideal_amount:
                                    monthly_savings += (actual_amount - ideal_amount)
            
            elif scenario == '積極的節約':
                # より積極的な節約を想定
                monthly_savings *= 1.5  # 50%増
            
            # 過去の平均貯蓄額（直近3ヶ月）
            if hasattr(self, 'historical_data') and len(self.historical_data) >= 3:
                recent_savings = [data['balance'] for data in self.historical_data[-3:]]
                avg_recent_savings = sum(recent_savings) / len(recent_savings) if recent_savings else monthly_savings
            else:
                avg_recent_savings = monthly_savings
            
            # 貯蓄のトレンドを加味
            savings_trend = monthly_savings / avg_recent_savings if avg_recent_savings > 0 else 1
            
            # 10年分の資産推移をシミュレーション
            years = 10
            months = years * 12
            
            # 初期資産（直近6ヶ月の貯蓄総額とする）
            if hasattr(self, 'historical_data'):
                initial_assets = sum(data['balance'] for data in self.historical_data if data['balance'] > 0)
            else:
                initial_assets = monthly_savings * 6  # 仮の初期資産
            
            # 資産推移のシリーズ
            asset_series = QLineSeries()
            asset_series.setName("総資産")
            
            assets = initial_assets
            for i in range(months + 1):
                asset_series.append(i / 12, assets)  # X軸は年数
                
                # 毎月の貯蓄を加算
                adjusted_savings = monthly_savings
                
                # トレンドを反映（時間とともに変化）
                if i > 0:
                    trend_factor = 1 + (savings_trend - 1) * min(1, i / 36)  # 3年かけて完全にトレンドを反映
                    adjusted_savings *= trend_factor
                
                assets += adjusted_savings
            
            # 比較用の基準シリーズ（現状維持）
            if scenario != '現状維持':
                baseline_series = QLineSeries()
                baseline_series.setName("現状維持")
                
                baseline_assets = initial_assets
                for i in range(months + 1):
                    baseline_series.append(i / 12, baseline_assets)
                    baseline_assets += monthly_savings
                
                chart.addSeries(baseline_series)
                
                # 基準シリーズのスタイル設定
                pen = baseline_series.pen()
                pen.setStyle(Qt.DotLine)
                pen.setWidth(2)
                pen.setColor(QColor("#9E9E9E"))  # グレー
                baseline_series.setPen(pen)
            
            # シリーズをチャートに追加
            chart.addSeries(asset_series)
            
            # X軸（年数）の設定
            axis_x = QValueAxis()
            axis_x.setRange(0, years)
            axis_x.setLabelFormat("%d年")
            axis_x.setTickCount(years + 1)
            chart.addAxis(axis_x, Qt.AlignBottom)
            asset_series.attachAxis(axis_x)
            if scenario != '現状維持':
                baseline_series.attachAxis(axis_x)
            
            # Y軸（資産額）の設定
            max_assets = max(monthly_savings * months + initial_assets, initial_assets * 2)
            axis_y = QValueAxis()
            axis_y.setRange(0, max_assets * 1.1)
            axis_y.setLabelFormat("%,.0f")
            chart.addAxis(axis_y, Qt.AlignLeft)
            asset_series.attachAxis(axis_y)
            if scenario != '現状維持':
                baseline_series.attachAxis(axis_y)
            
            # シリーズのカラーとスタイル設定
            pen = asset_series.pen()
            pen.setWidth(3)
            
            if scenario == '現状維持':
                pen.setColor(QColor("#2196F3"))  # 青
            elif scenario == '改善案適用':
                pen.setColor(QColor("#4CAF50"))  # 緑
            else:  # 積極的節約
                pen.setColor(QColor("#9C27B0"))  # 紫
            
            asset_series.setPen(pen)
            
            # チャートのタイトルと凡例
            chart.setTitle(f"{years}年間の資産推移予測（{scenario}シナリオ）")
        else:
            # データがない場合のダミーグラフ
            series = QLineSeries()
            chart.addSeries(series)
            chart.setTitle("十分なデータがありません")
        
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        # チャートビューに設定
        self.forecast_chart_view.setChart(chart)
  


class BackupManager:
    def __init__(self, db_path='budget.db', backup_dir='backups'):
        """バックアップマネージャークラスの初期化"""
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        # バックアップディレクトリが存在しない場合は作成
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
    
    def create_backup(self, custom_name=None):
        """データベースのバックアップを作成"""
        try:
            # バックアップファイル名の生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if custom_name:
                backup_name = f"{custom_name}_{timestamp}.db"
            else:
                backup_name = f"budget_backup_{timestamp}.db"
                
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # データベースファイルをコピー
            shutil.copy2(self.db_path, backup_path)
            
            return backup_path
        except Exception as e:
            raise Exception(f"バックアップの作成に失敗しました: {str(e)}")
    
    def restore_backup(self, backup_path):
        """バックアップからデータベースを復元"""
        try:
            # 現在のデータベースの自動バックアップを作成
            auto_backup_name = f"auto_backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            auto_backup_path = os.path.join(self.backup_dir, auto_backup_name)
            
            # 現在のDBをバックアップ
            shutil.copy2(self.db_path, auto_backup_path)
            
            # バックアップから復元
            shutil.copy2(backup_path, self.db_path)
            
            return True
        except Exception as e:
            raise Exception(f"復元に失敗しました: {str(e)}")
    
    def get_all_backups(self):
        """利用可能なすべてのバックアップを取得"""
        backups = []
        
        for file in os.listdir(self.backup_dir):
            if file.endswith('.db'):
                file_path = os.path.join(self.backup_dir, file)
                file_stat = os.stat(file_path)
                
                backups.append({
                    'name': file,
                    'path': file_path,
                    'size': file_stat.st_size,
                    'date': datetime.fromtimestamp(file_stat.st_mtime)
                })
        
        # 日付の新しい順にソート
        backups.sort(key=lambda x: x['date'], reverse=True)
        
        return backups
    
    def delete_backup(self, backup_path):
        """バックアップファイルを削除"""
        try:
            os.remove(backup_path)
            return True
        except Exception as e:
            raise Exception(f"バックアップの削除に失敗しました: {str(e)}")
    
    def auto_backup(self, max_backups=5):
        """自動バックアップを実行し、古いバックアップを削除"""
        try:
            # 新しいバックアップを作成
            backup_path = self.create_backup("auto")
            
            # バックアップリストを取得
            backups = self.get_all_backups()
            
            # 自動バックアップだけをフィルタリング
            auto_backups = [b for b in backups if b['name'].startswith('auto_')]
            
            # 最大数を超える古いバックアップを削除
            if len(auto_backups) > max_backups:
                for backup in auto_backups[max_backups:]:
                    self.delete_backup(backup['path'])
            
            return backup_path
        except Exception as e:
            raise Exception(f"自動バックアップに失敗しました: {str(e)}")

# バックアップ設定ダイアログ
class BackupSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("バックアップ設定")
        self.setMinimumWidth(400)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 自動バックアップの設定
        self.auto_backup_check = QCheckBox("アプリ起動時に自動バックアップを作成")
        layout.addWidget(self.auto_backup_check)
        
        # 保持するバックアップ数
        backup_count_layout = QHBoxLayout()
        backup_count_layout.addWidget(QLabel("保持する自動バックアップの数:"))
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 50)
        self.backup_count_spin.setValue(5)
        backup_count_layout.addWidget(self.backup_count_spin)
        
        layout.addLayout(backup_count_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """設定を読み込む"""
        # ここでは簡易的に実装。実際はファイルから読み込むなど
        # QSettingsなどを使うとよい
        self.auto_backup_check.setChecked(True)
        self.backup_count_spin.setValue(5)
    
    def save_settings(self):
        """設定を保存"""
        # 設定を保存する処理（実際のアプリケーション用に実装必要）
        self.accept()

# バックアップ管理ダイアログ
class BackupManagerDialog(QDialog):
    def __init__(self, backup_manager, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        self.setWindowTitle("バックアップ管理")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self.init_ui()
        self.load_backups()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # バックアップリスト
        self.backup_list = QListWidget()
        layout.addWidget(QLabel("利用可能なバックアップ:"))
        layout.addWidget(self.backup_list)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        
        self.create_button = QPushButton("新規バックアップ")
        self.create_button.clicked.connect(self.create_backup)
        
        self.restore_button = QPushButton("選択したバックアップから復元")
        self.restore_button.clicked.connect(self.restore_backup)
        
        self.delete_button = QPushButton("選択したバックアップを削除")
        self.delete_button.clicked.connect(self.delete_backup)
        
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.restore_button)
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
        
        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
    
    def load_backups(self):
        """バックアップリストを読み込む"""
        self.backup_list.clear()
        
        backups = self.backup_manager.get_all_backups()
        
        for backup in backups:
            size_mb = backup['size'] / (1024 * 1024)
            item_text = f"{backup['name']} - {backup['date'].strftime('%Y-%m-%d %H:%M:%S')} ({size_mb:.2f} MB)"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, backup['path'])
            self.backup_list.addItem(item)
    
    def create_backup(self):
        """新規バックアップを作成"""
        try:
            custom_name, ok = QFileDialog.getSaveFileName(
                self, "バックアップ名を入力", 
                f"budget_backup_{datetime.now().strftime('%Y%m%d')}",
                "データベースバックアップ (*.db)"
            )
            
            if not ok or not custom_name:
                return
                
            # ファイル名のみを取得（パスなし）
            custom_name = os.path.basename(custom_name)
            # 拡張子を削除
            custom_name = os.path.splitext(custom_name)[0]
            
            backup_path = self.backup_manager.create_backup(custom_name)
            QMessageBox.information(self, "成功", f"バックアップが正常に作成されました。\n{backup_path}")
            
            self.load_backups()
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))
    
    def restore_backup(self):
        """選択したバックアップから復元"""
        selected_items = self.backup_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "復元するバックアップを選択してください。")
            return
            
        backup_path = selected_items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "確認", 
            "選択したバックアップから復元します。\n"
            "現在のデータはすべて上書きされます。\n"
            "続行しますか？",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            self.backup_manager.restore_backup(backup_path)
            QMessageBox.information(
                self, "成功", 
                "バックアップから正常に復元されました。\n"
                "アプリケーションを再起動して変更を反映してください。"
            )
            
            # アプリケーションを終了
            self.accept()
            if self.parent():
                self.parent().close()
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))
    
    def delete_backup(self):
        """選択したバックアップを削除"""
        selected_items = self.backup_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "削除するバックアップを選択してください。")
            return
            
        backup_path = selected_items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "確認", 
            "選択したバックアップを削除します。\n"
            "この操作は元に戻せません。\n"
            "続行しますか？",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            self.backup_manager.delete_backup(backup_path)
            QMessageBox.information(self, "成功", "バックアップが正常に削除されました。")
            
            self.load_backups()
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))        

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
        c = conn.cursor()
        
        c.execute('UPDATE categories SET sort_order = ? WHERE id = ?', (target_order, current_id))
        c.execute('UPDATE categories SET sort_order = ? WHERE id = ?', (current_order, target_id))
        
        conn.commit()
        conn.close()
        
        # テーブル表示を更新
        self.load_categories()
        
        # 選択状態を移動先の行に移す
        self.category_table.selectRow(target_row)

# 2. 貯金目標設定・管理用のクラスを作成

class SavingsGoalDialog(QDialog):
    def __init__(self, goal_id=None, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.goal_id = goal_id
        self.setWindowTitle('貯金目標の設定')
        self.setMinimumWidth(400)
        self.initUI()
        
        if goal_id:
            self.load_goal_data()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # フォームレイアウト
        form_layout = QFormLayout()
        
        # 目標名
        self.name_input = QLineEdit()
        form_layout.addRow('目標名:', self.name_input)
        
        # 目標金額
        self.target_amount_input = QLineEdit()
        self.target_amount_input.setPlaceholderText('例: 1000000')
        form_layout.addRow('目標金額 (円):', self.target_amount_input)
        
        # 現在の貯金額
        self.current_amount_input = QLineEdit()
        self.current_amount_input.setPlaceholderText('例: 50000')
        form_layout.addRow('現在の貯金額 (円):', self.current_amount_input)
        
        # 開始日
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        form_layout.addRow('開始日:', self.start_date_edit)
        
        # 目標日
        self.target_date_edit = QDateEdit()
        self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.setDate(QDate.currentDate().addMonths(12))  # デフォルトは1年後
        self.target_date_checkbox = QCheckBox('期限を設定する')
        self.target_date_checkbox.setChecked(True)
        self.target_date_checkbox.stateChanged.connect(self.toggle_target_date)
        
        target_date_layout = QHBoxLayout()
        target_date_layout.addWidget(self.target_date_checkbox)
        target_date_layout.addWidget(self.target_date_edit)
        form_layout.addRow('目標日:', target_date_layout)
        
        # 説明
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        form_layout.addRow('説明:', self.description_input)
        
        # 色選択
        self.color_button = QPushButton()
        self.color_button.setFixedSize(30, 30)
        self.current_color = QColor('#4CAF50')  # デフォルト色
        self.update_color_button()
        self.color_button.clicked.connect(self.select_color)
        form_layout.addRow('色:', self.color_button)
        
        layout.addLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        save_button = QPushButton('保存')
        save_button.clicked.connect(self.save_goal)
        cancel_button = QPushButton('キャンセル')
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def toggle_target_date(self, state):
        self.target_date_edit.setEnabled(state == Qt.Checked)
    
    def update_color_button(self):
        style = f"background-color: {self.current_color.name()}; border: 1px solid #888;"
        self.color_button.setStyleSheet(style)
    
    def select_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.update_color_button()
    
    def load_goal_data(self):
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        c.execute('''
            SELECT name, target_amount, current_amount, start_date, target_date, description, color
            FROM savings_goals WHERE id = ?
        ''', (self.goal_id,))
        
        goal = c.fetchone()
        conn.close()
        
        if goal:
            name, target_amount, current_amount, start_date, target_date, description, color = goal
            
            self.name_input.setText(name)
            self.target_amount_input.setText(str(target_amount))
            self.current_amount_input.setText(str(current_amount))
            
            # 開始日の設定
            self.start_date_edit.setDate(QDate.fromString(start_date, 'yyyy-MM-dd'))
            
            # 目標日の設定
            if target_date:
                self.target_date_edit.setDate(QDate.fromString(target_date, 'yyyy-MM-dd'))
                self.target_date_checkbox.setChecked(True)
            else:
                self.target_date_checkbox.setChecked(False)
                self.target_date_edit.setEnabled(False)
            
            self.description_input.setPlainText(description or '')
            
            # 色の設定
            if color:
                self.current_color = QColor(color)
                self.update_color_button()
    
    def save_goal(self):
        # 入力値の検証
        try:
            name = self.name_input.text().strip()
            if not name:
                raise ValueError("目標名を入力してください")
            
            target_amount = float(self.target_amount_input.text().replace(',', ''))
            if target_amount <= 0:
                raise ValueError("目標金額は正の数を入力してください")
            
            current_amount_text = self.current_amount_input.text().strip()
            current_amount = float(current_amount_text.replace(',', '')) if current_amount_text else 0
            if current_amount < 0:
                raise ValueError("現在の貯金額は0以上の数を入力してください")
            
            start_date = self.start_date_edit.date().toString('yyyy-MM-dd')
            
            if self.target_date_checkbox.isChecked():
                target_date = self.target_date_edit.date().toString('yyyy-MM-dd')
                if self.target_date_edit.date() < self.start_date_edit.date():
                    raise ValueError("目標日は開始日より後の日付を設定してください")
            else:
                target_date = None
            
            description = self.description_input.toPlainText()
            color = self.current_color.name()
            
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            
            if self.goal_id:  # 既存の目標を更新
                c.execute('''
                    UPDATE savings_goals 
                    SET name = ?, target_amount = ?, current_amount = ?, start_date = ?, 
                        target_date = ?, description = ?, color = ?
                    WHERE id = ?
                ''', (name, target_amount, current_amount, start_date, 
                      target_date, description, color, self.goal_id))
            else:  # 新しい目標を作成
                c.execute('''
                    INSERT INTO savings_goals 
                    (name, target_amount, current_amount, start_date, target_date, description, color)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, target_amount, current_amount, start_date, 
                      target_date, description, color))
            
            conn.commit()
            conn.close()
            
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, '入力エラー', str(e))
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'保存中にエラーが発生しました: {str(e)}')


class SavingsGoalWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        self.load_goals()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        layout.addLayout(self.button_layout)
        
        # 目標一覧エリア
        self.goals_scroll_area = QScrollArea()
        self.goals_scroll_area.setWidgetResizable(True)
        self.goals_container = QWidget()
        self.goals_layout = QVBoxLayout(self.goals_container)
        self.goals_scroll_area.setWidget(self.goals_container)
        layout.addWidget(self.goals_scroll_area)
        
        # 新規目標ボタン
        self.add_goal_button = QPushButton('+ 新しい貯金目標を追加')
        self.add_goal_button.clicked.connect(self.add_new_goal)
        layout.addWidget(self.add_goal_button)
        
        self.setLayout(layout)
    
    def load_goals(self):
        # 既存の目標表示をクリア
        while self.goals_layout.count():
            item = self.goals_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        c.execute('''
            SELECT id, name, target_amount, current_amount, start_date, target_date, description, color, is_completed
            FROM savings_goals
            ORDER BY is_completed, start_date DESC
        ''')
        
        goals = c.fetchall()
        conn.close()
        
        if not goals:
            # 目標がない場合のメッセージ
            no_goals_label = QLabel("貯金目標がまだ設定されていません。\n「+ 新しい貯金目標を追加」ボタンをクリックして最初の目標を設定しましょう。")
            no_goals_label.setAlignment(Qt.AlignCenter)
            no_goals_label.setStyleSheet("color: #666; margin: 50px;")
            self.goals_layout.addWidget(no_goals_label)
            return
        
        # 各目標のカードを作成
        for goal in goals:
            goal_id, name, target_amount, current_amount, start_date, target_date, description, color, is_completed = goal
            self.add_goal_card(goal_id, name, target_amount, current_amount, start_date, target_date, description, color, is_completed)
    
    def add_goal_card(self, goal_id, name, target_amount, current_amount, start_date, target_date, description, color, is_completed):
        # 目標カードのフレーム作成
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"QFrame {{ border: 1px solid #ddd; border-radius: 8px; margin: 5px; background-color: #fff; }}")
        
        card_layout = QVBoxLayout()
        
        # 目標名と編集/削除ボタン
        header_layout = QHBoxLayout()
        title_label = QLabel(f"<b>{name}</b>")
        title_label.setStyleSheet(f"color: {color}; font-size: 16px;")
        header_layout.addWidget(title_label)
        
        # 編集ボタン
        edit_button = QPushButton("編集")
        edit_button.setFixedSize(60, 25)
        edit_button.clicked.connect(lambda: self.edit_goal(goal_id))
        
        # 削除ボタン
        delete_button = QPushButton("削除")
        delete_button.setFixedSize(60, 25)
        delete_button.clicked.connect(lambda: self.delete_goal(goal_id, name))
        
        # 完了/未完了の切り替えボタン
        complete_button = QPushButton("完了" if not is_completed else "未完了")
        complete_button.setFixedSize(60, 25)
        complete_button.clicked.connect(lambda: self.toggle_goal_completion(goal_id, is_completed))
        
        header_layout.addStretch()
        header_layout.addWidget(edit_button)
        header_layout.addWidget(delete_button)
        header_layout.addWidget(complete_button)
        
        card_layout.addLayout(header_layout)
        
        # 進捗バー
        progress_bar = QProgressBar()
        progress_value = min(100, int((current_amount / target_amount) * 100)) if target_amount > 0 else 0
        progress_bar.setValue(progress_value)
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{progress_value}% ({current_amount:,.0f}円 / {target_amount:,.0f}円)")
        
        # 進捗バーの色を設定
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                width: 10px;
            }}
        """)
        
        card_layout.addWidget(progress_bar)
        
        # 詳細情報
        details_layout = QFormLayout()
        
        # 開始日
        start_date_label = QLabel(start_date)
        details_layout.addRow("開始日:", start_date_label)
        
        # 目標日（設定されている場合）
        if target_date:
            # 残り日数の計算
            target_qdate = QDate.fromString(target_date, "yyyy-MM-dd")
            current_qdate = QDate.currentDate()
            days_left = current_qdate.daysTo(target_qdate)
            
            target_date_info = f"{target_date} (あと{days_left}日)" if days_left > 0 else f"{target_date} (期限超過)"
            target_date_label = QLabel(target_date_info)
            details_layout.addRow("目標日:", target_date_label)
        
        # 説明（あれば表示）
        if description:
            description_label = QLabel(description)
            description_label.setWordWrap(True)
            details_layout.addRow("説明:", description_label)
        
        # 平均必要貯金額
        if target_date and not is_completed:
            target_qdate = QDate.fromString(target_date, "yyyy-MM-dd")
            current_qdate = QDate.currentDate()
            days_left = current_qdate.daysTo(target_qdate)
            
            if days_left > 0:
                amount_left = target_amount - current_amount
                daily_saving = amount_left / days_left
                monthly_saving = daily_saving * 30
                
                savings_pace_label = QLabel(f"1日: {daily_saving:,.0f}円 / 月: {monthly_saving:,.0f}円")
                details_layout.addRow("目標達成に必要な貯金ペース:", savings_pace_label)
        
        card_layout.addLayout(details_layout)
        
        # 入金ボタン
        if not is_completed:
            deposit_button = QPushButton("入金を記録")
            deposit_button.clicked.connect(lambda: self.record_deposit(goal_id, name, target_amount, current_amount))
            card_layout.addWidget(deposit_button)
        
        card.setLayout(card_layout)
        self.goals_layout.addWidget(card)
    
    def add_new_goal(self):
        dialog = SavingsGoalDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_goals()
    
    def edit_goal(self, goal_id):
        dialog = SavingsGoalDialog(goal_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_goals()
    
    def delete_goal(self, goal_id, name):
        reply = QMessageBox.question(
            self, '確認', 
            f'貯金目標「{name}」を削除してもよろしいですか？\n関連する全ての入金記録も削除されます。',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            
            # 関連する入金記録を削除
            c.execute('DELETE FROM savings_transactions WHERE goal_id = ?', (goal_id,))
            
            # 目標を削除
            c.execute('DELETE FROM savings_goals WHERE id = ?', (goal_id,))
            
            conn.commit()
            conn.close()
            
            self.load_goals()
            
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'削除中にエラーが発生しました: {str(e)}')
    
    def toggle_goal_completion(self, goal_id, current_state):
        new_state = not current_state
        status_text = "完了" if new_state else "未完了"
        
        try:
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            c.execute('UPDATE savings_goals SET is_completed = ? WHERE id = ?', (int(new_state), goal_id))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, '状態変更', f'目標を{status_text}状態に変更しました。')
            self.load_goals()
            
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'状態変更中にエラーが発生しました: {str(e)}')
    
    def record_deposit(self, goal_id, goal_name, target_amount, current_amount):
        """目標への入金を記録"""
        # 入金ダイアログ
        amount, ok = QInputDialog.getDouble(
            self, '入金記録', 
            f'目標「{goal_name}」への入金額を入力してください:',
            0, 0, 1000000000, 0
        )
        
        if not ok or amount <= 0:
            return
        
        # 説明の入力
        description, ok = QInputDialog.getText(
            self, '入金記録', 
            '説明（任意）:',
            QLineEdit.Normal, ''
        )
        
        if not ok:
            return
        
        try:
            # 入金記録を追加
            today = QDate.currentDate().toString('yyyy-MM-dd')
            execute_query('''
                INSERT INTO savings_transactions (goal_id, amount, date, description)
                VALUES (?, ?, ?, ?)
            ''', (goal_id, amount, today, description))
            
            # 目標の現在金額を更新
            new_amount = current_amount + amount
            execute_query('UPDATE savings_goals SET current_amount = ? WHERE id = ?', (new_amount, goal_id))
            
            # 目標達成したか確認
            if new_amount >= target_amount:
                reply = QMessageBox.question(
                    self, 'おめでとうございます！', 
                    f'目標「{goal_name}」を達成しました！\n目標を完了状態に変更しますか？',
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    execute_query('UPDATE savings_goals SET is_completed = 1 WHERE id = ?', (goal_id,))
            
            QMessageBox.information(self, '入金完了', f'{amount:,.0f}円の入金を記録しました。')
            self.load_goals()
            
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'入金記録中にエラーが発生しました: {str(e)}')


class ExpenseAnalyzer:
    """支出データの分析とアドバイス生成を担当するクラス"""
    
    def __init__(self, db_path='budget.db'):
        self.db_path = db_path
        
    def get_expense_data(self, months=6):
        """直近の支出データを取得"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)
        
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT date, category, amount, description
            FROM expenses
            WHERE date >= ?
            ORDER BY date
        '''
        df = pd.read_sql_query(query, conn, params=(start_date.strftime('%Y-%m-%d'),))
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.strftime('%Y-%m')
            df['month_name'] = df['date'].dt.strftime('%Y年%m月')
        
        return df
    
    def get_monthly_income(self, months=6):
        """月次収入データを取得"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)
        
        start_year = start_date.year
        start_month = start_date.month
        end_year = end_date.year
        end_month = end_date.month
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 範囲内の全ての年月の組み合わせを生成
        income_data = {}
        current_date = start_date
        while (current_date.year < end_year) or (current_date.year == end_year and current_date.month <= end_month):
            year = current_date.year
            month = current_date.month
            month_key = f"{year}-{month:02d}"
            
            c.execute('''
                SELECT income FROM monthly_income
                WHERE year = ? AND month = ?
            ''', (year, month))
            
            result = c.fetchone()
            income_data[month_key] = result[0] if result else 0
            
            # 次の月に進む
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
            
            current_date = datetime(year, month, 1)
        
        conn.close()
        return income_data
    
    def get_category_goals(self, year, month):
        """カテゴリ別目標を取得"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT category, goal_amount FROM category_goals
            WHERE year = ? AND month = ?
        ''', (year, month))
        
        goals = {category: amount for category, amount in c.fetchall()}
        conn.close()
        return goals
    
    def analyze_monthly_trends(self):
        """月次支出傾向の分析"""
        df = self.get_expense_data()
        if df.empty:
            return {
                'status': 'error',
                'message': '十分なデータがありません。'
            }
        
        # 月別・カテゴリ別の支出集計
        try:
            monthly_category = df.pivot_table(
                index='month', 
                columns='category', 
                values='amount', 
                aggfunc='sum',
                fill_value=0
            ).reset_index()
        except Exception as e:
            print(f"ピボットテーブル作成中にエラー: {e}")
            return {
                'status': 'error',
                'message': 'データの集計中にエラーが発生しました。'
            }
        
        # 月別の総支出
        monthly_total = df.groupby('month')['amount'].sum().to_dict()
        
        # 月次収入
        monthly_income = self.get_monthly_income()
        
        # 月次収支
        monthly_balance = {}
        for month, expense in monthly_total.items():
            income = monthly_income.get(month, 0)
            monthly_balance[month] = income - expense
        
        # 前月比の変化
        months = sorted(monthly_total.keys())
        if len(months) >= 2:
            current_month = months[-1]
            prev_month = months[-2]
            
            current_expense = monthly_total[current_month]
            prev_expense = monthly_total[prev_month]
            
            change_pct = ((current_expense - prev_expense) / prev_expense * 100) if prev_expense > 0 else 0
            
            # カテゴリ別の前月比変化
            category_changes = {}
            for category in df['category'].unique():
                try:
                    # カテゴリが列として存在するかチェック
                    if category not in monthly_category.columns:
                        print(f"カテゴリ '{category}' はデータフレームの列として存在しません")
                        continue
                    
                    # 現在月のデータ行が存在するかチェック
                    current_month_rows = monthly_category[monthly_category['month'] == current_month]
                    if current_month_rows.empty:
                        print(f"現在月 '{current_month}' のデータが見つかりません")
                        continue
                    
                    # 前月のデータ行が存在するかチェック
                    prev_month_rows = monthly_category[monthly_category['month'] == prev_month]
                    if prev_month_rows.empty:
                        print(f"前月 '{prev_month}' のデータが見つかりません")
                        continue
                    
                    # データを安全に取得
                    current_cat = current_month_rows[category].values[0]
                    prev_cat = prev_month_rows[category].values[0]
                    
                    if prev_cat > 0:
                        cat_change_pct = (current_cat - prev_cat) / prev_cat * 100
                        category_changes[category] = {
                            'prev': prev_cat,
                            'current': current_cat,
                            'change_pct': cat_change_pct
                        }
                except Exception as e:
                    print(f"カテゴリ '{category}' のデータ処理中にエラー: {e}")
                    continue
            
            # 大きく増加したカテゴリ（10%以上の増加）を抽出
            increased_categories = {k: v for k, v in category_changes.items() if v['change_pct'] > 10 and v['current'] > 1000}
            
            # 大きく減少したカテゴリ（10%以上の減少）を抽出
            decreased_categories = {k: v for k, v in category_changes.items() if v['change_pct'] < -10 and v['prev'] > 1000}
            
            # 直近月のカテゴリ別目標と実績の比較
            try:
                current_year, current_month_num = current_month.split('-')
                category_goals = self.get_category_goals(int(current_year), int(current_month_num))
            except Exception as e:
                print(f"カテゴリ目標取得中にエラー: {e}")
                category_goals = {}
            
            goal_comparisons = {}
            for category, goal in category_goals.items():
                try:
                    # カテゴリが列として存在するかチェック
                    if category not in monthly_category.columns:
                        print(f"カテゴリ '{category}' はデータフレームの列として存在しません")
                        continue
                    
                    # 当月のデータ行が存在するかチェック
                    current_month_rows = monthly_category[monthly_category['month'] == current_month]
                    if current_month_rows.empty:
                        print(f"当月 '{current_month}' のデータが見つかりません")
                        continue
                    
                    # データを安全に取得
                    actual = current_month_rows[category].values[0]
                    
                    if goal > 0:
                        diff = actual - goal
                        diff_pct = (diff / goal) * 100
                        goal_comparisons[category] = {
                            'goal': goal,
                            'actual': actual,
                            'diff': diff,
                            'diff_pct': diff_pct
                        }
                except Exception as e:
                    print(f"カテゴリ '{category}' の目標比較中にエラー: {e}")
                    continue
            
            # 目標を超過したカテゴリを抽出
            exceeded_goals = {k: v for k, v in goal_comparisons.items() if v['diff'] > 0}
            
            # 目標を下回ったカテゴリを抽出
            below_goals = {k: v for k, v in goal_comparisons.items() if v['diff'] < 0}
            
            # 直近の月次データ
            current_data = {
                'expense': current_expense,
                'income': monthly_income.get(current_month, 0),
                'balance': monthly_balance.get(current_month, 0)
            }
            
            # 傾向分析のポイント
            analysis_points = []
            
            # 全体的な傾向
            if change_pct > 10:
                analysis_points.append(f"前月比で支出が{change_pct:.1f}%増加しています。詳細を確認しましょう。")
            elif change_pct < -10:
                analysis_points.append(f"前月比で支出が{-change_pct:.1f}%減少しています。素晴らしい節約です！")
            
            # 収支バランス
            if current_data['balance'] < 0:
                analysis_points.append(f"今月は支出が収入を上回っています。赤字額: {-current_data['balance']:,.0f}円")
            elif current_data['balance'] < current_data['income'] * 0.1:
                analysis_points.append(f"今月の黒字額は{current_data['balance']:,.0f}円と少なめです。貯蓄目標の達成が難しいかもしれません。")
            
            # カテゴリ別分析
            for category, data in increased_categories.items():
                analysis_points.append(f"{category}の支出が前月比{data['change_pct']:.1f}%増加しています。({data['prev']:,.0f}円→{data['current']:,.0f}円)")
            
            # 目標達成状況
            for category, data in exceeded_goals.items():
                analysis_points.append(f"{category}は目標を{data['diff_pct']:.1f}%超過しています。({data['goal']:,.0f}円の目標に対して{data['actual']:,.0f}円)")
            
            # 月名の取得を安全に行う
            try:
                current_month_name = df.loc[df['month'] == current_month, 'month_name'].iloc[0]
            except (IndexError, KeyError) as e:
                print(f"月名の取得中にエラー: {e}")
                current_month_name = current_month
                
            try:
                prev_month_name = df.loc[df['month'] == prev_month, 'month_name'].iloc[0]
            except (IndexError, KeyError) as e:
                print(f"月名の取得中にエラー: {e}")
                prev_month_name = prev_month
            
            return {
                'status': 'success',
                'monthly_total': monthly_total,
                'monthly_income': monthly_income,
                'monthly_balance': monthly_balance,
                'current_month': {
                    'name': current_month_name,
                    'data': current_data
                },
                'prev_month': {
                    'name': prev_month_name,
                    'data': {
                        'expense': prev_expense,
                        'income': monthly_income.get(prev_month, 0),
                        'balance': monthly_balance.get(prev_month, 0)
                    }
                },
                'change_pct': change_pct,
                'category_changes': category_changes,
                'increased_categories': increased_categories,
                'decreased_categories': decreased_categories,
                'goal_comparisons': goal_comparisons,
                'exceeded_goals': exceeded_goals,
                'below_goals': below_goals,
                'analysis_points': analysis_points
            }
        else:
            return {
                'status': 'error',
                'message': '十分なデータがありません。最低2ヶ月分のデータが必要です。'
            }
    
    def analyze_spending_patterns(self):
        """支出パターンの分析"""
        df = self.get_expense_data()
        if df.empty:
            return {
                'status': 'error',
                'message': '十分なデータがありません。'
            }
        
        # 頻繁に発生する支出を特定（同じ説明・カテゴリが3回以上）
        recurring_expenses = df.groupby(['category', 'description']).agg({
            'amount': ['count', 'mean', 'sum']
        }).reset_index()
        recurring_expenses.columns = ['category', 'description', 'count', 'avg_amount', 'total_amount']
        recurring_expenses = recurring_expenses[recurring_expenses['count'] >= 3].sort_values('count', ascending=False)
        
        # 大きな支出（上位10件）
        large_expenses = df.sort_values('amount', ascending=False).head(10)
        
        # カテゴリ別の支出割合
        category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)
        total_expense = category_totals.sum()
        category_percentages = (category_totals / total_expense * 100).to_dict()
        
        # 週末と平日の支出パターン
        df['weekday'] = df['date'].dt.weekday
        df['is_weekend'] = df['weekday'].apply(lambda x: 1 if x >= 5 else 0)
        
        weekday_expense = df[df['is_weekend'] == 0]['amount'].sum()
        weekend_expense = df[df['is_weekend'] == 1]['amount'].sum()
        
        weekday_days = df[df['is_weekend'] == 0]['date'].dt.date.nunique()
        weekend_days = df[df['is_weekend'] == 1]['date'].dt.date.nunique()
        
        avg_weekday = weekday_expense / weekday_days if weekday_days > 0 else 0
        avg_weekend = weekend_expense / weekend_days if weekend_days > 0 else 0
        
        # 月内の支出タイミング
        df['day_of_month'] = df['date'].dt.day
        early_month = df[df['day_of_month'] <= 10]['amount'].sum()
        mid_month = df[(df['day_of_month'] > 10) & (df['day_of_month'] <= 20)]['amount'].sum()
        late_month = df[df['day_of_month'] > 20]['amount'].sum()
        
        # パターン分析のポイント
        pattern_points = []
        
        # 主要カテゴリ分析
        top_categories = category_totals.head(3).index.tolist()
        pattern_points.append(f"支出の大部分は{', '.join(top_categories)}に集中しています。")
        
        # 頻繁な支出
        if not recurring_expenses.empty:
            top_recurring = recurring_expenses.iloc[0]
            pattern_points.append(f"最も頻繁な支出は{top_recurring['category']}の「{top_recurring['description']}」で、平均{top_recurring['avg_amount']:,.0f}円を{top_recurring['count']}回支払っています。")
        
        # 平日/週末パターン
        if avg_weekend > avg_weekday * 1.5:
            pattern_points.append(f"週末の支出（1日平均{avg_weekend:,.0f}円）は平日（1日平均{avg_weekday:,.0f}円）より大幅に多くなっています。")
        
        # 月内パターン
        total_monthly = early_month + mid_month + late_month
        if total_monthly > 0:
            early_pct = early_month / total_monthly * 100
            mid_pct = mid_month / total_monthly * 100
            late_pct = late_month / total_monthly * 100
            
            highest = max(early_pct, mid_pct, late_pct)
            if highest == early_pct and early_pct > 50:
                pattern_points.append(f"月初（1-10日）に支出が集中({early_pct:.1f}%)しています。月末の資金不足に注意しましょう。")
            elif highest == late_pct and late_pct > 50:
                pattern_points.append(f"月末（21日以降）に支出が集中({late_pct:.1f}%)しています。")
        
        return {
            'status': 'success',
            'recurring_expenses': recurring_expenses.to_dict('records') if not recurring_expenses.empty else [],
            'large_expenses': large_expenses.to_dict('records') if not large_expenses.empty else [],
            'category_percentages': category_percentages,
            'weekday_vs_weekend': {
                'avg_weekday': avg_weekday,
                'avg_weekend': avg_weekend
            },
            'monthly_timing': {
                'early_month': early_month,
                'mid_month': mid_month,
                'late_month': late_month
            },
            'pattern_points': pattern_points
        }
    
    def generate_savings_recommendations(self):
        """節約アドバイスの生成"""
        # 月次傾向分析
        trend_analysis = self.analyze_monthly_trends()
        # 支出パターン分析
        pattern_analysis = self.analyze_spending_patterns()
        
        if trend_analysis['status'] == 'error' or pattern_analysis['status'] == 'error':
            return {
                'status': 'error',
                'message': '十分なデータがないためアドバイスを生成できません。'
            }
        
        recommendations = []
        
        # 超過カテゴリに基づくアドバイス
        if 'exceeded_goals' in trend_analysis and trend_analysis['exceeded_goals']:
            for category, data in trend_analysis['exceeded_goals'].items():
                if data['diff_pct'] > 20:  # 目標を20%以上超過
                    recommendations.append({
                        'type': 'warning',
                        'title': f'{category}の支出が目標を大幅に超過',
                        'description': f"{category}の支出が目標を{data['diff_pct']:.1f}%超過しています。" + 
                                      f"目標は{data['goal']:,.0f}円ですが、実際は{data['actual']:,.0f}円使っています。" + 
                                      f"来月は{category}の支出を削減するよう意識しましょう。"
                    })
        
        # 増加カテゴリに基づくアドバイス
        if 'increased_categories' in trend_analysis and trend_analysis['increased_categories']:
            for category, data in trend_analysis['increased_categories'].items():
                if data['change_pct'] > 30:  # 30%以上の増加
                    recommendations.append({
                        'type': 'alert',
                        'title': f'{category}の支出が急増',
                        'description': f"{category}の支出が前月比{data['change_pct']:.1f}%増加しています。" + 
                                      f"前月は{data['prev']:,.0f}円でしたが、今月は{data['current']:,.0f}円です。" + 
                                      f"この増加が一時的なものか、継続的な傾向かを確認しましょう。"
                    })
        
        # 収支バランスに基づくアドバイス
        if 'current_month' in trend_analysis:
            current_data = trend_analysis['current_month']['data']
            if current_data['balance'] < 0:
                recommendations.append({
                    'type': 'critical',
                    'title': '収支がマイナスです',
                    'description': f"今月は支出（{current_data['expense']:,.0f}円）が" + 
                                  f"収入（{current_data['income']:,.0f}円）を" + 
                                  f"{-current_data['balance']:,.0f}円上回っています。" + 
                                  "緊急性の低い支出を見直し、収支バランスの改善を目指しましょう。"
                })
            elif current_data['balance'] < current_data['income'] * 0.2:
                recommendations.append({
                    'type': 'notice',
                    'title': '貯蓄率が低めです',
                    'description': f"今月の貯蓄額は{current_data['balance']:,.0f}円で、" + 
                                  f"収入の{(current_data['balance']/current_data['income']*100):.1f}%です。" + 
                                  "長期的な資産形成のためには、収入の20-30%の貯蓄を目指すことをおすすめします。"
                })
        
        # 支出パターンに基づくアドバイス
        if 'recurring_expenses' in pattern_analysis and pattern_analysis['recurring_expenses']:
            # 高額な定期的支出を抽出
            expensive_recurring = [
                item for item in pattern_analysis['recurring_expenses']
                if item['avg_amount'] > 5000 and item['count'] >= 3
            ]
            
            if expensive_recurring:
                for item in expensive_recurring[:2]:  # 上位2件のみアドバイス
                    recommendations.append({
                        'type': 'tip',
                        'title': f'定期的な{item["category"]}の支出を見直す',
                        'description': f"「{item['description']}」に毎回約{item['avg_amount']:,.0f}円、" + 
                                      f"合計{item['total_amount']:,.0f}円使っています。" + 
                                      "この支出は必要ですか？より安価な代替手段はありませんか？"
                    })
        
        # カテゴリ割合に基づくアドバイス
        if 'category_percentages' in pattern_analysis:
            for category, percentage in pattern_analysis['category_percentages'].items():
                # 食費が全体の30%以上
                if category == '食費' and percentage > 30:
                    recommendations.append({
                        'type': 'suggestion',
                        'title': '食費の割合が高め',
                        'description': f"食費が総支出の{percentage:.1f}%を占めています。" + 
                                      "自炊の回数を増やす、まとめ買いをする、特売日を活用するなどで食費を削減できるかもしれません。"
                    })
                # 娯楽が全体の20%以上
                elif category == '娯楽' and percentage > 20:
                    recommendations.append({
                        'type': 'suggestion',
                        'title': '娯楽費の見直し',
                        'description': f"娯楽費が総支出の{percentage:.1f}%を占めています。" + 
                                      "楽しみは大切ですが、無料や低コストの娯楽も取り入れることで、満足度を下げずに支出を抑えられるかもしれません。"
                    })
        
        # 平日/週末パターンに基づくアドバイス
        if 'weekday_vs_weekend' in pattern_analysis:
            weekday_data = pattern_analysis['weekday_vs_weekend']
            if weekday_data['avg_weekend'] > weekday_data['avg_weekday'] * 2:
                recommendations.append({
                    'type': 'insight',
                    'title': '週末の支出が突出',
                    'description': f"週末の平均支出（{weekday_data['avg_weekend']:,.0f}円/日）は" +
                                  f"平日（{weekday_data['avg_weekday']:,.0f}円/日）の2倍以上です。" +
                                  "週末の計画的な活動や予算設定で、支出をコントロールしやすくなります。"
                })
        
        # 全体的な節約アドバイス（データがあまりない場合も含む）
        general_tips = [
            {
                'type': 'tip',
                'title': '定期サブスクリプションの見直し',
                'description': "使用頻度の低い定期サブスクリプションサービスを確認してみましょう。必要ないものを解約することで、毎月の固定費を削減できます。"
            },
            {
                'type': 'tip',
                'title': '24時間ルールを試す',
                'description': "5,000円以上の衝動買いを減らすために、24時間ルールを試してみましょう。購入前に一日待つことで、本当に必要かどうか冷静に判断できます。"
            },
            {
                'type': 'tip',
                'title': '節約チャレンジの実施',
                'description': "1週間の「無駄遣いゼロチャレンジ」など短期間の節約目標を設定することで、無意識の支出を見つけやすくなります。"
            }
        ]
        
        # データに基づくアドバイスが少ない場合は一般的なアドバイスを追加
        if len(recommendations) < 3:
            needed = 3 - len(recommendations)
            recommendations.extend(general_tips[:needed])
        
        return {
            'status': 'success',
            'recommendations': recommendations
        }
    
    def forecast_future_expenses(self, months_ahead=3):
        """将来の支出予測"""
        df = self.get_expense_data()
        if df.empty:
            return {
                'status': 'error',
                'message': '予測するための十分なデータがありません。'
            }
        
        # 月別・カテゴリ別の支出集計
        monthly_category = df.pivot_table(
            index='month', 
            columns='category', 
            values='amount', 
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # 月別の総支出
        monthly_total = df.groupby('month')['amount'].sum().to_dict()
        
        # 月次収入
        monthly_income = self.get_monthly_income()
        
        # 予測の基礎となる直近のデータ（通常は直近3ヶ月の平均を使用）
        months = sorted(monthly_total.keys())
        recent_months = months[-3:] if len(months) >= 3 else months
        
        # カテゴリ別の直近平均を計算
        category_averages = {}
        for category in df['category'].unique():
            values = []
            for month in recent_months:
                if month in monthly_category['month'].values:
                    value = monthly_category.loc[monthly_category['month'] == month, category].values[0]
                    values.append(value)
            
            if values:
                category_averages[category] = sum(values) / len(values)
            else:
                category_averages[category] = 0
        
        # 収入の予測（直近の値を使用）
        if recent_months:
            latest_month = recent_months[-1]
            predicted_income = monthly_income.get(latest_month, 0)
        else:
            predicted_income = 0
        
        # 将来の月次データを予測
        future_predictions = []
        latest_date = datetime.strptime(months[-1], '%Y-%m')
        
        for i in range(1, months_ahead + 1):
            future_date = latest_date + timedelta(days=31 * i)
            future_month_key = future_date.strftime('%Y-%m')
            future_month_name = future_date.strftime('%Y年%m月')
            
            # カテゴリ別予測（基本は平均値だが、季節性などを加味するとより精度が上がる）
            predicted_expenses = category_averages.copy()
            
            # 12月は出費が増える傾向にある（単純な例）
            if future_date.month == 12:
                for category in predicted_expenses:
                    if category in ['娯楽', '食費']:
                        predicted_expenses[category] *= 1.2  # 20%増
            
            # 8月は旅行が増える（単純な例）
            if future_date.month == 8:
                if '交通費' in predicted_expenses:
                    predicted_expenses['交通費'] *= 1.3  # 30%増
            
            total_predicted = sum(predicted_expenses.values())
            predicted_balance = predicted_income - total_predicted
            
            future_predictions.append({
                'month_key': future_month_key,
                'month_name': future_month_name,
                'predicted_expenses': predicted_expenses,
                'total_predicted': total_predicted,
                'predicted_income': predicted_income,
                'predicted_balance': predicted_balance
            })
        
        return {
            'status': 'success',
            'category_averages': category_averages,
            'future_predictions': future_predictions
        }

class AIExpenseAdvisorWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # ExpenseAnalyzerをインポート
        self.analyzer = ExpenseAnalyzer()
        
        # UIの初期化
        self.initUI()
        
        # データの分析と表示
        self.load_analysis()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        layout.addLayout(self.button_layout)

        # ヘッダー
        header_layout = QHBoxLayout()
        title_label = QLabel("AI支出分析アドバイザー")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        refresh_button = QPushButton("分析更新")
        refresh_button.clicked.connect(self.load_analysis)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(refresh_button)
        
        layout.addLayout(header_layout)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # タブ1: アドバイス
        self.advice_tab = QWidget()
        self.setup_advice_tab()
        self.tab_widget.addTab(self.advice_tab, "パーソナルアドバイス")
        
        # タブ2: 支出パターン
        self.pattern_tab = QWidget()
        self.setup_pattern_tab()
        self.tab_widget.addTab(self.pattern_tab, "支出パターン分析")
        
        # タブ3: 傾向分析
        self.trend_tab = QWidget()
        self.setup_trend_tab()
        self.tab_widget.addTab(self.trend_tab, "支出傾向分析")
        
        # タブ4: 将来予測
        self.forecast_tab = QWidget()
        self.setup_forecast_tab()
        self.tab_widget.addTab(self.forecast_tab, "将来支出予測")
        
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)

    def setup_advice_tab(self):
        """アドバイスタブのUI設定"""
        layout = QVBoxLayout()
        
        # アドバイスリスト表示領域
        self.recommendations_layout = QVBoxLayout()
        
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_container = QWidget()
        scroll_container.setLayout(self.recommendations_layout)
        scroll_area.setWidget(scroll_container)
        
        layout.addWidget(scroll_area)
        
        self.advice_tab.setLayout(layout)
    
    def setup_pattern_tab(self):
        """支出パターンタブのUI設定"""
        layout = QVBoxLayout()
        
        # 支出パターンの概要セクション
        pattern_summary_group = QGroupBox("支出パターン概要")
        pattern_summary_layout = QVBoxLayout()
        self.pattern_summary_label = QLabel("データを分析中...")
        self.pattern_summary_label.setWordWrap(True)
        pattern_summary_layout.addWidget(self.pattern_summary_label)
        pattern_summary_group.setLayout(pattern_summary_layout)
        layout.addWidget(pattern_summary_group)
        
        # カテゴリ別の支出割合チャート
        category_chart_group = QGroupBox("カテゴリ別支出割合")
        category_chart_layout = QVBoxLayout()
        self.category_chart_view = QChartView()
        self.category_chart_view.setMinimumHeight(300)
        category_chart_layout.addWidget(self.category_chart_view)
        category_chart_group.setLayout(category_chart_layout)
        layout.addWidget(category_chart_group)
        
        # 頻繁な支出リスト
        recurring_group = QGroupBox("頻繁な支出")
        recurring_layout = QVBoxLayout()
        self.recurring_expenses_list = QListWidget()
        recurring_layout.addWidget(self.recurring_expenses_list)
        recurring_group.setLayout(recurring_layout)
        layout.addWidget(recurring_group)
        
        # 平日vs週末の支出パターン
        weekday_group = QGroupBox("平日/週末の支出パターン")
        weekday_layout = QFormLayout()
        self.weekday_avg_label = QLabel("0円")
        self.weekend_avg_label = QLabel("0円")
        weekday_layout.addRow("平日の平均支出:", self.weekday_avg_label)
        weekday_layout.addRow("週末の平均支出:", self.weekend_avg_label)
        weekday_group.setLayout(weekday_layout)
        layout.addWidget(weekday_group)
        
        self.pattern_tab.setLayout(layout)
    
    def setup_advice_tab(self):
        """アドバイスタブのUI設定"""
        layout = QVBoxLayout()
        
        # アドバイスリスト表示領域
        self.recommendations_layout = QVBoxLayout()
        
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_container = QWidget()
        scroll_container.setLayout(self.recommendations_layout)
        scroll_area.setWidget(scroll_container)
        
        layout.addWidget(scroll_area)
        
        self.advice_tab.setLayout(layout)
    
    def setup_pattern_tab(self):
        """支出パターンタブのUI設定"""
        layout = QVBoxLayout()
        
        # 支出パターンの概要セクション
        pattern_summary_group = QGroupBox("支出パターン概要")
        pattern_summary_layout = QVBoxLayout()
        self.pattern_summary_label = QLabel("データを分析中...")
        self.pattern_summary_label.setWordWrap(True)
        pattern_summary_layout.addWidget(self.pattern_summary_label)
        pattern_summary_group.setLayout(pattern_summary_layout)
        layout.addWidget(pattern_summary_group)
        
        # カテゴリ別の支出割合チャート
        category_chart_group = QGroupBox("カテゴリ別支出割合")
        category_chart_layout = QVBoxLayout()
        self.category_chart_view = QChartView()
        self.category_chart_view.setMinimumHeight(300)
        category_chart_layout.addWidget(self.category_chart_view)
        category_chart_group.setLayout(category_chart_layout)
        layout.addWidget(category_chart_group)
        
        # 頻繁な支出リスト
        recurring_group = QGroupBox("頻繁な支出")
        recurring_layout = QVBoxLayout()
        self.recurring_expenses_list = QListWidget()
        recurring_layout.addWidget(self.recurring_expenses_list)
        recurring_group.setLayout(recurring_layout)
        layout.addWidget(recurring_group)
        
        # 平日vs週末の支出パターン
        weekday_group = QGroupBox("平日/週末の支出パターン")
        weekday_layout = QFormLayout()
        self.weekday_avg_label = QLabel("0円")
        self.weekend_avg_label = QLabel("0円")
        weekday_layout.addRow("平日の平均支出:", self.weekday_avg_label)
        weekday_layout.addRow("週末の平均支出:", self.weekend_avg_label)
        weekday_group.setLayout(weekday_layout)
        layout.addWidget(weekday_group)
        
        self.pattern_tab.setLayout(layout)
    
    def setup_trend_tab(self):
        """支出傾向分析タブのUI設定"""
        layout = QVBoxLayout()
        
        # 月次推移チャート
        trend_chart_group = QGroupBox("月次支出推移")
        trend_chart_layout = QVBoxLayout()
        self.trend_chart_view = QChartView()
        self.trend_chart_view.setMinimumHeight(250)
        trend_chart_layout.addWidget(self.trend_chart_view)
        trend_chart_group.setLayout(trend_chart_layout)
        layout.addWidget(trend_chart_group)
        
        # 前月比較
        comparison_group = QGroupBox("前月比較")
        comparison_layout = QFormLayout()
        
        self.prev_month_label = QLabel("前月:")
        self.current_month_label = QLabel("当月:")
        self.change_pct_label = QLabel("0%")
        
        self.prev_expense_label = QLabel("0円")
        self.current_expense_label = QLabel("0円")
        
        self.prev_income_label = QLabel("0円")
        self.current_income_label = QLabel("0円")
        
        self.prev_balance_label = QLabel("0円")
        self.current_balance_label = QLabel("0円")
        
        comparison_layout.addRow("期間:", self.prev_month_label)
        comparison_layout.addRow("支出:", self.prev_expense_label)
        comparison_layout.addRow("収入:", self.prev_income_label)
        comparison_layout.addRow("収支:", self.prev_balance_label)
        
        comparison_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        comparison_layout.addRow("期間:", self.current_month_label)
        comparison_layout.addRow("支出:", self.current_expense_label)
        comparison_layout.addRow("収入:", self.current_income_label)
        comparison_layout.addRow("収支:", self.current_balance_label)
        
        comparison_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        comparison_layout.addRow("支出変化率:", self.change_pct_label)
        
        comparison_group.setLayout(comparison_layout)
        layout.addWidget(comparison_group)
        
        # カテゴリ別変化
        category_change_group = QGroupBox("カテゴリ別変化")
        category_change_layout = QVBoxLayout()
        self.category_change_list = QListWidget()
        category_change_layout.addWidget(self.category_change_list)
        category_change_group.setLayout(category_change_layout)
        layout.addWidget(category_change_group)
        
        self.trend_tab.setLayout(layout)
    
    def setup_forecast_tab(self):
        """将来予測タブのUI設定"""
        layout = QVBoxLayout()
        
        # 予測概要
        forecast_intro_label = QLabel("直近のデータに基づいた将来3ヶ月分の支出予測です。季節的な傾向なども考慮しています。")
        forecast_intro_label.setWordWrap(True)
        layout.addWidget(forecast_intro_label)
        
        # 予測チャート
        forecast_chart_group = QGroupBox("支出予測チャート")
        forecast_chart_layout = QVBoxLayout()
        self.forecast_chart_view = QChartView()
        self.forecast_chart_view.setMinimumHeight(250)
        forecast_chart_layout.addWidget(self.forecast_chart_view)
        forecast_chart_group.setLayout(forecast_chart_layout)
        layout.addWidget(forecast_chart_group)
        
        # 予測詳細
        forecast_details_group = QGroupBox("予測詳細")
        forecast_details_layout = QVBoxLayout()
        self.forecast_details_list = QListWidget()
        forecast_details_layout.addWidget(self.forecast_details_list)
        forecast_details_group.setLayout(forecast_details_layout)
        layout.addWidget(forecast_details_group)
        
        self.forecast_tab.setLayout(layout) 

    def load_analysis(self):
        """データの分析と表示の更新"""
        try:
            # 各種分析を実行
            self.savings_recommendations = self.analyzer.generate_savings_recommendations()
            self.spending_patterns = self.analyzer.analyze_spending_patterns()
            self.monthly_trends = self.analyzer.analyze_monthly_trends()
            self.future_forecast = self.analyzer.forecast_future_expenses()
            
            # 各タブのデータ表示を更新
            self.update_advice_tab()
            self.update_pattern_tab()
            self.update_trend_tab()
            self.update_forecast_tab()
            
        except Exception as e:
            QMessageBox.warning(self, "分析エラー", f"データの分析中にエラーが発生しました: {str(e)}")
    
    def update_advice_tab(self):
        """アドバイスタブのデータ表示を更新"""
        # 既存のアドバイスをクリア
        while self.recommendations_layout.count():
            item = self.recommendations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if self.savings_recommendations['status'] == 'error':
            error_label = QLabel(self.savings_recommendations['message'])
            error_label.setStyleSheet("color: red;")
            self.recommendations_layout.addWidget(error_label)
            return
        
        # アドバイスの種類に応じた色設定
        type_colors = {
            'critical': "#FFEBEE",  # 赤系の薄い色（緊急）
            'warning': "#FFF8E1",   # 黄色系の薄い色（警告）
            'alert': "#FFF3E0",     # オレンジ系の薄い色（注意）
            'notice': "#E8F5E9",    # 緑系の薄い色（通知）
            'tip': "#E3F2FD",       # 青系の薄い色（ヒント）
            'insight': "#F3E5F5",   # 紫系の薄い色（洞察）
            'suggestion': "#E0F7FA" # 水色系の薄い色（提案）
        }
        
        # 各アドバイスをカードとして表示
        for recommendation in self.savings_recommendations['recommendations']:
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            
            # アドバイスの種類に応じた背景色
            bg_color = type_colors.get(recommendation['type'], "#FFFFFF")
            card.setStyleSheet(f"QFrame {{ background-color: {bg_color}; border-radius: 8px; margin: 5px; padding: 10px; }}")
            
            card_layout = QVBoxLayout()
            
            # タイトル
            title_label = QLabel(f"<b>{recommendation['title']}</b>")
            title_label.setStyleSheet("font-size: 14px;")
            card_layout.addWidget(title_label)
            
            # 説明
            desc_label = QLabel(recommendation['description'])
            desc_label.setWordWrap(True)
            card_layout.addWidget(desc_label)
            
            card.setLayout(card_layout)
            self.recommendations_layout.addWidget(card)
        
        # 空のウィジェットを追加（スクロール用の余白）
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.recommendations_layout.addWidget(spacer)

    def update_pattern_tab(self):
        """支出パターンタブのデータ表示を更新"""
        if self.spending_patterns['status'] == 'error':
            self.pattern_summary_label.setText(self.spending_patterns['message'])
            return
        
        # パターン概要テキスト
        pattern_points = self.spending_patterns['pattern_points']
        summary_text = "<ul>"
        for point in pattern_points:
            summary_text += f"<li>{point}</li>"
        summary_text += "</ul>"
        self.pattern_summary_label.setText(summary_text)
        
        # カテゴリ別支出割合のパイチャート
        self.update_category_pie_chart()
        
        # 頻繁な支出リスト
        self.recurring_expenses_list.clear()
        for item in self.spending_patterns['recurring_expenses'][:10]:  # 上位10件のみ
            list_item = QListWidgetItem(
                f"{item['description']} ({item['category']}): {item['count']}回, 平均{item['avg_amount']:,.0f}円"
            )
            self.recurring_expenses_list.addItem(list_item)
        
        # 平日/週末の支出パターン
        weekday_data = self.spending_patterns['weekday_vs_weekend']
        self.weekday_avg_label.setText(f"{weekday_data['avg_weekday']:,.0f}円")
        self.weekend_avg_label.setText(f"{weekday_data['avg_weekend']:,.0f}円")
    
    def update_category_pie_chart(self):
        """カテゴリ別支出割合のパイチャートを更新"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # パイチャートのデータ作成
        series = QPieSeries()
        
        # カラーリスト（異なる色を用意）
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD',
            '#FFD93D', '#6C5B7B', '#F7A072', '#C06C84', '#95A5A6'
        ]
        
        # カテゴリ別割合データ
        category_percentages = self.spending_patterns['category_percentages']
        
        # 合計が少なすぎるカテゴリをまとめる（5%未満）
        other_total = 0
        for category, percentage in sorted(category_percentages.items(), key=lambda x: x[1], reverse=True):
            if percentage >= 3:  # 3%以上のカテゴリは個別に表示
                slice = series.append(f"{category} ({percentage:.1f}%)", percentage)
            else:
                other_total += percentage
        
        # その他カテゴリがあれば追加
        if other_total > 0:
            series.append(f"その他 ({other_total:.1f}%)", other_total)
        
        # 各スライスの色を設定
        for i, slice in enumerate(series.slices()):
            color_idx = i % len(colors)
            slice.setBrush(QColor(colors[color_idx]))
            slice.setLabelVisible(True)
        
        chart.addSeries(series)
        chart.setTitle("カテゴリ別支出割合")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        self.category_chart_view.setChart(chart)    

    def update_trend_tab(self):
        """支出傾向分析タブのデータ表示を更新"""
        if self.monthly_trends['status'] == 'error':
            # エラーメッセージ表示
            return
        
        # 月次推移チャートの更新
        self.update_trend_chart()
        
        # 前月/当月の比較データ表示
        current_month = self.monthly_trends['current_month']
        prev_month = self.monthly_trends['prev_month']
        
        self.current_month_label.setText(current_month['name'])
        self.current_expense_label.setText(f"{current_month['data']['expense']:,.0f}円")
        self.current_income_label.setText(f"{current_month['data']['income']:,.0f}円")
        self.current_balance_label.setText(f"{current_month['data']['balance']:,.0f}円")
        
        self.prev_month_label.setText(prev_month['name'])
        self.prev_expense_label.setText(f"{prev_month['data']['expense']:,.0f}円")
        self.prev_income_label.setText(f"{prev_month['data']['income']:,.0f}円")
        self.prev_balance_label.setText(f"{prev_month['data']['balance']:,.0f}円")
        
        change_pct = self.monthly_trends['change_pct']
        self.change_pct_label.setText(f"{change_pct:.1f}%")
        
        # カテゴリ別変化リスト
        self.category_change_list.clear()
        
        # 増加カテゴリ
        for category, data in self.monthly_trends.get('increased_categories', {}).items():
            item = QListWidgetItem(f"↗️ {category}: +{data['change_pct']:.1f}% ({data['prev']:,.0f}円→{data['current']:,.0f}円)")
            item.setForeground(QColor("#F44336"))  # 赤色で表示
            self.category_change_list.addItem(item)
        
        # 減少カテゴリ
        for category, data in self.monthly_trends.get('decreased_categories', {}).items():
            item = QListWidgetItem(f"↘️ {category}: {data['change_pct']:.1f}% ({data['prev']:,.0f}円→{data['current']:,.0f}円)")
            item.setForeground(QColor("#4CAF50"))  # 緑色で表示
            self.category_change_list.addItem(item)
    
    def update_trend_chart(self):
        """月次推移チャートを更新"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 月次データ
        monthly_total = self.monthly_trends['monthly_total']
        monthly_income = self.monthly_trends['monthly_income']
        monthly_balance = self.monthly_trends['monthly_balance']
        
        months = sorted(monthly_total.keys())
        
        # 支出ライン
        expense_series = QLineSeries()
        expense_series.setName("支出")
        
        # 収入ライン
        income_series = QLineSeries()
        income_series.setName("収入")
        
        # 収支ライン
        balance_series = QLineSeries()
        balance_series.setName("収支")
        
        for i, month in enumerate(months):
            expense_series.append(i, monthly_total[month])
            income_series.append(i, monthly_income.get(month, 0))
            balance_series.append(i, monthly_balance.get(month, 0))
        
        # シリーズの色設定
        expense_series.setColor(QColor("#F44336"))  # 赤色
        income_series.setColor(QColor("#4CAF50"))  # 緑色
        balance_series.setColor(QColor("#2196F3"))  # 青色
        
        # シリーズの線幅設定
        pen = QPen()
        pen.setWidth(3)
        
        expense_series.setPen(pen)
        income_series.setPen(pen)
        balance_series.setPen(pen)
        
        # チャートに追加
        chart.addSeries(expense_series)
        chart.addSeries(income_series)
        chart.addSeries(balance_series)
        
        # X軸設定
        axis_x = QValueAxis()
        axis_x.setRange(0, len(months) - 1)
        axis_x.setTickCount(len(months))
        axis_x.setLabelFormat("%d")
        
        # X軸のラベルをカスタマイズ
        for i, month in enumerate(months):
            axis_x.setLabelFormat("") # ラベルを消去
        
        chart.addAxis(axis_x, Qt.AlignBottom)
        expense_series.attachAxis(axis_x)
        income_series.attachAxis(axis_x)
        balance_series.attachAxis(axis_x)
        
        # Y軸設定
        axis_y = QValueAxis()
        all_values = []
        for month in months:
            all_values.append(monthly_total[month])
            all_values.append(monthly_income.get(month, 0))
            all_values.append(monthly_balance.get(month, 0))
        
        max_value = max(all_values) if all_values else 100000
        min_value = min(all_values) if all_values else 0
        
        axis_y.setRange(min(0, min_value * 1.1), max_value * 1.1)
        axis_y.setLabelFormat("%,.0f")
        
        chart.addAxis(axis_y, Qt.AlignLeft)
        expense_series.attachAxis(axis_y)
        income_series.attachAxis(axis_y)
        balance_series.attachAxis(axis_y)
        
        # チャートタイトル
        chart.setTitle("月次収支推移")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        self.trend_chart_view.setChart(chart)
    
    def update_forecast_tab(self):
        """将来予測タブのデータ表示を更新"""
        if self.future_forecast['status'] == 'error':
            error_label = QLabel(self.future_forecast['message'])
            error_label.setStyleSheet("color: red;")
            return
        
        # 予測チャートの更新
        self.update_forecast_chart()
        
        # 予測詳細リスト
        self.forecast_details_list.clear()
        
        for prediction in self.future_forecast['future_predictions']:
            month_name = prediction['month_name']
            total_expense = prediction['total_predicted']
            income = prediction['predicted_income']
            balance = prediction['predicted_balance']
            
            # 月ごとのサマリーアイテム
            summary_item = QListWidgetItem(f"■ {month_name}の予測")
            summary_item.setFont(QFont("", weight=QFont.Bold))
            self.forecast_details_list.addItem(summary_item)
            
            # 支出合計
            self.forecast_details_list.addItem(QListWidgetItem(f"予測支出: {total_expense:,.0f}円"))
            
            # 収入
            self.forecast_details_list.addItem(QListWidgetItem(f"予測収入: {income:,.0f}円"))
            
            # 収支
            balance_text = f"予測収支: {balance:,.0f}円"
            balance_item = QListWidgetItem(balance_text)
            
            if balance < 0:
                balance_item.setForeground(QColor("#F44336"))  # 赤色（赤字）
            else:
                balance_item.setForeground(QColor("#4CAF50"))  # 緑色（黒字）
            
            self.forecast_details_list.addItem(balance_item)
            
            # 主要カテゴリの予測
            top_categories = sorted(
                prediction['predicted_expenses'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]  # 上位5カテゴリ
            
            category_item = QListWidgetItem("主要カテゴリ予測:")
            category_item.setFont(QFont("", italic=True))
            self.forecast_details_list.addItem(category_item)
            
            for category, amount in top_categories:
                if amount > 0:
                    self.forecast_details_list.addItem(
                        QListWidgetItem(f"- {category}: {amount:,.0f}円")
                    )
            
            # 区切り
            self.forecast_details_list.addItem(QListWidgetItem(""))
    
    def update_forecast_chart(self):
        """予測チャートを更新"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 履歴データ
        monthly_total = self.monthly_trends['monthly_total']
        months = sorted(monthly_total.keys())
        
        # 予測データ
        future_predictions = self.future_forecast['future_predictions']
        
        # バーセット（履歴）
        history_set = QBarSet("実績")
        history_set.setColor(QColor("#4CAF50"))  # 緑色
        
        # バーセット（予測）
        forecast_set = QBarSet("予測")
        forecast_set.setColor(QColor("#2196F3"))  # 青色
        
        # X軸ラベル
        x_labels = []
        
        # 履歴データを追加
        for month in months:
            history_set.append(monthly_total[month])
            x_labels.append(month)  # 'YYYY-MM'形式
        
        # 予測データを追加
        for prediction in future_predictions:
            forecast_set.append(prediction['total_predicted'])
            x_labels.append(prediction['month_key'])
        
        # バーシリーズ
        series = QBarSeries()
        series.append(history_set)
        series.append(forecast_set)
        
        # チャートに追加
        chart.addSeries(series)
        
        # X軸設定
        axis_x = QBarCategoryAxis()
        # 日本語表示のため、'YYYY-MM'形式を'YYYY年MM月'形式に変換
        axis_x.append([f"{x.split('-')[0]}年{x.split('-')[1]}月" for x in x_labels])
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        # Y軸設定
        axis_y = QValueAxis()
        all_values = []
        for month in months:
            all_values.append(monthly_total[month])
        for prediction in future_predictions:
            all_values.append(prediction['total_predicted'])
        
        max_value = max(all_values) if all_values else 100000
        
        axis_y.setRange(0, max_value * 1.1)
        axis_y.setLabelFormat("%,.0f")
        
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # チャートタイトル
        chart.setTitle("支出実績と予測")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        self.forecast_chart_view.setChart(chart)  

import json
import csv         

class CreditCardImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('クレジットカード明細取込')
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # 現在のフォーマット設定（デフォルト値）
        self.current_format = {
            'encoding': 'utf-8',
            'date_format': '%Y/%m/%d',
            'skip_rows': 0,
            'negation_needed': True,
            'date_column': '利用日',
            'amount_column': '利用金額',
            'description_column': '利用店名・商品名',
            'category_mapping': {
                'vs カ)マルエツ': '食費'
            }
        }
        
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # ステップ表示
        self.step_label = QLabel('ステップ 1/3: CSVファイルの選択とフォーマット設定')
        self.step_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        layout.addWidget(self.step_label)
        
        # スタックウィジェットで複数ステップを管理
        self.stack = QStackedWidget()
        
        # ステップ1: ファイル選択とフォーマット設定
        step1_widget = QWidget()
        step1_layout = QVBoxLayout()
        
        # ファイル選択エリア
        file_group = QGroupBox('CSVファイル選択')
        file_layout = QHBoxLayout()
        
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText('CSVファイルを選択してください')
        
        browse_button = QPushButton('参照...')
        browse_button.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(browse_button)
        file_group.setLayout(file_layout)
        step1_layout.addWidget(file_group)
        
        # フォーマット選択エリア
        format_group = QGroupBox('フォーマット設定')
        format_layout = QVBoxLayout()
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(['一般的なクレジットカード', 'その他'])
        self.format_combo.currentIndexChanged.connect(self.toggle_custom_settings)
        format_layout.addWidget(self.format_combo)
        
        # カスタム設定エリア（その他選択時）
        self.custom_settings_widget = QWidget()
        custom_layout = QFormLayout()
        
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(['utf-8', 'shift-jis', 'cp932', 'euc-jp'])
        custom_layout.addRow('文字エンコーディング:', self.encoding_combo)
        
        self.date_format_input = QLineEdit()
        self.date_format_input.setPlaceholderText('%Y/%m/%d や %Y年%m月%d日 など')
        self.date_format_input.setText('%Y/%m/%d')
        custom_layout.addRow('日付フォーマット:', self.date_format_input)
        
        self.skip_rows_spin = QSpinBox()
        self.skip_rows_spin.setRange(0, 10)
        custom_layout.addRow('スキップする行数:', self.skip_rows_spin)
        
        self.negation_needed_check = QCheckBox()
        custom_layout.addRow('金額を負数に変換:', self.negation_needed_check)
        
        self.custom_settings_widget.setLayout(custom_layout)
        self.custom_settings_widget.hide()
        
        format_layout.addWidget(self.custom_settings_widget)
        format_group.setLayout(format_layout)
        step1_layout.addWidget(format_group)
        
        # 次へボタン
        next_button1 = QPushButton('次へ')
        next_button1.clicked.connect(self.proceed_to_step2)
        step1_layout.addWidget(next_button1, alignment=Qt.AlignRight)
        
        step1_widget.setLayout(step1_layout)
        
        # ステップ2: ヘッダーマッピング
        step2_widget = QWidget()
        step2_layout = QVBoxLayout()
        
        mapping_label = QLabel('CSVの列を家計簿の項目にマッピングしてください:')
        step2_layout.addWidget(mapping_label)
        
        mapping_group = QGroupBox('列マッピング')
        mapping_layout = QFormLayout()
        
        self.date_column_combo = QComboBox()
        mapping_layout.addRow('日付列:', self.date_column_combo)
        
        self.amount_column_combo = QComboBox()
        mapping_layout.addRow('金額列:', self.amount_column_combo)
        
        self.description_column_combo = QComboBox()
        mapping_layout.addRow('説明列:', self.description_column_combo)
        
        mapping_group.setLayout(mapping_layout)
        step2_layout.addWidget(mapping_group)
        
        # カテゴリグループボックスの設定
        self.category_group = QGroupBox('カテゴリマッピング')
        category_layout = QVBoxLayout()

        category_label = QLabel('キーワードによる自動カテゴリ分類:')
        category_layout.addWidget(category_label)

        self.category_mapping_table = QTableWidget(0, 2)
        self.category_mapping_table.setHorizontalHeaderLabels(['キーワード', 'カテゴリ'])
        self.category_mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        category_layout.addWidget(self.category_mapping_table)

        # ボタンのレイアウト - 上段
        button_layout1 = QHBoxLayout()

        add_mapping_button = QPushButton('マッピング追加')
        add_mapping_button.clicked.connect(self.add_category_mapping)
        button_layout1.addWidget(add_mapping_button)

        batch_add_button = QPushButton('一括追加')
        batch_add_button.clicked.connect(self.batch_add_category_mappings)
        button_layout1.addWidget(batch_add_button)

        self.delete_mapping_button = QPushButton('選択したマッピングを削除')
        self.delete_mapping_button.clicked.connect(self.delete_category_mapping)
        button_layout1.addWidget(self.delete_mapping_button)

        clear_all_button = QPushButton('すべて削除')
        clear_all_button.clicked.connect(self.clear_all_category_mappings)
        clear_all_button.setStyleSheet('color: red;')
        button_layout1.addWidget(clear_all_button)

        category_layout.addLayout(button_layout1)

        # ボタンのレイアウト - 下段（インポート/エクスポート）
        button_layout2 = QHBoxLayout()

        save_mapping_button = QPushButton('JSONに保存')
        save_mapping_button.clicked.connect(self.save_category_mappings)
        button_layout2.addWidget(save_mapping_button)

        load_mapping_button = QPushButton('JSONから読込')
        load_mapping_button.clicked.connect(self.load_category_mappings)
        button_layout2.addWidget(load_mapping_button)

        export_csv_button = QPushButton('CSVにエクスポート')
        export_csv_button.clicked.connect(self.export_to_csv)
        button_layout2.addWidget(export_csv_button)

        import_csv_button = QPushButton('CSVからインポート')
        import_csv_button.clicked.connect(self.import_from_csv)
        button_layout2.addWidget(import_csv_button)

        category_layout.addLayout(button_layout2)

        self.category_group.setLayout(category_layout)
        step2_layout.addWidget(self.category_group)
        
        # 戻る・次へボタン
        button_layout2 = QHBoxLayout()
        back_button2 = QPushButton('戻る')
        back_button2.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        
        next_button2 = QPushButton('次へ')
        next_button2.clicked.connect(self.proceed_to_step3)
        
        button_layout2.addWidget(back_button2)
        button_layout2.addStretch()
        button_layout2.addWidget(next_button2)
        step2_layout.addLayout(button_layout2)
        
        step2_widget.setLayout(step2_layout)
        
        # ステップ3: プレビューと確認
        step3_widget = QWidget()
        step3_layout = QVBoxLayout()
        
        preview_label = QLabel('取り込み内容のプレビュー:')
        step3_layout.addWidget(preview_label)
        
        self.preview_table = QTableWidget(0, 4)
        self.preview_table.setHorizontalHeaderLabels(['日付', '金額', '説明', 'カテゴリ'])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        step3_layout.addWidget(self.preview_table)
        
        # 重複チェック
        self.duplicate_check = QCheckBox('取り込み時に重複をチェックする')
        self.duplicate_check.setChecked(True)
        step3_layout.addWidget(self.duplicate_check)
        
        # 取り込み期間指定
        date_range_group = QGroupBox('取り込み期間指定（すべての明細を取り込むにはチェックを外してください）')
        date_range_layout = QHBoxLayout()
        
        self.date_range_check = QCheckBox()
        self.date_range_check.setChecked(True)
        date_range_layout.addWidget(self.date_range_check)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        date_range_layout.addWidget(QLabel('開始日:'))
        date_range_layout.addWidget(self.start_date_edit)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_range_layout.addWidget(QLabel('終了日:'))
        date_range_layout.addWidget(self.end_date_edit)
        
        date_range_group.setLayout(date_range_layout)
        step3_layout.addWidget(date_range_group)
        
        # 戻る・取り込みボタン
        button_layout3 = QHBoxLayout()
        back_button3 = QPushButton('戻る')
        back_button3.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        self.import_button = QPushButton('取り込み実行')
        self.import_button.clicked.connect(self.execute_import)
        self.import_button.setStyleSheet('background-color: #4CAF50; color: white; font-weight: bold;')
        
        button_layout3.addWidget(back_button3)
        button_layout3.addStretch()
        button_layout3.addWidget(self.import_button)
        step3_layout.addLayout(button_layout3)
        
        step3_widget.setLayout(step3_layout)
        
        # スタックウィジェットに各ステップを追加
        self.stack.addWidget(step1_widget)
        self.stack.addWidget(step2_widget)
        self.stack.addWidget(step3_widget)
        
        layout.addWidget(self.stack)
        
        self.setLayout(layout)

    def toggle_custom_settings(self, index):
        """フォーマット選択に応じてカスタム設定の表示/非表示を切り替え"""
        if index == 1:  # 「その他」が選択された場合
            self.custom_settings_widget.show()
        else:
            self.custom_settings_widget.hide()
    
    def browse_file(self):
        """CSVファイルを選択するダイアログを表示"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'CSVファイルを選択', '', 'CSVファイル (*.csv);;すべてのファイル (*.*)'
        )
        
        if file_path:
            self.file_path_input.setText(file_path)
    
    def normalize_text(self, text):
        """全角/半角を統一する（全角→半角に変換）"""
        import unicodedata
        return unicodedata.normalize('NFKC', text).lower()

    def delete_category_mapping(self):
        """選択されたカテゴリマッピングを削除"""
        selected_items = self.category_mapping_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', 'マッピングを選択してください')
            return
            
        row = selected_items[0].row()
        keyword = self.category_mapping_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, '確認', 
            f'マッピング "{keyword}" を削除してもよろしいですか？',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if keyword in self.current_format['category_mapping']:
                del self.current_format['category_mapping'][keyword]
                self.update_category_mapping_table()
        
    def add_category_mapping(self):
        """カテゴリマッピングを追加"""
        keyword, ok = QInputDialog.getText(self, 'キーワード追加', 'キーワード:')
        if ok and keyword:
            # キーワードを正規化（全角→半角、大文字→小文字）
            normalized_keyword = self.normalize_text(keyword)
            
            category_list = [
                '食費', '交通費', '娯楽', 'その他', '住宅', 
                '水道光熱費', '美容', '通信費', '日用品', '健康', '教育'
            ]
            
            category, ok = QInputDialog.getItem(
                self, 'カテゴリ選択', 'カテゴリ:', category_list, 0, False
            )
            
            if ok and category:
                self.current_format['category_mapping'][normalized_keyword] = category
                self.update_category_mapping_table()
    
    def update_category_mapping_table(self):
        """カテゴリマッピングテーブルを更新"""
        self.category_mapping_table.setRowCount(0)
        
        for keyword, category in self.current_format['category_mapping'].items():
            row = self.category_mapping_table.rowCount()
            self.category_mapping_table.insertRow(row)
            
            self.category_mapping_table.setItem(row, 0, QTableWidgetItem(keyword))
            self.category_mapping_table.setItem(row, 1, QTableWidgetItem(category))
    
    def proceed_to_step2(self):
        """ステップ2に進む前の処理"""
        # ファイルが選択されているか確認
        if not self.file_path_input.text():
            QMessageBox.warning(self, '警告', 'CSVファイルを選択してください')
            return
        
        # カスタム設定の取得（その他選択時）
        if self.format_combo.currentText() == 'その他':
            self.current_format['encoding'] = self.encoding_combo.currentText()
            self.current_format['date_format'] = self.date_format_input.text()
            self.current_format['skip_rows'] = self.skip_rows_spin.value()
            self.current_format['negation_needed'] = self.negation_needed_check.isChecked()
        
        # CSVファイルの読み込み
        try:
            # PandasでCSVを読み込む
            self.csv_data = pd.read_csv(
                self.file_path_input.text(),
                encoding=self.current_format['encoding'],
                skiprows=self.current_format['skip_rows']
            )
            
            # 列マッピングのドロップダウンを更新
            column_names = self.csv_data.columns.tolist()
            
            self.date_column_combo.clear()
            self.date_column_combo.addItems(column_names)
            if self.current_format['date_column'] in column_names:
                self.date_column_combo.setCurrentText(self.current_format['date_column'])
            
            self.amount_column_combo.clear()
            self.amount_column_combo.addItems(column_names)
            if self.current_format['amount_column'] in column_names:
                self.amount_column_combo.setCurrentText(self.current_format['amount_column'])
            
            self.description_column_combo.clear()
            self.description_column_combo.addItems(column_names)
            if self.current_format['description_column'] in column_names:
                self.description_column_combo.setCurrentText(self.current_format['description_column'])
            
            # カテゴリマッピングテーブルの更新
            self.update_category_mapping_table()
            
            # ステップ2に進む
            self.step_label.setText('ステップ 2/3: 列マッピングとカテゴリ設定')
            self.stack.setCurrentIndex(1)
            
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'CSVファイルの読み込みに失敗しました:\n{str(e)}')
    
    def proceed_to_step3(self):
        """ステップ3に進む前の処理"""
        # マッピング情報の保存
        self.header_mapping = {
            'date': self.date_column_combo.currentText(),
            'amount': self.amount_column_combo.currentText(),
            'description': self.description_column_combo.currentText()
        }
        
        # プレビューデータの生成
        try:
            self.generate_preview_data()
            
            # プレビューテーブルの更新
            self.preview_table.setRowCount(0)
            
            # 最大10行までプレビュー表示
            for row_idx, row_data in enumerate(self.preview_data[:10]):
                self.preview_table.insertRow(row_idx)
                
                self.preview_table.setItem(row_idx, 0, QTableWidgetItem(row_data['date']))
                self.preview_table.setItem(row_idx, 1, QTableWidgetItem(f"{row_data['amount']:,.0f}"))
                self.preview_table.setItem(row_idx, 2, QTableWidgetItem(row_data['description']))
                self.preview_table.setItem(row_idx, 3, QTableWidgetItem(row_data['category']))
            
            # ステップ3に進む
            self.step_label.setText('ステップ 3/3: プレビューと取り込み実行')
            self.stack.setCurrentIndex(2)
            
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'データ処理に失敗しました:\n{str(e)}')
    
    def generate_preview_data(self):
        """プレビューデータを生成"""
        self.preview_data = []
        
        date_col = self.header_mapping['date']
        amount_col = self.header_mapping['amount']
        description_col = self.header_mapping['description']
        
        for _, row in self.csv_data.iterrows():
            try:
                # 日付処理
                date_str = str(row[date_col])
                date_obj = pd.to_datetime(date_str, format=self.current_format['date_format'])
                formatted_date = date_obj.strftime('%Y-%m-%d')
                
                # 金額処理
                amount = float(str(row[amount_col]).replace(',', '').replace('円', '').strip())
                if self.current_format['negation_needed']:
                    amount = -amount
                
                # 金額の絶対値を使用（支出として記録するため）
                amount = abs(amount)
                
                # 説明処理
                description = str(row[description_col])
                
                # 説明文を正規化して比較用に準備
                normalized_description = self.normalize_text(description)
                
                # カテゴリ推定
                category = 'その他'  # デフォルト
                for keyword, mapped_category in self.current_format['category_mapping'].items():
                    normalized_keyword = self.normalize_text(keyword)
                    if normalized_keyword in normalized_description:
                        category = mapped_category
                        break
                
                self.preview_data.append({
                    'date': formatted_date,
                    'amount': amount,
                    'description': description,
                    'category': category
                })
                
            except Exception as e:
                print(f"行の処理中にエラー: {e}")
                continue
    
    def execute_import(self):
        """取り込みを実行"""
        # 期間制限の処理
        filtered_data = self.preview_data
        if self.date_range_check.isChecked():
            start_date = self.start_date_edit.date().toString('yyyy-MM-dd')
            end_date = self.end_date_edit.date().toString('yyyy-MM-dd')
            
            filtered_data = [
                data for data in self.preview_data
                if start_date <= data['date'] <= end_date
            ]
        
        total_records = len(filtered_data)
        if total_records == 0:
            QMessageBox.warning(self, '警告', '取り込むデータがありません')
            return
        
        # 取り込みの確認
        reply = QMessageBox.question(
            self, '確認',
            f'{total_records}件のクレジットカード明細を取り込みます。よろしいですか？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 取り込み実行
        try:
            imported_count = self.import_to_database(filtered_data)
            
            QMessageBox.information(
                self, '取り込み完了',
                f'{imported_count}件のクレジットカード明細を取り込みました。'
            )
            
            # ダイアログを閉じる
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'取り込み処理に失敗しました:\n{str(e)}')
    
    def import_to_database(self, data):
        """データベースへの取り込み処理"""
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        imported_count = 0
        duplicate_count = 0
        
        for item in data:
            date = item['date']
            category = item['category']
            amount = abs(item['amount'])  # 支出なので絶対値を使用
            description = f"クレジットカード: {item['description']}"
            
            # 重複チェック
            if self.duplicate_check.isChecked():
                c.execute('''
                    SELECT id FROM expenses
                    WHERE date = ? AND category = ? AND amount = ? AND description = ?
                ''', (date, category, amount, description))
                
                if c.fetchone():
                    duplicate_count += 1
                    continue
            
            # データベースに追加
            try:
                c.execute('''
                    INSERT INTO expenses (date, category, amount, description)
                    VALUES (?, ?, ?, ?)
                ''', (date, category, amount, description))
                
                imported_count += 1
                
            except Exception as e:
                print(f"行の挿入中にエラー: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        if duplicate_count > 0:
            QMessageBox.information(
                self, '重複スキップ',
                f'{duplicate_count}件の重複データはスキップされました。'
            )
        
        return imported_count
    
    # インポート履歴の保存
    def save_import_history(self, file_name, format_name, record_count):
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        import_date = QDate.currentDate().toString('yyyy-MM-dd')
        
        c.execute('''
            INSERT INTO credit_card_imports 
            (import_date, file_name, format_name, record_count)
            VALUES (?, ?, ?, ?)
        ''', (import_date, file_name, format_name, record_count))
        
        conn.commit()
        conn.close() 

    def clear_all_category_mappings(self):
        """カテゴリマッピングをすべて削除する"""
        reply = QMessageBox.question(
            self, '確認', 
            'すべてのカテゴリマッピングを削除してもよろしいですか？\nこの操作は元に戻せません。',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_format['category_mapping'] = {}  # 空の辞書にリセット
            self.update_category_mapping_table()  # テーブル表示を更新
            QMessageBox.information(self, '完了', 'すべてのカテゴリマッピングを削除しました。')

    def save_category_mappings(self):
        """現在のカテゴリマッピングを保存する"""
        # マッピング名の入力ダイアログ
        mapping_name, ok = QInputDialog.getText(
            self, 'マッピング保存', 
            'マッピング設定の名前を入力してください:',
            QLineEdit.Normal, 'マイカスタムマッピング'
        )
        
        if not ok or not mapping_name:
            return
            
        try:
            # マッピングデータをJSONに変換
            mapping_data = {
                'name': mapping_name,
                'category_mapping': self.current_format['category_mapping']
            }
            mapping_json = json.dumps(mapping_data, ensure_ascii=False, indent=2)
            
            # 保存先ファイルの選択ダイアログ
            file_path, _ = QFileDialog.getSaveFileName(
                self, 'マッピング保存先', 
                f'{mapping_name}.json',
                'JSONファイル (*.json)'
            )
            
            if not file_path:
                return
                
            # ファイルに保存
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(mapping_json)
                
            QMessageBox.information(self, '保存完了', f'カテゴリマッピングを"{file_path}"に保存しました。')
            
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'保存中にエラーが発生しました: {str(e)}')

    def load_category_mappings(self):
        """保存されたカテゴリマッピングを読み込む"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'マッピング読み込み', 
            '',
            'JSONファイル (*.json)'
        )
        
        if not file_path:
            return
            
        try:
            # ファイルからJSON読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                mapping_data = json.loads(f.read())
                
            # 読み込んだデータが正しい形式かチェック
            if 'category_mapping' not in mapping_data:
                raise ValueError('カテゴリマッピングデータが見つかりません')
                
            # 現在のマッピングを上書きする前に確認
            reply = QMessageBox.question(
                self, '確認', 
                '現在のカテゴリマッピングを読み込んだデータで上書きしますか？',
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.current_format['category_mapping'] = mapping_data['category_mapping']
                self.update_category_mapping_table()
                
                mapping_name = mapping_data.get('name', 'カスタムマッピング')
                QMessageBox.information(self, '読み込み完了', f'カテゴリマッピング"{mapping_name}"を読み込みました。')
                
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'読み込み中にエラーが発生しました: {str(e)}')

    def batch_add_category_mappings(self):
        """複数のカテゴリマッピングを一括追加するダイアログ"""
        dialog = QDialog(self)
        dialog.setWindowTitle('一括カテゴリマッピング追加')
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout()
        
        # 説明ラベル
        label = QLabel('各行に「キーワード,カテゴリ」の形式で入力してください。')
        layout.addWidget(label)
        
        # テキスト入力エリア
        text_edit = QTextEdit()
        text_edit.setPlaceholderText('例:\nコンビニ,食費\n電車,交通費\nアマゾン,その他')
        layout.addWidget(text_edit)
        
        # カテゴリリスト
        category_list = [
            '食費', '交通費', '娯楽', 'その他', '住宅', 
            '水道光熱費', '美容', '通信費', '日用品', '健康', '教育'
        ]
        
        # カテゴリ一覧表示
        category_label = QLabel('利用可能なカテゴリ: ' + ', '.join(category_list))
        category_label.setWordWrap(True)
        layout.addWidget(category_label)
        
        # ボタン
        button_layout = QHBoxLayout()
        cancel_button = QPushButton('キャンセル')
        cancel_button.clicked.connect(dialog.reject)
        
        add_button = QPushButton('追加')
        add_button.clicked.connect(dialog.accept)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(add_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # ダイアログ実行
        if dialog.exec_() == QDialog.Accepted:
            text = text_edit.toPlainText()
            if not text.strip():
                return
                
            added_count = 0
            error_count = 0
            
            for line in text.strip().split('\n'):
                if ',' in line:
                    keyword, category = line.split(',', 1)
                    keyword = keyword.strip()
                    category = category.strip()
                    
                    if not keyword or not category:
                        error_count += 1
                        continue
                        
                    if category not in category_list:
                        error_count += 1
                        continue
                    
                    # キーワードを正規化
                    normalized_keyword = self.normalize_text(keyword)
                    
                    # マッピングに追加
                    self.current_format['category_mapping'][normalized_keyword] = category
                    added_count += 1
            
            # テーブル更新
            self.update_category_mapping_table()
            
            # 結果通知
            result_message = f'{added_count}件のマッピングを追加しました。'
            if error_count > 0:
                result_message += f'\n{error_count}件は形式が正しくないため追加されませんでした。'
                
            QMessageBox.information(self, '一括追加結果', result_message)

    def export_to_csv(self):
        """現在のカテゴリマッピングをCSVファイルにエクスポート"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'マッピングをCSVにエクスポート', 
            'category_mappings.csv',
            'CSVファイル (*.csv)'
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['キーワード', 'カテゴリ'])  # ヘッダー行
                
                for keyword, category in self.current_format['category_mapping'].items():
                    writer.writerow([keyword, category])
                    
            QMessageBox.information(self, 'エクスポート完了', f'カテゴリマッピングを"{file_path}"にエクスポートしました。')
            
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'エクスポート中にエラーが発生しました: {str(e)}')

    def import_from_csv(self):
        """CSVファイルからカテゴリマッピングをインポート"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'CSVからマッピングをインポート', 
            '',
            'CSVファイル (*.csv)'
        )
        
        if not file_path:
            return
            
        try:
            # 現在のマッピングを置き換えるか、追加するかを確認
            reply = QMessageBox.question(
                self, 'インポート方法', 
                '現在のマッピングを置き換えますか？「いいえ」を選択すると既存のマッピングに追加されます。',
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            replace_existing = (reply == QMessageBox.Yes)
            
            # 既存のマッピングをクリアする場合
            if replace_existing:
                self.current_format['category_mapping'] = {}
                
            # CSVファイル読み込み
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                header = next(reader, None)  # ヘッダー行をスキップ
                
                added_count = 0
                for row in reader:
                    if len(row) >= 2:
                        keyword = row[0].strip()
                        category = row[1].strip()
                        
                        if keyword and category:
                            normalized_keyword = self.normalize_text(keyword)
                            self.current_format['category_mapping'][normalized_keyword] = category
                            added_count += 1
                            
            # テーブル更新
            self.update_category_mapping_table()
            
            QMessageBox.information(self, 'インポート完了', f'{added_count}件のマッピングを{("インポート" if replace_existing else "追加")}しました。')
            
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'インポート中にエラーが発生しました: {str(e)}')  

class ComprehensiveAnalysisWidget(BaseWidget):
    """全データを分析・可視化するウィジェット"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.load_all_data()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # ナビゲーションボタン
        layout.addLayout(self.button_layout)
        
        # タイトル
        title_label = QLabel("<h1>📊 全データ総合分析</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # データ期間選択
        period_group = QGroupBox("分析期間")
        period_layout = QHBoxLayout()
        
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            '全期間', '過去1年', '過去6ヶ月', '過去3ヶ月',
            '今年', '昨年', 'カスタム期間'
        ])
        self.period_combo.currentIndexChanged.connect(self.update_analysis)
        
        # カスタム期間用
        self.custom_start = QDateEdit()
        self.custom_start.setCalendarPopup(True)
        self.custom_start.setDate(QDate.currentDate().addMonths(-12))
        
        self.custom_end = QDateEdit()
        self.custom_end.setCalendarPopup(True)
        self.custom_end.setDate(QDate.currentDate())
        
        period_layout.addWidget(QLabel("期間:"))
        period_layout.addWidget(self.period_combo)
        period_layout.addWidget(QLabel("開始:"))
        period_layout.addWidget(self.custom_start)
        period_layout.addWidget(QLabel("終了:"))
        period_layout.addWidget(self.custom_end)
        
        update_button = QPushButton("分析更新")
        update_button.clicked.connect(self.update_analysis)
        period_layout.addWidget(update_button)
        
        period_group.setLayout(period_layout)
        layout.addWidget(period_group)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # タブ1: 総合サマリー
        self.summary_tab = QWidget()
        self.setup_summary_tab()
        self.tab_widget.addTab(self.summary_tab, "📈 総合サマリー")
        
        # タブ2: 詳細統計
        self.statistics_tab = QWidget()
        self.setup_statistics_tab()
        self.tab_widget.addTab(self.statistics_tab, "📊 詳細統計")
        
        # タブ3: カテゴリ分析
        self.category_tab = QWidget()
        self.setup_category_tab()
        self.tab_widget.addTab(self.category_tab, "🏷️ カテゴリ分析")
        
        # タブ4: 時系列分析
        self.timeline_tab = QWidget()
        self.setup_timeline_tab()
        self.tab_widget.addTab(self.timeline_tab, "📅 時系列分析")
        
        # タブ5: データエクスポート
        self.export_tab = QWidget()
        self.setup_export_tab()
        self.tab_widget.addTab(self.export_tab, "💾 データエクスポート")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def load_all_data(self):
        """データベースから全データを読み込む"""
        conn = sqlite3.connect('budget.db')
        
        # 支出データ
        self.expenses_df = pd.read_sql_query(
            'SELECT * FROM expenses ORDER BY date',
            conn
        )
        if not self.expenses_df.empty:
            self.expenses_df['date'] = pd.to_datetime(self.expenses_df['date'])
        
        # 収入データ
        self.income_df = pd.read_sql_query(
            'SELECT * FROM monthly_income ORDER BY year, month',
            conn
        )
        
        # 目標データ
        self.monthly_goals_df = pd.read_sql_query(
            'SELECT * FROM monthly_goals ORDER BY year, month',
            conn
        )
        
        self.category_goals_df = pd.read_sql_query(
            'SELECT * FROM category_goals ORDER BY year, month, category',
            conn
        )
        
        # 貯金目標データ
        self.savings_goals_df = pd.read_sql_query(
            'SELECT * FROM savings_goals ORDER BY start_date',
            conn
        )
        
        # 定期支払いデータ
        self.recurring_df = pd.read_sql_query(
            'SELECT * FROM recurring_expenses WHERE is_active = 1',
            conn
        )
        
        conn.close()
        
        # 初回分析
        self.update_analysis()
    
    def get_filtered_data(self):
        """期間フィルタを適用したデータを取得"""
        if self.expenses_df.empty:
            return pd.DataFrame()
        
        period = self.period_combo.currentText()
        df = self.expenses_df.copy()
        
        today = pd.Timestamp.now()
        
        if period == '過去1年':
            start_date = today - pd.DateOffset(years=1)
            df = df[df['date'] >= start_date]
        elif period == '過去6ヶ月':
            start_date = today - pd.DateOffset(months=6)
            df = df[df['date'] >= start_date]
        elif period == '過去3ヶ月':
            start_date = today - pd.DateOffset(months=3)
            df = df[df['date'] >= start_date]
        elif period == '今年':
            df = df[df['date'].dt.year == today.year]
        elif period == '昨年':
            df = df[df['date'].dt.year == today.year - 1]
        elif period == 'カスタム期間':
            start = pd.Timestamp(self.custom_start.date().toPyDate())
            end = pd.Timestamp(self.custom_end.date().toPyDate())
            df = df[(df['date'] >= start) & (df['date'] <= end)]
        
        return df
    
    def setup_summary_tab(self):
        """総合サマリータブのUI"""
        layout = QVBoxLayout()
        
        # サマリーカード群
        cards_layout = QHBoxLayout()
        
        # 総支出カード
        self.total_expense_card = self.create_summary_card(
            "💰 総支出", "0円", "#FF6B6B"
        )
        cards_layout.addWidget(self.total_expense_card)
        
        # 総収入カード
        self.total_income_card = self.create_summary_card(
            "💵 総収入", "0円", "#4CAF50"
        )
        cards_layout.addWidget(self.total_income_card)
        
        # 純貯蓄カード
        self.net_savings_card = self.create_summary_card(
            "💎 純貯蓄", "0円", "#2196F3"
        )
        cards_layout.addWidget(self.net_savings_card)
        
        # 平均貯蓄率カード
        self.avg_savings_rate_card = self.create_summary_card(
            "📊 平均貯蓄率", "0%", "#9C27B0"
        )
        cards_layout.addWidget(self.avg_savings_rate_card)
        
        layout.addLayout(cards_layout)
        
        # 月次推移グラフ
        self.summary_chart_view = QChartView()
        self.summary_chart_view.setMinimumHeight(300)
        layout.addWidget(self.summary_chart_view)
        
        # 主要統計情報
        stats_group = QGroupBox("主要統計情報")
        stats_layout = QFormLayout()
        
        self.record_count_label = QLabel("0件")
        self.first_record_label = QLabel("-")
        self.last_record_label = QLabel("-")
        self.avg_monthly_expense_label = QLabel("0円")
        self.max_monthly_expense_label = QLabel("0円")
        self.min_monthly_expense_label = QLabel("0円")
        
        stats_layout.addRow("総記録数:", self.record_count_label)
        stats_layout.addRow("最初の記録:", self.first_record_label)
        stats_layout.addRow("最新の記録:", self.last_record_label)
        stats_layout.addRow("月平均支出:", self.avg_monthly_expense_label)
        stats_layout.addRow("最大月次支出:", self.max_monthly_expense_label)
        stats_layout.addRow("最小月次支出:", self.min_monthly_expense_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        self.summary_tab.setLayout(layout)
    
    def create_summary_card(self, title, value, color):
        """サマリーカードを作成"""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        card_layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        value_label.setObjectName("value_label")
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        
        card.setLayout(card_layout)
        return card
    
    def setup_statistics_tab(self):
        """詳細統計タブのUI"""
        layout = QVBoxLayout()
        
        # 統計テーブル
        self.stats_table = QTableWidget(0, 2)
        self.stats_table.setHorizontalHeaderLabels(['項目', '値'])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.stats_table)
        
        self.statistics_tab.setLayout(layout)
    
    def setup_category_tab(self):
        """カテゴリ分析タブのUI"""
        layout = QVBoxLayout()
        
        # カテゴリ別集計テーブル
        self.category_table = QTableWidget(0, 6)
        self.category_table.setHorizontalHeaderLabels([
            'カテゴリ', '総額', '平均', '最大', '最小', '回数'
        ])
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.category_table)
        
        # カテゴリ別円グラフ
        self.category_chart_view = QChartView()
        self.category_chart_view.setMinimumHeight(300)
        layout.addWidget(self.category_chart_view)
        
        self.category_tab.setLayout(layout)
    
    def setup_timeline_tab(self):
        """時系列分析タブのUI"""
        layout = QVBoxLayout()
        
        # 時系列グラフ
        self.timeline_chart_view = QChartView()
        self.timeline_chart_view.setMinimumHeight(400)
        layout.addWidget(self.timeline_chart_view)
        
        # 月次データテーブル
        self.monthly_table = QTableWidget(0, 4)
        self.monthly_table.setHorizontalHeaderLabels([
            '年月', '収入', '支出', '収支'
        ])
        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.monthly_table)
        
        self.timeline_tab.setLayout(layout)
    
    def setup_export_tab(self):
        """データエクスポートタブのUI"""
        layout = QVBoxLayout()
        
        # エクスポート形式選択
        format_group = QGroupBox("エクスポート形式")
        format_layout = QVBoxLayout()
        
        self.export_csv_button = QPushButton("📄 CSV形式でエクスポート")
        self.export_csv_button.clicked.connect(lambda: self.export_data('csv'))
        
        self.export_excel_button = QPushButton("📊 Excel形式でエクスポート")
        self.export_excel_button.clicked.connect(lambda: self.export_data('excel'))
        
        self.export_json_button = QPushButton("🔧 JSON形式でエクスポート")
        self.export_json_button.clicked.connect(lambda: self.export_data('json'))
        
        format_layout.addWidget(self.export_csv_button)
        format_layout.addWidget(self.export_excel_button)
        format_layout.addWidget(self.export_json_button)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # エクスポート対象選択
        target_group = QGroupBox("エクスポート対象")
        target_layout = QVBoxLayout()
        
        self.export_expenses_check = QCheckBox("支出データ")
        self.export_expenses_check.setChecked(True)
        
        self.export_income_check = QCheckBox("収入データ")
        self.export_income_check.setChecked(True)
        
        self.export_goals_check = QCheckBox("目標データ")
        self.export_goals_check.setChecked(True)
        
        target_layout.addWidget(self.export_expenses_check)
        target_layout.addWidget(self.export_income_check)
        target_layout.addWidget(self.export_goals_check)
        
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # 分析レポート生成
        report_group = QGroupBox("分析レポート")
        report_layout = QVBoxLayout()
        
        self.generate_report_button = QPushButton("📋 詳細レポートを生成")
        self.generate_report_button.clicked.connect(self.generate_detailed_report)
        
        report_layout.addWidget(self.generate_report_button)
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)
        
        layout.addStretch()
        self.export_tab.setLayout(layout)
    
    def update_analysis(self):
        """分析データを更新"""
        df = self.get_filtered_data()
        
        if df.empty:
            QMessageBox.warning(self, '警告', '指定期間にデータがありません')
            return
        
        # サマリー更新
        self.update_summary(df)
        
        # 統計更新
        self.update_statistics(df)
        
        # カテゴリ分析更新
        self.update_category_analysis(df)
        
        # 時系列分析更新
        self.update_timeline_analysis(df)
    
    def update_summary(self, df):
        """サマリー情報を更新"""
        # 総支出
        total_expense = df['amount'].sum()
        
        # 総収入の計算
        if not df.empty:
            years_months = df['date'].dt.to_period('M').unique()
            total_income = 0
            
            for ym in years_months:
                year = ym.year
                month = ym.month
                income_row = self.income_df[
                    (self.income_df['year'] == year) &
                    (self.income_df['month'] == month)
                ]
                if not income_row.empty:
                    total_income += income_row['income'].sum()
        else:
            total_income = 0
        
        # 純貯蓄
        net_savings = total_income - total_expense
        
        # 平均貯蓄率
        avg_savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
        
        # カード更新
        self.update_card_value(self.total_expense_card, f"{total_expense:,.0f}円")
        self.update_card_value(self.total_income_card, f"{total_income:,.0f}円")
        self.update_card_value(self.net_savings_card, f"{net_savings:,.0f}円")
        self.update_card_value(self.avg_savings_rate_card, f"{avg_savings_rate:.1f}%")
        
        # 基本統計
        self.record_count_label.setText(f"{len(df):,}件")
        
        if not df.empty:
            self.first_record_label.setText(df['date'].min().strftime('%Y年%m月%d日'))
            self.last_record_label.setText(df['date'].max().strftime('%Y年%m月%d日'))
            
            # 月次集計
            monthly_expense = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
            
            self.avg_monthly_expense_label.setText(f"{monthly_expense.mean():,.0f}円")
            self.max_monthly_expense_label.setText(f"{monthly_expense.max():,.0f}円")
            self.min_monthly_expense_label.setText(f"{monthly_expense.min():,.0f}円")
        
        # グラフ更新
        self.update_summary_chart(df)
    
    def update_card_value(self, card, value):
        """カードの値を更新"""
        value_label = card.findChild(QLabel, "value_label")
        if value_label:
            value_label.setText(value)
    
    def update_summary_chart(self, df):
        """サマリーグラフを更新"""
        if df.empty:
            return
        
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 月次集計
        monthly_data = df.groupby(df['date'].dt.to_period('M')).agg({
            'amount': 'sum'
        }).reset_index()
        
        monthly_data['date'] = monthly_data['date'].dt.to_timestamp()
        
        # 支出ライン
        expense_series = QLineSeries()
        expense_series.setName("月次支出")
        
        for _, row in monthly_data.iterrows():
            expense_series.append(
                row['date'].timestamp() * 1000,
                row['amount']
            )
        
        expense_series.setColor(QColor("#FF6B6B"))
        pen = QPen()
        pen.setWidth(3)
        expense_series.setPen(pen)
        
        chart.addSeries(expense_series)
        chart.setTitle("月次支出推移")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        self.summary_chart_view.setChart(chart)
    
    def update_statistics(self, df):
        """詳細統計を更新"""
        self.stats_table.setRowCount(0)
        
        if df.empty:
            return
        
        stats = {
            '総支出額': f"{df['amount'].sum():,.0f}円",
            '平均支出額': f"{df['amount'].mean():,.0f}円",
            '中央値': f"{df['amount'].median():,.0f}円",
            '標準偏差': f"{df['amount'].std():,.0f}円",
            '最大支出': f"{df['amount'].max():,.0f}円",
            '最小支出': f"{df['amount'].min():,.0f}円",
            '記録数': f"{len(df):,}件",
            '記録日数': f"{df['date'].dt.date.nunique():,}日",
            '1日平均支出': f"{df['amount'].sum() / df['date'].dt.date.nunique():,.0f}円",
        }
        
        for key, value in stats.items():
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)
            self.stats_table.setItem(row, 0, QTableWidgetItem(key))
            self.stats_table.setItem(row, 1, QTableWidgetItem(value))
    
    def update_category_analysis(self, df):
        """カテゴリ分析を更新"""
        if df.empty:
            return
        
        # カテゴリ別集計
        category_stats = df.groupby('category').agg({
            'amount': ['sum', 'mean', 'max', 'min', 'count']
        }).reset_index()
        
        category_stats.columns = ['category', 'sum', 'mean', 'max', 'min', 'count']
        category_stats = category_stats.sort_values('sum', ascending=False)
        
        # テーブル更新
        self.category_table.setRowCount(0)
        
        for _, row in category_stats.iterrows():
            row_idx = self.category_table.rowCount()
            self.category_table.insertRow(row_idx)
            
            self.category_table.setItem(row_idx, 0, QTableWidgetItem(row['category']))
            self.category_table.setItem(row_idx, 1, QTableWidgetItem(f"{row['sum']:,.0f}"))
            self.category_table.setItem(row_idx, 2, QTableWidgetItem(f"{row['mean']:,.0f}"))
            self.category_table.setItem(row_idx, 3, QTableWidgetItem(f"{row['max']:,.0f}"))
            self.category_table.setItem(row_idx, 4, QTableWidgetItem(f"{row['min']:,.0f}"))
            self.category_table.setItem(row_idx, 5, QTableWidgetItem(f"{int(row['count']):,}"))
        
        # 円グラフ更新
        self.update_category_chart(category_stats)
    
    def update_category_chart(self, category_stats):
        """カテゴリ別円グラフを更新"""
        chart = QChart()
        series = QPieSeries()
        
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD',
            '#FFD93D', '#6C5B7B', '#F7A072', '#C06C84', '#95A5A6'
        ]
        
        for i, (_, row) in enumerate(category_stats.iterrows()):
            slice = series.append(row['category'], row['sum'])
            slice.setLabelVisible(True)
            slice.setLabel(f"{row['category']}\n{row['sum']:,.0f}円")
            slice.setColor(QColor(colors[i % len(colors)]))
        
        chart.addSeries(series)
        chart.setTitle("カテゴリ別支出割合")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        self.category_chart_view.setChart(chart)
    
    def update_timeline_analysis(self, df):
        """時系列分析を更新"""
        if df.empty:
            return
        
        # 月次集計
        monthly_data = df.groupby(df['date'].dt.to_period('M')).agg({
            'amount': 'sum'
        }).reset_index()
        
        monthly_data['year_month'] = monthly_data['date'].apply(
            lambda x: f"{x.year}/{x.month:02d}"
        )
        
        # テーブル更新
        self.monthly_table.setRowCount(0)
        
        for _, row in monthly_data.iterrows():
            year = row['date'].year
            month = row['date'].month
            
            # 収入取得
            income_row = self.income_df[
                (self.income_df['year'] == year) &
                (self.income_df['month'] == month)
            ]
            income = income_row['income'].values[0] if not income_row.empty else 0
            
            expense = row['amount']
            balance = income - expense
            
            row_idx = self.monthly_table.rowCount()
            self.monthly_table.insertRow(row_idx)
            
            self.monthly_table.setItem(row_idx, 0, QTableWidgetItem(row['year_month']))
            self.monthly_table.setItem(row_idx, 1, QTableWidgetItem(f"{income:,.0f}"))
            self.monthly_table.setItem(row_idx, 2, QTableWidgetItem(f"{expense:,.0f}"))
            
            balance_item = QTableWidgetItem(f"{balance:,.0f}")
            if balance < 0:
                balance_item.setForeground(QColor("#FF6B6B"))
            else:
                balance_item.setForeground(QColor("#4CAF50"))
            
            self.monthly_table.setItem(row_idx, 3, balance_item)
    
    def export_data(self, format_type):
        """データをエクスポート"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if format_type == 'csv':
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 'CSVファイルを保存',
                    f'家計簿データ_{timestamp}.csv',
                    'CSVファイル (*.csv)'
                )
                
                if file_path:
                    df = self.get_filtered_data()
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                    QMessageBox.information(self, '成功', f'データをエクスポートしました:\n{file_path}')
            
            elif format_type == 'excel':
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 'Excelファイルを保存',
                    f'家計簿データ_{timestamp}.xlsx',
                    'Excelファイル (*.xlsx)'
                )
                
                if file_path:
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        if self.export_expenses_check.isChecked():
                            self.get_filtered_data().to_excel(
                                writer, sheet_name='支出データ', index=False
                            )
                        
                        if self.export_income_check.isChecked():
                            self.income_df.to_excel(
                                writer, sheet_name='収入データ', index=False
                            )
                        
                        if self.export_goals_check.isChecked():
                            self.monthly_goals_df.to_excel(
                                writer, sheet_name='月間目標', index=False
                            )
                            self.category_goals_df.to_excel(
                                writer, sheet_name='カテゴリ目標', index=False
                            )
                    
                    QMessageBox.information(self, '成功', f'データをエクスポートしました:\n{file_path}')
            
            elif format_type == 'json':
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 'JSONファイルを保存',
                    f'家計簿データ_{timestamp}.json',
                    'JSONファイル (*.json)'
                )
                
                if file_path:
                    data = {
                        'expenses': self.get_filtered_data().to_dict('records'),
                        'income': self.income_df.to_dict('records'),
                        'goals': self.monthly_goals_df.to_dict('records')
                    }
                    
                    import json
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                    
                    QMessageBox.information(self, '成功', f'データをエクスポートしました:\n{file_path}')
        
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'エクスポートに失敗しました:\n{str(e)}')
    
    def generate_detailed_report(self):
        """詳細レポートを生成"""
        df = self.get_filtered_data()
        
        if df.empty:
            QMessageBox.warning(self, '警告', '分析対象のデータがありません')
            return
        
        # レポート生成ダイアログ
        report_text = self.create_report_text(df)
        
        dialog = QDialog(self)
        dialog.setWindowTitle('詳細分析レポート')
        dialog.setMinimumWidth(800)
        dialog.setMinimumHeight(600)
        
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(report_text)
        layout.addWidget(text_edit)
        
        # 保存ボタン
        save_button = QPushButton('レポートを保存')
        save_button.clicked.connect(lambda: self.save_report(report_text))
        layout.addWidget(save_button)
        
        close_button = QPushButton('閉じる')
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def create_report_text(self, df):
        """レポートテキストを作成"""
        total_expense = df['amount'].sum()
        avg_expense = df['amount'].mean()
        
        # カテゴリ別集計
        category_stats = df.groupby('category')['amount'].sum().sort_values(ascending=False)
        
        # 月次集計
        monthly_stats = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
        
        report = f"""
        <h1>家計簿 詳細分析レポート</h1>
        <p>生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        <p>分析期間: {self.period_combo.currentText()}</p>
        
        <h2>📊 総合サマリー</h2>
        <ul>
            <li><b>総支出額:</b> {total_expense:,.0f}円</li>
            <li><b>平均支出額:</b> {avg_expense:,.0f}円</li>
            <li><b>記録数:</b> {len(df):,}件</li>
            <li><b>記録期間:</b> {df['date'].min().strftime('%Y年%m月%d日')} 〜 {df['date'].max().strftime('%Y年%m月%d日')}</li>
        </ul>
        
        <h2>🏷️ カテゴリ別支出トップ5</h2>
        <ol>
        """
        
        for category, amount in category_stats.head(5).items():
            percentage = (amount / total_expense * 100)
            report += f"<li><b>{category}:</b> {amount:,.0f}円 ({percentage:.1f}%)</li>"
        
        report += """
        </ol>
        
        <h2>📅 月次支出推移</h2>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>年月</th>
                <th>支出額</th>
            </tr>
        """
        
        for period, amount in monthly_stats.items():
            report += f"""
            <tr>
                <td>{period.year}年{period.month}月</td>
                <td>{amount:,.0f}円</td>
            </tr>
            """
        
        report += "</table>"
        
        return report
    
    def save_report(self, report_text):
        """レポートを保存"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'レポートを保存',
            f"家計簿レポート_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            'HTMLファイル (*.html)'
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            QMessageBox.information(self, '成功', f'レポートを保存しました:\n{file_path}')                      

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BudgetApp()
    window.show()
    sys.exit(app.exec_())