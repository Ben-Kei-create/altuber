# AITuberシステム

このプロジェクトは、GoogleのGemini API、VOICEVOX、OBSを使用して、AIがVTuberとして振る舞うためのシステムです。YouTube Liveのコメントを読み取り、それに応答することができます。

## 主な機能

-   **AIチャット:** GoogleのGemini APIを使用して、ユーザーの入力に対する応答を生成します。
-   **音声合成:** AIの応答テキストをVOICEVOXを使用して音声に変換します。
-   **OBS連携:** OBSのシーンやテキストソースを制御します。
-   **YouTube Live連携:** YouTube Liveのコメントをリアルタイムで取得し、AIへの入力として使用します。

## ファイル構成

-   `aituber_system.py`: システム全体を統括するメインファイルです。
-   `obs_controller.py`: `obsws-python`ライブラリを使用してOBSを制御します。
-   `play_sound.py`: `sounddevice`ライブラリを使用して音声を再生します。
-   `voicevox_adapter.py`: VOICEVOX APIと連携するためのアダプターです。
-   `voicevox_speaker.py`: VOICEVOXを使用して音声を合成・再生するシンプルなスクリプトです。
-   `youtube_comment_adapter.py`: `pytchat`ライブラリを使用してYouTube Liveのコメントを取得します。
-   `.env`: APIキーなどの設定を記述するファイルです。
-   `requirements.txt`: プロジェクトに必要なPythonライブラリの一覧です。

## セットアップ方法

1.  **必要なライブラリのインストール:**
    ```
    pip install -r requirements.txt
    ```
2.  **`.env`ファイルの設定:**
    プロジェクトのルートディレクトリに`.env`ファイルを作成し、以下の内容を記述してください。
    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    VOICEVOX_SPEAKER_ID=3
    AUDIO_OUTPUT_DEVICE_NAME="CABLE Input"
    OBS_HOST="localhost"
    OBS_PORT=4455
    OBS_PASSWORD="YOUR_OBS_WEBSOCKET_PASSWORD"
    OBS_ANSWER_TEXT_SOURCE="Answer"
    OBS_QUESTION_TEXT_SOURCE="Question"
    YOUTUBE_LIVE_VIDEO_ID="YOUR_YOUTUBE_LIVE_VIDEO_ID"
    ```

## 実行方法

以下のコマンドでメインのスクリプトを実行します。
```
python aituber_system.py
```
