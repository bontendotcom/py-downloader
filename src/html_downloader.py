import os
import flet as ft
import requests
from urllib.parse import urlparse
import configparser # configparserをインポート
import html_downloader
import sys

# 設定ファイルのパス
CONFIG_FILE = "config.ini"

def save_credentials(username, password):
    config = configparser.ConfigParser()
    config['AUTH'] = {'username': username, 'password': password}
    with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
        config.write(configfile)

def load_credentials():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding='utf-8')
    username = config.get('AUTH', 'username', fallback='')
    password = config.get('AUTH', 'password', fallback='')
    return username, password

def download_file(url, username, password):
    try:
        response = requests.get(url, auth=(username, password), verify=True, stream=True)
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
        page.title = "HTML File Downloader"
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.window_resizable = True  # ウィンドウサイズを変更可能に設定
        page.window_maximized = False  # ウィンドウの最大化を無効化
        page.window_width = 1920  # ウィンドウ幅を設定
        page.window_height = 1080  # ウィンドウ高さを設定
        page.update()  # ウィンドウサイズの変更を適用
        page.padding = 40
        page.scroll = ft.ScrollMode.AUTO  # ページ全体をスクロール可能に設定

        # 認証情報を読み込む
        initial_username, initial_password = load_credentials()

        username_field = ft.TextField(label="ユーザー名", value=initial_username, width=800)
        password_field = ft.TextField(label="パスワード", password=True, can_reveal_password=True, value=initial_password, width=800)

        def on_credentials_change(e):
            save_credentials(username_field.value, password_field.value)

        username_field.on_change = on_credentials_change
        password_field.on_change = on_credentials_change

        def on_urls_text_change(e):
            # テキストフィールドの内容が変更された際に値を更新
            urls_text.value = e.control.value
            page.update()

        urls_text = ft.TextField(
            label="ダウンロードしたいURLを1行ずつ入力してください",
            multiline=True,
            width=800,
            autofocus=True,  # フィールドを自動的にフォーカス
            keyboard_type="text",  # キーボードタイプを明示的に設定
            on_change=on_urls_text_change  # ペースト操作を含む変更をサポート
        )
        output_text = ft.TextField(label="実行結果", multiline=True, width=800, read_only=True)
        progress_bar = ft.ProgressBar(width=800, height=10, value=0.0, visible=True) # heightを10に設定

        # FilePickerのインスタンスを作成し、ページに追加
        file_picker = ft.FilePicker(on_result=lambda e: page.run_task(handle_file_picker_result, e))
        page.overlay.append(file_picker)

        page.window_close = lambda e: (page.window_close(), sys.exit(0))  # ウィンドウが閉じられたら強制終了

        async def handle_file_picker_result(e: ft.FilePickerResultEvent):
            download_folder = e.path if e.path else None

            if not download_folder:
                page.snack_bar = ft.SnackBar(ft.Text("ダウンロード先フォルダが選択されませんでした。"))
                page.update()  # 非同期ではなく同期的に更新
                return

            urls = [line.strip() for line in urls_text.value.splitlines() if line.strip()]
            if not urls:
                page.snack_bar = ft.SnackBar(ft.Text("URLを1つ以上入力してください。"))
                page.update()  # 非同期ではなく同期的に更新
                return

            username = username_field.value
            password = password_field.value
            if not username or not password:
                page.snack_bar = ft.SnackBar(ft.Text("ユーザー名とパスワードを入力してください。"))
                page.update()  # 非同期ではなく同期的に更新
                return

            total_urls = len(urls)
            success_count = 0
            failed_urls = []

            output_text.value = ""
            progress_bar.value = 0.0  # ダウンロード開始時に0.0にリセット
            progress_bar.visible = True
            page.update()  # 非同期ではなく同期的に更新

            for index, url in enumerate(urls, start=1):
                output_text.value += f"[{index}/{total_urls}] Processing {url}...\n"
                page.update()  # 非同期ではなく同期的に更新
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

                # プログレスバーの値を更新
                progress_bar.value = index / total_urls
                page.update()  # 非同期ではなく同期的に更新

            output_text.value += f"\nDownload completed.\nRetrieved {success_count} out of {total_urls} files."
            if failed_urls:
                failed_urls_text_area.value = "\n".join(failed_urls)
                failed_urls_text_area.visible = True  # 失敗したURLがある場合のみ表示
                redownload_button.visible = True  # 失敗したURLがある場合のみ表示
                output_text.value += "\n\n失敗したURLは下のテキストエリアに表示されています。\n「取得に失敗したURLを再ダウンロード」ボタンで再試行できます。"
            else:
                failed_urls_text_area.value = "取得に失敗したURL：なし"  # 失敗したURLがない場合はメッセージを表示
                failed_urls_text_area.visible = True  # 常に表示
                redownload_button.visible = False  # 失敗したURLがない場合は非表示
            progress_bar.value = 1.0  # ダウンロード完了時に1.0に設定
            page.update()  # 非同期ではなく同期的に更新

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
            label="取得に失敗したURL",
            multiline=True,
            width=800,
            read_only=False,  # ユーザーが修正できるように変更
            visible=True  # 常に表示
        )
        redownload_button = ft.ElevatedButton(
            "取得に失敗したURLを再ダウンロード",
            on_click=lambda e: page.run_task(redownload_failed_urls),
            visible=False  # 最初は非表示
        )

        async def redownload_failed_urls():
            # 取得に失敗したURLをurls_textに設定し、ダウンロードを再開する
            urls_text.value = failed_urls_text_area.value
            failed_urls_text_area.visible = False
            redownload_button.visible = False
            page.update()
            await run_download(None) # run_downloadを呼び出して再ダウンロードを開始

        page.add(
            ft.Column(
                [
                    username_field,  # ユーザー名入力フィールドを追加
                    password_field,  # パスワード入力フィールドを追加
                    urls_text,
                    ft.ElevatedButton("実行", on_click=run_download),
                    progress_bar,
                    ft.Column(
                        [output_text, failed_urls_text_area],
                        scroll=ft.ScrollMode.AUTO,  # 内部の実行結果エリアをスクロール可能に設定
                        spacing=40,  # マージンを調整
                    ),
                    redownload_button,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=800, # 幅を800に変更
                spacing=40,  # マージンを調整
            ),
        )
        urls_text.focus()
        page.update()

    except Exception as e:  # exceptブロックをtryの後に配置
        print(f"An error occurred: {e}")
        page.snack_bar = ft.SnackBar(ft.Text(f"エラーが発生しました: {e}"))
        page.update()

if __name__ == "__main__":
    ft.app(target=main)
