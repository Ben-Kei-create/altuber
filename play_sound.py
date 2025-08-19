import sounddevice as sd
import numpy as np
import io
import wave

class PlaySound:
    def __init__(self):
        self.devices = sd.query_devices()
        print("--- デバッグ情報: 利用可能なサウンドデバイス --- ")
        for i, device in enumerate(self.devices):
            print(f"  ID: {i}, Name: {device['name']}, Host API: {device['hostapi']}, Max Output Channels: {device['max_output_channels']}")
        print("--------------------------------------")

    def play_audio_data(self, data: np.ndarray, rate: int, output_device_id: int = None):
        """
        numpy配列の音声データとサンプリングレートを指定されたサウンドデバイスで再生します。

        Args:
            data (np.ndarray): 音声データ (numpy配列)。
            rate (int): サンプリングレート。
            output_device_id (int, optional): 音声を出力するデバイスのID。Noneの場合、デフォルトの出力デバイスを使用します。
        """
        print(f"--- デバッグ情報: 音声再生開始 (出力デバイスID: {output_device_id}, サンプリングレート: {rate}) ---")
        try:
            # sounddeviceで再生
            sd.play(data, samplerate=rate, device=output_device_id)
            sd.wait() # 再生が完了するまで待機
            print("--- デバッグ情報: 音声再生完了 ---")

        except Exception as e:
            print(f"エラー: 音声再生中に問題が発生しました: {e}")
            print("--- デバッグ情報: 音声再生エラー ---")

if __name__ == "__main__":
    # テスト用のダミーWAVデータを作成
    sample_rate = 44100  # サンプルレート
    duration = 1.0       # 1秒
    frequency = 440      # 440Hzのサイン波

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    amplitude = np.iinfo(np.int16).max * 0.5 # 振幅
    data = amplitude * np.sin(2 * np.pi * frequency * t)
    audio_data_np = data.astype(np.float32) # sounddeviceはfloat32を推奨

    player = PlaySound()
    print("ダミー音声の再生テストを開始します。")
    # デフォルトの出力デバイスで再生
    player.play_audio_data(audio_data_np, sample_rate)

    # 特定のデバイスIDを指定して再生する場合
    # print("特定のデバイスIDで再生テストを開始します。(ID: 0)")
    # player.play_audio_data(audio_data_np, sample_rate, output_device_id=0)

    print("ダミー音声の再生テストが完了しました。")