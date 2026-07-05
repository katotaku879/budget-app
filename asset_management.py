# -*- coding: utf-8 -*-
"""資産管理画面

銀行・証券口座の残高管理と資産推移チャート。"""
from PyQt5.QtWidgets import (
    QWidget,
    QDialog,
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
from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtGui import QColor, QPen, QBrush
from PyQt5.QtChart import (
    QChart,
    QChartView,
    QPieSeries,
    QPieSlice,
    QValueAxis,
    QLineSeries,
    QAreaSeries,
    QCategoryAxis
)
import sqlite3
from datetime import datetime
from common import BaseWidget
from account_dialogs import AddAccountDialog, EditAccountDialog, UpdateBalanceDialog


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
        
        period = self.period_combo.currentText()
        
        # 期間に応じた日数を計算
        if period == '過去3ヶ月':
            days = 90
        elif period == '過去6ヶ月':
            days = 180
        elif period == '過去1年':
            days = 365
        else:  # 全期間
            days = None
        
        
        # データベース接続
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        try:
            # まず現在の資産データを確認
            c.execute('SELECT COUNT(*) FROM assets WHERE balance > 0')
            asset_count = c.fetchone()[0]
            
            if asset_count > 0:
                c.execute('SELECT account_name, balance FROM assets WHERE balance > 0')
                assets = c.fetchall()
                for name, balance in assets:
                    pass
            
            # 履歴テーブルの確認
            c.execute('SELECT COUNT(*) FROM asset_history')
            history_count = c.fetchone()[0]
            
            # 履歴データがない場合の初期化
            if history_count == 0 and asset_count > 0:
                today = datetime.now().strftime('%Y-%m-%d')
                
                c.execute('SELECT id, balance FROM assets WHERE balance > 0')
                assets = c.fetchall()
                
                for asset_id, balance in assets:
                    c.execute('''
                        INSERT INTO asset_history (asset_id, record_date, balance)
                        VALUES (?, ?, ?)
                    ''', (asset_id, today, balance))
                
                conn.commit()
            
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
            
            if history_data:
                for date, balance in history_data:
                    pass
            
            conn.close()
            
            # チャート作成
            chart = QChart()
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            if history_data and len(history_data) > 0:

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
            
            self.history_chart_view.setChart(chart)
            
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
                    
                    conn.commit()
            
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
