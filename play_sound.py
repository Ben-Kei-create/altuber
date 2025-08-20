import sounddevice as sd
import numpy as np
import io
import wave
import logging
import asyncio # asyncioをインポート

class PlaySound:
    def __init__(self):
        self.devices = sd.query_devices()
        logging.debug("--- デバッグ情報: 利用可能なサウンドデバイス --- ")
        for i, device in enumerate(self.devices):
            logging.debug(f"  ID: {i}, Name: {device['name']}, Host API: {device['hostapi']}, Max Output Channels: {device['max_output_channels']}")
        logging.debug("--------------------------------------")

    def get_device_id_by_name(self, name: str):
        """
        デバイス名からデバイスIDを取得します。
        """
        for i, device in enumerate(self.devices):
            if name.lower() in device['name'].lower():
                logging.debug(f"--- デバッグ情報: デバイス名 '{name}' に一致するID: {i} を見つけました。 ---")
                return i
        logging.warning(f"--- デバッグ情報: デバイス名 '{name}' に一致するデバイスが見つかりませんでした。 ---")
        return None

    async def play_audio_data(self, data: np.ndarray, rate: int, output_device_id: int = None):
        """
        numpy配列の音声データとサンプリングレートを指定されたサウンドデバイスで再生します。

        Args:
            data (np.ndarray): 音声データ (numpy配列)。
            rate (int): サンプリングレート。
            output_device_id (int, optional): 音声を出力するデバイスのID。Noneの場合、デフォルトの出力デバイスを使用します。
        """
        logging.debug(f"--- デバッグ情報: 音声再生開始 (出力デバイスID: {output_device_id}, サンプリングレート: {rate}) ---")
        try:
            # sounddevice.playは同期的なのでasyncio.to_threadでラップ
            await asyncio.to_thread(sd.play, data, samplerate=rate, device=output_device_id)
            await asyncio.to_thread(sd.wait) # 再生が完了するまで待機
            logging.debug("--- デバッグ情報: 音声再生完了 ---")

        except Exception as e:
            logging.error(f"エラー: 音声再生中に問題が発生しました: {e}")
            logging.debug("--- デバッグ情報: 音声再生エラー ---")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("PlaySoundのテストを開始します。")
    # テスト用のダミーWAVデータを作成
    sample_rate = 44100  # サンプルレート
    duration = 1.0       # 1秒
    frequency = 440      # 440Hzのサイン波

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    amplitude = np.iinfo(np.int16).max * 0.5 # 振幅
    data = amplitude * np.sin(2 * np.pi * frequency * t)
    audio_data_np = data.astype(np.float32) # sounddeviceはfloat32を推奨

    player = PlaySound()
    logging.info("ダミー音声の再生テストを開始します。")
    # デフォルトの出力デバイスで再生
    async def test_play_audio():
        await player.play_audio_data(audio_data_np, sample_rate)

        # 特定のデバイスIDを指定して再生する場合
        # logging.info("特定のデバイスIDで再生テストを開始します。(ID: 0)")
        # await player.play_audio_data(audio_data_np, sample_rate, output_device_id=0)

        # デバイス名でIDを取得するテスト
        cable_input_id = player.get_device_id_by_name("CABLE Input")
        if cable_input_id is not None:
            logging.info(f"CABLE Input のID: {cable_input_id}")
            # await player.play_audio_data(audio_data_np, sample_rate, output_device_id=cable_input_id)

        logging.info("ダミー音声の再生テストが完了しました。")

    asyncio.run(test_play_audio())
