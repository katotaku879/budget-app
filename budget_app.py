# -*- coding: utf-8 -*-
"""家計簿アプリ 起動用エントリポイント

アプリ本体は main_window.py の BudgetApp クラス。
各画面・ダイアログは機能ごとに別ファイルへ分割されている:
  db_utils.py               … DB操作の共通関数
  common.py                 … 日付ヘルパー・基底ウィジェット・共用ダイアログ
  main_window.py            … メインウィンドウ（画面の生成・切替）
  income_expense.py         … 入出金管理画面（メイン画面）
  breakdown.py              … 内訳画面（円グラフ）
  monthly_report.py         … 月次レポート画面
  goal_management.py        … 目標管理画面
  diagnostic_report.py      … 家計診断レポート画面
  comprehensive_analysis.py … 全データ分析画面
  asset_management.py       … 資産管理画面
  account_dialogs.py        … 口座の追加・編集・残高更新ダイアログ
  credit_card_import.py     … クレジットカード明細取込
  pasmo_import.py           … PASMO明細取込（PDF解析）
  category_management.py    … カテゴリ管理ダイアログ
  backup.py                 … バックアップ作成・復元
"""
import sys

from PyQt5.QtWidgets import QApplication

from main_window import BudgetApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BudgetApp()
    window.show()
    sys.exit(app.exec_())
