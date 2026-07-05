# -*- coding: utf-8 -*-
"""PASMO利用明細取込ダイアログ

PASMOのPDF明細を解析して交通費として取込む（pdfplumberは使用時に読み込む）。"""
from PyQt5.QtWidgets import (
    QWidget,
    QDialog,
    QMessageBox,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QStackedWidget,
    QFileDialog
)
from PyQt5.QtCore import Qt, QDate
import sqlite3
import os


class PasmoImportDialog(QDialog):
    """モバイルPASMO残額ご利用明細PDF取込ダイアログ"""

    # 除外する種別
    EXCLUDE_TYPES = ['繰', 'ｶｰﾄﾞ']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('PASMO明細取込')
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.preview_data = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # ステップ表示
        self.step_label = QLabel('ステップ 1/2: PDFファイルの選択')
        self.step_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        layout.addWidget(self.step_label)

        self.stack = QStackedWidget()

        # ---- ステップ1: ファイル選択 ----
        step1_widget = QWidget()
        step1_layout = QVBoxLayout()

        info_label = QLabel(
            'モバイルPASMO会員メニューサイト (mobile.pasmo.jp) から\n'
            'ダウンロードした「残額ご利用明細」PDFを選択してください。'
        )
        step1_layout.addWidget(info_label)

        file_group = QGroupBox('PDFファイル選択')
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText('PDFファイルを選択してください')
        browse_button = QPushButton('参照...')
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(browse_button)
        file_group.setLayout(file_layout)
        step1_layout.addWidget(file_group)

        next_button1 = QPushButton('解析して次へ')
        next_button1.clicked.connect(self.parse_and_proceed)
        step1_layout.addWidget(next_button1, alignment=Qt.AlignRight)

        step1_widget.setLayout(step1_layout)

        # ---- ステップ2: プレビューと取込 ----
        step2_widget = QWidget()
        step2_layout = QVBoxLayout()

        self.summary_label = QLabel('')
        step2_layout.addWidget(self.summary_label)

        self.preview_table = QTableWidget(0, 4)
        self.preview_table.setHorizontalHeaderLabels(['日付', '区間', '金額', 'カテゴリ'])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        step2_layout.addWidget(self.preview_table)

        # === 取り込みモード選択 ===
        mode_group = QGroupBox('取り込みモード')
        mode_layout = QVBoxLayout()

        # 一括取り込み（デフォルト）
        self.bulk_mode_radio = QCheckBox('一括取り込み（合計金額を1件の交通費として登録）')
        self.bulk_mode_radio.setChecked(True)
        self.bulk_mode_radio.setStyleSheet('font-weight: bold;')
        mode_layout.addWidget(self.bulk_mode_radio)

        # 一括取り込み用の日付選択
        self.bulk_date_layout = QHBoxLayout()
        self.bulk_date_layout.addWidget(QLabel('  取り込み日付:'))
        self.bulk_date_edit = QDateEdit()
        self.bulk_date_edit.setCalendarPopup(True)
        self.bulk_date_edit.setDate(QDate.currentDate())
        self.bulk_date_layout.addWidget(self.bulk_date_edit)
        self.bulk_total_label = QLabel('')
        self.bulk_total_label.setStyleSheet('font-weight: bold; color: #1565C0; margin-left: 10px;')
        self.bulk_date_layout.addWidget(self.bulk_total_label)
        self.bulk_date_layout.addStretch()
        mode_layout.addLayout(self.bulk_date_layout)

        # チェックのON/OFFで個別取り込み設定の表示切替
        self.bulk_mode_radio.toggled.connect(self._toggle_import_mode)

        mode_group.setLayout(mode_layout)
        mode_group.hide()  # 一括モードUIを非表示
        step2_layout.addWidget(mode_group)

        # === 個別取り込み設定（一括モードOFF時に表示） ===
        self.individual_group = QGroupBox('個別取り込み設定')
        individual_layout = QVBoxLayout()

        # 重複チェック
        self.duplicate_check = QCheckBox('取り込み時に重複をチェックする')
        self.duplicate_check.setChecked(True)
        individual_layout.addWidget(self.duplicate_check)

        # 取り込み期間指定
        date_range_layout = QHBoxLayout()
        self.date_range_check = QCheckBox()
        self.date_range_check.setChecked(True)
        date_range_layout.addWidget(self.date_range_check)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-6))
        date_range_layout.addWidget(QLabel('開始日:'))
        date_range_layout.addWidget(self.start_date_edit)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_range_layout.addWidget(QLabel('終了日:'))
        date_range_layout.addWidget(self.end_date_edit)
        individual_layout.addLayout(date_range_layout)

        self.individual_group.setLayout(individual_layout)
        self.individual_group.setVisible(True)   # 常時表示
        step2_layout.addWidget(self.individual_group)

        # 戻る・取り込みボタン
        button_layout = QHBoxLayout()
        back_button = QPushButton('戻る')
        back_button.clicked.connect(lambda: (
            self.step_label.setText('ステップ 1/2: PDFファイルの選択'),
            self.stack.setCurrentIndex(0)
        ))
        self.import_button = QPushButton('取り込み実行')
        self.import_button.clicked.connect(self.execute_import)
        self.import_button.setStyleSheet('background-color: #4CAF50; color: white; font-weight: bold;')
        button_layout.addWidget(back_button)
        button_layout.addStretch()
        button_layout.addWidget(self.import_button)
        step2_layout.addLayout(button_layout)

        step2_widget.setLayout(step2_layout)

        self.stack.addWidget(step1_widget)
        self.stack.addWidget(step2_widget)
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'PASMO PDFファイルを選択', '',
            'PDFファイル (*.pdf);;すべてのファイル (*.*)'
        )
        if file_path:
            self.file_path_input.setText(file_path)

    def _infer_start_year(self, file_path):
        """ファイル名から開始年を推定する"""
        import re
        basename = os.path.basename(file_path)
        # PB80F224032817377_20250104_20260211120230.pdf のようなパターン
        m = re.search(r'_(\d{4})\d{4}_', basename)
        if m:
            return int(m.group(1))
        return QDate.currentDate().year()

    def parse_and_proceed(self):
        """PDFを解析してステップ2に進む"""
        if not self.file_path_input.text():
            QMessageBox.warning(self, '警告', 'PDFファイルを選択してください')
            return

        try:
            import pdfplumber
        except ImportError:
            QMessageBox.critical(
                self, 'エラー',
                'pdfplumber がインストールされていません。\n\n'
                'コマンドプロンプトで以下を実行してください:\n'
                'pip install pdfplumber'
            )
            return

        try:
            self.preview_data = self.parse_pasmo_pdf(self.file_path_input.text())

            if not self.preview_data:
                QMessageBox.warning(self, '警告', '取り込み可能なデータが見つかりませんでした。')
                return

            # プレビューテーブル更新
            self.preview_table.setRowCount(0)
            for row_idx, row_data in enumerate(self.preview_data):
                self.preview_table.insertRow(row_idx)
                self.preview_table.setItem(row_idx, 0, QTableWidgetItem(row_data['date']))
                self.preview_table.setItem(row_idx, 1, QTableWidgetItem(row_data['description'].replace('PASMO: ', '')))
                self.preview_table.setItem(row_idx, 2, QTableWidgetItem(f"¥{row_data['amount']:,.0f}"))

                # カテゴリはComboBoxで編集可能に
                category_combo = QComboBox()
                categories = ['交通費', '食費', '娯楽', 'その他', '住宅',
                              '水道光熱費', '美容', '通信費', '日用品', '健康', '教育']
                category_combo.addItems(categories)
                category_combo.setCurrentText(row_data['category'])
                category_combo.currentTextChanged.connect(
                    lambda text, idx=row_idx: self._update_category(idx, text)
                )
                self.preview_table.setCellWidget(row_idx, 3, category_combo)

            # 期間を先月全体（1日〜末日）に自動設定
            today = QDate.currentDate()
            first_of_this_month = QDate(today.year(), today.month(), 1)
            last_month_end = first_of_this_month.addDays(-1)
            last_month_start = QDate(last_month_end.year(), last_month_end.month(), 1)
            self.start_date_edit.setDate(last_month_start)
            self.end_date_edit.setDate(last_month_end)

            total = len(self.preview_data)
            total_amount = sum(d['amount'] for d in self.preview_data)
            self.summary_label.setText(
                f'解析結果: {total}件の交通利用 (合計 ¥{total_amount:,.0f})'
            )
            self.bulk_total_label.setText(f'合計: ¥{total_amount:,.0f}（{total}件分）')

            self.step_label.setText('ステップ 2/2: プレビューと取り込み実行')
            self.stack.setCurrentIndex(1)

        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'PDF解析に失敗しました:\n{str(e)}')

    def _toggle_import_mode(self, bulk_checked):
        """一括/個別モードの切り替え"""
        self.individual_group.setVisible(not bulk_checked)

    def _update_category(self, row_idx, text):
        """プレビューデータのカテゴリを更新"""
        if row_idx < len(self.preview_data):
            self.preview_data[row_idx]['category'] = text

    def parse_pasmo_pdf(self, file_path):
        """PASMO PDFを解析してデータリストを返す"""
        import pdfplumber
        import re

        start_year = self._infer_start_year(file_path)
        results = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split('\n')
                prev_month = None

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # データ行: "MM DD 種別 ..." のパターン
                    m = re.match(r'^(\d{2})\s+(\d{2})\s+(.+)$', line)
                    if not m:
                        continue

                    month = int(m.group(1))
                    day = int(m.group(2))
                    rest = m.group(3)

                    # 年の推定: 月が前の行より小さくなったら年を+1
                    if prev_month is not None and month < prev_month:
                        start_year += 1
                    prev_month = month

                    # 種別を判定
                    # 繰越行: "繰 ..."
                    if rest.startswith('繰'):
                        continue

                    # チャージ行: "ｶｰﾄﾞ ..." (差額が正)
                    if rest.startswith('ｶｰﾄﾞ'):
                        continue

                    # 鉄道利用行: "入 {駅名} 出 {駅名} \金額 差額"
                    # または: "定 {駅名} 出 {駅名} \金額 差額"
                    ride_match = re.match(
                        r'^(入|定)\s+(.+?)\s+出\s+(.+?)\s+\\[\\\d,.]+\s+([+-][\d,]+)$',
                        rest
                    )
                    if ride_match:
                        ride_type = ride_match.group(1)
                        station_from = ride_match.group(2).strip()
                        station_to = ride_match.group(3).strip()
                        diff_str = ride_match.group(4).replace(',', '')
                        diff = int(diff_str)

                        if diff >= 0:
                            continue  # 正の差額はチャージ等なのでスキップ

                        amount = abs(diff)
                        date_str = f'{start_year}-{month:02d}-{day:02d}'

                        # 「地　渋谷」→「渋谷(地下鉄)」のように整形
                        station_from = self._clean_station_name(station_from)
                        station_to = self._clean_station_name(station_to)

                        description = f'PASMO: {station_from} → {station_to}'
                        category = '交通費'

                        results.append({
                            'date': date_str,
                            'amount': amount,
                            'description': description,
                            'category': category
                        })

        return results

    def _clean_station_name(self, name):
        """駅名を整形する（地　渋谷 → 渋谷 など）"""
        import re
        # 「地　渋谷」「地 渋谷」→「渋谷」（地下鉄プレフィックス除去）
        m = re.match(r'^地[\s　]+(.+)$', name)
        if m:
            return m.group(1)
        # 「東武　柏」→「東武 柏」（全角スペースをスペースに）
        name = name.replace('\u3000', ' ')
        return name

    def execute_import(self):
        """取り込みを実行"""
        self._execute_individual_import()

    def _execute_bulk_import(self):
        """一括取り込み: 合計金額を1件の交通費として登録"""
        total_amount = sum(d['amount'] for d in self.preview_data)
        chosen_date = self.bulk_date_edit.date().toString('yyyy-MM-dd')
        record_count = len(self.preview_data)

        # 期間を説明に含める
        dates = sorted([d['date'] for d in self.preview_data])
        period = f'{dates[0]} ~ {dates[-1]}' if dates else ''
        description = f'PASMO交通費({period}、{record_count}件)'

        reply = QMessageBox.question(
            self, '確認',
            f'以下の内容で取り込みます:\n\n'
            f'  日付: {chosen_date}\n'
            f'  カテゴリ: 交通費\n'
            f'  金額: ¥{total_amount:,.0f}\n'
            f'  説明: {description}\n\n'
            f'よろしいですか？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 接続はtryの外で開き、finallyで必ず閉じる（閉じ忘れ防止）
        conn = sqlite3.connect('budget.db')
        try:
            c = conn.cursor()

            c.execute('''
                INSERT INTO expenses (date, category, amount, description)
                VALUES (?, ?, ?, ?)
            ''', (chosen_date, '交通費', total_amount, description))

            # インポート履歴を記録
            import_date = QDate.currentDate().toString('yyyy-MM-dd')
            file_name = os.path.basename(self.file_path_input.text())
            c.execute('''
                INSERT INTO credit_card_imports
                (import_date, file_name, format_name, record_count)
                VALUES (?, ?, ?, ?)
            ''', (import_date, file_name, 'モバイルPASMO(一括)', 1))

            # 支出と履歴の両方が成功したときだけ確定する
            conn.commit()

            QMessageBox.information(
                self, '取り込み完了',
                f'PASMO交通費 ¥{total_amount:,.0f} を {chosen_date} として取り込みました。'
            )
            self.accept()

        except Exception as e:
            conn.rollback()  # 途中まで書き込んだ分を取り消す
            QMessageBox.critical(self, 'エラー', f'取り込み処理に失敗しました:\n{str(e)}')
        finally:
            conn.close()     # 成功・失敗にかかわらず必ず接続を閉じる

    def _execute_individual_import(self):
        """個別取り込み: 各明細を個別に登録"""
        filtered_data = self.preview_data
        if self.date_range_check.isChecked():
            start_date = self.start_date_edit.date().toString('yyyy-MM-dd')
            end_date = self.end_date_edit.date().toString('yyyy-MM-dd')
            filtered_data = [
                d for d in self.preview_data
                if start_date <= d['date'] <= end_date
            ]

        total_records = len(filtered_data)
        if total_records == 0:
            QMessageBox.warning(self, '警告', '取り込むデータがありません')
            return

        reply = QMessageBox.question(
            self, '確認',
            f'{total_records}件のPASMO明細を取り込みます。よろしいですか？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 接続はtryの外で開き、finallyで必ず閉じる（閉じ忘れ防止）
        conn = sqlite3.connect('budget.db')
        try:
            c = conn.cursor()
            imported_count = 0
            duplicate_count = 0

            for item in filtered_data:
                date = item['date']
                category = item['category']
                amount = item['amount']
                description = item['description']

                # 重複チェック
                if self.duplicate_check.isChecked():
                    c.execute('''
                        SELECT id FROM expenses
                        WHERE date = ? AND category = ? AND amount = ? AND description = ?
                    ''', (date, category, amount, description))
                    if c.fetchone():
                        duplicate_count += 1
                        continue

                c.execute('''
                    INSERT INTO expenses (date, category, amount, description)
                    VALUES (?, ?, ?, ?)
                ''', (date, category, amount, description))
                imported_count += 1

            conn.commit()

            # インポート履歴を記録
            import_date = QDate.currentDate().toString('yyyy-MM-dd')
            file_name = os.path.basename(self.file_path_input.text())
            c.execute('''
                INSERT INTO credit_card_imports
                (import_date, file_name, format_name, record_count)
                VALUES (?, ?, ?, ?)
            ''', (import_date, file_name, 'モバイルPASMO', imported_count))
            conn.commit()

            if duplicate_count > 0:
                QMessageBox.information(
                    self, '重複スキップ',
                    f'{duplicate_count}件の重複データはスキップされました。'
                )

            QMessageBox.information(
                self, '取り込み完了',
                f'{imported_count}件のPASMO明細を取り込みました。'
            )
            self.accept()

        except Exception as e:
            conn.rollback()  # 途中まで書き込んだ分を取り消す
            QMessageBox.critical(self, 'エラー', f'取り込み処理に失敗しました:\n{str(e)}')
        finally:
            conn.close()     # 成功・失敗にかかわらず必ず接続を閉じる
