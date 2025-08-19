import requests
import json
import io
import soundfile as sf
import numpy as np

class VoicevoxAdapter:
    VOICEVOX_API_BASE_URL = "http://localhost:50021"

    def __init__(self):
        print("--- デバッグ情報: VoicevoxAdapter インスタンス化 ---")

    def __create_audio_query(self, text: str, speaker_id: int):
        """
        VOICEVOX APIのaudio_queryエンドポイントにリクエストを送信し、音声合成クエリを生成します。
        """
        query_payload = {"text": text, "speaker": speaker_id}
        print(f"--- デバッグ情報: __create_audio_query リクエストペイロード -> {query_payload} ---")
        audio_query_response = requests.post(
            f"{self.VOICEVOX_API_BASE_URL}/audio_query",
            params=query_payload
        )
        audio_query_response.raise_for_status() # HTTPエラーがあれば例外を発生
        query_data = audio_query_response.json()
        print(f"--- デバッグ情報: __create_audio_query レスポンス -> {query_data} ---")
        return query_data

    def __create_request_audio(self, query_data: dict, speaker_id: int):
        """
        VOICEVOX APIのsynthesisエンドポイントにリクエストを送信し、音声バイト列を生成します。
        """
        synthesis_payload = {"speaker": speaker_id}
        print(f"--- デバッグ情報: __create_request_audio リクエストペイロード -> {synthesis_payload} ---")
        synthesis_response = requests.post(
            f"{self.VOICEVOX_API_BASE_URL}/synthesis",
            headers={"Content-Type": "application/json"},
            params=synthesis_payload,
            data=json.dumps(query_data)
        )
        synthesis_response.raise_for_status() # HTTPエラーがあれば例外を発生
        print("--- デバッグ情報: __create_request_audio レスポンス (バイナリデータ) 受信 ---")
        return synthesis_response.content

    def get_voice(self, text: str, speaker_id: int = 3):
        """
        VOICEVOX APIを使用してテキストを音声に変換し、numpy配列とサンプリングレートを返します。

        Args:
            text (str): 音声に変換するテキスト。
            speaker_id (int): VOICEVOXの話者ID。

        Returns:
            tuple[np.ndarray, int]: 音声データ (numpy配列) とサンプリングレート。
                                    エラーが発生した場合は (None, None) を返します。
        """
        print(f"--- デバッグ情報: VoicevoxAdapter.get_voice 開始 (テキスト: '{text}', 話者ID: {speaker_id}) ---")
        try:
            # 1. audio_query (音声合成クエリの生成)
            query_data = self.__create_audio_query(text, speaker_id)

            # 2. synthesis (音声合成)
            audio_bytes = self.__create_request_audio(query_data, speaker_id)

            # 3. バイト列から音声データを読み込み、numpy配列とサンプリングレートを取得
            data, rate = sf.read(io.BytesIO(audio_bytes))
            print("--- デバッグ情報: 音声データ (numpy配列) とサンプリングレート取得完了 ---")
            return data, rate

        except requests.exceptions.ConnectionError:
            print("エラー: VOICEVOXアプリケーションが起動していません。またはAPIサーバーに接続できません。")
            print("VOICEVOXアプリケーションを起動してから再度お試しください。")
        except requests.exceptions.RequestException as e:
            print(f"VOICEVOX APIリクエストエラー: {e}")
            print(f"レスポンス内容: {e.response.text if e.response else 'N/A'}")
        except Exception as e:
            print(f"予期せぬエラーが発生しました: {e}")
        return None, None

if __name__ == "__main__":
    print("VOICEVOXアダプタークラスのテストを開始します。")
    adapter = VoicevoxAdapter()

    # テスト用のテキストと話者ID
    test_text = "こんにちは、VOICEVOXアダプタークラスのテストです。"
    test_speaker_id = 3 # ずんだもん (ノーマル)

    data, rate = adapter.get_voice(test_text, test_speaker_id)

    if data is not None and rate is not None:
        print(f"取得した音声データの形状: {data.shape}, サンプリングレート: {rate}")
        # ここでPlaySoundクラスを使って再生することも可能
        from play_sound import PlaySound
        player = PlaySound()
        player.play_audio_data(data, rate)
    else:
        print("音声データの取得に失敗しました。")

    print("VOICEVOXアダプタークラスのテストが完了しました。")