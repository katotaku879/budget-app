#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天カードCSVを家計簿アプリに自動インポートするCLIツール
"""
import sys
import sqlite3
import pandas as pd
from datetime import datetime
import os

def classify_category(store_name):
    """店舗名からカテゴリを自動判定"""
    # カテゴリ分類ルール
    rules = {
        # 食費
        'マルエツ': '食費',
        'カ)マルエツ': '食費',
        'イオン': '食費',
        'イオンモール': '食費',
        'セブン': '食費',
        'ローソン': '食費',
        'ファミ': '食費',
        'スーパー': '食費',
        'マクドナルド': '食費',
        'スタバ': '食費',
        'ドトール': '食費',
        
        
        # 交通費
        '電車': '交通費',
        'バス': '交通費',
        '定期': '交通費',
        
        # 娯楽
        'CLAUDE': '娯楽',
        'APPLE': '娯楽',
        'NETFLIX': '娯楽',
        'AMAZON': '娯楽',
        'SPOTIFY': '娯楽',
        
        # 日用品
        'ドラッグ': '日用品',
        'マツキヨ': '日用品',
        'ココカラ': '日用品',
        'ウェルシア': '日用品',
        
        # 住宅
        '家賃': '住宅',
        '不動産': '住宅',
        
        # 水道光熱費
        '電気': '水道光熱費',
        'ガス': '水道光熱費',
        '水道': '水道光熱費',
        '東京': '水道光熱費',
        
        
        # 通信費
        'ソフトバンク': '通信費',
        'オプテージ': '通信費',
        'Wi-Fi': '通信費',
        '携帯': '通信費',

        
        # 美容
        '美容': '美容',
        '理容': '美容',
        'サロン': '美容',
        'ララルー': '美容',
        'スクエア': '美容',
        
        # 健康
        '病院': '健康',
        'クリニック': '健康',
        '薬局': '健康',
        'ジム': '健康',
        'トウエンティーフォージム': '健康',
        
        # その他
        '楽天証券': 'その他',
        'E-ビーシーマート': 'その他',
        'ドン キホーテ': 'その他',
    }
    
    # 店舗名に含まれるキーワードでマッチング
    for keyword, category in rules.items():
        if keyword.upper() in store_name.upper():
            return category
    
    return 'その他'

def import_rakuten_csv(csv_path, db_path='budget.db'):
    """楽天カードCSVをインポート"""
    
    if not os.path.exists(csv_path):
        print(f"❌ エラー: ファイルが見つかりません: {csv_path}")
        return False
    
    try:
        # CSVを読み込み（楽天カードの形式）
        # UTF-8 BOM付きで読み込み
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        
        print(f"📄 CSVファイル読み込み: {len(df)}件")
        print(f"   カラム: {df.columns.tolist()}")
        
        # 必要な列を抽出
        # 列名: 利用日, 利用店名・商品名, 利用金額
        df = df[['利用日', '利用店名・商品名', '利用金額']]
        df.columns = ['date', 'store', 'amount']
        
        # データクレンジング
        df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d', errors='coerce')
        df = df.dropna(subset=['date'])  # 日付が無効な行を削除
        
        # 金額をカンマ除去して数値に変換
        if df['amount'].dtype == 'object':
            df['amount'] = df['amount'].astype(str).str.replace(',', '').astype(float)
        
        # カテゴリ自動分類
        df['category'] = df['store'].apply(classify_category)
        
        # データベースに挿入
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        inserted_count = 0
        duplicate_count = 0
        
        for _, row in df.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d')
            store = row['store']
            amount = row['amount']
            category = row['category']
            
            # 重複チェック（同じ日付・店舗・金額の組み合わせ）
            cursor.execute('''
                SELECT COUNT(*) FROM expenses 
                WHERE date=? AND description LIKE ? AND amount=?
            ''', (date_str, f"%{store}%", amount))
            
            if cursor.fetchone()[0] == 0:
                # 新規レコードを挿入
                cursor.execute('''
                    INSERT INTO expenses (date, category, amount, description)
                    VALUES (?, ?, ?, ?)
                ''', (
                    date_str,
                    category,
                    amount,
                    f"クレジットカード: {store}"
                ))
                inserted_count += 1
            else:
                duplicate_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ インポート完了!")
        print(f"   新規登録: {inserted_count}件")
        print(f"   重複スキップ: {duplicate_count}件")
        
        # カテゴリ別集計を表示
        if inserted_count > 0:
            print(f"\n📊 カテゴリ別登録件数:")
            category_counts = df.groupby('category').size().to_dict()
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   {cat}: {count}件")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python cli_import.py <CSVファイルパス> [データベースパス]")
        print("例: python cli_import.py enavi202510.csv")
        print("例: python cli_import.py enavi202510.csv budget.db")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else 'budget.db'
    
    success = import_rakuten_csv(csv_path, db_path)
    
    sys.exit(0 if success else 1)