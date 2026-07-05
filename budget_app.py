# 正しいインポート文の修正版

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
    QSizePolicy, QSpacerItem, QInputDialog
)

# PyQt5 コアとグラフィック（修正版）
from PyQt5.QtCore import Qt, QDate, QMargins, QPointF
from PyQt5.QtGui import QFont, QColor, QPen, QBrush

# PyQt5 チャート関連（修正版）
from PyQt5.QtChart import (
    QChart, QChartView, QPieSeries, QPieSlice, QBarSeries,
    QBarSet, QValueAxis, QBarCategoryAxis, QLineSeries,
    QAreaSeries, QCategoryAxis
)

# その他のライブラリ
import sqlite3
import pandas as pd
import os
import sys
import io
import requests
from datetime import datetime, timedelta
from db_utils import get_db_connection, execute_query, get_categories, execute_many, fetch_df

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

class BudgetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_database()
        # self.initUI()  # 古いメソッドをコメントアウト
        
        # バックアップマネージャーの初期化
        self.backup_manager = BackupManager()
        
        self.enhanced_init_ui()  # 新しいメソッドを呼び出す
        
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

        # 資産管理テーブルの作成
        execute_query('''
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_type TEXT NOT NULL,  -- 'bank' または 'securities'
                account_name TEXT NOT NULL,  -- 銀行名や証券会社名
                balance REAL NOT NULL DEFAULT 0,  -- 残高または評価額
                last_updated TEXT,  -- 最終更新日
                notes TEXT,  -- 備考（口座種別など）
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        ''')
        
        # 資産履歴テーブルの作成
        execute_query('''
            CREATE TABLE IF NOT EXISTS asset_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                record_date TEXT NOT NULL,  -- 記録日
                balance REAL NOT NULL,  -- その時点での残高
                FOREIGN KEY (asset_id) REFERENCES assets(id)
            )
        ''')
        
        # インデックスの作成（検索高速化）
        execute_query('''
            CREATE INDEX IF NOT EXISTS idx_asset_history_date 
            ON asset_history(record_date)
        ''')
        
        execute_query('''
            CREATE INDEX IF NOT EXISTS idx_asset_history_asset_id
            ON asset_history(asset_id)
        ''')

        # 支出テーブルのインデックス（検索・フィルター高速化）
        execute_query('CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)')
        execute_query('CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)')

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
            'comprehensive_analysis': ComprehensiveAnalysisWidget,
            'asset_management': AssetManagementWidget  # ←この行があるか確認
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
            'comprehensive_analysis': self.comprehensive_analysis_widget,
            'asset_management': self.asset_management_widget
        }

        # ボタン名とターゲットウィジェットのマッピング
        button_targets = {
            'income_expense_button': self.income_expense_widget,
            'breakdown_button': self.breakdown_widget,
            'monthly_report_button': self.monthly_report_widget,
            'goal_management_button': self.goal_management_widget,
            'diagnostic_report_button': self.diagnostic_report_widget,
            'comprehensive_analysis_button': self.comprehensive_analysis_widget,
            'asset_management_button': self.asset_management_widget
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
                except Exception as e:
                    # 失敗した場合は警告を出すだけにする
                    print(f"Warning: Could not add button to {type(widget).__name__}: {e}")
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
                # 成功時はメッセージを表示しない（完全に自動）
            except Exception as e:
                print(f"自動バックアップエラー: {e}")
                # 失敗したことをユーザーに知らせる。
                # 黙って失敗し続けると「バックアップがあると思っていたのに無かった」
                # という最悪の事態につながるため、必ず画面で通知する
                QMessageBox.warning(
                    self, '自動バックアップ失敗',
                    f'自動バックアップに失敗しました。\n\n{e}\n\n'
                    'バックアップ管理画面から手動バックアップをお試しください。'
                )

    def show_category_management(self):
        """カテゴリ管理ダイアログを表示"""
        dialog = CategoryManagementDialog(self)
        dialog.exec_()

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
    '''収入と支出を管理・表示するメインウィジェット'''
    def __init__(self, parent=None):
        super().__init__(parent)  # BaseWidget の初期化
        self.current_year, self.current_month = DateHelper.get_current_year_month()
        self.initUI()
        self.load_monthly_income()      # ←この行を追加
        self.update_monthly_expense()

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
        
        # 収入入力ボタン
        save_income_button = QPushButton('収入を保存')
        save_income_button.clicked.connect(self.save_monthly_income)
        layout.addLayout(summary_layout)
        layout.addWidget(save_income_button)

        # 期間選択
        year_month_layout = QHBoxLayout()
        self.prev_month_button = QPushButton('◀ 前月')
        self.next_month_button = QPushButton('次月 ▶')
        self.period_label = QLabel(f'{self.current_year}年{self.current_month}月')
        
        year_month_layout.addWidget(self.prev_month_button)
        year_month_layout.addWidget(self.period_label)
        year_month_layout.addWidget(self.next_month_button)
        year_month_layout.addStretch()
        
        self.prev_month_button.clicked.connect(self.show_prev_month)
        self.next_month_button.clicked.connect(self.show_next_month)
        
        layout.addLayout(year_month_layout)

        # 入力フォーム
        form_layout = QFormLayout()

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        form_layout.addRow('日付:', self.date_input)

        # カテゴリ選択（動的に読み込み）
        self.category_input = QComboBox()
        try:
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            c.execute('SELECT name FROM categories ORDER BY sort_order')
            db_categories = [row[0] for row in c.fetchall()]
            conn.close()
            self.category_input.addItems(db_categories)
            
        except Exception as e:
            # エラー時はデフォルトカテゴリを使用
            print(f"カテゴリ取得エラー: {e}")
            self.category_input.addItems(get_categories())
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

        # ========== シンプルな表示設定エリア ==========
        display_group = QGroupBox('表示設定')
        display_main_layout = QVBoxLayout()

        # 1行目: 検索バー
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('キーワードで検索（説明文・カテゴリ）')
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.update_expense_table_display)

        self.amount_min_input = QLineEdit()
        self.amount_min_input.setPlaceholderText('最小金額')
        self.amount_min_input.setFixedWidth(100)
        self.amount_min_input.editingFinished.connect(self.update_expense_table_display)

        self.amount_max_input = QLineEdit()
        self.amount_max_input.setPlaceholderText('最大金額')
        self.amount_max_input.setFixedWidth(100)
        self.amount_max_input.editingFinished.connect(self.update_expense_table_display)

        search_layout.addWidget(QLabel('検索:'))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(QLabel('金額:'))
        search_layout.addWidget(self.amount_min_input)
        search_layout.addWidget(QLabel('〜'))
        search_layout.addWidget(self.amount_max_input)
        display_main_layout.addLayout(search_layout)

        # 2行目: 既存の並び替え・フィルター
        display_layout = QHBoxLayout()

        # 並び替えオプション
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['日付順（新しい順）', '日付順（古い順）', 'カテゴリ別', '金額順（高い順）', '金額順（安い順）'])

        # カテゴリフィルター
        self.filter_combo = QComboBox()
        self.filter_combo.addItem('全てのカテゴリ')

        # 表示件数
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(['50件', '100件', '200件', '全て'])

        display_layout.addWidget(QLabel('並び替え:'))
        display_layout.addWidget(self.sort_combo)
        display_layout.addWidget(QLabel('カテゴリ:'))
        display_layout.addWidget(self.filter_combo)
        display_layout.addWidget(QLabel('表示件数:'))
        display_layout.addWidget(self.limit_combo)
        display_layout.addStretch()
        display_main_layout.addLayout(display_layout)

        display_group.setLayout(display_main_layout)
        layout.addWidget(display_group)

        # カテゴリ別合計表示ラベル
        self.category_total_label = QLabel('')
        self.category_total_label.setFont(QFont('', 11, QFont.Bold))
        self.category_total_label.setStyleSheet('color: #1565C0; padding: 5px; background-color: #E3F2FD; border-radius: 4px;')
        layout.addWidget(self.category_total_label)

        # カテゴリをロードしてイベント接続
        self.load_categories_for_filter()
        self.sort_combo.currentIndexChanged.connect(self.update_expense_table_display)
        self.filter_combo.currentIndexChanged.connect(self.update_expense_table_display)
        self.limit_combo.currentIndexChanged.connect(self.update_expense_table_display)

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

        # 楽天PAY明細取込ボタン
        self.rakuten_pay_import_button = QPushButton('楽天PAY明細取込')
        self.rakuten_pay_import_button.clicked.connect(self.show_rakuten_pay_import_dialog)
        layout.addWidget(self.rakuten_pay_import_button)

        # PayPay明細取込ボタン
        self.paypay_import_button = QPushButton('PayPay明細取込')
        self.paypay_import_button.clicked.connect(self.show_paypay_import_dialog)
        layout.addWidget(self.paypay_import_button)

        # PASMO明細取込ボタン
        self.pasmo_import_button = QPushButton('PASMO明細取込')
        self.pasmo_import_button.clicked.connect(self.show_pasmo_import_dialog)
        layout.addWidget(self.pasmo_import_button)

        # CSVエクスポートボタン
        self.export_button = QPushButton('CSVエクスポート')
        self.export_button.clicked.connect(self.export_to_excel)
        layout.addWidget(self.export_button)

        # PDFエクスポートボタン（全データ）
        self.pdf_export_button = QPushButton('PDF全データエクスポート')
        self.pdf_export_button.clicked.connect(self.export_all_to_pdf)
        layout.addWidget(self.pdf_export_button)

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

        # カテゴリ別予算アラート表示エリア
        self.budget_alert_label = QLabel('')
        self.budget_alert_label.setWordWrap(True)
        self.budget_alert_label.setVisible(False)
        goal_progress_layout.addWidget(self.budget_alert_label)

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

            # カテゴリ別予算アラートの更新
            self.update_budget_alerts()

        except Exception as e:
            print(f"目標進捗表示の更新中にエラー: {e}")

    def update_budget_alerts(self):
        """カテゴリ別予算の超過アラートを表示"""
        try:
            # カテゴリ別目標を取得
            goals = execute_query('''
                SELECT category, goal_amount FROM category_goals
                WHERE year = ? AND month = ?
            ''', (self.current_year, self.current_month), fetch_all=True)

            if not goals:
                self.budget_alert_label.setVisible(False)
                return

            # カテゴリ別実績を取得
            actuals = execute_query('''
                SELECT category, SUM(amount) FROM expenses
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
                GROUP BY category
            ''', (str(self.current_year), f"{self.current_month:02d}"), fetch_all=True)

            actual_dict = {row[0]: row[1] for row in actuals} if actuals else {}

            alerts = []
            for category, goal_amount in goals:
                if goal_amount <= 0:
                    continue
                actual = actual_dict.get(category, 0)
                ratio = actual / goal_amount * 100

                if ratio >= 100:
                    alerts.append(f'<span style="color:#D32F2F; font-weight:bold;">[超過] {category}: {actual:,.0f}円 / {goal_amount:,.0f}円 ({ratio:.0f}%)</span>')
                elif ratio >= 80:
                    alerts.append(f'<span style="color:#F57F17; font-weight:bold;">[注意] {category}: {actual:,.0f}円 / {goal_amount:,.0f}円 ({ratio:.0f}%)</span>')

            if alerts:
                self.budget_alert_label.setText('<br>'.join(alerts))
                self.budget_alert_label.setVisible(True)
            else:
                self.budget_alert_label.setVisible(False)

        except Exception as e:
            print(f"予算アラート更新エラー: {e}")

    def update_expense_in_db(self, expense_id, date, category, amount, description):
        
        execute_query('''
            UPDATE expenses
            SET date = ?, category = ?, amount = ?, description = ?
            WHERE id = ?
        ''', (date, category, amount, description, expense_id))

    def delete_expense_from_db(self, expense_id):
        
        execute_query('DELETE FROM expenses WHERE id = ?', (expense_id,))

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

    def update_table(self):
        """テーブル更新（新システム専用）"""
        try:
            print(f"=== update_table（新システム専用）===")
            
            # 古いシステムを完全無効化
            # self.is_updating = True
            # 既存のpandas処理をすべてコメントアウト
            
            # 新システムのみ実行
            if hasattr(self, 'load_current_month_expenses'):
                self.load_current_month_expenses()
            else:
                print("新システムが利用できません")
                
        except Exception as e:
            print(f"update_table エラー: {e}")

        

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
                # Noneチェックを追加
                id_item = self.expense_table.item(row, 0)
                if id_item is None:
                    print(f"警告: 行{row}のIDセルがNoneです")
                    return
                expense_id = int(id_item.text())
                
                date_item = self.expense_table.item(row, 1)
                if date_item is None:
                    print(f"警告: 行{row}の日付セルがNoneです")
                    return
                date = date_item.text()
                
                # カテゴリの処理(コンボボックスかテキストか判定)
                category_widget = self.expense_table.cellWidget(row, 2)
                if category_widget and isinstance(category_widget, QComboBox):
                    category = category_widget.currentText()
                else:
                    category_item = self.expense_table.item(row, 2)
                    if category_item is None:
                        print(f"警告: 行{row}のカテゴリセルがNoneです")
                        return
                    category = category_item.text() if category_item else ''
                
                # 金額の処理を改善
                amount_item = self.expense_table.item(row, 3)
                if amount_item is None:
                    print(f"警告: 行{row}の金額セルがNoneです")
                    return
                amount_text = amount_item.text()
                
                # カンマ、空白、円記号、マイナス記号を処理
                amount_text = amount_text.replace(',', '').replace(' ', '').replace('円', '').replace('−', '-').replace('－', '-')
                
                # 空文字列チェック
                if not amount_text.strip():
                    raise ValueError("金額が入力されていません")
                
                amount = float(amount_text)
                
                # 金額が負数でない場合は絶対値を使用(支出として記録)
                if amount < 0:
                    amount = abs(amount)
                
                description_item = self.expense_table.item(row, 4)
                if description_item is None:
                    print(f"警告: 行{row}の説明セルがNoneです")
                    return
                description = description_item.text()
                
                # データベース更新(共通関数を使用)
                execute_query('''
                    UPDATE expenses 
                    SET date = ?, category = ?, amount = ?, description = ?
                    WHERE id = ?
                ''', (date, category, amount, description, expense_id))
                
                print(f"データ更新成功: ID={expense_id}, 金額={amount}")  # デバッグ用
                
                # 表示を更新(金額編集時は少し待つ)
                if column == 3:  # 金額列の場合
                    QApplication.processEvents()  # UI更新を待つ
                
                self.update_monthly_expense()
                if hasattr(self, 'update_goal_progress'):
                    self.update_goal_progress()  # 目標進捗も更新
                
            except ValueError as e:
                print(f"値エラー: {e}")
                QMessageBox.warning(self, '警告', f'入力値が正しくありません: {str(e)}\n数値を正しく入力してください。')
                self.update_table()
            except Exception as e:
                print(f"予期しないエラー: {e}")
                import traceback
                traceback.print_exc()
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
        
    def register_past_recurring_expenses(self):
        """過去の定期支払いを遡って登録する"""
        # 登録期間の設定ダイアログを表示
        # 開始月・終了月を先月全体（1日〜末日）に自動設定
        today = QDate.currentDate()
        first_of_this_month = QDate(today.year(), today.month(), 1)
        last_month_end = first_of_this_month.addDays(-1)
        start_date = QDate(last_month_end.year(), last_month_end.month(), 1)  # 先月1日

        end_date = last_month_end  # 先月末日
        
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

    def show_rakuten_pay_import_dialog(self):
        """楽天PAY明細取込ダイアログを表示（URL自動取得対応）"""
        import json as _json

        # 保存済みURLを読み込み
        url = ''
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rakuten_pay_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = _json.load(f)
                    url = config.get('sheet_url', '')
            except Exception as e:
                # 設定ファイルが壊れて読めない場合はユーザーに知らせる。
                # url が空のままなので、この後の既存フローでURL入力ダイアログが開く
                QMessageBox.warning(
                    self, '設定ファイル読込エラー',
                    f'楽天PAYの設定ファイルが読み込めませんでした。\n\n{e}\n\n'
                    'URLを再入力してください。'
                )

        # URLが未設定なら入力ダイアログ
        if not url:
            url, ok = QInputDialog.getText(
                self, '楽天PAY設定',
                'Google SheetsのCSV公開URLを入力してください:\n\n'
                '（Google Sheetsで ファイル > 共有 > ウェブに公開 >\n'
                '「楽天PAY明細」シート > CSV形式 > 公開 で取得できます）'
            )
            if not ok or not url:
                return
            # URLを保存
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    _json.dump({'sheet_url': url}, f, ensure_ascii=False)
            except Exception as e:
                # 保存に失敗しても取込処理は続行できるが、
                # 次回また入力し直しになることをユーザーに知らせておく
                QMessageBox.warning(
                    self, '設定保存エラー',
                    f'URLの保存に失敗しました。\n\n{e}\n\n'
                    '取込は続行しますが、次回また入力が必要になります。'
                )

        # ダイアログ作成
        dialog = CreditCardImportDialog(self)
        dialog.format_combo.setCurrentText('楽天PAY')

        # URLからCSVデータを取得してStep2から開始
        try:
            dialog.load_from_url(url)
            dialog.proceed_to_step2_from_url()
        except Exception as e:
            QMessageBox.warning(
                self, '取得失敗',
                f'URLからのデータ取得に失敗しました:\n{str(e)}\n\nファイル選択に切り替えます。'
            )

        if dialog.exec_() == QDialog.Accepted:
            self.update_table()
            self.update_monthly_expense()

    def show_paypay_import_dialog(self):
        """PayPay明細取込ダイアログを表示（CSVファイル選択方式）"""
        dialog = CreditCardImportDialog(self)
        dialog.format_combo.setCurrentText('PayPay')

        if dialog.exec_() == QDialog.Accepted:
            self.update_table()
            self.update_monthly_expense()

    def show_pasmo_import_dialog(self):
        """PASMO明細取込ダイアログを表示（PDF取込）"""
        dialog = PasmoImportDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_table()
            self.update_monthly_expense()

    def load_categories_for_filter(self):
        """フィルター用のカテゴリを読み込む"""
        try:
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            c.execute('SELECT name FROM categories ORDER BY sort_order')
            categories = [row[0] for row in c.fetchall()]
            conn.close()
            
            for category in categories:
                self.filter_combo.addItem(category)
        except Exception as e:
            print(f"カテゴリ読み込みエラー: {e}")

    def load_current_month_expenses(self):
        """現在の月の支出データを読み込む（デバッグ強化版）"""
        try:
            print(f"=== データ読み込み開始: {self.current_year}年{self.current_month}月 ===")
            
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            
            # まず全データを確認
            c.execute('SELECT COUNT(*) FROM expenses')
            total_count = c.fetchone()[0]
            print(f"expenses テーブルの総レコード数: {total_count}")
            
            # 今月のデータを確認
            c.execute('''
                SELECT COUNT(*) FROM expenses
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ''', (str(self.current_year), f"{self.current_month:02d}"))
            
            month_count = c.fetchone()[0]
            print(f"今月（{self.current_year}年{self.current_month}月）のレコード数: {month_count}")
            
            # 実際のデータを取得
            c.execute('''
                SELECT id, date, category, amount, description
                FROM expenses
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
                ORDER BY date DESC, id DESC
            ''', (str(self.current_year), f"{self.current_month:02d}"))
            
            self.current_expense_data = c.fetchall()
            conn.close()
            
            print(f"実際に読み込まれたデータ: {len(self.current_expense_data)}件")
            
            # データ内容を詳細表示
            if self.current_expense_data:
                print("=== 読み込まれたデータの詳細 ===")
                for i, row in enumerate(self.current_expense_data):
                    print(f"  {i+1}. ID:{row[0]}, 日付:{row[1]}, カテゴリ:{row[2]}, 金額:{row[3]}, 説明:{row[4]}")
            else:
                print("=== データが0件です ===")
                # 他の月のデータがあるか確認
                conn = sqlite3.connect('budget.db')
                c = conn.cursor()
                c.execute('SELECT DISTINCT strftime("%Y-%m", date) FROM expenses ORDER BY date DESC LIMIT 5')
                other_months = c.fetchall()
                conn.close()
                print("他の月のデータ:")
                for month in other_months:
                    print(f"  {month[0]}")
            
            # 表示更新
            self.update_expense_table_display()
            
        except Exception as e:
            print(f"load_current_month_expenses エラー: {e}")
            import traceback
            traceback.print_exc()

    def update_expense_table_display(self):
        """支出テーブルの表示を更新(安全版)"""
        try:
            print("=== update_expense_table_display 開始(安全版) ===")
            
            # is_updatingフラグを設定
            self.is_updating = True
            
            # 全ての必要なウィジェットが存在します
            print("全ての必要なウィジェットが存在します")
            
            # データ読み込み開始
            print(f"=== データ読み込み開始: {self.current_year}年{self.current_month}月 ===")
            
            # データベースから支出データを取得
            query = '''
                SELECT id, date, category, amount, description
                FROM expenses
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            '''
            
            month_str = f'{self.current_month:02d}'
            all_data = execute_query(query, (str(self.current_year), month_str), fetch_all=True)
            
            print(f"expensesテーブルの総レコード数: {len(all_data) if all_data else 0}")
            print(f"今月({self.current_year}年{self.current_month}月)のレコード数: {len(all_data) if all_data else 0}")
            
            if all_data:
                print(f"実際に読み込まれたデータ: {len(all_data)}件")
                print("=== 読み込まれたデータの詳細 ===")
                for i, row in enumerate(all_data[:5]):  # 最初の5件だけ表示
                    print(f"  {i+1}. ID:{row[0]}, 日付:{row[1]}, カテゴリ:{row[2]}, 金額:{row[3]}, 説明:{row[4]}")
            
            # フィルタリング処理
            selected_category = self.filter_combo.currentText()
            print(f"選択されたカテゴリ: '{selected_category}'")

            filtered_data = all_data
            if selected_category != '全てのカテゴリ':
                filtered_data = [row for row in filtered_data if row[2] == selected_category]
                print(f"カテゴリフィルタ後のデータ件数: {len(filtered_data)}")

            # キーワード検索フィルター
            search_text = self.search_input.text().strip().lower()
            if search_text:
                filtered_data = [row for row in filtered_data
                                 if search_text in (row[2] or '').lower() or search_text in (row[4] or '').lower()]

            # 金額範囲フィルター
            amount_min_text = self.amount_min_input.text().replace(',', '').strip()
            amount_max_text = self.amount_max_input.text().replace(',', '').strip()
            if amount_min_text:
                try:
                    amount_min = float(amount_min_text)
                    filtered_data = [row for row in filtered_data if row[3] >= amount_min]
                except ValueError:
                    pass
            if amount_max_text:
                try:
                    amount_max = float(amount_max_text)
                    filtered_data = [row for row in filtered_data if row[3] <= amount_max]
                except ValueError:
                    pass
            
            # 並び替えオプション
            sort_option = self.sort_combo.currentText()
            print(f"並び替えオプション: '{sort_option}'")

            if sort_option == '日付順（新しい順）':  # 全角括弧に変更
                filtered_data = sorted(filtered_data, key=lambda x: x[1], reverse=True)
                print("日付順(新しい順)でソート完了")
            elif sort_option == '日付順（古い順）':  # 全角括弧に変更
                filtered_data = sorted(filtered_data, key=lambda x: x[1])
                print("日付順(古い順)でソート完了")
            elif sort_option == 'カテゴリ別':
                self.is_updating = False
                self.display_expenses_grouped_by_category(filtered_data)
                print("=== update_expense_table_display 完了(カテゴリ別表示) ===")
                return
            elif sort_option == '金額順（高い順）':  # 全角括弧に変更
                filtered_data = sorted(filtered_data, key=lambda x: x[3], reverse=True)
                print("金額順(高い順)でソート完了")
            elif sort_option == '金額順（安い順）':  # 全角括弧に変更
                filtered_data = sorted(filtered_data, key=lambda x: x[3])
                print("金額順(安い順)でソート完了")
            else:
                print(f"⚠️ 不明な並び替えオプション: '{sort_option}'")
            
            # 表示件数制限
            limit_text = self.limit_combo.currentText()
            print(f"表示件数: '{limit_text}'")
            
            if limit_text != '全て':
                limit = int(limit_text.replace('件', ''))
                filtered_data = filtered_data[:limit]
            
            print(f"最終データ件数: {len(filtered_data)}")
            
            # ここからが重要な修正部分
            # テーブルに安全にデータを設定
            if filtered_data:
                self.expense_table.setRowCount(len(filtered_data))
                
                # **データベースからカテゴリリストを取得**
                try:
                    conn = sqlite3.connect('budget.db')
                    c = conn.cursor()
                    c.execute('SELECT name FROM categories ORDER BY sort_order')
                    categories = [row[0] for row in c.fetchall()]
                    conn.close()
                except Exception as e:
                    print(f"カテゴリ取得エラー: {e}")
                    categories = get_categories()
                
                print("=== テーブルにデータを設定中 ===")
                for row, row_data in enumerate(filtered_data):
                    if not row_data or len(row_data) < 5:
                        print(f"行{row}: データが不完全です")
                        continue
                        
                    try:
                        expense_id, date, category, amount, description = row_data
                        
                        # 安全に文字列に変換
                        safe_id = str(expense_id or '')
                        safe_date = str(date or '')
                        safe_category = str(category or '')
                        safe_amount = float(amount or 0)
                        safe_description = str(description or '')
                        
                        # IDカラム
                        self.expense_table.setItem(row, 0, QTableWidgetItem(safe_id))
                        
                        # 日付カラム
                        self.expense_table.setItem(row, 1, QTableWidgetItem(safe_date))
                        
                        # **カテゴリ列にコンボボックスを設定**
                        category_combo = QComboBox()
                        category_combo.addItems(categories)
                        current_index = category_combo.findText(safe_category)
                        if current_index >= 0:
                            category_combo.setCurrentIndex(current_index)
                        
                        # コンボボックスの変更イベントを接続
                        category_combo.currentIndexChanged.connect(
                            lambda idx, r=row: self.on_category_combo_changed(r)
                        )
                        
                        self.expense_table.setCellWidget(row, 2, category_combo)
                        
                        # 金額カラム
                        amount_item = QTableWidgetItem(f"{safe_amount:,.0f}円")
                        amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.expense_table.setItem(row, 3, amount_item)
                        
                        # 説明カラム
                        self.expense_table.setItem(row, 4, QTableWidgetItem(safe_description))
                        
                        if row < 5:  # 最初の5行だけログ出力
                            print(f"行{row}設定: {safe_date} {safe_category} {safe_amount} {safe_description}")
                            
                    except Exception as e:
                        print(f"行{row}のデータ設定エラー: {e}")
                        print(f"問題のデータ: {row_data}")
                        continue
                
                print(f"=== テーブル設定完了: {len(filtered_data)}行 ===")
            else:
                self.expense_table.setRowCount(0)
                print("表示するデータがありません")

            # カテゴリ合計を更新
            self.update_category_total_label(filtered_data, selected_category)

            self.is_updating = False
            print("=== update_expense_table_display 完了(安全版) ===")
            
        except Exception as e:
            self.is_updating = False
            print(f"update_expense_table_display 全体エラー: {e}")
            import traceback
            traceback.print_exc()

    def display_expenses_grouped_by_category(self, data):
        """カテゴリ別にグループ化して表示"""
        grouped_data = {}
        for row in data:
            category = row[2]
            if category not in grouped_data:
                grouped_data[category] = []
            grouped_data[category].append(row)
        
        total_rows = sum(len(items) + 1 for items in grouped_data.values())
        self.expense_table.setRowCount(total_rows)
        
        current_row = 0
        for category, items in grouped_data.items():
            category_total = sum(item[3] for item in items)
            header_item = QTableWidgetItem(f"【{category}】 ({len(items)}件、合計: {category_total:,.0f}円)")
            header_item.setBackground(QColor("#E3F2FD"))
            header_item.setFont(QFont("", weight=QFont.Bold))
            
            self.expense_table.setItem(current_row, 0, QTableWidgetItem(""))
            self.expense_table.setItem(current_row, 1, QTableWidgetItem(""))
            self.expense_table.setItem(current_row, 2, header_item)
            self.expense_table.setItem(current_row, 3, QTableWidgetItem(""))
            self.expense_table.setItem(current_row, 4, QTableWidgetItem(""))
            self.expense_table.setSpan(current_row, 1, 1, 4)
            current_row += 1
            
            for row_data in items:
                exp_id, date, category, amount, description = row_data
                self.expense_table.setItem(current_row, 0, QTableWidgetItem(str(exp_id)))
                self.expense_table.setItem(current_row, 1, QTableWidgetItem(date))
                self.expense_table.setItem(current_row, 2, QTableWidgetItem(category))
                self.expense_table.setItem(current_row, 3, QTableWidgetItem(f"{amount:,.0f}円"))
                self.expense_table.setItem(current_row, 4, QTableWidgetItem(description))
                current_row += 1

        # カテゴリ合計を更新（カテゴリ別表示の場合は全体の合計を表示）
        selected_category = self.filter_combo.currentText()
        self.update_category_total_label(data, selected_category)

    def update_category_total_label(self, data, selected_category):
        """カテゴリ別合計ラベルを更新"""
        try:
            if not data or selected_category == '全てのカテゴリ':
                self.category_total_label.setText('')
                return

            total_amount = sum(row[3] for row in data if row[3])
            item_count = len(data)

            self.category_total_label.setText(
                f'【{selected_category}】 合計: {total_amount:,.0f}円 ({item_count}件)'
            )
        except Exception as e:
            print(f"カテゴリ合計表示エラー: {e}")
            self.category_total_label.setText('')

    def export_to_excel(self):
        """現在の月のデータをCSVファイルにエクスポート"""
        try:
            # データベースから現在月のデータを取得
            query = '''
                SELECT date, category, amount, description
                FROM expenses
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
                ORDER BY date
            '''
            month_str = f'{self.current_month:02d}'
            data = execute_query(query, (str(self.current_year), month_str), fetch_all=True)

            if not data:
                QMessageBox.information(self, 'エクスポート', 'エクスポートするデータがありません。')
                return

            # DataFrameに変換
            df = pd.DataFrame(data, columns=['日付', 'カテゴリ', '金額', '説明'])

            # 保存先を選択
            default_filename = f'家計簿_{self.current_year}年{self.current_month}月.csv'
            file_path, _ = QFileDialog.getSaveFileName(
                self, 'CSVファイルを保存', default_filename, 'CSV Files (*.csv)'
            )

            if file_path:
                # CSVファイルに保存（BOM付きUTF-8でExcelでも文字化けなし）
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                QMessageBox.information(self, 'エクスポート完了', f'データを保存しました:\n{file_path}')

        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'エクスポート中にエラーが発生しました:\n{e}')

    def export_all_to_pdf(self):
        """全データをPDFファイルにエクスポート"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            # 日本語フォントを登録
            font_path = None
            font_paths = [
                'C:/Windows/Fonts/msgothic.ttc',
                'C:/Windows/Fonts/meiryo.ttc',
                'C:/Windows/Fonts/YuGothM.ttc',
            ]
            for fp in font_paths:
                if os.path.exists(fp):
                    font_path = fp
                    break

            if font_path:
                pdfmetrics.registerFont(TTFont('JapaneseFont', font_path))
                font_name = 'JapaneseFont'
            else:
                font_name = 'Helvetica'

            # 全データを取得
            query = '''
                SELECT date, category, amount, description
                FROM expenses
                ORDER BY date DESC
            '''
            data = execute_query(query, fetch_all=True)

            if not data:
                QMessageBox.information(self, 'エクスポート', 'エクスポートするデータがありません。')
                return

            # 保存先を選択
            default_filename = f'家計簿_全データ_{datetime.now().strftime("%Y%m%d")}.pdf'
            file_path, _ = QFileDialog.getSaveFileName(
                self, 'PDFファイルを保存', default_filename, 'PDF Files (*.pdf)'
            )

            if not file_path:
                return

            # PDF作成
            doc = SimpleDocTemplate(file_path, pagesize=A4,
                                    leftMargin=15*mm, rightMargin=15*mm,
                                    topMargin=15*mm, bottomMargin=15*mm)

            elements = []

            # タイトル
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('Title', fontName=font_name, fontSize=16, alignment=1)
            elements.append(Paragraph('家計簿 全データ一覧', title_style))
            elements.append(Spacer(1, 10*mm))

            # テーブルデータ作成
            table_data = [['日付', 'カテゴリ', '金額', '説明']]
            total_amount = 0
            for row in data:
                date_str = str(row[0]) if row[0] else ''
                category = str(row[1]) if row[1] else ''
                amount = row[2] if row[2] else 0
                description = str(row[3]) if row[3] else ''
                total_amount += amount
                table_data.append([date_str, category, f'{amount:,.0f}円', description])

            # 合計行を追加
            table_data.append(['', '合計', f'{total_amount:,.0f}円', f'({len(data)}件)'])

            # テーブル作成
            col_widths = [25*mm, 30*mm, 30*mm, 85*mm]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)

            table_style = TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
                ('FONTNAME', (0, -1), (-1, -1), font_name),
            ])
            table.setStyle(table_style)

            elements.append(table)

            # PDF出力
            doc.build(elements)
            QMessageBox.information(self, 'エクスポート完了', f'PDFを保存しました:\n{file_path}')

        except ImportError:
            QMessageBox.critical(self, 'エラー', 'reportlabがインストールされていません。\npip install reportlab を実行してください。')
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'PDFエクスポート中にエラーが発生しました:\n{e}')

    def display_expenses_normal_table(self, data):
        """通常のテーブル表示（デバッグ強化版）"""
        try:
            print(f"=== display_expenses_normal_table 開始 ===")
            print(f"受け取ったデータ件数: {len(data) if data else 0}")
            
            if self.expense_table is None:
                print("❌ expense_table が None です")
                return
                
            print(f"テーブルの行数を設定: {len(data)}行")
            
            # スパンをクリア
            self.expense_table.clearSpans()
            
            if not data:
                print("データが空のため、テーブルを空にします")
                return
            
            for row, row_data in enumerate(data):
                if not row_data or len(row_data) < 5:
                    print(f"❌ 行 {row}: データが不完全です - {row_data}")
                    continue
                    
                try:
                    exp_id, date, category, amount, description = row_data
                    
                    print(f"行 {row} 設定中: ID:{exp_id}, 日付:{date}, カテゴリ:{category}, 金額:{amount}")
                    
                    # 安全にアイテムを設定
                    self.expense_table.setItem(row, 0, QTableWidgetItem(str(exp_id or '')))
                    self.expense_table.setItem(row, 1, QTableWidgetItem(str(date or '')))
                    self.expense_table.setItem(row, 2, QTableWidgetItem(str(category or '')))
                    self.expense_table.setItem(row, 3, QTableWidgetItem(f"{amount or 0:,.0f}円"))
                    self.expense_table.setItem(row, 4, QTableWidgetItem(str(description or '')))
                    
                    print(f"✅ 行 {row} 設定完了")
                    
                except Exception as e:
                    print(f"❌ 行 {row} の設定エラー: {e}")
                    
            print(f"=== display_expenses_normal_table 完了 ===")
                    
        except Exception as e:
            print(f"❌ display_expenses_normal_table エラー: {e}")
         
    def show_prev_month(self):
        self.current_year, self.current_month = DateHelper.get_prev_month(self.current_year, self.current_month)
        self.period_label.setText(f'{self.current_year}年{self.current_month}月')

        self.load_monthly_income()
        self.update_table()
        self.update_monthly_expense()

        

    def show_next_month(self):
        self.current_year, self.current_month = DateHelper.get_next_month(self.current_year, self.current_month)
        self.period_label.setText(f'{self.current_year}年{self.current_month}月')
        
        self.load_monthly_income()
        self.update_table()
        self.update_monthly_expense()
        # カテゴリ表示のデータ更新
        if hasattr(self, 'load_current_month_expenses'):
            self.load_current_month_expenses()

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
        self.category_combo.addItems(get_categories())
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
        self.category_combo.addItems(get_categories())

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
    
    def _copy_database(self, source_path, dest_path):
        """SQLiteの公式バックアップ機能でデータベースを安全にコピーする

        以前は shutil.copy2（ただのファイルコピー）を使っていたが、
        アプリがDBに書き込んでいる最中にコピーすると壊れたコピーが
        できる恐れがあった。SQLiteのbackup APIは書き込みの区切りを
        見ながらコピーするので、いつ実行しても必ず正常なコピーになる。
        """
        src = sqlite3.connect(source_path)   # コピー元のDBを開く
        dst = sqlite3.connect(dest_path)     # コピー先のDBを作る（無ければ新規作成）
        try:
            src.backup(dst)                  # SQLiteが安全にコピーしてくれる
        finally:
            # 成功・失敗にかかわらず必ず接続を閉じる
            dst.close()
            src.close()

    def _validate_backup_file(self, backup_path):
        """復元前にバックアップファイルが正常か検査する

        壊れたファイルや空のファイルで本体DBを上書きしてしまうと
        全データを失うため、復元処理の前に必ずこの検査を通す。
        問題があれば Exception を投げて復元を中止する（本体DBには触らない）。
        """
        # 検査1: ファイルが存在して中身があるか
        if not os.path.exists(backup_path):
            raise Exception("バックアップファイルが見つかりません")
        if os.path.getsize(backup_path) == 0:
            raise Exception("バックアップファイルが空です。このファイルからは復元できません")

        try:
            # 検査2: 読み取り専用モードで開く（mode=ro は read only の意味。
            # 検査のつもりでファイルを変更してしまう事故を防ぐ）
            conn = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True)
            try:
                c = conn.cursor()

                # 検査3: SQLite自身にファイルの整合性をチェックしてもらう
                # 正常なら 'ok' という1行だけが返ってくる
                result = c.execute("PRAGMA integrity_check").fetchone()
                if result is None or result[0] != "ok":
                    raise Exception("バックアップファイルが破損しています")

                # 検査4: 家計簿アプリのDBかどうか（expensesテーブルの有無）を確認
                c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'"
                )
                if c.fetchone() is None:
                    raise Exception("このファイルは家計簿アプリのバックアップではありません（expensesテーブルがありません）")
            finally:
                conn.close()
        except sqlite3.DatabaseError:
            # SQLiteとして開けない = データベースファイルではない
            raise Exception("このファイルはデータベースファイルではないため復元できません")

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

            # SQLiteの安全なコピー機能でバックアップを作成
            self._copy_database(self.db_path, backup_path)

            return backup_path
        except Exception as e:
            raise Exception(f"バックアップの作成に失敗しました: {str(e)}")

    def restore_backup(self, backup_path):
        """バックアップからデータベースを復元"""
        # 復元前にバックアップファイルを検査する。
        # 壊れたファイルならここで例外になり、本体DBは一切変更されない
        self._validate_backup_file(backup_path)

        try:
            # 現在のデータベースの自動バックアップを作成
            auto_backup_name = f"auto_backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            auto_backup_path = os.path.join(self.backup_dir, auto_backup_name)

            # 現在のDBをバックアップ（万一のとき元に戻せるように）
            self._copy_database(self.db_path, auto_backup_path)

            # バックアップから復元
            self._copy_database(backup_path, self.db_path)

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

import json
import csv         

class CreditCardImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('クレジットカード明細取込')
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # フォーマットプリセット
        self.format_presets = {
            '一般的なクレジットカード': {
                'encoding': 'utf-8',
                'date_format': '%Y/%m/%d',
                'skip_rows': 0,
                'negation_needed': True,
                'date_column': '利用日',
                'amount_column': '利用金額',
                'description_column': '利用店名・商品名',
                'description_prefix': 'クレジットカード: ',
                'category_mapping': {
                    'ﾏﾙｴﾂ': '食費',
                    'ﾄｳｷﾖｳﾃﾞﾝﾘﾖｸ': '水道光熱費',
                    'CLAUDE.AI SUBSCRIPTI': '娯楽',
                    'ｽｲﾄﾞｳﾘ': '水道光熱費'
                },
                'exclude_keywords': [
                    'ﾓﾊﾞｲﾙﾊﾟｽﾓ',
                    '楽天証券投信積立０．５％～',
                    '楽天キャッシュ　チャージ',
                    'APPLE COM BILL',
                    'ﾄｳｴﾝﾃｲ',
                    'ｸﾗｽ',
                    'ソフトバンク（Ｂ）',
                    'ｾｲﾌﾞﾃﾂﾄﾞｳ'
                ]
            },
            '楽天PAY': {
                'encoding': 'utf-8',
                'date_format': '%Y/%m/%d',
                'skip_rows': 0,
                'negation_needed': False,
                'date_column': '日付',
                'amount_column': '金額',
                'description_column': '店舗名',
                'description_prefix': '楽天PAY: ',
                'category_mapping': {},
                'exclude_keywords': []
            },
            'PayPay': {
                'encoding': 'utf-8-sig',
                'date_format': '%Y/%m/%d %H:%M:%S',
                'skip_rows': 0,
                'negation_needed': False,
                'date_column': '取引日',
                'amount_column': '出金金額（円）',
                'description_column': '取引先',
                'description_prefix': 'PayPay: ',
                'category_mapping': {},
                'exclude_keywords': []
            }
        }

        # 現在のフォーマット設定（デフォルト値）
        self.current_format = dict(self.format_presets['一般的なクレジットカード'])
        
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
        self.format_combo.addItems(['一般的なクレジットカード', '楽天PAY', 'PayPay', 'その他'])
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

        # 除外キーワードグループボックス
        self.exclude_group = QGroupBox('除外キーワード')
        exclude_layout = QVBoxLayout()

        exclude_label = QLabel('以下のキーワードを含む明細は取り込みから除外されます:')
        exclude_layout.addWidget(exclude_label)

        self.exclude_keywords_list = QListWidget()
        exclude_layout.addWidget(self.exclude_keywords_list)

        exclude_button_layout = QHBoxLayout()

        add_exclude_button = QPushButton('追加')
        add_exclude_button.clicked.connect(self.add_exclude_keyword)
        exclude_button_layout.addWidget(add_exclude_button)

        delete_exclude_button = QPushButton('選択したキーワードを削除')
        delete_exclude_button.clicked.connect(self.delete_exclude_keyword)
        exclude_button_layout.addWidget(delete_exclude_button)

        exclude_layout.addLayout(exclude_button_layout)

        self.exclude_group.setLayout(exclude_layout)
        step2_layout.addWidget(self.exclude_group)

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
        """フォーマット選択に応じてカスタム設定の表示/非表示とプリセット切替え"""
        import copy
        format_name = self.format_combo.currentText()

        if format_name == 'その他':
            self.custom_settings_widget.show()
        else:
            self.custom_settings_widget.hide()

        # プリセットが存在する場合、current_formatを切替え
        if format_name in self.format_presets:
            self.current_format = copy.deepcopy(self.format_presets[format_name])

        # ウィンドウタイトルを更新
        if format_name == '楽天PAY':
            self.setWindowTitle('楽天PAY明細取込')
        elif format_name == 'PayPay':
            self.setWindowTitle('PayPay明細取込')
        else:
            self.setWindowTitle('クレジットカード明細取込')

    def _get_format_label(self):
        """現在のフォーマットに応じた明細ラベルを返す"""
        format_name = self.format_combo.currentText()
        if format_name == '楽天PAY':
            return '楽天PAY明細'
        if format_name == 'PayPay':
            return 'PayPay明細'
        return 'クレジットカード明細'

    def load_from_url(self, url):
        """Google Sheets公開URLからCSVデータを取得"""
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        response.encoding = 'utf-8'
        self.csv_data = pd.read_csv(io.StringIO(response.text))
        self.file_path_input.setText('Google Sheets URL')

    def proceed_to_step2_from_url(self):
        """URL経由でCSVデータ読込済みの状態からStep2に進む"""
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

        self.update_category_mapping_table()
        self.update_exclude_keywords_list()

        self.step_label.setText('ステップ 2/3: 列マッピングとカテゴリ設定')
        self.stack.setCurrentIndex(1)

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
            
            category_list = get_categories()

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

    def update_exclude_keywords_list(self):
        """除外キーワードリストを更新"""
        self.exclude_keywords_list.clear()
        for keyword in self.current_format['exclude_keywords']:
            self.exclude_keywords_list.addItem(QListWidgetItem(keyword))

    def add_exclude_keyword(self):
        """除外キーワードを追加"""
        keyword, ok = QInputDialog.getText(self, '除外キーワード追加', 'キーワード:')
        if ok and keyword:
            keyword = keyword.strip()
            if keyword and keyword not in self.current_format['exclude_keywords']:
                self.current_format['exclude_keywords'].append(keyword)
                self.update_exclude_keywords_list()

    def delete_exclude_keyword(self):
        """選択された除外キーワードを削除"""
        selected_items = self.exclude_keywords_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', '削除するキーワードを選択してください')
            return

        keyword = selected_items[0].text()

        reply = QMessageBox.question(
            self, '確認',
            f'除外キーワード "{keyword}" を削除してもよろしいですか？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if keyword in self.current_format['exclude_keywords']:
                self.current_format['exclude_keywords'].remove(keyword)
                self.update_exclude_keywords_list()

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

            # 除外キーワードリストの更新
            self.update_exclude_keywords_list()

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
            
            # 期間指定を先月全体（1日〜末日）に自動設定
            today = QDate.currentDate()
            first_of_this_month = QDate(today.year(), today.month(), 1)
            last_month_end = first_of_this_month.addDays(-1)
            last_month_start = QDate(last_month_end.year(), last_month_end.month(), 1)
            self.start_date_edit.setDate(last_month_start)
            self.end_date_edit.setDate(last_month_end)

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
                amount_str = str(row[amount_col]).replace(',', '').replace('円', '').strip()
                if amount_str == '' or amount_str == 'nan' or amount_str == '-':
                    continue
                amount = float(amount_str)
                if self.current_format['negation_needed']:
                    amount = -amount

                # 金額の絶対値を使用（支出として記録するため）
                amount = abs(amount)
                if amount == 0:
                    continue
                
                # 説明処理
                description = str(row[description_col])
                
                # 説明文を正規化して比較用に準備
                normalized_description = self.normalize_text(description)

                # 除外キーワードチェック
                excluded = False
                credit_prefix = self.normalize_text(self.current_format.get('description_prefix', 'クレジットカード: '))
                for exclude_keyword in self.current_format['exclude_keywords']:
                    normalized_exclude = self.normalize_text(exclude_keyword)
                    if normalized_exclude.startswith(credit_prefix):
                        normalized_exclude = normalized_exclude[len(credit_prefix):]
                    if normalized_exclude and normalized_exclude in normalized_description:
                        excluded = True
                        break
                if excluded:
                    continue

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
            f'{total_records}件の{self._get_format_label()}を取り込みます。よろしいですか？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 取り込み実行
        try:
            imported_count = self.import_to_database(filtered_data)
            
            QMessageBox.information(
                self, '取り込み完了',
                f'{imported_count}件の{self._get_format_label()}を取り込みました。'
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
        failed_count = 0  # 取込に失敗した行数（黙って欠落させないためカウントする）

        # try/finally で囲み、途中で何が起きても接続を必ず閉じる
        # （閉じ忘れはDBロックの原因になり、後続の操作が失敗しやすくなる）
        try:
            for item in data:
                date = item['date']
                category = item['category']
                amount = abs(item['amount'])  # 支出なので絶対値を使用
                prefix = self.current_format.get('description_prefix', 'クレジットカード: ')
                description = f"{prefix}{item['description']}"

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
                    failed_count += 1  # 失敗を記録して次の行へ
                    continue

            conn.commit()
        finally:
            conn.close()

        if duplicate_count > 0:
            QMessageBox.information(
                self, '重複スキップ',
                f'{duplicate_count}件の重複データはスキップされました。'
            )

        # 取込に失敗した行があればユーザーに知らせる。
        # 黙って欠落させると「明細と合計が合わない」原因不明の不整合になるため
        if failed_count > 0:
            QMessageBox.warning(
                self, '取込エラー',
                f'{failed_count}件のデータが取り込めませんでした。\n'
                '取込結果と元の明細を照合して確認してください。'
            )

        return imported_count
    
    # インポート履歴の保存
    def save_import_history(self, file_name, format_name, record_count):
        conn = sqlite3.connect('budget.db')
        try:
            c = conn.cursor()

            import_date = QDate.currentDate().toString('yyyy-MM-dd')

            c.execute('''
                INSERT INTO credit_card_imports
                (import_date, file_name, format_name, record_count)
                VALUES (?, ?, ?, ?)
            ''', (import_date, file_name, format_name, record_count))

            conn.commit()
        except Exception as e:
            conn.rollback()
            # 履歴の保存は補助機能なので、失敗しても取込自体は成功している。
            # ダイアログは出さずログだけ残す
            print(f"インポート履歴の保存に失敗: {e}")
        finally:
            conn.close()  # 必ず接続を閉じる

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
                'category_mapping': self.current_format['category_mapping'],
                'exclude_keywords': self.current_format['exclude_keywords']
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
                if 'exclude_keywords' in mapping_data:
                    self.current_format['exclude_keywords'] = mapping_data['exclude_keywords']
                    self.update_exclude_keywords_list()

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
        category_list = get_categories()

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


class PasmoImportDialog(QDialog):
    """モバイルPASMO残額ご利用明細PDF取込ダイアログ"""

    # 除外する種別
    EXCLUDE_TYPES = ['繰', 'ｶｰﾄﾞ']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('PASMO明細取込')
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.preview_data = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # ステップ表示
        self.step_label = QLabel('ステップ 1/2: PDFファイルの選択')
        self.step_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        layout.addWidget(self.step_label)

        self.stack = QStackedWidget()

        # ---- ステップ1: ファイル選択 ----
        step1_widget = QWidget()
        step1_layout = QVBoxLayout()

        info_label = QLabel(
            'モバイルPASMO会員メニューサイト (mobile.pasmo.jp) から\n'
            'ダウンロードした「残額ご利用明細」PDFを選択してください。'
        )
        step1_layout.addWidget(info_label)

        file_group = QGroupBox('PDFファイル選択')
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText('PDFファイルを選択してください')
        browse_button = QPushButton('参照...')
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(browse_button)
        file_group.setLayout(file_layout)
        step1_layout.addWidget(file_group)

        next_button1 = QPushButton('解析して次へ')
        next_button1.clicked.connect(self.parse_and_proceed)
        step1_layout.addWidget(next_button1, alignment=Qt.AlignRight)

        step1_widget.setLayout(step1_layout)

        # ---- ステップ2: プレビューと取込 ----
        step2_widget = QWidget()
        step2_layout = QVBoxLayout()

        self.summary_label = QLabel('')
        step2_layout.addWidget(self.summary_label)

        self.preview_table = QTableWidget(0, 4)
        self.preview_table.setHorizontalHeaderLabels(['日付', '区間', '金額', 'カテゴリ'])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        step2_layout.addWidget(self.preview_table)

        # === 取り込みモード選択 ===
        mode_group = QGroupBox('取り込みモード')
        mode_layout = QVBoxLayout()

        # 一括取り込み（デフォルト）
        self.bulk_mode_radio = QCheckBox('一括取り込み（合計金額を1件の交通費として登録）')
        self.bulk_mode_radio.setChecked(True)
        self.bulk_mode_radio.setStyleSheet('font-weight: bold;')
        mode_layout.addWidget(self.bulk_mode_radio)

        # 一括取り込み用の日付選択
        self.bulk_date_layout = QHBoxLayout()
        self.bulk_date_layout.addWidget(QLabel('  取り込み日付:'))
        self.bulk_date_edit = QDateEdit()
        self.bulk_date_edit.setCalendarPopup(True)
        self.bulk_date_edit.setDate(QDate.currentDate())
        self.bulk_date_layout.addWidget(self.bulk_date_edit)
        self.bulk_total_label = QLabel('')
        self.bulk_total_label.setStyleSheet('font-weight: bold; color: #1565C0; margin-left: 10px;')
        self.bulk_date_layout.addWidget(self.bulk_total_label)
        self.bulk_date_layout.addStretch()
        mode_layout.addLayout(self.bulk_date_layout)

        # チェックのON/OFFで個別取り込み設定の表示切替
        self.bulk_mode_radio.toggled.connect(self._toggle_import_mode)

        mode_group.setLayout(mode_layout)
        mode_group.hide()  # 一括モードUIを非表示
        step2_layout.addWidget(mode_group)

        # === 個別取り込み設定（一括モードOFF時に表示） ===
        self.individual_group = QGroupBox('個別取り込み設定')
        individual_layout = QVBoxLayout()

        # 重複チェック
        self.duplicate_check = QCheckBox('取り込み時に重複をチェックする')
        self.duplicate_check.setChecked(True)
        individual_layout.addWidget(self.duplicate_check)

        # 取り込み期間指定
        date_range_layout = QHBoxLayout()
        self.date_range_check = QCheckBox()
        self.date_range_check.setChecked(True)
        date_range_layout.addWidget(self.date_range_check)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-6))
        date_range_layout.addWidget(QLabel('開始日:'))
        date_range_layout.addWidget(self.start_date_edit)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_range_layout.addWidget(QLabel('終了日:'))
        date_range_layout.addWidget(self.end_date_edit)
        individual_layout.addLayout(date_range_layout)

        self.individual_group.setLayout(individual_layout)
        self.individual_group.setVisible(True)   # 常時表示
        step2_layout.addWidget(self.individual_group)

        # 戻る・取り込みボタン
        button_layout = QHBoxLayout()
        back_button = QPushButton('戻る')
        back_button.clicked.connect(lambda: (
            self.step_label.setText('ステップ 1/2: PDFファイルの選択'),
            self.stack.setCurrentIndex(0)
        ))
        self.import_button = QPushButton('取り込み実行')
        self.import_button.clicked.connect(self.execute_import)
        self.import_button.setStyleSheet('background-color: #4CAF50; color: white; font-weight: bold;')
        button_layout.addWidget(back_button)
        button_layout.addStretch()
        button_layout.addWidget(self.import_button)
        step2_layout.addLayout(button_layout)

        step2_widget.setLayout(step2_layout)

        self.stack.addWidget(step1_widget)
        self.stack.addWidget(step2_widget)
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'PASMO PDFファイルを選択', '',
            'PDFファイル (*.pdf);;すべてのファイル (*.*)'
        )
        if file_path:
            self.file_path_input.setText(file_path)

    def _infer_start_year(self, file_path):
        """ファイル名から開始年を推定する"""
        import re
        basename = os.path.basename(file_path)
        # PB80F224032817377_20250104_20260211120230.pdf のようなパターン
        m = re.search(r'_(\d{4})\d{4}_', basename)
        if m:
            return int(m.group(1))
        return QDate.currentDate().year()

    def parse_and_proceed(self):
        """PDFを解析してステップ2に進む"""
        if not self.file_path_input.text():
            QMessageBox.warning(self, '警告', 'PDFファイルを選択してください')
            return

        try:
            import pdfplumber
        except ImportError:
            QMessageBox.critical(
                self, 'エラー',
                'pdfplumber がインストールされていません。\n\n'
                'コマンドプロンプトで以下を実行してください:\n'
                'pip install pdfplumber'
            )
            return

        try:
            self.preview_data = self.parse_pasmo_pdf(self.file_path_input.text())

            if not self.preview_data:
                QMessageBox.warning(self, '警告', '取り込み可能なデータが見つかりませんでした。')
                return

            # プレビューテーブル更新
            self.preview_table.setRowCount(0)
            for row_idx, row_data in enumerate(self.preview_data):
                self.preview_table.insertRow(row_idx)
                self.preview_table.setItem(row_idx, 0, QTableWidgetItem(row_data['date']))
                self.preview_table.setItem(row_idx, 1, QTableWidgetItem(row_data['description'].replace('PASMO: ', '')))
                self.preview_table.setItem(row_idx, 2, QTableWidgetItem(f"¥{row_data['amount']:,.0f}"))

                # カテゴリはComboBoxで編集可能に
                category_combo = QComboBox()
                categories = ['交通費', '食費', '娯楽', 'その他', '住宅',
                              '水道光熱費', '美容', '通信費', '日用品', '健康', '教育']
                category_combo.addItems(categories)
                category_combo.setCurrentText(row_data['category'])
                category_combo.currentTextChanged.connect(
                    lambda text, idx=row_idx: self._update_category(idx, text)
                )
                self.preview_table.setCellWidget(row_idx, 3, category_combo)

            # 期間を先月全体（1日〜末日）に自動設定
            today = QDate.currentDate()
            first_of_this_month = QDate(today.year(), today.month(), 1)
            last_month_end = first_of_this_month.addDays(-1)
            last_month_start = QDate(last_month_end.year(), last_month_end.month(), 1)
            self.start_date_edit.setDate(last_month_start)
            self.end_date_edit.setDate(last_month_end)

            total = len(self.preview_data)
            total_amount = sum(d['amount'] for d in self.preview_data)
            self.summary_label.setText(
                f'解析結果: {total}件の交通利用 (合計 ¥{total_amount:,.0f})'
            )
            self.bulk_total_label.setText(f'合計: ¥{total_amount:,.0f}（{total}件分）')

            self.step_label.setText('ステップ 2/2: プレビューと取り込み実行')
            self.stack.setCurrentIndex(1)

        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'PDF解析に失敗しました:\n{str(e)}')

    def _toggle_import_mode(self, bulk_checked):
        """一括/個別モードの切り替え"""
        self.individual_group.setVisible(not bulk_checked)

    def _update_category(self, row_idx, text):
        """プレビューデータのカテゴリを更新"""
        if row_idx < len(self.preview_data):
            self.preview_data[row_idx]['category'] = text

    def parse_pasmo_pdf(self, file_path):
        """PASMO PDFを解析してデータリストを返す"""
        import pdfplumber
        import re

        start_year = self._infer_start_year(file_path)
        results = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split('\n')
                prev_month = None

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # データ行: "MM DD 種別 ..." のパターン
                    m = re.match(r'^(\d{2})\s+(\d{2})\s+(.+)$', line)
                    if not m:
                        continue

                    month = int(m.group(1))
                    day = int(m.group(2))
                    rest = m.group(3)

                    # 年の推定: 月が前の行より小さくなったら年を+1
                    if prev_month is not None and month < prev_month:
                        start_year += 1
                    prev_month = month

                    # 種別を判定
                    # 繰越行: "繰 ..."
                    if rest.startswith('繰'):
                        continue

                    # チャージ行: "ｶｰﾄﾞ ..." (差額が正)
                    if rest.startswith('ｶｰﾄﾞ'):
                        continue

                    # 鉄道利用行: "入 {駅名} 出 {駅名} \金額 差額"
                    # または: "定 {駅名} 出 {駅名} \金額 差額"
                    ride_match = re.match(
                        r'^(入|定)\s+(.+?)\s+出\s+(.+?)\s+\\[\\\d,.]+\s+([+-][\d,]+)$',
                        rest
                    )
                    if ride_match:
                        ride_type = ride_match.group(1)
                        station_from = ride_match.group(2).strip()
                        station_to = ride_match.group(3).strip()
                        diff_str = ride_match.group(4).replace(',', '')
                        diff = int(diff_str)

                        if diff >= 0:
                            continue  # 正の差額はチャージ等なのでスキップ

                        amount = abs(diff)
                        date_str = f'{start_year}-{month:02d}-{day:02d}'

                        # 「地　渋谷」→「渋谷(地下鉄)」のように整形
                        station_from = self._clean_station_name(station_from)
                        station_to = self._clean_station_name(station_to)

                        description = f'PASMO: {station_from} → {station_to}'
                        category = '交通費'

                        results.append({
                            'date': date_str,
                            'amount': amount,
                            'description': description,
                            'category': category
                        })

        return results

    def _clean_station_name(self, name):
        """駅名を整形する（地　渋谷 → 渋谷 など）"""
        import re
        # 「地　渋谷」「地 渋谷」→「渋谷」（地下鉄プレフィックス除去）
        m = re.match(r'^地[\s　]+(.+)$', name)
        if m:
            return m.group(1)
        # 「東武　柏」→「東武 柏」（全角スペースをスペースに）
        name = name.replace('\u3000', ' ')
        return name

    def execute_import(self):
        """取り込みを実行"""
        self._execute_individual_import()

    def _execute_bulk_import(self):
        """一括取り込み: 合計金額を1件の交通費として登録"""
        total_amount = sum(d['amount'] for d in self.preview_data)
        chosen_date = self.bulk_date_edit.date().toString('yyyy-MM-dd')
        record_count = len(self.preview_data)

        # 期間を説明に含める
        dates = sorted([d['date'] for d in self.preview_data])
        period = f'{dates[0]} ~ {dates[-1]}' if dates else ''
        description = f'PASMO交通費({period}、{record_count}件)'

        reply = QMessageBox.question(
            self, '確認',
            f'以下の内容で取り込みます:\n\n'
            f'  日付: {chosen_date}\n'
            f'  カテゴリ: 交通費\n'
            f'  金額: ¥{total_amount:,.0f}\n'
            f'  説明: {description}\n\n'
            f'よろしいですか？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 接続はtryの外で開き、finallyで必ず閉じる（閉じ忘れ防止）
        conn = sqlite3.connect('budget.db')
        try:
            c = conn.cursor()

            c.execute('''
                INSERT INTO expenses (date, category, amount, description)
                VALUES (?, ?, ?, ?)
            ''', (chosen_date, '交通費', total_amount, description))

            # インポート履歴を記録
            import_date = QDate.currentDate().toString('yyyy-MM-dd')
            file_name = os.path.basename(self.file_path_input.text())
            c.execute('''
                INSERT INTO credit_card_imports
                (import_date, file_name, format_name, record_count)
                VALUES (?, ?, ?, ?)
            ''', (import_date, file_name, 'モバイルPASMO(一括)', 1))

            # 支出と履歴の両方が成功したときだけ確定する
            conn.commit()

            QMessageBox.information(
                self, '取り込み完了',
                f'PASMO交通費 ¥{total_amount:,.0f} を {chosen_date} として取り込みました。'
            )
            self.accept()

        except Exception as e:
            conn.rollback()  # 途中まで書き込んだ分を取り消す
            QMessageBox.critical(self, 'エラー', f'取り込み処理に失敗しました:\n{str(e)}')
        finally:
            conn.close()     # 成功・失敗にかかわらず必ず接続を閉じる

    def _execute_individual_import(self):
        """個別取り込み: 各明細を個別に登録"""
        filtered_data = self.preview_data
        if self.date_range_check.isChecked():
            start_date = self.start_date_edit.date().toString('yyyy-MM-dd')
            end_date = self.end_date_edit.date().toString('yyyy-MM-dd')
            filtered_data = [
                d for d in self.preview_data
                if start_date <= d['date'] <= end_date
            ]

        total_records = len(filtered_data)
        if total_records == 0:
            QMessageBox.warning(self, '警告', '取り込むデータがありません')
            return

        reply = QMessageBox.question(
            self, '確認',
            f'{total_records}件のPASMO明細を取り込みます。よろしいですか？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 接続はtryの外で開き、finallyで必ず閉じる（閉じ忘れ防止）
        conn = sqlite3.connect('budget.db')
        try:
            c = conn.cursor()
            imported_count = 0
            duplicate_count = 0

            for item in filtered_data:
                date = item['date']
                category = item['category']
                amount = item['amount']
                description = item['description']

                # 重複チェック
                if self.duplicate_check.isChecked():
                    c.execute('''
                        SELECT id FROM expenses
                        WHERE date = ? AND category = ? AND amount = ? AND description = ?
                    ''', (date, category, amount, description))
                    if c.fetchone():
                        duplicate_count += 1
                        continue

                c.execute('''
                    INSERT INTO expenses (date, category, amount, description)
                    VALUES (?, ?, ?, ?)
                ''', (date, category, amount, description))
                imported_count += 1

            conn.commit()

            # インポート履歴を記録
            import_date = QDate.currentDate().toString('yyyy-MM-dd')
            file_name = os.path.basename(self.file_path_input.text())
            c.execute('''
                INSERT INTO credit_card_imports
                (import_date, file_name, format_name, record_count)
                VALUES (?, ?, ?, ?)
            ''', (import_date, file_name, 'モバイルPASMO', imported_count))
            conn.commit()

            if duplicate_count > 0:
                QMessageBox.information(
                    self, '重複スキップ',
                    f'{duplicate_count}件の重複データはスキップされました。'
                )

            QMessageBox.information(
                self, '取り込み完了',
                f'{imported_count}件のPASMO明細を取り込みました。'
            )
            self.accept()

        except Exception as e:
            conn.rollback()  # 途中まで書き込んだ分を取り消す
            QMessageBox.critical(self, 'エラー', f'取り込み処理に失敗しました:\n{str(e)}')
        finally:
            conn.close()     # 成功・失敗にかかわらず必ず接続を閉じる


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

class AssetManagementWidget(BaseWidget):
    """銀行・証券の資産管理ウィジェット"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.load_assets()
    
    def initUI(self):
        layout = QVBoxLayout()

    
        
        # ナビゲーションボタン
        layout.addLayout(self.button_layout)
        
        # タイトル
        title_label = QLabel("<h1>💰 資産管理</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 総資産表示カード
        self.total_assets_card = self.create_total_assets_card()
        layout.addWidget(self.total_assets_card)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # タブ1: 資産一覧
        self.assets_list_tab = QWidget()
        self.setup_assets_list_tab()
        self.tab_widget.addTab(self.assets_list_tab, "📋 資産一覧")
        
        # タブ2: 銀行口座
        self.bank_tab = QWidget()
        self.setup_bank_tab()
        self.tab_widget.addTab(self.bank_tab, "🏦 銀行口座")
        
        # タブ3: 証券口座
        self.securities_tab = QWidget()
        self.setup_securities_tab()
        self.tab_widget.addTab(self.securities_tab, "📈 証券口座")
        
        # タブ4: 資産推移
        self.history_tab = QWidget()
        self.setup_history_tab()
        self.tab_widget.addTab(self.history_tab, "📊 資産推移")

        # タブ5: 資産構成（円グラフ）
        self.composition_tab = QWidget()
        self.setup_asset_composition_tab()
        self.tab_widget.addTab(self.composition_tab, "🥧 資産構成")    
        
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)
    
    def create_total_assets_card(self):
        """総資産表示カードを作成"""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        card.setMinimumHeight(150)
        
        card_layout = QVBoxLayout()
        
        # タイトル
        title = QLabel("💎 総資産")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        
        # 総資産額
        self.total_assets_label = QLabel("0円")
        self.total_assets_label.setStyleSheet("color: white; font-size: 36px; font-weight: bold;")
        self.total_assets_label.setAlignment(Qt.AlignCenter)
        
        # 内訳
        breakdown_layout = QHBoxLayout()
        
        self.bank_total_label = QLabel("🏦 銀行: 0円")
        self.bank_total_label.setStyleSheet("color: white; font-size: 14px;")
        
        self.securities_total_label = QLabel("📈 証券: 0円")
        self.securities_total_label.setStyleSheet("color: white; font-size: 14px;")
        
        breakdown_layout.addWidget(self.bank_total_label)
        breakdown_layout.addStretch()
        breakdown_layout.addWidget(self.securities_total_label)
        
        card_layout.addWidget(title)
        card_layout.addWidget(self.total_assets_label)
        card_layout.addLayout(breakdown_layout)
        
        card.setLayout(card_layout)
        return card
    
    def setup_assets_list_tab(self):
        """資産一覧タブのUI"""
        layout = QVBoxLayout()
        
        # 資産一覧テーブル
        self.assets_table = QTableWidget(0, 5)
        self.assets_table.setHorizontalHeaderLabels([
            '種別', '口座名', '残高', '更新日', '備考'
        ])
        self.assets_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.assets_table)
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("🔄 更新")
        refresh_button.clicked.connect(self.load_assets)
        
        add_button = QPushButton("➕ 口座追加")
        add_button.clicked.connect(self.show_add_account_dialog)
        
        edit_button = QPushButton("✏️ 編集")
        edit_button.clicked.connect(self.edit_selected_account)
        
        delete_button = QPushButton("🗑️ 削除")
        delete_button.clicked.connect(self.delete_selected_account)
        delete_button.setStyleSheet("background-color: #FF6B6B; color: white;")
        
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        
        layout.addLayout(button_layout)
        
        self.assets_list_tab.setLayout(layout)
    
    def setup_bank_tab(self):
        """銀行口座タブのUI"""
        layout = QVBoxLayout()
        
        # 銀行口座一覧
        self.bank_table = QTableWidget(0, 4)
        self.bank_table.setHorizontalHeaderLabels([
            '銀行名', '口座種別', '残高', '更新日'
        ])
        self.bank_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("<b>🏦 銀行口座一覧</b>"))
        layout.addWidget(self.bank_table)
        
        # 銀行口座合計
        bank_total_layout = QHBoxLayout()
        bank_total_layout.addStretch()
        self.bank_subtotal_label = QLabel("銀行口座合計: 0円")
        self.bank_subtotal_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        bank_total_layout.addWidget(self.bank_subtotal_label)
        layout.addLayout(bank_total_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        add_bank_button = QPushButton("➕ 銀行口座追加")
        add_bank_button.clicked.connect(lambda: self.show_add_account_dialog('bank'))
        
        update_balance_button = QPushButton("💰 残高更新")
        update_balance_button.clicked.connect(self.update_bank_balance)
        
        button_layout.addWidget(add_bank_button)
        button_layout.addWidget(update_balance_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.bank_tab.setLayout(layout)
    
    def setup_securities_tab(self):
        """証券口座タブのUI"""
        layout = QVBoxLayout()
        
        # 証券口座一覧
        self.securities_table = QTableWidget(0, 4)
        self.securities_table.setHorizontalHeaderLabels([
            '証券会社', '口座種別', '評価額', '更新日'
        ])
        self.securities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("<b>📈 証券口座一覧</b>"))
        layout.addWidget(self.securities_table)
        
        # 証券口座合計
        securities_total_layout = QHBoxLayout()
        securities_total_layout.addStretch()
        self.securities_subtotal_label = QLabel("証券口座合計: 0円")
        self.securities_subtotal_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
        securities_total_layout.addWidget(self.securities_subtotal_label)
        layout.addLayout(securities_total_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        add_securities_button = QPushButton("➕ 証券口座追加")
        add_securities_button.clicked.connect(lambda: self.show_add_account_dialog('securities'))
        
        update_value_button = QPushButton("💹 評価額更新")
        update_value_button.clicked.connect(self.update_securities_value)
        
        button_layout.addWidget(add_securities_button)
        button_layout.addWidget(update_value_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.securities_tab.setLayout(layout)
    
    def setup_history_tab(self):
        """資産推移タブのUI"""
        layout = QVBoxLayout()
        
        # 期間選択
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("表示期間:"))
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(['過去3ヶ月', '過去6ヶ月', '過去1年', '全期間'])
        self.period_combo.currentIndexChanged.connect(self.update_history_chart)
        
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()
        
        layout.addLayout(period_layout)
        
        # 資産推移チャート
        self.history_chart_view = QChartView()
        self.history_chart_view.setMinimumHeight(400)
        layout.addWidget(self.history_chart_view)
        
        self.history_tab.setLayout(layout)
    
    def load_assets(self):
        """資産データを読み込む"""
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        # 全資産取得
        c.execute('''
            SELECT id, account_type, account_name, balance, last_updated, notes
            FROM assets
            ORDER BY account_type, account_name
        ''')
        
        all_assets = c.fetchall()
        conn.close()
        
        # 総資産計算
        total_assets = sum(asset[3] for asset in all_assets)
        bank_total = sum(asset[3] for asset in all_assets if asset[1] == 'bank')
        securities_total = sum(asset[3] for asset in all_assets if asset[1] == 'securities')
        
        # 総資産カード更新
        self.total_assets_label.setText(f"{total_assets:,.0f}円")
        self.bank_total_label.setText(f"🏦 銀行: {bank_total:,.0f}円")
        self.securities_total_label.setText(f"📈 証券: {securities_total:,.0f}円")
        
        # 資産一覧テーブル更新
        self.update_assets_table(all_assets)
        
        # 銀行口座テーブル更新
        bank_assets = [asset for asset in all_assets if asset[1] == 'bank']
        self.update_bank_table(bank_assets)
        self.bank_subtotal_label.setText(f"銀行口座合計: {bank_total:,.0f}円")
        
        # 証券口座テーブル更新
        securities_assets = [asset for asset in all_assets if asset[1] == 'securities']
        self.update_securities_table(securities_assets)
        self.securities_subtotal_label.setText(f"証券口座合計: {securities_total:,.0f}円")
        
        # 資産推移チャート更新
        self.update_history_chart()

        # 初期履歴データを作成（履歴がない場合）
        self.create_initial_asset_history()

        # 資産構成円グラフ更新
        if hasattr(self, 'composition_tab'):
            self.update_asset_composition_charts()
    
    def update_assets_table(self, assets):
        """資産一覧テーブルを更新"""
        self.assets_table.setRowCount(0)
        
        for asset in assets:
            asset_id, account_type, account_name, balance, last_updated, notes = asset
            
            row = self.assets_table.rowCount()
            self.assets_table.insertRow(row)
            
            # 種別の表示名
            type_name = "🏦 銀行" if account_type == 'bank' else "📈 証券"
            
            self.assets_table.setItem(row, 0, QTableWidgetItem(type_name))
            self.assets_table.setItem(row, 1, QTableWidgetItem(account_name))
            self.assets_table.setItem(row, 2, QTableWidgetItem(f"{balance:,.0f}円"))
            self.assets_table.setItem(row, 3, QTableWidgetItem(last_updated or '-'))
            self.assets_table.setItem(row, 4, QTableWidgetItem(notes or '-'))
            
            # IDを非表示データとして保存
            self.assets_table.item(row, 0).setData(Qt.UserRole, asset_id)
    
    def update_bank_table(self, bank_assets):
        """銀行口座テーブルを更新"""
        self.bank_table.setRowCount(0)
        
        for asset in bank_assets:
            asset_id, _, account_name, balance, last_updated, notes = asset
            
            row = self.bank_table.rowCount()
            self.bank_table.insertRow(row)
            
            self.bank_table.setItem(row, 0, QTableWidgetItem(account_name))
            self.bank_table.setItem(row, 1, QTableWidgetItem(notes or '普通預金'))
            self.bank_table.setItem(row, 2, QTableWidgetItem(f"{balance:,.0f}円"))
            self.bank_table.setItem(row, 3, QTableWidgetItem(last_updated or '-'))
            
            self.bank_table.item(row, 0).setData(Qt.UserRole, asset_id)
    
    def update_securities_table(self, securities_assets):
        """証券口座テーブルを更新"""
        self.securities_table.setRowCount(0)
        
        for asset in securities_assets:
            asset_id, _, account_name, balance, last_updated, notes = asset
            
            row = self.securities_table.rowCount()
            self.securities_table.insertRow(row)
            
            self.securities_table.setItem(row, 0, QTableWidgetItem(account_name))
            self.securities_table.setItem(row, 1, QTableWidgetItem(notes or '一般口座'))
            self.securities_table.setItem(row, 2, QTableWidgetItem(f"{balance:,.0f}円"))
            self.securities_table.setItem(row, 3, QTableWidgetItem(last_updated or '-'))
            
            self.securities_table.item(row, 0).setData(Qt.UserRole, asset_id)
    
    def show_add_account_dialog(self, account_type=None):
        """口座追加ダイアログを表示"""
        dialog = AddAccountDialog(account_type, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_assets()
    
    def edit_selected_account(self):
        """選択された口座を編集"""
        selected_items = self.assets_table.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, '警告', '編集する口座を選択してください')
            return
        
        row = selected_items[0].row()
        asset_id = self.assets_table.item(row, 0).data(Qt.UserRole)
        
        dialog = EditAccountDialog(asset_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_assets()
    
    def delete_selected_account(self):
        """選択された口座を削除"""
        selected_items = self.assets_table.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, '警告', '削除する口座を選択してください')
            return
        
        row = selected_items[0].row()
        asset_id = self.assets_table.item(row, 0).data(Qt.UserRole)
        account_name = self.assets_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, '確認',
            f'「{account_name}」を削除してもよろしいですか？\n関連する履歴データも削除されます。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            conn = sqlite3.connect('budget.db')
            try:
                c = conn.cursor()

                # 履歴データも削除
                c.execute('DELETE FROM asset_history WHERE asset_id = ?', (asset_id,))

                # 資産データ削除
                c.execute('DELETE FROM assets WHERE id = ?', (asset_id,))

                # 2つの削除が両方成功したときだけ確定する
                conn.commit()

                QMessageBox.information(self, '成功', '口座を削除しました')
                self.load_assets()

            except Exception as e:
                # 途中で失敗したら rollback で削除を全部なかったことにする。
                # これで「履歴だけ消えて口座が残る」ような中途半端な状態を防ぐ
                conn.rollback()
                QMessageBox.critical(self, 'エラー', f'削除中にエラーが発生しました: {str(e)}')
            finally:
                # 成功・失敗にかかわらず必ず接続を閉じる（閉じ忘れ防止）
                conn.close()
    
    def update_bank_balance(self):
        """銀行口座残高を一括更新"""
        dialog = UpdateBalanceDialog('bank', parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_assets()
    
    def update_securities_value(self):
        """証券口座評価額を一括更新"""
        dialog = UpdateBalanceDialog('securities', parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_assets()
    
    
    def update_history_chart(self):
        """資産推移チャートを更新（診断・修正版）"""
        print("=== 資産推移チャート更新開始 ===")
        
        period = self.period_combo.currentText()
        print(f"選択期間: {period}")
        
        # 期間に応じた日数を計算
        if period == '過去3ヶ月':
            days = 90
        elif period == '過去6ヶ月':
            days = 180
        elif period == '過去1年':
            days = 365
        else:  # 全期間
            days = None
        
        print(f"フィルタ日数: {days}")
        
        # データベース接続
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        try:
            # まず現在の資産データを確認
            c.execute('SELECT COUNT(*) FROM assets WHERE balance > 0')
            asset_count = c.fetchone()[0]
            print(f"資産テーブルのレコード数: {asset_count}")
            
            if asset_count > 0:
                c.execute('SELECT account_name, balance FROM assets WHERE balance > 0')
                assets = c.fetchall()
                print("現在の資産:")
                for name, balance in assets:
                    print(f"  {name}: {balance:,.0f}円")
            
            # 履歴テーブルの確認
            c.execute('SELECT COUNT(*) FROM asset_history')
            history_count = c.fetchone()[0]
            print(f"履歴テーブルのレコード数: {history_count}")
            
            # 履歴データがない場合の初期化
            if history_count == 0 and asset_count > 0:
                print("履歴データがないため、現在のデータから初期化中...")
                today = datetime.now().strftime('%Y-%m-%d')
                
                c.execute('SELECT id, balance FROM assets WHERE balance > 0')
                assets = c.fetchall()
                
                for asset_id, balance in assets:
                    c.execute('''
                        INSERT INTO asset_history (asset_id, record_date, balance)
                        VALUES (?, ?, ?)
                    ''', (asset_id, today, balance))
                    print(f"  資産ID {asset_id} の履歴を作成: {balance:,.0f}円")
                
                conn.commit()
                print("履歴データ初期化完了")
            
            # 履歴データを取得
            if days:
                query = '''
                    SELECT record_date, SUM(balance) as total_balance
                    FROM asset_history
                    WHERE record_date >= date('now', ?)
                    GROUP BY record_date
                    ORDER BY record_date
                '''
                c.execute(query, (f'-{days} days',))
            else:
                query = '''
                    SELECT record_date, SUM(balance) as total_balance
                    FROM asset_history
                    GROUP BY record_date
                    ORDER BY record_date
                '''
                c.execute(query)
            
            history_data = c.fetchall()
            print(f"取得した履歴データ数: {len(history_data)}")
            
            if history_data:
                print("履歴データ:")
                for date, balance in history_data:
                    print(f"  {date}: {balance:,.0f}円")
            
            conn.close()
            
            # チャート作成
            chart = QChart()
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            if history_data and len(history_data) > 0:
                print("チャート作成中...")

                # 上辺の線（データ） - selfに保持してGC防止
                self._history_upper = QLineSeries()
                # 下辺の線（y=0）
                self._history_lower = QLineSeries()

                for i, (record_date, total_balance) in enumerate(history_data):
                    val = total_balance if total_balance is not None else 0
                    self._history_upper.append(i, val)
                    self._history_lower.append(i, 0)

                # エリアシリーズ作成
                area_series = QAreaSeries(self._history_upper, self._history_lower)
                area_series.setName("総資産")

                # 線の色（ティール系）
                teal_color = QColor("#2d8a8a")
                pen = QPen(teal_color)
                pen.setWidth(3)
                area_series.setPen(pen)

                # 塗りつぶし色（薄いティール）
                fill_color = QColor("#2d8a8a")
                fill_color.setAlpha(30)
                area_series.setBrush(QBrush(fill_color))

                chart.addSeries(area_series)

                # --- X軸設定（年月ラベル） ---
                axis_x = QCategoryAxis()
                n = len(history_data)
                axis_x.setRange(0, max(1, n - 1))

                # 表示するラベル数を決定（4〜6個程度）
                label_count = min(6, n)
                if label_count >= 2:
                    step = max(1, (n - 1) // (label_count - 1))
                    indices = list(range(0, n, step))
                    if indices[-1] != n - 1:
                        indices.append(n - 1)
                else:
                    indices = [0]

                for idx in indices:
                    record_date = history_data[idx][0]
                    # "YYYY-MM-DD" → "YYYY年M月"
                    try:
                        parts = record_date.split('-')
                        year = int(parts[0])
                        month = int(parts[1])
                        label = f"{year}年{month}月"
                    except (IndexError, ValueError):
                        label = record_date
                    axis_x.append(label, idx)

                axis_x.setLabelsPosition(QCategoryAxis.AxisLabelsPositionOnValue)
                # グリッド線スタイル
                grid_pen_x = QPen(QColor("#dddddd"))
                grid_pen_x.setStyle(Qt.DashLine)
                axis_x.setGridLinePen(grid_pen_x)
                chart.addAxis(axis_x, Qt.AlignBottom)
                area_series.attachAxis(axis_x)

                # --- Y軸設定（万単位ラベル） ---
                values = [balance for _, balance in history_data if balance is not None]
                if values:
                    max_value = max(values)

                    # 万単位で適切な刻みを計算
                    max_man = max_value / 10000
                    if max_man <= 5:
                        tick_man = 1
                    elif max_man <= 10:
                        tick_man = 2
                    elif max_man <= 25:
                        tick_man = 5
                    elif max_man <= 50:
                        tick_man = 10
                    elif max_man <= 100:
                        tick_man = 20
                    else:
                        tick_man = 50

                    y_max_man = ((int(max_man) // tick_man) + 1) * tick_man + tick_man

                    axis_y = QCategoryAxis()
                    axis_y.setRange(0, y_max_man * 10000)

                    val = tick_man
                    while val <= y_max_man:
                        axis_y.append(f"{val}万", val * 10000)
                        val += tick_man

                    axis_y.setLabelsPosition(QCategoryAxis.AxisLabelsPositionOnValue)
                    # グリッド線スタイル
                    grid_pen_y = QPen(QColor("#dddddd"))
                    grid_pen_y.setStyle(Qt.DashLine)
                    axis_y.setGridLinePen(grid_pen_y)
                    chart.addAxis(axis_y, Qt.AlignLeft)
                    area_series.attachAxis(axis_y)

            else:
                # 空のチャート
                series = QLineSeries()
                series.setName("データなし")
                chart.addSeries(series)

                axis_x = QValueAxis()
                axis_x.setRange(0, 1)
                chart.addAxis(axis_x, Qt.AlignBottom)
                series.attachAxis(axis_x)

                axis_y = QValueAxis()
                axis_y.setRange(0, 1000000)
                axis_y.setLabelFormat("%,.0f")
                chart.addAxis(axis_y, Qt.AlignLeft)
                series.attachAxis(axis_y)

                chart.setTitle("資産データがありません\n口座を追加して残高を入力してください")

            # スタイル設定
            chart.legend().setVisible(False)
            chart.setTitle("")
            chart.setBackgroundRoundness(0)
            chart.setMargins(QMargins(10, 10, 10, 10))
            
            print("チャートをビューに設定中...")
            self.history_chart_view.setChart(chart)
            print("チャート設定完了")
            
        except Exception as e:
            print(f"エラー発生: {e}")
            import traceback
            traceback.print_exc()
            
            # エラー時のチャート
            error_chart = QChart()
            error_chart.setTitle(f"エラーが発生しました: {str(e)}")
            self.history_chart_view.setChart(error_chart)
            
            try:
                conn.close()
            except Exception as e:
                print(f"DB接続クローズエラー: {e}")
        
        print("=== 資産推移チャート更新終了 ===")

    def create_initial_asset_history(self):
        """現在の資産データから初期履歴データを作成（重複チェック付き）"""
        try:
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 今日の履歴データが既にあるかチェック
            c.execute('SELECT COUNT(*) FROM asset_history WHERE record_date = ?', (today,))
            existing_count = c.fetchone()[0]
            
            if existing_count > 0:
                print(f"今日（{today}）の履歴データは既に存在します。スキップします。")
                conn.close()
                return
            
            # 既存の履歴データ数をチェック
            c.execute('SELECT COUNT(*) FROM asset_history')
            history_count = c.fetchone()[0]
            
            if history_count == 0:
                # 現在の資産データを取得
                c.execute('''
                    SELECT id, balance
                    FROM assets
                    WHERE balance > 0
                ''')
                assets = c.fetchall()
                
                if assets:
                    # 各資産の現在の残高を履歴として追加
                    for asset_id, balance in assets:
                        c.execute('''
                            INSERT INTO asset_history (asset_id, record_date, balance)
                            VALUES (?, ?, ?)
                        ''', (asset_id, today, balance))
                        print(f"  資産ID {asset_id} の履歴を作成: {balance:,.0f}円")
                    
                    conn.commit()
                    print("履歴データ初期化完了")
            
            conn.close()
            
        except Exception as e:
            print(f"履歴データ作成エラー: {e}")
            try:
                conn.close()
            except Exception as e:
                print(f"DB接続クローズエラー: {e}")

    def record_daily_asset_history(self):
        """日次の資産履歴を記録（重複チェック付き）"""
        try:
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 今日の履歴が既にあるかチェック
            c.execute('SELECT COUNT(*) FROM asset_history WHERE record_date = ?', (today,))
            existing_count = c.fetchone()[0]
            
            if existing_count > 0:
                print(f"今日（{today}）の履歴は既に記録済みです")
                conn.close()
                return
            
            # 現在の資産データを取得
            c.execute('''
                SELECT id, balance
                FROM assets
                WHERE balance > 0
            ''')
            assets = c.fetchall()
            
            if assets:
                for asset_id, balance in assets:
                    c.execute('''
                        INSERT INTO asset_history (asset_id, record_date, balance)
                        VALUES (?, ?, ?)
                    ''', (asset_id, today, balance))
                
                conn.commit()
                print(f"日次履歴を記録しました（{len(assets)}件）")
            
            conn.close()
            
        except Exception as e:
            print(f"日次履歴記録エラー: {e}")
            try:
                conn.close()
            except Exception as e:
                print(f"DB接続クローズエラー: {e}")    

    def setup_asset_composition_tab(self):
        """資産構成タブのUI（円グラフ）"""
        layout = QVBoxLayout()
        
        # タイトル
        title_label = QLabel("<h2>💰 資産構成</h2>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 統計情報カード
        self.composition_stats_card = self.create_composition_stats_card()
        layout.addWidget(self.composition_stats_card)
        
        # 円グラフエリア
        chart_layout = QHBoxLayout()
        
        # メイン円グラフ（銀行 vs 証券）
        self.main_pie_chart_view = QChartView()
        self.main_pie_chart_view.setMinimumHeight(400)
        chart_layout.addWidget(self.main_pie_chart_view)
        
        # 詳細円グラフ（口座別）
        self.detailed_pie_chart_view = QChartView()
        self.detailed_pie_chart_view.setMinimumHeight(400)
        chart_layout.addWidget(self.detailed_pie_chart_view)
        
        layout.addLayout(chart_layout)
        
        self.composition_tab.setLayout(layout)

    def create_composition_stats_card(self):
        """資産構成統計情報カードを作成"""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        card.setMaximumHeight(120)
        
        card_layout = QVBoxLayout()
        
        # 統計情報を横に並べる
        stats_layout = QHBoxLayout()
        
        # 銀行割合
        self.bank_percentage_label = QLabel("🏦 銀行: 0%")
        self.bank_percentage_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #28a745;")
        
        # 証券割合
        self.securities_percentage_label = QLabel("📈 証券: 0%")
        self.securities_percentage_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007bff;")
        
        # 最大口座
        self.largest_account_label = QLabel("💎 最大口座: -")
        self.largest_account_label.setStyleSheet("font-size: 14px; color: #6c757d;")
        
        # 口座数
        self.account_count_label = QLabel("📊 口座数: 0")
        self.account_count_label.setStyleSheet("font-size: 14px; color: #6c757d;")
        
        stats_layout.addWidget(self.bank_percentage_label)
        stats_layout.addWidget(self.securities_percentage_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.largest_account_label)
        stats_layout.addWidget(self.account_count_label)
        
        card_layout.addLayout(stats_layout)
        card.setLayout(card_layout)
        
        return card

    def update_asset_composition_charts(self):
        """資産構成円グラフを更新"""
        # データベースから資産データを取得
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        # 全資産取得
        c.execute('''
            SELECT account_type, account_name, balance, notes
            FROM assets
            WHERE balance > 0
            ORDER BY balance DESC
        ''')
        
        assets = c.fetchall()
        conn.close()
        
        if not assets:
            # データがない場合の処理
            self.show_empty_pie_charts()
            return
        
        # 合計資産計算
        total_assets = sum(asset[2] for asset in assets)
        bank_total = sum(asset[2] for asset in assets if asset[0] == 'bank')
        securities_total = sum(asset[2] for asset in assets if asset[0] == 'securities')
        
        # 統計情報更新
        self.update_composition_stats(total_assets, bank_total, securities_total, assets)
        
        # メイン円グラフ（銀行 vs 証券）
        self.create_main_composition_chart(bank_total, securities_total, total_assets)
        
        # 詳細円グラフ（口座別）
        self.create_detailed_composition_chart(assets, total_assets)

    def update_composition_stats(self, total_assets, bank_total, securities_total, assets):
        """資産構成統計情報を更新"""
        if total_assets > 0:
            bank_percentage = (bank_total / total_assets) * 100
            securities_percentage = (securities_total / total_assets) * 100
            
            self.bank_percentage_label.setText(f"🏦 銀行: {bank_percentage:.1f}%")
            self.securities_percentage_label.setText(f"📈 証券: {securities_percentage:.1f}%")
            
            # 最大口座
            if assets:
                largest_account = assets[0]  # 残高順でソート済み
                largest_name = largest_account[1]
                largest_balance = largest_account[2]
                largest_percentage = (largest_balance / total_assets) * 100
                self.largest_account_label.setText(f"💎 最大口座: {largest_name} ({largest_percentage:.1f}%)")
            
            # 口座数
            self.account_count_label.setText(f"📊 口座数: {len(assets)}件")
        else:
            self.bank_percentage_label.setText("🏦 銀行: 0%")
            self.securities_percentage_label.setText("📈 証券: 0%")
            self.largest_account_label.setText("💎 最大口座: -")
            self.account_count_label.setText("📊 口座数: 0件")

    def create_main_composition_chart(self, bank_total, securities_total, total_assets):
        """メイン資産構成円グラフを作成（銀行 vs 証券）"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        series = QPieSeries()
        series.setHoleSize(0.35)  # ドーナツ型にする
        
        if total_assets > 0:
            # 銀行のスライス
            if bank_total > 0:
                bank_slice = QPieSlice(f"🏦 銀行\n{bank_total:,.0f}円", bank_total)
                bank_slice.setColor(QColor("#28a745"))  # 緑色
                bank_slice.setLabelVisible(True)
                bank_slice.setLabelPosition(QPieSlice.LabelOutside)
                series.append(bank_slice)
            
            # 証券のスライス
            if securities_total > 0:
                securities_slice = QPieSlice(f"📈 証券\n{securities_total:,.0f}円", securities_total)
                securities_slice.setColor(QColor("#007bff"))  # 青色
                securities_slice.setLabelVisible(True)
                securities_slice.setLabelPosition(QPieSlice.LabelOutside)
                series.append(securities_slice)
            
            # パーセンテージ表示を有効化
            for slice in series.slices():
                percentage = slice.percentage() * 100
                slice.setLabel(f"{slice.label()}\n{percentage:.1f}%")
                
                # ホバー効果
                slice.setExploded(False)
                slice.hovered.connect(lambda state, s=slice: s.setExploded(state))
        
        chart.addSeries(series)
        chart.setTitle("資産配分（銀行 vs 証券）")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        
        self.main_pie_chart_view.setChart(chart)

    def create_detailed_composition_chart(self, assets, total_assets):
        """詳細資産構成円グラフを作成（口座別）"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        series = QPieSeries()
        series.setHoleSize(0.35)  # ドーナツ型にする
        
        if total_assets > 0 and assets:
            # 色のパレット
            colors = [
                "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
                "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F",
                "#BB8FCE", "#85C1E9", "#F8C471", "#82E0AA"
            ]
            
            # 上位8口座まで表示（小さすぎる口座は「その他」にまとめる）
            main_assets = assets[:8]
            other_assets = assets[8:]
            
            color_index = 0
            
            for asset in main_assets:
                account_type, account_name, balance, notes = asset
                
                # 口座タイプのアイコン
                icon = "🏦" if account_type == 'bank' else "📈"
                
                # スライス作成
                slice_label = f"{icon} {account_name}"
                if notes and notes != account_name:
                    slice_label += f"\n({notes})"
                
                account_slice = QPieSlice(slice_label, balance)
                account_slice.setColor(QColor(colors[color_index % len(colors)]))
                account_slice.setLabelVisible(True)
                account_slice.setLabelPosition(QPieSlice.LabelOutside)
                
                # パーセンテージ追加
                percentage = (balance / total_assets) * 100
                account_slice.setLabel(f"{slice_label}\n{balance:,.0f}円\n{percentage:.1f}%")
                
                # ホバー効果
                account_slice.hovered.connect(lambda state, s=account_slice: s.setExploded(state))
                
                series.append(account_slice)
                color_index += 1
            
            # その他の口座をまとめる
            if other_assets:
                other_total = sum(asset[2] for asset in other_assets)
                other_percentage = (other_total / total_assets) * 100
                
                other_slice = QPieSlice(f"💼 その他\n{other_total:,.0f}円\n{other_percentage:.1f}%", other_total)
                other_slice.setColor(QColor("#BDC3C7"))  # グレー
                other_slice.setLabelVisible(True)
                other_slice.setLabelPosition(QPieSlice.LabelOutside)
                
                series.append(other_slice)
        
        chart.addSeries(series)
        chart.setTitle("詳細資産配分（口座別）")
        chart.legend().setVisible(False)  # ラベルが詳細なので凡例は非表示
        
        self.detailed_pie_chart_view.setChart(chart)

    def show_empty_pie_charts(self):
        """データがない場合の円グラフ表示"""
        # メインチャート
        main_chart = QChart()
        main_chart.setTitle("資産データがありません")
        self.main_pie_chart_view.setChart(main_chart)
        
        # 詳細チャート
        detailed_chart = QChart()
        detailed_chart.setTitle("資産データがありません")
        self.detailed_pie_chart_view.setChart(detailed_chart)    


class AddAccountDialog(QDialog):
    """口座追加ダイアログ"""
    
    def __init__(self, account_type=None, parent=None):
        super().__init__(parent)
        self.account_type = account_type
        self.setWindowTitle('口座追加')
        self.setMinimumWidth(400)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # 種別選択
        self.type_combo = QComboBox()
        self.type_combo.addItems(['銀行', '証券'])
        if self.account_type == 'bank':
            self.type_combo.setCurrentText('銀行')
        elif self.account_type == 'securities':
            self.type_combo.setCurrentText('証券')
        
        form_layout.addRow('種別:', self.type_combo)
        
        # 口座名
        self.account_name_input = QLineEdit()
        self.account_name_input.setPlaceholderText('例: 三菱UFJ銀行、SBI証券')
        form_layout.addRow('口座名:', self.account_name_input)
        
        # 残高/評価額
        self.balance_input = QLineEdit()
        self.balance_input.setPlaceholderText('例: 1000000')
        form_layout.addRow('残高/評価額 (円):', self.balance_input)
        
        # 備考
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText('例: 普通預金、NISA口座')
        form_layout.addRow('備考:', self.notes_input)
        
        layout.addLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        save_button = QPushButton('保存')
        save_button.clicked.connect(self.save_account)
        
        cancel_button = QPushButton('キャンセル')
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_account(self):
        """口座を保存"""
        try:
            account_type_text = self.type_combo.currentText()
            account_type = 'bank' if account_type_text == '銀行' else 'securities'
            
            account_name = self.account_name_input.text().strip()
            if not account_name:
                raise ValueError("口座名を入力してください")
            
            balance_text = self.balance_input.text().strip().replace(',', '')
            if not balance_text:
                raise ValueError("残高を入力してください")
            
            balance = float(balance_text)
            if balance < 0:
                raise ValueError("残高は0以上の値を入力してください")
            
            notes = self.notes_input.text().strip()
            
            today = QDate.currentDate().toString('yyyy-MM-dd')
            
            conn = sqlite3.connect('budget.db')
            try:
                c = conn.cursor()

                # 資産データ挿入
                c.execute('''
                    INSERT INTO assets (account_type, account_name, balance, last_updated, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (account_type, account_name, balance, today, notes))

                asset_id = c.lastrowid

                # 履歴データも記録
                c.execute('''
                    INSERT INTO asset_history (asset_id, record_date, balance)
                    VALUES (?, ?, ?)
                ''', (asset_id, today, balance))

                # 口座と履歴の両方が成功したときだけ確定する
                conn.commit()
            except Exception:
                conn.rollback()  # 口座だけ登録され履歴が無い中途半端な状態を防ぐ
                raise            # 下のexceptでユーザーに通知する
            finally:
                conn.close()     # 必ず接続を閉じる

            QMessageBox.information(self, '成功', '口座を追加しました')
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, '入力エラー', str(e))
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'保存中にエラーが発生しました: {str(e)}')


class EditAccountDialog(QDialog):
    """口座編集ダイアログ"""
    
    def __init__(self, asset_id, parent=None):
        super().__init__(parent)
        self.asset_id = asset_id
        self.setWindowTitle('口座編集')
        self.setMinimumWidth(400)
        self.initUI()
        self.load_data()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # 口座名
        self.account_name_input = QLineEdit()
        form_layout.addRow('口座名:', self.account_name_input)
        
        # 残高/評価額
        self.balance_input = QLineEdit()
        form_layout.addRow('残高/評価額 (円):', self.balance_input)
        
        # 備考
        self.notes_input = QLineEdit()
        form_layout.addRow('備考:', self.notes_input)
        
        layout.addLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        save_button = QPushButton('保存')
        save_button.clicked.connect(self.save_changes)
        
        cancel_button = QPushButton('キャンセル')
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        """データを読み込む"""
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT account_name, balance, notes
            FROM assets
            WHERE id = ?
        ''', (self.asset_id,))
        
        result = c.fetchone()
        conn.close()
        
        if result:
            account_name, balance, notes = result
            self.account_name_input.setText(account_name)
            self.balance_input.setText(str(balance))
            self.notes_input.setText(notes or '')
    
    def save_changes(self):
        """変更を保存"""
        try:
            account_name = self.account_name_input.text().strip()
            if not account_name:
                raise ValueError("口座名を入力してください")
            
            balance_text = self.balance_input.text().strip().replace(',', '')
            if not balance_text:
                raise ValueError("残高を入力してください")
            
            balance = float(balance_text)
            if balance < 0:
                raise ValueError("残高は0以上の値を入力してください")
            
            notes = self.notes_input.text().strip()
            
            today = QDate.currentDate().toString('yyyy-MM-dd')
            
            conn = sqlite3.connect('budget.db')
            try:
                c = conn.cursor()

                # 資産データ更新
                c.execute('''
                    UPDATE assets
                    SET account_name = ?, balance = ?, last_updated = ?, notes = ?
                    WHERE id = ?
                ''', (account_name, balance, today, notes, self.asset_id))

                # 履歴データを記録
                c.execute('''
                    INSERT INTO asset_history (asset_id, record_date, balance)
                    VALUES (?, ?, ?)
                ''', (self.asset_id, today, balance))

                # 更新と履歴の両方が成功したときだけ確定する
                conn.commit()
            except Exception:
                conn.rollback()  # 中途半端な更新を防ぐ
                raise            # 下のexceptでユーザーに通知する
            finally:
                conn.close()     # 必ず接続を閉じる

            QMessageBox.information(self, '成功', '口座情報を更新しました')
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, '入力エラー', str(e))
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'保存中にエラーが発生しました: {str(e)}')


class UpdateBalanceDialog(QDialog):
    """残高一括更新ダイアログ"""
    
    def __init__(self, account_type, parent=None):
        super().__init__(parent)
        self.account_type = account_type
        type_name = '銀行' if account_type == 'bank' else '証券'
        self.setWindowTitle(f'{type_name}口座残高更新')
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # 説明
        type_name = '銀行' if self.account_type == 'bank' else '証券'
        info_label = QLabel(f'<b>{type_name}口座の残高を一括で更新します</b>')
        layout.addWidget(info_label)
        
        # 口座リストテーブル
        self.accounts_table = QTableWidget(0, 4)
        self.accounts_table.setHorizontalHeaderLabels([
            '口座名', '現在の残高', '新しい残高', 'ID'
        ])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.accounts_table.setColumnHidden(3, True)  # IDを非表示
        
        layout.addWidget(self.accounts_table)
        
        # データ読み込み
        self.load_accounts()
        
        # ボタン
        button_layout = QHBoxLayout()
        
        save_button = QPushButton('一括更新')
        save_button.clicked.connect(self.save_balances)
        
        cancel_button = QPushButton('キャンセル')
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_accounts(self):
        """口座データを読み込む"""
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT id, account_name, balance
            FROM assets
            WHERE account_type = ?
            ORDER BY account_name
        ''', (self.account_type,))
        
        accounts = c.fetchall()
        conn.close()
        
        self.accounts_table.setRowCount(len(accounts))
        
        for row, (asset_id, account_name, balance) in enumerate(accounts):
            self.accounts_table.setItem(row, 0, QTableWidgetItem(account_name))
            self.accounts_table.setItem(row, 1, QTableWidgetItem(f"{balance:,.0f}円"))
            
            # 新しい残高入力欄
            new_balance_input = QLineEdit()
            new_balance_input.setText(str(balance))
            new_balance_input.setPlaceholderText('新しい残高')
            self.accounts_table.setCellWidget(row, 2, new_balance_input)
            
            # IDを保存
            self.accounts_table.setItem(row, 3, QTableWidgetItem(str(asset_id)))
    
    def save_balances(self):
        """残高を一括保存"""
        try:
            today = QDate.currentDate().toString('yyyy-MM-dd')
            updates = []
            
            for row in range(self.accounts_table.rowCount()):
                asset_id = int(self.accounts_table.item(row, 3).text())
                new_balance_input = self.accounts_table.cellWidget(row, 2)
                new_balance_text = new_balance_input.text().strip().replace(',', '')
                
                if new_balance_text:
                    new_balance = float(new_balance_text)
                    updates.append((asset_id, new_balance))
            
            if not updates:
                QMessageBox.warning(self, '警告', '更新する残高を入力してください')
                return
            
            conn = sqlite3.connect('budget.db')
            try:
                c = conn.cursor()

                for asset_id, new_balance in updates:
                    # 資産データ更新
                    c.execute('''
                        UPDATE assets
                        SET balance = ?, last_updated = ?
                        WHERE id = ?
                    ''', (new_balance, today, asset_id))

                    # 履歴データ記録
                    c.execute('''
                        INSERT INTO asset_history (asset_id, record_date, balance)
                        VALUES (?, ?, ?)
                    ''', (asset_id, today, new_balance))

                # 全口座の更新が成功したときだけ確定する
                conn.commit()
            except Exception:
                conn.rollback()  # 一部の口座だけ更新された中途半端な状態を防ぐ
                raise            # 下のexceptでユーザーに通知する
            finally:
                conn.close()     # 必ず接続を閉じる

            type_name = '銀行' if self.account_type == 'bank' else '証券'
            QMessageBox.information(self, '成功', f'{len(updates)}件の{type_name}口座を更新しました')
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, '入力エラー', '正しい数値を入力してください')
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'更新中にエラーが発生しました: {str(e)}')                                

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BudgetApp()
    window.show()
    sys.exit(app.exec_())