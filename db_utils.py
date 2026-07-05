# -*- coding: utf-8 -*-
"""データベース操作の共通関数

全画面から使われるDB接続・クエリ実行のヘルパー。"""
import sqlite3
import pandas as pd


# データベースユーティリティ関数
def get_db_connection():
    """データベース接続を取得"""
    return sqlite3.connect('budget.db')


def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    """SQLクエリを実行し、必要に応じて結果を取得

    try/finally で囲むことで、SQL実行中にエラーが起きても
    必ず rollback（書きかけの変更を取り消し）と close（接続を閉じる）が
    行われる。閉じ忘れた接続はDBのロックを握り続け、
    後続の操作が「database is locked」で失敗する原因になる。
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute(query, params)

        result = None
        if fetch_one:
            result = c.fetchone()
        elif fetch_all:
            result = c.fetchall()

        conn.commit()
        return result
    except Exception:
        conn.rollback()  # 途中まで実行した変更をなかったことにする
        raise            # エラー自体は呼び出し側にそのまま伝える（既存のexcept処理を活かすため）
    finally:
        conn.close()     # 成功・失敗にかかわらず必ず接続を閉じる


def get_categories():
    """DBからカテゴリ名リストを取得（sort_order順）"""
    result = execute_query('SELECT name FROM categories ORDER BY sort_order', fetch_all=True)
    if result:
        return [row[0] for row in result]
    return ['食費', '交通費', '娯楽', 'その他', '住宅', '水道光熱費', '美容', '通信費', '日用品', '健康', '教育']


def execute_many(query, param_list):
    """複数のクエリを一括実行（エラー時はrollback、接続は必ず閉じる）"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.executemany(query, param_list)
        conn.commit()
    except Exception:
        conn.rollback()  # 一括実行の途中で失敗したら全部取り消す（半端な取込を防ぐ）
        raise
    finally:
        conn.close()


def fetch_df(query, params=()):
    """SQLクエリを実行し、結果をPandasのDataFrameとして取得（接続は必ず閉じる）"""
    conn = get_db_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()  # 読み取り専用なのでrollback不要だが、closeは必ず行う
