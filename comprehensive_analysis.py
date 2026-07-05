# -*- coding: utf-8 -*-
"""全データ分析画面

全期間の支出データを統計・グラフ・レポートで多角的に分析する。"""
from PyQt5.QtWidgets import (
    QWidget,
    QDialog,
    QMessageBox,
    QPushButton,
    QLabel,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QFrame,
    QTabWidget,
    QFileDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QLineSeries
import sqlite3
import pandas as pd
from datetime import datetime
import json
from common import BaseWidget


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
