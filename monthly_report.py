# -*- coding: utf-8 -*-
"""月次レポート画面

直近6ヶ月の収支推移・カテゴリ別グラフを表示する。"""
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout
)
from PyQt5.QtCore import Qt, QDate, QMargins, QPointF
from PyQt5.QtGui import QColor
from PyQt5.QtChart import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QValueAxis,
    QBarCategoryAxis,
    QLineSeries
)
import sqlite3
import pandas as pd
from db_utils import get_categories
from common import DateHelper, BaseWidget


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

    def update_display(self):
        """月次レポート全体を更新する

        以前は「目標なしの旧版」と「目標つきのenhanced版」が併存し、
        月ナビと目標更新で表示が食い違っていたため、目標つき版に一本化した。
        """
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

    def get_6month_data(self):
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

    def update_table(self, months_data):
        """収支リストのテーブルを更新（目標行つき）"""
        # 全期間のカテゴリを取得
        all_categories = set()
        for data in months_data:
            all_categories.update(data['expenses_by_category'].keys())
        all_categories = sorted(list(all_categories))
        
        # テーブルの設定
        self.summary_table.clear()
        # 行数 = カテゴリ数 + 収入行 + 支出合計行 + 収支合計行 + 貯蓄目標行 + 目標達成率行(計5行)
        # ※以前は +6 で確保していたため最下部に空行が1行できていた
        row_count = len(all_categories) + 5
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
