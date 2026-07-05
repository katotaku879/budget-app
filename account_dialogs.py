# -*- coding: utf-8 -*-
"""口座関連ダイアログ

口座の追加・編集・残高一括更新。資産管理画面から呼ばれる。"""
from PyQt5.QtWidgets import (
    QDialog,
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
    QFormLayout
)
from PyQt5.QtCore import QDate
import sqlite3


class AddAccountDialog(QDialog):
    """口座追加ダイアログ"""
    
    def __init__(self, account_type=None, parent=None):
        super().__init__(parent)
        self.account_type = account_type
        self.setWindowTitle('口座追加')
        self.setMinimumWidth(400)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # 種別選択
        self.type_combo = QComboBox()
        self.type_combo.addItems(['銀行', '証券'])
        if self.account_type == 'bank':
            self.type_combo.setCurrentText('銀行')
        elif self.account_type == 'securities':
            self.type_combo.setCurrentText('証券')
        
        form_layout.addRow('種別:', self.type_combo)
        
        # 口座名
        self.account_name_input = QLineEdit()
        self.account_name_input.setPlaceholderText('例: 三菱UFJ銀行、SBI証券')
        form_layout.addRow('口座名:', self.account_name_input)
        
        # 残高/評価額
        self.balance_input = QLineEdit()
        self.balance_input.setPlaceholderText('例: 1000000')
        form_layout.addRow('残高/評価額 (円):', self.balance_input)
        
        # 備考
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText('例: 普通預金、NISA口座')
        form_layout.addRow('備考:', self.notes_input)
        
        layout.addLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        save_button = QPushButton('保存')
        save_button.clicked.connect(self.save_account)
        
        cancel_button = QPushButton('キャンセル')
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_account(self):
        """口座を保存"""
        try:
            account_type_text = self.type_combo.currentText()
            account_type = 'bank' if account_type_text == '銀行' else 'securities'
            
            account_name = self.account_name_input.text().strip()
            if not account_name:
                raise ValueError("口座名を入力してください")
            
            balance_text = self.balance_input.text().strip().replace(',', '')
            if not balance_text:
                raise ValueError("残高を入力してください")
            
            balance = float(balance_text)
            if balance < 0:
                raise ValueError("残高は0以上の値を入力してください")
            
            notes = self.notes_input.text().strip()
            
            today = QDate.currentDate().toString('yyyy-MM-dd')
            
            conn = sqlite3.connect('budget.db')
            try:
                c = conn.cursor()

                # 資産データ挿入
                c.execute('''
                    INSERT INTO assets (account_type, account_name, balance, last_updated, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (account_type, account_name, balance, today, notes))

                asset_id = c.lastrowid

                # 履歴データも記録
                c.execute('''
                    INSERT INTO asset_history (asset_id, record_date, balance)
                    VALUES (?, ?, ?)
                ''', (asset_id, today, balance))

                # 口座と履歴の両方が成功したときだけ確定する
                conn.commit()
            except Exception:
                conn.rollback()  # 口座だけ登録され履歴が無い中途半端な状態を防ぐ
                raise            # 下のexceptでユーザーに通知する
            finally:
                conn.close()     # 必ず接続を閉じる

            QMessageBox.information(self, '成功', '口座を追加しました')
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, '入力エラー', str(e))
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'保存中にエラーが発生しました: {str(e)}')


class EditAccountDialog(QDialog):
    """口座編集ダイアログ"""
    
    def __init__(self, asset_id, parent=None):
        super().__init__(parent)
        self.asset_id = asset_id
        self.setWindowTitle('口座編集')
        self.setMinimumWidth(400)
        self.initUI()
        self.load_data()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # 口座名
        self.account_name_input = QLineEdit()
        form_layout.addRow('口座名:', self.account_name_input)
        
        # 残高/評価額
        self.balance_input = QLineEdit()
        form_layout.addRow('残高/評価額 (円):', self.balance_input)
        
        # 備考
        self.notes_input = QLineEdit()
        form_layout.addRow('備考:', self.notes_input)
        
        layout.addLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        save_button = QPushButton('保存')
        save_button.clicked.connect(self.save_changes)
        
        cancel_button = QPushButton('キャンセル')
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        """データを読み込む"""
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT account_name, balance, notes
            FROM assets
            WHERE id = ?
        ''', (self.asset_id,))
        
        result = c.fetchone()
        conn.close()
        
        if result:
            account_name, balance, notes = result
            self.account_name_input.setText(account_name)
            self.balance_input.setText(str(balance))
            self.notes_input.setText(notes or '')
    
    def save_changes(self):
        """変更を保存"""
        try:
            account_name = self.account_name_input.text().strip()
            if not account_name:
                raise ValueError("口座名を入力してください")
            
            balance_text = self.balance_input.text().strip().replace(',', '')
            if not balance_text:
                raise ValueError("残高を入力してください")
            
            balance = float(balance_text)
            if balance < 0:
                raise ValueError("残高は0以上の値を入力してください")
            
            notes = self.notes_input.text().strip()
            
            today = QDate.currentDate().toString('yyyy-MM-dd')
            
            conn = sqlite3.connect('budget.db')
            try:
                c = conn.cursor()

                # 資産データ更新
                c.execute('''
                    UPDATE assets
                    SET account_name = ?, balance = ?, last_updated = ?, notes = ?
                    WHERE id = ?
                ''', (account_name, balance, today, notes, self.asset_id))

                # 履歴データを記録
                c.execute('''
                    INSERT INTO asset_history (asset_id, record_date, balance)
                    VALUES (?, ?, ?)
                ''', (self.asset_id, today, balance))

                # 更新と履歴の両方が成功したときだけ確定する
                conn.commit()
            except Exception:
                conn.rollback()  # 中途半端な更新を防ぐ
                raise            # 下のexceptでユーザーに通知する
            finally:
                conn.close()     # 必ず接続を閉じる

            QMessageBox.information(self, '成功', '口座情報を更新しました')
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, '入力エラー', str(e))
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'保存中にエラーが発生しました: {str(e)}')


class UpdateBalanceDialog(QDialog):
    """残高一括更新ダイアログ"""
    
    def __init__(self, account_type, parent=None):
        super().__init__(parent)
        self.account_type = account_type
        type_name = '銀行' if account_type == 'bank' else '証券'
        self.setWindowTitle(f'{type_name}口座残高更新')
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # 説明
        type_name = '銀行' if self.account_type == 'bank' else '証券'
        info_label = QLabel(f'<b>{type_name}口座の残高を一括で更新します</b>')
        layout.addWidget(info_label)
        
        # 口座リストテーブル
        self.accounts_table = QTableWidget(0, 4)
        self.accounts_table.setHorizontalHeaderLabels([
            '口座名', '現在の残高', '新しい残高', 'ID'
        ])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.accounts_table.setColumnHidden(3, True)  # IDを非表示
        
        layout.addWidget(self.accounts_table)
        
        # データ読み込み
        self.load_accounts()
        
        # ボタン
        button_layout = QHBoxLayout()
        
        save_button = QPushButton('一括更新')
        save_button.clicked.connect(self.save_balances)
        
        cancel_button = QPushButton('キャンセル')
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_accounts(self):
        """口座データを読み込む"""
        conn = sqlite3.connect('budget.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT id, account_name, balance
            FROM assets
            WHERE account_type = ?
            ORDER BY account_name
        ''', (self.account_type,))
        
        accounts = c.fetchall()
        conn.close()
        
        self.accounts_table.setRowCount(len(accounts))
        
        for row, (asset_id, account_name, balance) in enumerate(accounts):
            self.accounts_table.setItem(row, 0, QTableWidgetItem(account_name))
            self.accounts_table.setItem(row, 1, QTableWidgetItem(f"{balance:,.0f}円"))
            
            # 新しい残高入力欄
            new_balance_input = QLineEdit()
            new_balance_input.setText(str(balance))
            new_balance_input.setPlaceholderText('新しい残高')
            self.accounts_table.setCellWidget(row, 2, new_balance_input)
            
            # IDを保存
            self.accounts_table.setItem(row, 3, QTableWidgetItem(str(asset_id)))
    
    def save_balances(self):
        """残高を一括保存"""
        try:
            today = QDate.currentDate().toString('yyyy-MM-dd')
            updates = []
            
            for row in range(self.accounts_table.rowCount()):
                asset_id = int(self.accounts_table.item(row, 3).text())
                new_balance_input = self.accounts_table.cellWidget(row, 2)
                new_balance_text = new_balance_input.text().strip().replace(',', '')
                
                if new_balance_text:
                    new_balance = float(new_balance_text)
                    updates.append((asset_id, new_balance))
            
            if not updates:
                QMessageBox.warning(self, '警告', '更新する残高を入力してください')
                return
            
            conn = sqlite3.connect('budget.db')
            try:
                c = conn.cursor()

                for asset_id, new_balance in updates:
                    # 資産データ更新
                    c.execute('''
                        UPDATE assets
                        SET balance = ?, last_updated = ?
                        WHERE id = ?
                    ''', (new_balance, today, asset_id))

                    # 履歴データ記録
                    c.execute('''
                        INSERT INTO asset_history (asset_id, record_date, balance)
                        VALUES (?, ?, ?)
                    ''', (asset_id, today, new_balance))

                # 全口座の更新が成功したときだけ確定する
                conn.commit()
            except Exception:
                conn.rollback()  # 一部の口座だけ更新された中途半端な状態を防ぐ
                raise            # 下のexceptでユーザーに通知する
            finally:
                conn.close()     # 必ず接続を閉じる

            type_name = '銀行' if self.account_type == 'bank' else '証券'
            QMessageBox.information(self, '成功', f'{len(updates)}件の{type_name}口座を更新しました')
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, '入力エラー', '正しい数値を入力してください')
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'更新中にエラーが発生しました: {str(e)}')                                
