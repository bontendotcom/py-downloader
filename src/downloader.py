import os
import flet as ft
import requests
from urllib.parse import urlparse
# from tkinter import filedialog, messagebox # Tkinterは使用しないためコメントアウト

def load_authentication(file_path, page: ft.Page):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                username, password = lines[0].strip().split(',')
                return username, password
    except FileNotFoundError:
        page.snack_bar = ft.SnackBar(ft.Text(f"エラー: 認証ファイルが見つかりません: {file_path}"))
        page.update()
    except Exception as e:
        page.snack_bar = ft.SnackBar(ft.Text(f"エラー: 認証ファイルの読み込みエラー: {e}"))
        page.update()
    return None, None

def download_file(url, username, password):
    try:
        response = requests.get(url, auth=(username, password), verify=False, stream=True)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        return None

def url_to_save_path(download_folder, url):
    parsed = urlparse(url)
    netloc = parsed.netloc
    path = parsed.path
    if path.endswith('/'):
        path = path + 'index.html'
    elif not os.path.splitext(path)[1]:
        path = path + '/index.html'
    if path.startswith('/'):
        path = path[1:]
    return os.path.join(download_folder, netloc, path)

def main(page: ft.Page):
    try:
        page.title = "Python Downloader"
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.window_width = 600
        page.window_height = 800
        page.padding = 20

        urls_text = ft.TextField(label="ダウンロードしたいURLを1行ずつ入力してください:", multiline=True, height=100, width=500)
        output_text = ft.TextField(label="出力:", multiline=True, height=300, width=500, read_only=True)
        progress_bar = ft.ProgressBar(width=500, visible=False)

        # FilePickerのインスタンスを作成し、ページに追加
        file_picker = ft.FilePicker(on_result=lambda e: page.run_task(handle_file_picker_result, e))
        page.overlay.append(file_picker)

        def on_window_event(e: ft.ControlEvent):
            if e.data == "close":
                os._exit(0) # ウィンドウが閉じられたら強制終了
        page.on_window_event = on_window_event

        async def handle_file_picker_result(e: ft.FilePickerResultEvent):
            download_folder = e.path if e.path else None

            if not download_folder:
                page.snack_bar = ft.SnackBar(ft.Text("ダウンロード先フォルダが選択されませんでした。"))
                page.update()
                return

            urls = [line.strip() for line in urls_text.value.splitlines() if line.strip()]
            if not urls: # このチェックはrun_downloadで既にされているが、念のため
                page.snack_bar = ft.SnackBar(ft.Text("URLを1つ以上入力してください。"))
                page.update()
                return

            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            auth_path = os.path.join(script_dir, "authentication.txt")
            username, password = load_authentication(auth_path, page)
            if not username or not password:
                return

            total_urls = len(urls)
            success_count = 0
            failed_urls = []

            output_text.value = ""
            progress_bar.value = None
            progress_bar.visible = True
            page.update()

            for index, url in enumerate(urls, start=1):
                output_text.value += f"[{index}/{total_urls}] Processing {url}...\n"
                page.update()
                response = download_file(url, username, password)
                if response:
                    save_path = url_to_save_path(download_folder, url)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    try:
                        with open(save_path, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        output_text.value += f"  → Success: {save_path}\n"
                        success_count += 1
                    except Exception as e:
                        output_text.value += f"  → Failed to save: {e}\n"
                        failed_urls.append(url)
                else:
                    output_text.value += "  → Failed\n"
                    failed_urls.append(url)
                page.update()

            output_text.value += f"\nDownload completed.\nRetrieved {success_count} out of {total_urls} files.\n"
            if failed_urls:
                failed_urls_text_area.value = "\n".join(failed_urls)
                failed_urls_text_area.visible = True
                redownload_button.visible = True
                output_text.value += "\n失敗したURLは下のテキストエリアに表示されています。\n「エラーURLを再ダウンロード」ボタンで再試行できます。\n"
            else:
                failed_urls_text_area.visible = False
                redownload_button.visible = False
            progress_bar.visible = False
            page.update()

        async def run_download(e):
            urls = [line.strip() for line in urls_text.value.splitlines() if line.strip()]
            if not urls:
                page.snack_bar = ft.SnackBar(ft.Text("URLを1つ以上入力してください。"))
                page.update()
                return
            
            # FletのFilePickerでフォルダ選択ダイアログを表示
            file_picker.get_directory_path(dialog_title="ダウンロード先フォルダを選択してください")
            # 結果はon_resultハンドラで処理されるため、ここでは待機しない

        failed_urls_text_area = ft.TextField(
            label="失敗したURL:",
            multiline=True,
            height=150,
            width=500,
            read_only=False, # ユーザーが修正できるように変更
            visible=False # 最初は非表示
        )
        redownload_button = ft.ElevatedButton(
            "エラーURLを再ダウンロード",
            on_click=lambda e: page.run_task(redownload_failed_urls),
            visible=False # 最初は非表示
        )

        async def redownload_failed_urls():
            # 失敗したURLをurls_textに設定し、ダウンロードを再開する
            urls_text.value = failed_urls_text_area.value
            failed_urls_text_area.visible = False
            redownload_button.visible = False
            page.update()
            await run_download(None) # run_downloadを呼び出して再ダウンロードを開始

        page.add(
            ft.Column(
                [
                    urls_text,
                    ft.ElevatedButton("実行", on_click=run_download),
                    output_text,
                    progress_bar,
                    failed_urls_text_area, # 新しいテキストエリアを追加
                    redownload_button,     # 新しいボタンを追加
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=600,
                # padding=20, # Remove padding
            ),
            # ft.TextButton("Close", on_click=lambda _: page.window_close()), # Closeボタンは削除
        )
        page.update()
    except Exception as e:
        print(f"An error occurred: {e}")
        page.snack_bar = ft.SnackBar(ft.Text(f"エラーが発生しました: {e}"))
        page.update()
        pass

ft.app(target=main)
