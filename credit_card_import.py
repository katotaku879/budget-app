# -*- coding: utf-8 -*-
"""クレジットカード明細取込ダイアログ

楽天カード/楽天PAY/PayPay等のCSV取込。URL経由のGoogle Sheets取得にも対応。"""
from PyQt5.QtWidgets import (
    QWidget,
    QDialog,
    QMessageBox,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QInputDialog
)
from PyQt5.QtCore import Qt, QDate
import sqlite3
import pandas as pd
import json
import csv
import io
import requests
from db_utils import get_categories


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
