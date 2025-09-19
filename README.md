# Python Downloader

このプロジェクトは、`list.txt` ファイルからURLを読み込み、`requests` ライブラリを使って対応するファイルをダウンロードするシンプルなPython製ダウンローダーです。認証が必要なリソースに対応するため、`authentication.txt` ファイルから認証情報も取得します。

## プロジェクト構成

```
python-downloader
├── list.txt
├── authentication.txt
├── src
│   ├── downloader.py      # ダウンロードのメインロジック
│   └── types
│       └── index.py       # ダウンローダーで使用するデータ型やインターフェース
├── requirements.txt        # プロジェクト依存パッケージ
└── README.md               # プロジェクトのドキュメント
```


## インストール方法

必要な依存パッケージをインストールするには、以下のコマンドを実行してください。

```
pip install -r requirements.txt
```

## 使い方

1. ダウンロードしたいURLを1行ずつ記載した `list.txt` ファイルを用意します。
2. ユーザー名とパスワードを以下の形式で記載した `authentication.txt` ファイルを作成します。
   ```
   username,password
   ```
3. ダウンローダースクリプトを実行します。

```
python src/downloader.py
```

スクリプトは各ファイルのダウンロードを試み、成功した数とダウンロードに失敗したURLを報告します。

## ライセンス

このプロジェクトはMITライセンスのもとで公開されています。