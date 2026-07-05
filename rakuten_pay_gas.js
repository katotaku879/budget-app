// ============================================================
// 楽天PAY メール自動抽出 Google Apps Script
// ============================================================
// 使い方:
// 1. Googleスプレッドシートを新規作成
// 2. 拡張機能 > Apps Script を開く
// 3. このコードを貼り付けて保存
// 4. extractRakutenPayEmails を手動実行（初回は権限承認が必要）
// 5. createDailyTrigger を実行して毎日自動実行を設定
// 6. データが溜まったら ファイル > ダウンロード > CSV で家計簿アプリに取込
// ============================================================

var CONFIG = {
  GMAIL_QUERY: 'from:no-reply@pay.rakuten.co.jp subject:楽天ペイ',
  PROCESSED_LABEL: '楽天PAY処理済み',
  SHEET_NAME: '楽天PAY明細',
  HEADERS: ['日付', '店舗名', '金額'],
  MAX_THREADS: 50
};

// ============================================================
// メイン処理: 楽天PAYメールを抽出してスプレッドシートに記録
// ============================================================
function extractRakutenPayEmails() {
  // 処理済みラベルを取得または作成
  var label = getOrCreateLabel(CONFIG.PROCESSED_LABEL);

  // 未処理のメールを検索
  var query = CONFIG.GMAIL_QUERY + ' -label:' + CONFIG.PROCESSED_LABEL;
  var threads = GmailApp.search(query, 0, CONFIG.MAX_THREADS);

  if (threads.length === 0) {
    Logger.log('新しい楽天PAYメールはありません');
    return;
  }

  // スプレッドシートのシートを取得または作成
  var sheet = getOrCreateSheet();

  // 各メールを処理（パース成功したスレッドのみ追跡）
  var newRecords = [];
  var successThreads = [];

  for (var i = 0; i < threads.length; i++) {
    var messages = threads[i].getMessages();
    var threadRecords = [];
    var allParsed = true;

    for (var j = 0; j < messages.length; j++) {
      var message = messages[j];
      var body = message.getPlainBody(); // プレーンテキスト本文

      // メール本文からデータを抽出
      var data = parseRakutenPayEmail(body);

      if (data) {
        threadRecords.push([data.date, data.storeName, data.amount]);
      } else {
        Logger.log('パース失敗 - 件名: ' + message.getSubject() + ', 日時: ' + message.getDate());
        allParsed = false;
      }
    }

    if (allParsed && threadRecords.length > 0) {
      for (var k = 0; k < threadRecords.length; k++) {
        newRecords.push(threadRecords[k]);
      }
      successThreads.push(threads[i]);
    } else if (!allParsed) {
      Logger.log('スレッドスキップ（パース失敗あり） - スレッドID: ' + threads[i].getId());
    }
  }

  // スプレッドシートに書き込み → 成功後にのみラベル付与
  if (newRecords.length > 0) {
    var lastRow = sheet.getLastRow();
    sheet.getRange(lastRow + 1, 1, newRecords.length, 3).setValues(newRecords);
    Logger.log(newRecords.length + '件の楽天PAY明細を追加しました');

    // 日付の降順（新しい順）でソート（ヘッダー行を除く）
    var dataLastRow = sheet.getLastRow();
    if (dataLastRow > 1) {
      sheet.getRange(2, 1, dataLastRow - 1, 3).sort({ column: 1, ascending: false });
      Logger.log('日付の降順でソートしました');
    }

    // 書き込み成功後にラベルを付与
    for (var m = 0; m < successThreads.length; m++) {
      successThreads[m].addLabel(label);
    }
    Logger.log(successThreads.length + '件のスレッドを処理済みにしました');
  }
}

// ============================================================
// メール本文の解析
// ============================================================
function parseRakutenPayEmail(body) {
  try {
    // 日付を抽出（ご利用日時）- プレーンテキスト対応
    var dateMatch = body.match(/ご利用日時[\s\S]{0,100}?(\d{4}\/\d{1,2}\/\d{1,2})/);

    // 店舗名を抽出（ご利用店舗）- プレーンテキスト対応
    var storeMatch = body.match(/ご利用店舗[\s\S]{0,100}?(\S[^\n\r]*)/);

    // 金額を抽出（決済総額）- プレーンテキスト対応
    var rawAmount = null;
    var amountMatch = body.match(/決済総額[\s\S]{0,200}?([¥￥][\d,，０-９]+)/);
    if (amountMatch) {
      rawAmount = amountMatch[1];
    }

    if (!dateMatch || !storeMatch || !rawAmount) {
      Logger.log('必要なフィールドが見つかりません');
      return null;
    }

    var rawDate = dateMatch[1].trim();
    var storeName = storeMatch[1].trim();

    // 日付を変換: "2026/05/20(火) 08:40" -> "2026/05/20"
    var dateFormatted = parseDate(rawDate);

    // 金額を変換: "¥1,500" -> 1500
    var amount = parseAmount(rawAmount);

    return {
      date: dateFormatted,
      storeName: storeName,
      amount: amount
    };

  } catch (e) {
    Logger.log('パースエラー: ' + e.message);
    return null;
  }
}

// HTMLタグとHTMLエンティティを除去
function stripHtml(html) {
  return html
    .replace(/<[^>]*>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&yen;/g, '¥')
    .replace(/&#165;/g, '¥')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&#\d+;/g, '');
}

// 日付をパース: "2026/02/08(日) 12:18" -> "2026/02/08"
function parseDate(dateStr) {
  // パターン1: "2026/02/08(日) 12:18" 形式
  var match = dateStr.match(/(\d{4}\/\d{1,2}\/\d{1,2})/);
  if (match) {
    return match[1];
  }
  // パターン2: "2024年10月21日" 形式
  match = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
  if (match) {
    var month = ('0' + match[2]).slice(-2);
    var day = ('0' + match[3]).slice(-2);
    return match[1] + '/' + month + '/' + day;
  }
  return dateStr; // パターン不一致時はそのまま返す
}

// 金額をパース: "¥1,500" or "1,500円" -> 1500（全角文字対応）
function parseAmount(amountStr) {
  var cleaned = amountStr
    .replace(/[¥￥円]/g, '')
    .replace(/[，,]/g, '')
    .replace(/[０-９]/g, function(c) {
      return String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
    })
    .replace(/\s/g, '')
    .trim();
  return parseInt(cleaned, 10);
}

// ============================================================
// スプレッドシート関連
// ============================================================
function getOrCreateSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.SHEET_NAME);

  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.SHEET_NAME);
    sheet.getRange(1, 1, 1, CONFIG.HEADERS.length).setValues([CONFIG.HEADERS]);
    sheet.getRange(1, 1, 1, CONFIG.HEADERS.length).setFontWeight('bold');
  }

  return sheet;
}

function getOrCreateLabel(labelName) {
  var label = GmailApp.getUserLabelByName(labelName);
  if (!label) {
    label = GmailApp.createLabel(labelName);
  }
  return label;
}

// ============================================================
// 毎日自動実行トリガーの設定（1回だけ実行してください）
// ============================================================
function createDailyTrigger() {
  // 既存のトリガーを削除
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'extractRakutenPayEmails') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }

  // 毎日8時に実行するトリガーを作成
  ScriptApp.newTrigger('extractRakutenPayEmails')
    .timeBased()
    .atHour(8)
    .everyDays(1)
    .create();

  Logger.log('日次トリガーを設定しました（毎日8時実行）');
}

// ============================================================
// 処理済みラベルをリセット（再取込したい場合に使用）
// ============================================================
function resetProcessedLabel() {
  var label = GmailApp.getUserLabelByName(CONFIG.PROCESSED_LABEL);
  if (!label) {
    Logger.log('処理済みラベルが見つかりません');
    return;
  }

  var threads = label.getThreads();
  for (var i = 0; i < threads.length; i++) {
    threads[i].removeLabel(label);
  }
  Logger.log(threads.length + '件のスレッドからラベルを削除しました');
}

// ============================================================
// 直近N日分の処理済みラベルをリセット（部分的な再取込に使用）
// 使い方: reprocessRecentEmails(7) → 直近7日分のラベルを削除
//         その後 extractRakutenPayEmails() を実行して再取込
// ============================================================
function reprocessRecentEmails(days) {
  if (!days || days <= 0) {
    days = 7;
  }

  var label = GmailApp.getUserLabelByName(CONFIG.PROCESSED_LABEL);
  if (!label) {
    Logger.log('処理済みラベルが見つかりません');
    return;
  }

  var query = CONFIG.GMAIL_QUERY + ' label:' + CONFIG.PROCESSED_LABEL + ' newer_than:' + days + 'd';
  var threads = GmailApp.search(query);

  if (threads.length === 0) {
    Logger.log('直近' + days + '日以内の処理済みメールはありません');
    return;
  }

  for (var i = 0; i < threads.length; i++) {
    threads[i].removeLabel(label);
  }
  Logger.log(threads.length + '件のスレッドからラベルを削除しました（直近' + days + '日分）');
}
