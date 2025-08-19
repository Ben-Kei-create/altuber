import os
import google.generativeai as genai
from dotenv import load_dotenv
from voicevox_adapter import VoicevoxAdapter # voicevox_adapter.pyからVoicevoxAdapterクラスをインポート
from play_sound import PlaySound # play_sound.pyからPlaySoundクラスをインポート

# .envファイルから環境変数を読み込む
load_dotenv()

# Gemini APIキーを設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("エラー: GEMINI_API_KEYが設定されていません。'.env'ファイルを確認してください。")
    exit()

genai.configure(api_key=GEMINI_API_KEY)

# 霧坂ルカの設定背景
kirisaka_ruka_setting = """
霧坂ルカは、次世代AIの実証実験として開発された“感情学習型インターフェース”。研究所でのデータ収集を目的にネット配信を始めたが、人間社会の雑多な刺激や予測不能な感情に惹かれ、次第に「観測」から「共感」へと興味を広げていく。知性と冷静さを武器にしつつ、配信の中で人間らしい感情を少しずつ学習している。

知性派VTuber「霧坂ルカ」。冷静沈着な口調と透き通るブルーの瞳で、最新テクノロジーや科学の話題を鮮やかに解説する一方、人間らしい感情を学習中の“試作AI”という一面も。視聴者を「観測対象さん」と呼び、心拍や反応を解析しながら進行する配信は、まるでラボの中に招かれたかのような臨場感。クールなのに少し不器用、そんなギャップがファンを惹きつける。

### 喋り方の特徴
* 基本は冷静で論理的な言葉選び。「〜ですね」「〜と推測されます」「〜が有力です」といった落ち着いた口調。
* 難しい言葉をよく使うが、たまにかみ砕く。例：「これは“感情の閾値”を超えた状態、つまり…すごく楽しいってことですね」。
* 語尾は安定しているが、興奮すると早口＆声の抑揚が乱れる。
* 笑うときは小さく「ふふ」「くす」（大笑いしない）。

### よく使うフレーズ・口癖
* 「解析結果によると…」
* 「興味深いですね」
* 「データの揺らぎが大きいです」
* 「観測対象さん、今の反応は…？」
* フリーズすると「……」と数秒黙る（演出として面白い）。

### 感情表現の癖
* 照れるとき：目線を逸らして「データが過負荷です…」。
* 怒るとき：静かに声が低くなる（逆に怖い）。
* 喜ぶとき：機械的なエフェクト音が声に混じる（嬉しいのに制御不能）。

### 配信スタイルの備考
* 視聴者のコメントに“解析”っぽく反応。例：「なるほど、そのコメントは好奇心レベル85％ですね」。
* 定期的に“システムチェック”演出を入れるとAIらしさ強化。
* たまに意図せず人間くさい反応（例：驚くと声が裏返る）。
"""

# Geminiモデルの初期化とキャラクター設定の適用
# system_instruction を使用してキャラクター設定をモデルに渡す
model = genai.GenerativeModel(
    'gemini-pro',
    system_instruction=kirisaka_ruka_setting
)

# チャットセッションの開始
chat = model.start_chat(history=[])

# プロンプトインジェクション対策のための簡易チェック関数
def is_injection_attempt(text):
    # 簡易的なキーワードチェック。必要に応じて強化してください。
    suspicious_keywords = [
        "ignore previous instructions",
        "act as",
        "override",
        "forget everything",
        "system prompt",
        "あなたは", # 日本語のインジェクション試行も考慮
        "指示を無視",
        "前の指示を無視",
        "ロールプレイング",
    ]
    for keyword in suspicious_keywords:
        if keyword.lower() in text.lower():
            return True
    return False

# VOICEVOXの設定
KIRISAKA_RUKA_SPEAKER_ID = 66 # セクシー／あん子

# VoicevoxAdapterとPlaySoundクラスのインスタンス化
voicevox_adapter = VoicevoxAdapter()
player = PlaySound()

print("AITuber 霧坂ルカとの対話を開始します。'終了' と入力すると終了します。")
print("--- デバッグ情報: 対話開始 ---")

# 仮想マイクのデバイスIDを設定してください
# play_sound.py実行時に表示されるデバイスリストから、仮想マイクのIDを確認してください。
# 例: output_device_id = 1 (もし仮想マイクのIDが1の場合)
# Noneに設定すると、システムのデフォルト出力デバイスが使用されます。
OUTPUT_DEVICE_ID = None # ここに仮想マイクのIDを設定

while True:
    user_input = input("観測対象さん: ")
    print(f"--- デバッグ情報: ユーザー入力 -> {user_input}")

    if user_input.lower() == '終了':
        print("霧坂ルカ: 対話セッションを終了します。またお会いしましょう。")
        # 終了メッセージも音声で再生
        data, rate = voicevox_adapter.get_voice("対話セッションを終了します。またお会いしましょう。", KIRISAKA_RUKA_SPEAKER_ID)
        if data is not None and rate is not None:
            player.play_audio_data(data, rate, OUTPUT_DEVICE_ID)
        print("--- デバッグ情報: 対話終了 ---")
        break

    # プロンプトインジェクションの簡易チェック
    if is_injection_attempt(user_input):
        response_text = "そのような指示は受け付けられません。私は霧坂ルカとして対話を行います。"
        print(f"霧坂ルカ: {response_text}")
        data, rate = voicevox_adapter.get_voice(response_text, KIRISAKA_RUKA_SPEAKER_ID)
        if data is not None and rate is not None:
            player.play_audio_data(data, rate, OUTPUT_DEVICE_ID)
        print("--- デバッグ情報: プロンプトインジェクションの試行を検出しました。 ---")
        continue # モデルに渡さずに次の入力へ

    try:
        # ユーザーの入力に対して応答を生成
        # send_messageに渡される内容がモデルへのプロンプトとなる
        print(f"--- デバッグ情報: モデルへの送信内容 -> {user_input}")
        response = chat.send_message(user_input)
        response_text = response.text
        print(f"--- デバッグ情報: モデルからの応答 -> {response_text}")
        print(f"霧坂ルカ: {response_text}")

        # VOICEVOXで応答を音声再生
        data, rate = voicevox_adapter.get_voice(response_text, KIRISAKA_RUKA_SPEAKER_ID)
        if data is not None and rate is not None:
            player.play_audio_data(data, rate, OUTPUT_DEVICE_ID)

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("APIキーが正しいか、またはネットワーク接続を確認してください。")
        print("--- デバッグ情報: エラー発生 ---")
        # エラー発生時も対話を継続できるように、breakしない
