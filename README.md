# kindle2pdf

Kindle for PC のページを自動でスクリーンショットしてPDFに変換するツール

## 概要

このツールは、Kindle for PC (Windowsデスクトップアプリ) で開いている本のページを自動的にキャプチャし、1つのPDFファイルにまとめます。

## 機能

- Kindle for PC のウィンドウを自動検出
- PageDownキーで自動ページめくり
- 各ページのスクリーンショットを自動撮影
- 最終ページの自動検出（画像の類似度で判定）
- スクリーンショットをPDFに自動変換
- 重複ページの自動削除

## セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. Kindle for PC の準備

- Kindle for PC がインストールされていることを確認
- キャプチャしたい本を開く
- 最初のページに移動

## 使い方

### 基本的な使い方

```bash
python kindle2pdf.py
```

実行すると：
1. Kindleウィンドウを自動検出
2. 5秒のカウントダウン（この間にKindleウィンドウをアクティブにする）
3. 自動でページをキャプチャ（PageDownキーで次のページへ）
4. 最終ページを検出したら自動停止
5. PDFファイルを `output/kindle_book_YYYYMMDD_HHMMSS.pdf` に生成

### オプション

```bash
# 出力ディレクトリを指定
python kindle2pdf.py --output-dir my_books

# ページめくり後の待機時間を変更（秒）
python kindle2pdf.py --wait-time 1.0

# 最大ページ数を指定（無限ループ防止）
python kindle2pdf.py --max-pages 500

# スクリーンショットを削除せずに保持
python kindle2pdf.py --keep-screenshots

# 出力PDFファイル名を指定
python kindle2pdf.py --output-filename my_book.pdf

# 同一ページ判定の類似度閾値を変更（0.0-1.0）
# 注意: 通常はデフォルト(0.9999)で問題ありません
python kindle2pdf.py --similarity 0.9998

# すべてのオプションを組み合わせ
python kindle2pdf.py --output-dir books --wait-time 0.8 --output-filename novel.pdf
```

### ヘルプ

```bash
python kindle2pdf.py --help
```

## 仕組み

1. **ウィンドウ検出**: `pygetwindow` でKindleウィンドウを検索
2. **スクリーンショット**: `pyautogui` で画面全体をキャプチャ
3. **ページめくり**: `pyautogui` でPageDownキーを送信
4. **最終ページ検出**: `opencv-python` で前のページとの画像類似度を計算
   - ピクセル単位で差分を検出（差分が5以上のピクセルを変更とカウント）
   - デフォルト閾値: 0.9999（99.99%以上一致 = ほぼ完全一致のみを同一ページと判定）
   - 3回連続で同じページが検出されたら終了と判定
   - 重複したページは自動削除
5. **PDF生成**: `img2pdf` でスクリーンショットをPDFに変換
6. **クリーンアップ**: 一時ファイルを自動削除（`--keep-screenshots` オプションで保持可能）

## 注意事項

- Kindle for PC がフルスクリーンモードの場合は、ウィンドウモードに変更してください
- スクリプト実行中は他の操作を行わないでください（マウス・キーボード操作が自動化されます）
- 画面全体がキャプチャされるため、Kindleウィンドウ以外の部分も含まれます
- 最終ページの検出は画像の類似度で判定するため、まれに誤検出する可能性があります
- 個人利用の範囲でご使用ください

## トラブルシューティング

### Kindleウィンドウが見つからない

- Kindle for PC が起動しているか確認
- 本が開いているか確認
- ウィンドウのタイトルに "Kindle" が含まれているか確認

### 最終ページに到達する前に止まってしまう

**原因**: 類似度閾値が低すぎて、異なるページを「同じページ」と誤判定している

**解決策**:
- デフォルトの類似度閾値は `0.9999` (ほぼ完全一致) に設定されています
- それでも止まる場合は、さらに厳格に: `--similarity 0.99999`
- 画面にアニメーションや時計などの動的要素がある場合は、それらを隠してから実行

### 本当の最終ページで止まらない

**原因**: 最終ページに到達してもページめくりが続いている

**解決策**:
- `--max-pages` オプションで最大ページ数を指定（例: `--max-pages 300`）
- または、手動で途中停止（Ctrl+C）してから、不要なページをあとで削除

### ページめくりが速すぎる/遅すぎる

- `--wait-time` オプションで待機時間を調整（例: `--wait-time 1.0`）

## ライセンス

MIT License

## 開発者向け

### クラス構成

- `Kindle2PDF`: メインクラス
  - `find_kindle_window()`: Kindleウィンドウの検索
  - `capture_screenshot()`: スクリーンショット撮影
  - `images_are_similar()`: 画像の類似度判定
  - `turn_page()`: ページめくり
  - `capture_all_pages()`: 全ページキャプチャ
  - `create_pdf()`: PDF生成
  - `cleanup_temp_files()`: 一時ファイル削除
  - `run()`: メイン処理