# -*- coding: utf-8 -*-
"""内訳画面

月ごとの支出内訳を円グラフで表示する。"""
from PyQt5.QtWidgets import (
    QDialog,
    QPushButton,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QFormLayout
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
from db_utils import execute_query, fetch_df
from common import DateHelper, BaseWidget, YearMonthDialog, CHART_PALETTE


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
        """収支・カテゴリ別テーブル（目標列つき）・円グラフを更新する

        以前は「目標列なしの旧版」と「目標列ありのenhanced版」が併存し、
        月切替と目標更新で表示が食い違っていたため、目標列あり版に一本化した。
        """
        income, expense_df = self.load_monthly_data()
        
        # 収入表示の更新
        self.monthly_income_input.setText(f"{income:,.0f}")
        
        # 総支出の計算と表示
        total_expense = expense_df['total_amount'].sum() if not expense_df.empty else 0
        self.monthly_expense_label.setText(f"{total_expense:,.0f} 円")
        
        # 収支の計算と表示
        balance = income - total_expense
        self.monthly_balance_label.setText(f"{balance:,.0f} 円")
        
        # カテゴリ別目標を取得（共通ヘルパー経由なので接続の閉じ忘れがない）
        rows = execute_query('''
            SELECT category, goal_amount FROM category_goals
            WHERE year = ? AND month = ?
        ''', (self.current_year, self.current_month), fetch_all=True)
        category_goals = {category: amount for category, amount in (rows or [])}
        
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

    def create_enhanced_pie_chart(self, expense_df, total_expense, category_goals):
        """カテゴリ別支出と目標を表示する円グラフを作成"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)

        # 円グラフのデータを作成
        series = QPieSeries()

        # カラーリスト（全画面共通のパレットを使用）
        colors = CHART_PALETTE

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
