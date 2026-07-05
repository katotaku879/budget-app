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
from comprehensive_analysis import ComprehensiveAnalysisWidget
from diagnostic_report import DiagnosticReportWidget
from goal_management import GoalManagementWidget
from monthly_report import MonthlyReportWidget
from breakdown import BreakdownWidget
from pasmo_import import PasmoImportDialog
from credit_card_import import CreditCardImportDialog
from category_management import CategoryManagementDialog
from backup import BackupManager, BackupSettingsDialog, BackupManagerDialog
from account_dialogs import AddAccountDialog, EditAccountDialog, UpdateBalanceDialog
from common import DateHelper, BaseWidget, YearMonthDialog, EditableTableItem, RecurringExpenseDialog
from db_utils import get_db_connection, execute_query, get_categories, execute_many, fetch_df

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BudgetApp()
    window.show()
    sys.exit(app.exec_())