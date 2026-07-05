# -*- coding: utf-8 -*-
"""バックアップ機能

SQLite backup APIによる安全なバックアップ作成・検証付き復元と設定/管理ダイアログ。"""
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QMessageBox,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox,
    QDateEdit, QCalendarWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QFrame,
    QScrollArea, QStackedWidget, QTabWidget, QListWidget, QListWidgetItem,
    QAction, QFileDialog, QDialogButtonBox, QProgressBar, QProgressDialog,
    QSizePolicy, QSpacerItem, QInputDialog
)
from PyQt5.QtCore import Qt, QDate, QMargins, QPointF
from PyQt5.QtGui import QFont, QColor, QPen, QBrush
import sqlite3
import os
from datetime import datetime


class BackupManager:
    def __init__(self, db_path='budget.db', backup_dir='backups'):
        """バックアップマネージャークラスの初期化"""
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        # バックアップディレクトリが存在しない場合は作成
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
    
    def _copy_database(self, source_path, dest_path):
        """SQLiteの公式バックアップ機能でデータベースを安全にコピーする

        以前は shutil.copy2（ただのファイルコピー）を使っていたが、
        アプリがDBに書き込んでいる最中にコピーすると壊れたコピーが
        できる恐れがあった。SQLiteのbackup APIは書き込みの区切りを
        見ながらコピーするので、いつ実行しても必ず正常なコピーになる。
        """
        src = sqlite3.connect(source_path)   # コピー元のDBを開く
        dst = sqlite3.connect(dest_path)     # コピー先のDBを作る（無ければ新規作成）
        try:
            src.backup(dst)                  # SQLiteが安全にコピーしてくれる
        finally:
            # 成功・失敗にかかわらず必ず接続を閉じる
            dst.close()
            src.close()

    def _validate_backup_file(self, backup_path):
        """復元前にバックアップファイルが正常か検査する

        壊れたファイルや空のファイルで本体DBを上書きしてしまうと
        全データを失うため、復元処理の前に必ずこの検査を通す。
        問題があれば Exception を投げて復元を中止する（本体DBには触らない）。
        """
        # 検査1: ファイルが存在して中身があるか
        if not os.path.exists(backup_path):
            raise Exception("バックアップファイルが見つかりません")
        if os.path.getsize(backup_path) == 0:
            raise Exception("バックアップファイルが空です。このファイルからは復元できません")

        try:
            # 検査2: 読み取り専用モードで開く（mode=ro は read only の意味。
            # 検査のつもりでファイルを変更してしまう事故を防ぐ）
            conn = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True)
            try:
                c = conn.cursor()

                # 検査3: SQLite自身にファイルの整合性をチェックしてもらう
                # 正常なら 'ok' という1行だけが返ってくる
                result = c.execute("PRAGMA integrity_check").fetchone()
                if result is None or result[0] != "ok":
                    raise Exception("バックアップファイルが破損しています")

                # 検査4: 家計簿アプリのDBかどうか（expensesテーブルの有無）を確認
                c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'"
                )
                if c.fetchone() is None:
                    raise Exception("このファイルは家計簿アプリのバックアップではありません（expensesテーブルがありません）")
            finally:
                conn.close()
        except sqlite3.DatabaseError:
            # SQLiteとして開けない = データベースファイルではない
            raise Exception("このファイルはデータベースファイルではないため復元できません")

    def create_backup(self, custom_name=None):
        """データベースのバックアップを作成"""
        try:
            # バックアップファイル名の生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if custom_name:
                backup_name = f"{custom_name}_{timestamp}.db"
            else:
                backup_name = f"budget_backup_{timestamp}.db"

            backup_path = os.path.join(self.backup_dir, backup_name)

            # SQLiteの安全なコピー機能でバックアップを作成
            self._copy_database(self.db_path, backup_path)

            return backup_path
        except Exception as e:
            raise Exception(f"バックアップの作成に失敗しました: {str(e)}")

    def restore_backup(self, backup_path):
        """バックアップからデータベースを復元"""
        # 復元前にバックアップファイルを検査する。
        # 壊れたファイルならここで例外になり、本体DBは一切変更されない
        self._validate_backup_file(backup_path)

        try:
            # 現在のデータベースの自動バックアップを作成
            auto_backup_name = f"auto_backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            auto_backup_path = os.path.join(self.backup_dir, auto_backup_name)

            # 現在のDBをバックアップ（万一のとき元に戻せるように）
            self._copy_database(self.db_path, auto_backup_path)

            # バックアップから復元
            self._copy_database(backup_path, self.db_path)

            return True
        except Exception as e:
            raise Exception(f"復元に失敗しました: {str(e)}")
    
    def get_all_backups(self):
        """利用可能なすべてのバックアップを取得"""
        backups = []
        
        for file in os.listdir(self.backup_dir):
            if file.endswith('.db'):
                file_path = os.path.join(self.backup_dir, file)
                file_stat = os.stat(file_path)
                
                backups.append({
                    'name': file,
                    'path': file_path,
                    'size': file_stat.st_size,
                    'date': datetime.fromtimestamp(file_stat.st_mtime)
                })
        
        # 日付の新しい順にソート
        backups.sort(key=lambda x: x['date'], reverse=True)
        
        return backups
    
    def delete_backup(self, backup_path):
        """バックアップファイルを削除"""
        try:
            os.remove(backup_path)
            return True
        except Exception as e:
            raise Exception(f"バックアップの削除に失敗しました: {str(e)}")
    
    def auto_backup(self, max_backups=5):
        """自動バックアップを実行し、古いバックアップを削除"""
        try:
            # 新しいバックアップを作成
            backup_path = self.create_backup("auto")
            
            # バックアップリストを取得
            backups = self.get_all_backups()
            
            # 自動バックアップだけをフィルタリング
            auto_backups = [b for b in backups if b['name'].startswith('auto_')]
            
            # 最大数を超える古いバックアップを削除
            if len(auto_backups) > max_backups:
                for backup in auto_backups[max_backups:]:
                    self.delete_backup(backup['path'])
            
            return backup_path
        except Exception as e:
            raise Exception(f"自動バックアップに失敗しました: {str(e)}")


# バックアップ設定ダイアログ
class BackupSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("バックアップ設定")
        self.setMinimumWidth(400)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 自動バックアップの設定
        self.auto_backup_check = QCheckBox("アプリ起動時に自動バックアップを作成")
        layout.addWidget(self.auto_backup_check)
        
        # 保持するバックアップ数
        backup_count_layout = QHBoxLayout()
        backup_count_layout.addWidget(QLabel("保持する自動バックアップの数:"))
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 50)
        self.backup_count_spin.setValue(5)
        backup_count_layout.addWidget(self.backup_count_spin)
        
        layout.addLayout(backup_count_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """設定を読み込む"""
        # ここでは簡易的に実装。実際はファイルから読み込むなど
        # QSettingsなどを使うとよい
        self.auto_backup_check.setChecked(True)
        self.backup_count_spin.setValue(5)
    
    def save_settings(self):
        """設定を保存"""
        # 設定を保存する処理（実際のアプリケーション用に実装必要）
        self.accept()


# バックアップ管理ダイアログ
class BackupManagerDialog(QDialog):
    def __init__(self, backup_manager, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        self.setWindowTitle("バックアップ管理")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self.init_ui()
        self.load_backups()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # バックアップリスト
        self.backup_list = QListWidget()
        layout.addWidget(QLabel("利用可能なバックアップ:"))
        layout.addWidget(self.backup_list)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        
        self.create_button = QPushButton("新規バックアップ")
        self.create_button.clicked.connect(self.create_backup)
        
        self.restore_button = QPushButton("選択したバックアップから復元")
        self.restore_button.clicked.connect(self.restore_backup)
        
        self.delete_button = QPushButton("選択したバックアップを削除")
        self.delete_button.clicked.connect(self.delete_backup)
        
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.restore_button)
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
        
        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
    
    def load_backups(self):
        """バックアップリストを読み込む"""
        self.backup_list.clear()
        
        backups = self.backup_manager.get_all_backups()
        
        for backup in backups:
            size_mb = backup['size'] / (1024 * 1024)
            item_text = f"{backup['name']} - {backup['date'].strftime('%Y-%m-%d %H:%M:%S')} ({size_mb:.2f} MB)"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, backup['path'])
            self.backup_list.addItem(item)
    
    def create_backup(self):
        """新規バックアップを作成"""
        try:
            custom_name, ok = QFileDialog.getSaveFileName(
                self, "バックアップ名を入力", 
                f"budget_backup_{datetime.now().strftime('%Y%m%d')}",
                "データベースバックアップ (*.db)"
            )
            
            if not ok or not custom_name:
                return
                
            # ファイル名のみを取得（パスなし）
            custom_name = os.path.basename(custom_name)
            # 拡張子を削除
            custom_name = os.path.splitext(custom_name)[0]
            
            backup_path = self.backup_manager.create_backup(custom_name)
            QMessageBox.information(self, "成功", f"バックアップが正常に作成されました。\n{backup_path}")
            
            self.load_backups()
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))
    
    def restore_backup(self):
        """選択したバックアップから復元"""
        selected_items = self.backup_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "復元するバックアップを選択してください。")
            return
            
        backup_path = selected_items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "確認", 
            "選択したバックアップから復元します。\n"
            "現在のデータはすべて上書きされます。\n"
            "続行しますか？",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            self.backup_manager.restore_backup(backup_path)
            QMessageBox.information(
                self, "成功", 
                "バックアップから正常に復元されました。\n"
                "アプリケーションを再起動して変更を反映してください。"
            )
            
            # アプリケーションを終了
            self.accept()
            if self.parent():
                self.parent().close()
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))
    
    def delete_backup(self):
        """選択したバックアップを削除"""
        selected_items = self.backup_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "削除するバックアップを選択してください。")
            return
            
        backup_path = selected_items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "確認", 
            "選択したバックアップを削除します。\n"
            "この操作は元に戻せません。\n"
            "続行しますか？",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            self.backup_manager.delete_backup(backup_path)
            QMessageBox.information(self, "成功", "バックアップが正常に削除されました。")
            
            self.load_backups()
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))        
