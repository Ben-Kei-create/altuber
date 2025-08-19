import requests
import json
import tempfile
import os
from playsound import playsound

VOICEVOX_API_BASE_URL = "http://localhost:50021"

def synthesize_voicevox(text: str, speaker_id: int = 3):
    """
    VOICEVOX APIを使用してテキストを音声に変換し、再生します。

    Args:
        text (str): 音声に変換するテキスト。
        speaker_id (int): VOICEVOXの話者ID。デフォルトは3（ずんだもん）。
    """
    print(f"--- デバッグ情報: VOICEVOX音声合成開始 (テキスト: '{text}', 話者ID: {speaker_id}) ---")
    try:
        # 1. audio_query (音声合成クエリの生成)
        query_payload = {"text": text, "speaker": speaker_id}
        print(f"--- デバッグ情報: audio_query リクエストペイロード -> {query_payload} ---")
        audio_query_response = requests.post(
            f"{VOICEVOX_API_BASE_URL}/audio_query",
            params=query_payload
        )
        audio_query_response.raise_for_status() # HTTPエラーがあれば例外を発生
        query_data = audio_query_response.json()
        print(f"--- デバッグ情報: audio_query レスポンス -> {query_data} ---")

        # 2. synthesis (音声合成)
        synthesis_payload = {"speaker": speaker_id}
        print(f"--- デバッグ情報: synthesis リクエストペイロード -> {synthesis_payload} ---")
        synthesis_response = requests.post(
            f"{VOICEVOX_API_BASE_URL}/synthesis",
            headers={"Content-Type": "application/json"},
            params=synthesis_payload,
            data=json.dumps(query_data)
        )
        synthesis_response.raise_for_status() # HTTPエラーがあれば例外を発生
        print("--- デバッグ情報: synthesis レスポンス (バイナリデータ) 受信 ---")

        # 3. 音声データの保存と再生
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fp:
            fp.write(synthesis_response.content)
            temp_wav_path = fp.name
        print(f"--- デバッグ情報: 一時WAVファイル保存 -> {temp_wav_path} ---")

        playsound(temp_wav_path)
        print("--- デバッグ情報: 音声再生完了 ---")

    except requests.exceptions.ConnectionError:
        print("エラー: VOICEVOXアプリケーションが起動していません。またはAPIサーバーに接続できません。")
        print("VOICEVOXアプリケーションを起動してから再度お試しください。")
    except requests.exceptions.RequestException as e:
        print(f"VOICEVOX APIリクエストエラー: {e}")
        print(f"レスポンス内容: {e.response.text if e.response else 'N/A'}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
    finally:
        # 一時ファイルを削除
        if 'temp_wav_path' in locals() and os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
            print(f"--- デバッグ情報: 一時WAVファイル削除 -> {temp_wav_path} ---")

if __name__ == "__main__":
    print("VOICEVOX音声合成テストを開始します。")
    # テスト用のテキストと話者ID
    test_text = "こんにちは、私はずんだもんなのだ。"
    test_speaker_id = 3 # ずんだもん (ノーマル)

    synthesize_voicevox(test_text, test_speaker_id)

    print("別の話者でテストします。")
    # 他の話者IDを試す場合は、VOICEVOXアプリケーションで確認してください。
    # 例: 四国めたん (ノーマル) は 2
    test_text_2 = "これは四国めたんの声です。"
    test_speaker_id_2 = 2 # 四国めたん (ノーマル)
    synthesize_voicevox(test_text_2, test_speaker_id_2)

    print("VOICEVOX音声合成テストが完了しました。")
