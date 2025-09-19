import os
import flet as ft
import requests
from urllib.parse import urlparse
from tkinter import filedialog, messagebox

def load_authentication(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                username, password = lines[0].strip().split(',')
                return username, password
    except FileNotFoundError:
        messagebox.showerror("エラー", f"認証ファイルが見つかりません: {file_path}")
    except Exception as e:
        messagebox.showerror("エラー", f"認証ファイルの読み込みエラー: {e}")
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

def select_download_folder():
    folder = filedialog.askdirectory(title="ダウンロード先フォルダを選択してください")
    return folder

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

        def run_download(e):
            urls = [line.strip() for line in urls_text.value.splitlines() if line.strip()]
            if not urls:
                page.window_title_bar_hidden = False
                page.update()
                page.snack_bar = ft.SnackBar(ft.Text("URLを1つ以上入力してください。"))
                page.update()
                return

            download_folder = filedialog.askdirectory(title="ダウンロード先フォルダを選択してください")
            if not download_folder:
                page.window_title_bar_hidden = False
                page.update()
                page.snack_bar = ft.SnackBar(ft.Text("ダウンロード先フォルダが選択されませんでした。"))
                page.update()
                return

            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            auth_path = os.path.join(script_dir, "authentication.txt")
            username, password = load_authentication(auth_path)
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
                output_text.value += "\n▼ List of failed URLs:\n------------------------------\n"
                for failed_url in failed_urls:
                    output_text.value += f"{failed_url}\n"
                output_text.value += "------------------------------\nPlease copy the above URLs.\n"
            progress_bar.visible = False
            page.update()

        page.add(
            ft.Column(
                [
                    urls_text,
                    ft.ElevatedButton("実行", on_click=run_download),
                    output_text,
                    progress_bar,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=600,
                # padding=20, # Remove padding
            ),
            ft.TextButton("Close", on_click=lambda _: page.window_close()),
        )
        page.update()
    except Exception as e:
        print(f"An error occurred: {e}")
        page.snack_bar = ft.SnackBar(ft.Text(f"エラーが発生しました: {e}"))
        page.update()
        pass

ft.app(target=main)
