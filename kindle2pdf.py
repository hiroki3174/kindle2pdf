#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kindle for PC スクリーンショット → PDF 変換ツール

使い方:
1. Kindle for PC でキャプチャしたい本を開く
2. 最初のページに移動する
3. このスクリプトを実行する
4. Kindleウィンドウをアクティブにする（5秒の猶予あり）
"""

import os
import time
import sys
from pathlib import Path
from datetime import datetime

import pyautogui
import pygetwindow as gw
from PIL import Image
import img2pdf
import cv2
import numpy as np


class Kindle2PDF:
    def __init__(self, output_dir="output", wait_time=0.5, similarity_threshold=0.95):
        """
        Args:
            output_dir (str): スクリーンショットとPDFの保存先ディレクトリ
            wait_time (float): ページめくり後の待機時間（秒）
            similarity_threshold (float): 同一ページと判定する類似度（0.0-1.0）
        """
        self.output_dir = Path(output_dir)
        self.wait_time = wait_time
        self.similarity_threshold = similarity_threshold
        self.screenshots = []
        self.temp_dir = self.output_dir / "temp_screenshots"

        # ディレクトリ作成
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def find_kindle_window(self):
        """Kindleウィンドウを検索"""
        print("Kindleウィンドウを検索中...")
        windows = gw.getWindowsWithTitle("Kindle")

        if not windows:
            print("エラー: Kindleウィンドウが見つかりません。")
            print("Kindle for PC が起動していて、本が開いていることを確認してください。")
            return None

        # 最初に見つかったKindleウィンドウを使用
        kindle_window = windows[0]
        print(f"Kindleウィンドウを発見: {kindle_window.title}")
        return kindle_window

    def activate_kindle_window(self, kindle_window):
        """Kindleウィンドウをアクティブ化"""
        try:
            kindle_window.activate()
            time.sleep(1)  # ウィンドウがアクティブになるまで待機
            return True
        except Exception as e:
            print(f"警告: ウィンドウのアクティブ化に失敗: {e}")
            print("手動でKindleウィンドウをクリックしてアクティブにしてください...")
            time.sleep(3)
            return True

    def capture_screenshot(self, page_num):
        """スクリーンショットを撮影"""
        screenshot_path = self.temp_dir / f"page_{page_num:04d}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        self.screenshots.append(screenshot_path)
        print(f"ページ {page_num} をキャプチャしました")
        return screenshot_path

    def images_are_similar(self, img_path1, img_path2):
        """
        2つの画像が類似しているかを判定

        Returns:
            bool: 類似している場合True
        """
        # 画像を読み込み
        img1 = cv2.imread(str(img_path1))
        img2 = cv2.imread(str(img_path2))

        if img1 is None or img2 is None:
            return False

        # サイズが異なる場合は類似していないと判定
        if img1.shape != img2.shape:
            return False

        # グレースケールに変換
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # 構造類似性指標 (SSIM) で比較
        # SSIMは-1〜1の範囲で、1に近いほど類似
        score = cv2.matchTemplate(gray1, gray2, cv2.TM_CCOEFF_NORMED)[0][0]

        # より正確な比較: ピクセル単位での差分
        diff = cv2.absdiff(gray1, gray2)
        non_zero_count = np.count_nonzero(diff)
        total_pixels = diff.size
        similarity = 1 - (non_zero_count / total_pixels)

        print(f"  画像類似度: {similarity:.4f}")

        return similarity >= self.similarity_threshold

    def turn_page(self):
        """PageDownキーでページをめくる"""
        pyautogui.press('pagedown')
        time.sleep(self.wait_time)

    def capture_all_pages(self, max_pages=1000, duplicate_check_count=3):
        """
        全ページをキャプチャ

        Args:
            max_pages (int): 最大ページ数（無限ループ防止）
            duplicate_check_count (int): 何回連続で同じページが出たら終了とするか
        """
        print("\n" + "="*60)
        print("キャプチャを開始します...")
        print(f"- 待機時間: {self.wait_time}秒")
        print(f"- 最大ページ数: {max_pages}")
        print(f"- 同一ページ判定: {duplicate_check_count}回連続")
        print("="*60 + "\n")

        duplicate_count = 0
        page_num = 1

        while page_num <= max_pages:
            # スクリーンショット撮影
            current_screenshot = self.capture_screenshot(page_num)

            # 前のページと比較（2ページ目以降）
            if page_num > 1:
                prev_screenshot = self.screenshots[-2]

                if self.images_are_similar(prev_screenshot, current_screenshot):
                    duplicate_count += 1
                    print(f"  → 前のページと同じです (連続{duplicate_count}回目)")

                    if duplicate_count >= duplicate_check_count:
                        print(f"\n{duplicate_check_count}回連続で同じページが検出されました。")
                        print("最終ページに到達したと判断します。")
                        # 重複した画像を削除
                        for i in range(duplicate_check_count):
                            last_img = self.screenshots.pop()
                            if last_img.exists():
                                last_img.unlink()
                                print(f"重複画像を削除: {last_img.name}")
                        break
                else:
                    duplicate_count = 0

            # 次のページへ
            self.turn_page()
            page_num += 1

        print(f"\nキャプチャ完了: 合計 {len(self.screenshots)} ページ")

    def create_pdf(self, output_filename=None):
        """スクリーンショットからPDFを生成"""
        if not self.screenshots:
            print("エラー: スクリーンショットがありません。")
            return None

        # 出力ファイル名を生成
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"kindle_book_{timestamp}.pdf"

        output_path = self.output_dir / output_filename

        print(f"\nPDFを生成中: {output_path}")

        # 画像をPDFに変換
        with open(output_path, "wb") as f:
            # img2pdfは画像パスのリストを受け取る
            f.write(img2pdf.convert([str(img) for img in self.screenshots]))

        print(f"PDF生成完了: {output_path}")
        print(f"総ページ数: {len(self.screenshots)}")

        return output_path

    def cleanup_temp_files(self, keep_screenshots=False):
        """一時ファイルを削除"""
        if not keep_screenshots:
            print("\n一時ファイルをクリーンアップ中...")
            for img_path in self.screenshots:
                if img_path.exists():
                    img_path.unlink()

            # 空のディレクトリも削除
            if self.temp_dir.exists() and not any(self.temp_dir.iterdir()):
                self.temp_dir.rmdir()

            print("クリーンアップ完了")
        else:
            print(f"\nスクリーンショットを保持: {self.temp_dir}")

    def run(self, max_pages=1000, keep_screenshots=False, output_filename=None):
        """
        メイン処理

        Args:
            max_pages (int): 最大ページ数
            keep_screenshots (bool): スクリーンショットを保持するか
            output_filename (str): 出力PDFファイル名
        """
        print("\n" + "="*60)
        print("Kindle to PDF Converter")
        print("="*60)

        # Kindleウィンドウを検索
        kindle_window = self.find_kindle_window()
        if not kindle_window:
            return False

        # 準備時間
        print("\n5秒後にキャプチャを開始します...")
        print("Kindleウィンドウをアクティブにして、最初のページに移動してください。")
        for i in range(5, 0, -1):
            print(f"{i}...")
            time.sleep(1)

        # Kindleウィンドウをアクティブ化
        self.activate_kindle_window(kindle_window)

        # 全ページをキャプチャ
        self.capture_all_pages(max_pages=max_pages)

        # PDFを生成
        if self.screenshots:
            pdf_path = self.create_pdf(output_filename)

            # 一時ファイルをクリーンアップ
            self.cleanup_temp_files(keep_screenshots=keep_screenshots)

            print("\n" + "="*60)
            print("完了!")
            print(f"PDF: {pdf_path}")
            print("="*60 + "\n")

            return True
        else:
            print("\nエラー: キャプチャされたページがありません。")
            return False


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Kindle for PC のページをスクリーンショットしてPDFに変換"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="出力ディレクトリ（デフォルト: output）"
    )
    parser.add_argument(
        "--wait-time",
        type=float,
        default=0.5,
        help="ページめくり後の待機時間（秒、デフォルト: 0.5）"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=1000,
        help="最大ページ数（デフォルト: 1000）"
    )
    parser.add_argument(
        "--keep-screenshots",
        action="store_true",
        help="スクリーンショットを保持する"
    )
    parser.add_argument(
        "--output-filename",
        help="出力PDFファイル名（デフォルト: kindle_book_YYYYMMDD_HHMMSS.pdf）"
    )
    parser.add_argument(
        "--similarity",
        type=float,
        default=0.95,
        help="同一ページ判定の類似度閾値（0.0-1.0、デフォルト: 0.95）"
    )

    args = parser.parse_args()

    # Kindle2PDFインスタンス作成
    converter = Kindle2PDF(
        output_dir=args.output_dir,
        wait_time=args.wait_time,
        similarity_threshold=args.similarity
    )

    # 実行
    success = converter.run(
        max_pages=args.max_pages,
        keep_screenshots=args.keep_screenshots,
        output_filename=args.output_filename
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
