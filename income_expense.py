# -*- coding: utf-8 -*-
"""入出金管理画面（メイン画面）

支出の入力・編集・削除、収入登録、各種明細取込の入り口。"""
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QFrame,
    QFileDialog,
    QDialogButtonBox,
    QProgressBar,
    QProgressDialog,
    QInputDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
import sqlite3
import pandas as pd
import os
from datetime import datetime
from db_utils import execute_query, get_categories
from common import DateHelper, BaseWidget, YearMonthDialog, RecurringExpenseDialog
from credit_card_import import CreditCardImportDialog
from pasmo_import import PasmoImportDialog


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
            
            # 古いシステムを完全無効化
            # self.is_updating = True
            # 既存のpandas処理をすべてコメントアウト
            
            # 新システムのみ実行
            if hasattr(self, 'load_current_month_expenses'):
                self.load_current_month_expenses()
            else:
                pass
                
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
                    return
                expense_id = int(id_item.text())
                
                date_item = self.expense_table.item(row, 1)
                if date_item is None:
                    return
                date = date_item.text()
                
                # カテゴリの処理(コンボボックスかテキストか判定)
                category_widget = self.expense_table.cellWidget(row, 2)
                if category_widget and isinstance(category_widget, QComboBox):
                    category = category_widget.currentText()
                else:
                    category_item = self.expense_table.item(row, 2)
                    if category_item is None:
                        return
                    category = category_item.text() if category_item else ''
                
                # 金額の処理を改善
                amount_item = self.expense_table.item(row, 3)
                if amount_item is None:
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
                    return
                description = description_item.text()
                
                # データベース更新(共通関数を使用)
                execute_query('''
                    UPDATE expenses 
                    SET date = ?, category = ?, amount = ?, description = ?
                    WHERE id = ?
                ''', (date, category, amount, description, expense_id))
                
                
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
            
            conn = sqlite3.connect('budget.db')
            c = conn.cursor()
            
            # まず全データを確認
            c.execute('SELECT COUNT(*) FROM expenses')
            total_count = c.fetchone()[0]
            
            # 今月のデータを確認
            c.execute('''
                SELECT COUNT(*) FROM expenses
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ''', (str(self.current_year), f"{self.current_month:02d}"))
            
            month_count = c.fetchone()[0]
            
            # 実際のデータを取得
            c.execute('''
                SELECT id, date, category, amount, description
                FROM expenses
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
                ORDER BY date DESC, id DESC
            ''', (str(self.current_year), f"{self.current_month:02d}"))
            
            self.current_expense_data = c.fetchall()
            conn.close()
            
            
            # データ内容を詳細表示
            if self.current_expense_data:
                for i, row in enumerate(self.current_expense_data):
                    pass
            else:
                # 他の月のデータがあるか確認
                conn = sqlite3.connect('budget.db')
                c = conn.cursor()
                c.execute('SELECT DISTINCT strftime("%Y-%m", date) FROM expenses ORDER BY date DESC LIMIT 5')
                other_months = c.fetchall()
                conn.close()
                for month in other_months:
                    pass
            
            # 表示更新
            self.update_expense_table_display()
            
        except Exception as e:
            print(f"load_current_month_expenses エラー: {e}")
            import traceback
            traceback.print_exc()

    def update_expense_table_display(self):
        """支出テーブルの表示を更新(安全版)"""
        try:
            
            # is_updatingフラグを設定
            self.is_updating = True
            
            # 全ての必要なウィジェットが存在します
            
            # データ読み込み開始
            
            # データベースから支出データを取得
            query = '''
                SELECT id, date, category, amount, description
                FROM expenses
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            '''
            
            month_str = f'{self.current_month:02d}'
            all_data = execute_query(query, (str(self.current_year), month_str), fetch_all=True)
            
            
            if all_data:
                for i, row in enumerate(all_data[:5]):  # 最初の5件だけ表示
                    pass
            
            # フィルタリング処理
            selected_category = self.filter_combo.currentText()

            filtered_data = all_data
            if selected_category != '全てのカテゴリ':
                filtered_data = [row for row in filtered_data if row[2] == selected_category]

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

            if sort_option == '日付順（新しい順）':  # 全角括弧に変更
                filtered_data = sorted(filtered_data, key=lambda x: x[1], reverse=True)
            elif sort_option == '日付順（古い順）':  # 全角括弧に変更
                filtered_data = sorted(filtered_data, key=lambda x: x[1])
            elif sort_option == 'カテゴリ別':
                self.is_updating = False
                self.display_expenses_grouped_by_category(filtered_data)
                return
            elif sort_option == '金額順（高い順）':  # 全角括弧に変更
                filtered_data = sorted(filtered_data, key=lambda x: x[3], reverse=True)
            elif sort_option == '金額順（安い順）':  # 全角括弧に変更
                filtered_data = sorted(filtered_data, key=lambda x: x[3])
            else:
                pass
            
            # 表示件数制限
            limit_text = self.limit_combo.currentText()
            
            if limit_text != '全て':
                limit = int(limit_text.replace('件', ''))
                filtered_data = filtered_data[:limit]
            
            
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
                
                for row, row_data in enumerate(filtered_data):
                    if not row_data or len(row_data) < 5:
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
                            pass
                            
                    except Exception as e:
                        print(f"行{row}のデータ設定エラー: {e}")
                        continue
                
            else:
                self.expense_table.setRowCount(0)

            # カテゴリ合計を更新
            self.update_category_total_label(filtered_data, selected_category)

            self.is_updating = False
            
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
            
            if self.expense_table is None:
                return
                
            
            # スパンをクリア
            self.expense_table.clearSpans()
            
            if not data:
                return
            
            for row, row_data in enumerate(data):
                if not row_data or len(row_data) < 5:
                    continue
                    
                try:
                    exp_id, date, category, amount, description = row_data
                    
                    
                    # 安全にアイテムを設定
                    self.expense_table.setItem(row, 0, QTableWidgetItem(str(exp_id or '')))
                    self.expense_table.setItem(row, 1, QTableWidgetItem(str(date or '')))
                    self.expense_table.setItem(row, 2, QTableWidgetItem(str(category or '')))
                    self.expense_table.setItem(row, 3, QTableWidgetItem(f"{amount or 0:,.0f}円"))
                    self.expense_table.setItem(row, 4, QTableWidgetItem(str(description or '')))
                    
                    
                except Exception as e:
                    print(f"❌ 行 {row} の設定エラー: {e}")
                    
                    
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
