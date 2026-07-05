# -*- coding: utf-8 -*-
"""家計診断レポート画面

健全性スコア・改善ポイント・将来予測を表示する。"""
from PyQt5.QtWidgets import (
    QWidget,
    QMessageBox,
    QPushButton,
    QLabel,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QTabWidget
)
from PyQt5.QtCore import Qt, QDate
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
from db_utils import execute_query, fetch_df
from common import DateHelper, BaseWidget


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
  
