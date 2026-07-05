# -*- coding: utf-8 -*-
"""メインウィンドウ

全画面の生成・ナビゲーション・DB初期化・自動バックアップを担当する。"""
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
import os
from datetime import datetime
from db_utils import get_db_connection, execute_query, get_categories, execute_many, fetch_df
from common import DateHelper, BaseWidget, YearMonthDialog, EditableTableItem, RecurringExpenseDialog
from backup import BackupManager, BackupSettingsDialog, BackupManagerDialog
from category_management import CategoryManagementDialog
from income_expense import IncomeExpenseWidget
from breakdown import BreakdownWidget
from monthly_report import MonthlyReportWidget
from goal_management import GoalManagementWidget
from diagnostic_report import DiagnosticReportWidget
from comprehensive_analysis import ComprehensiveAnalysisWidget
from asset_management import AssetManagementWidget


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
