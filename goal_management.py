# -*- coding: utf-8 -*-
"""目標管理画面

月間・カテゴリ別の目標設定と進捗表示。"""
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QMessageBox,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QFrame,
    QTabWidget,
    QProgressBar
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from PyQt5.QtChart import QChart, QChartView, QValueAxis, QBarCategoryAxis, QLineSeries
import sqlite3
from db_utils import execute_query, get_categories
from common import DateHelper, BaseWidget


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
