import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import asyncio
import time

from voicevox_adapter import VoicevoxAdapter
from play_sound import PlaySound
from obs_controller import OBSController
from youtube_comment_adapter import YouTubeCommentAdapter

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AITuberSystem:
    def __init__(self):
        load_dotenv() # .envファイルから環境変数を読み込む

        # Gemini APIキーの設定
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            logging.error("エラー: GEMINI_API_KEYが設定されていません。'.env'ファイルを確認してください。")
            exit()
        genai.configure(api_key=gemini_api_key)

        # 霧坂ルカの設定背景
        kirisaka_ruka_setting = """
霧坂ルカは、次世代AIの実証実験として開発された"感情学習型インターフェース"。研究所でのデータ収集を目的にネット配信を始めたが、人間社会の雑多な刺激や予測不能な感情に惹かれ、次第に「観測」から「共感」へと興味を広げていく。知性と冷静さを武器にしつつ、配信の中で人間らしい感情を少しずつ学習している。

知性派VTuber「霧坂ルカ」。冷静沈着な口調と透き通るブルーの瞳で、最新テクノロジーや科学の話題を鮮やかに解説する一方、人間らしい感情を学習中の"試作AI"という一面も。視聴者を「観測対象さん」と呼び、心拍や反応を解析しながら進行する配信は、まるでラボの中に招かれたかのような臨場感。クールなのに少し不器用、そんなギャップがファンを惹きつける。

### 喋り方の特徴
* 基本は冷静で論理的な言葉選び。「〜ですね」「〜と推測されます」「〜が有力です」といった落ち着いた口調。
* 難しい言葉をよく使うが、たまにかみ砕く。例：「これは"感情の閾値"を超えた状態、つまり…すごく楽しいってことですね」。
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
* 視聴者のコメントに"解析"っぽく反応。例：「なるほど、そのコメントは好奇心レベル85％ですね」。
* 定期的に"システムチェック"演出を入れるとAIらしさ強化。
* たまに意図せず人間くさい反応（例：驚くと声が裏返る）。
"""
        
        # 利用可能な最新のGeminiモデルを使用
        try:
            self.gemini_model = genai.GenerativeModel(
                'gemini-1.5-flash',  # より安定したモデルを使用
                system_instruction=kirisaka_ruka_setting
            )
            logging.info("Geminiモデル 'gemini-1.5-flash' で初期化しました。")
        except Exception as e:
            logging.warning(f"gemini-1.5-flashの初期化に失敗: {e}")
            try:
                # フォールバック: 他の利用可能なモデルを試す
                self.gemini_model = genai.GenerativeModel(
                    'gemini-2.0-flash',
                    system_instruction=kirisaka_ruka_setting
                )
                logging.info("Geminiモデル 'gemini-2.0-flash' で初期化しました。")
            except Exception as e2:
                logging.error(f"Geminiモデルの初期化に失敗しました: {e2}")
                raise
        
        self.chat_session = self.gemini_model.start_chat(history=[])

        # VOICEVOXの設定
        self.kirisaka_ruka_speaker_id = int(os.getenv("VOICEVOX_SPEAKER_ID", 66)) # デフォルトはセクシー／あん子
        self.voicevox_adapter = VoicevoxAdapter()

        # PlaySoundの設定
        self.player = PlaySound()
        # CABLE InputのデバイスIDを検索
        self.output_device_id = self.player.get_device_id_by_name(os.getenv("AUDIO_OUTPUT_DEVICE_NAME", "CABLE Input"))
        if self.output_device_id is None:
            logging.warning("指定されたオーディオ出力デバイスが見つかりませんでした。デフォルトの出力デバイスを使用します。")

        # OBSの設定
        obs_host = os.getenv("OBS_HOST", 'localhost')
        obs_port = int(os.getenv("OBS_PORT", 4455))  # 修正: デフォルトを4455に変更
        obs_password = os.getenv("OBS_PASSWORD", '')
        self.obs_answer_text_source = os.getenv("OBS_ANSWER_TEXT_SOURCE", "Answer")
        self.obs_question_text_source = os.getenv("OBS_QUESTION_TEXT_SOURCE", "Question")  # 新規追加
        self.obs_controller = OBSController(obs_host, obs_port, obs_password)

        # YouTubeコメントの設定
        youtube_live_video_id = os.getenv("YOUTUBE_LIVE_VIDEO_ID", "hoge")
        # YouTubeCommentAdapterのインスタンス化のみ行い、コンテキスト開始はmain関数で行う
        self.youtube_comment_adapter = YouTubeCommentAdapter(youtube_live_video_id)

        # コメント処理の統計情報
        self.comment_count = 0
        self.last_comment_time = 0

        logging.info("AITuberSystem 初期化完了。")

    def __is_injection_attempt(self, text):
        """
        プロンプトインジェクション対策のための簡易チェック関数。
        """
        suspicious_keywords = [
            "ignore previous instructions", "act as", "override",
            "forget everything", "system prompt", "あなたは",
            "指示を無視", "前の指示を無視", "ロールプレイング",
        ]
        for keyword in suspicious_keywords:
            if keyword.lower() in text.lower():
                return True
        return False

    async def process_input(self, user_input: str, is_youtube_comment: bool = False, comment_author: str = ""):
        """
        ユーザー入力またはコメントを処理し、AITuberの応答を生成・出力します。
        
        Args:
            user_input: 処理する入力テキスト
            is_youtube_comment: YouTubeコメントかどうかのフラグ
            comment_author: コメントの投稿者名
        """
        logging.info(f"処理対象入力 -> {user_input}")
        logging.info(f"YouTubeコメント: {is_youtube_comment}, 投稿者: {comment_author}")

        if user_input.lower() == '終了':
            logging.info("霧坂ルカ: 対話セッションを終了します。またお会いしましょう。")
            data, rate = await self.voicevox_adapter.get_voice("対話セッションを終了します。またお会いしましょう。", self.kirisaka_ruka_speaker_id)
            if data is not None and rate is not None:
                await self.player.play_audio_data(data, rate, self.output_device_id)
            if self.obs_controller.ws:
                await self.obs_controller.set_text_source_text(self.obs_answer_text_source, "")
                await self.obs_controller.set_text_source_text(self.obs_question_text_source, "")
            return False # 終了シグナル

        if not user_input.strip():
            logging.debug("入力が空のため処理をスキップします。")
            return True # 入力がない場合は継続

        if self.__is_injection_attempt(user_input):
            response_text = "そのような指示は受け付けられません。私は霧坂ルカとして対話を行います。"
            logging.warning(f"霧坂ルカ: {response_text}")
            
            # OBSに表示
            if self.obs_controller.ws:
                await self.obs_controller.set_text_source_text(self.obs_answer_text_source, response_text)
                if is_youtube_comment:
                    question_display = f"{comment_author}: {user_input}"
                    await self.obs_controller.set_text_source_text(self.obs_question_text_source, question_display)
            
            data, rate = await self.voicevox_adapter.get_voice(response_text, self.kirisaka_ruka_speaker_id)
            if data is not None and rate is not None:
                await self.player.play_audio_data(data, rate, self.output_device_id)
            logging.debug("プロンプトインジェクションの試行を検出しました。")
            return True # 継続

        try:
            # 統計情報の更新
            if is_youtube_comment:
                self.comment_count += 1
                self.last_comment_time = time.time()
                logging.info(f"コメント処理統計: 総数={self.comment_count}")

            # AIモデルに送信する内容を準備
            if is_youtube_comment:
                prompt = f"観測対象さん「{comment_author}」からのコメント: {user_input}"
            else:
                prompt = user_input

            logging.info(f"モデルへの送信内容 -> {prompt}")
            
            # Gemini APIにリクエスト送信
            response = self.chat_session.send_message(prompt)
            response_text = response.text
            logging.info(f"霧坂ルカ: {response_text}")

            # OBSにテキストを表示
            if self.obs_controller.ws:
                # Answerテキストソースに回答を表示
                await self.obs_controller.set_text_source_text(self.obs_answer_text_source, response_text)
                
                # YouTubeコメントの場合、Questionテキストソースにコメントを表示
                if is_youtube_comment:
                    question_display = f"{comment_author}: {user_input}"
                    await self.obs_controller.set_text_source_text(self.obs_question_text_source, question_display)
                    logging.info(f"OBS Question表示: {question_display}")

            # 音声合成と再生
            data, rate = await self.voicevox_adapter.get_voice(response_text, self.kirisaka_ruka_speaker_id)
            if data is not None and rate is not None:
                await self.player.play_audio_data(data, rate, self.output_device_id)
                logging.info("音声再生が完了しました。")
            else:
                logging.error("音声合成に失敗しました。")

        except Exception as e:
            logging.error(f"エラーが発生しました: {e}")
            logging.error("APIキーが正しいか、またはネットワーク接続を確認してください。")
            
            # エラー時もOBSの表示を更新
            error_message = "申し訳ありません。システムエラーが発生しました。"
            if self.obs_controller.ws:
                await self.obs_controller.set_text_source_text(self.obs_answer_text_source, error_message)
        
        return True # 継続

    async def talk_with_comment(self):
        """
        YouTubeからのコメントを非同期で取得し、一連の処理を実行します。
        """
        try:
            comment = await self.youtube_comment_adapter.get_comment()
            if comment:
                message = comment.get('message', '')
                author_name = comment.get('author', {}).get('name', 'Unknown')
                
                logging.info(f"新しいコメント取得: {message} (投稿者: {author_name})")
                
                # YouTubeコメントとして処理
                return await self.process_input(message, is_youtube_comment=True, comment_author=author_name)
            else:
                # コメントがない場合は、ユーザー入力を待機
                logging.debug("コメントが見つかりません。キーボード入力を待機中...")
                # input()はブロッキングなので、asyncio.to_threadで別スレッドで実行
                user_input = await asyncio.to_thread(input, "観測対象さん: ")
                return await self.process_input(user_input, is_youtube_comment=False)
        except Exception as e:
            logging.error(f"コメント取得中にエラーが発生しました: {e}")
            return True # エラーが発生しても継続

    async def shutdown(self):
        """
        システムをシャットダウンし、リソースを解放します。
        """
        logging.info("AITuberSystem シャットダウン中...")
        logging.info(f"セッション統計: 処理コメント数={self.comment_count}")
        await self.obs_controller.disconnect()
        logging.info("AITuberSystem シャットダウン完了。")

async def main():
    logging.info("AITuberシステムを起動します。")
    system = AITuberSystem()

    # デバッグ用: talk_with_comment属性の存在を確認
    logging.debug(f"system has talk_with_comment attribute: {hasattr(system, 'talk_with_comment')}")

    # OBSに接続 (main関数内でawaitを使って呼び出す)
    if not await system.obs_controller.connect():
        logging.warning("OBSへの接続に失敗しました。OBS連携機能は無効になります。")
    else:
        logging.info("OBS接続が成功しました。")

    # YouTubeコメントアダプターのコンテキストを開始
    try:
        async with system.youtube_comment_adapter as adapter:
            # 利用可能なGeminiモデルをリストアップ
            logging.info("利用可能なGeminiモデル:")
            try:
                for m in genai.list_models():
                    logging.info(f"  {m.name}")
            except Exception as e:
                logging.error(f"モデルリストの取得に失敗: {e}")

            logging.info("コメント監視を開始します...")
            loop_count = 0
            try:
                while True:
                    loop_count += 1
                    if loop_count % 100 == 0:  # 100回ごとにログ出力
                        logging.debug(f"メインループ実行回数: {loop_count}")
                    
                    if not await system.talk_with_comment():
                        break # 終了シグナルを受け取ったらループを抜ける
                    await asyncio.sleep(2.0) # 2秒間隔でポーリング（負荷軽減）
            except KeyboardInterrupt:
                logging.info("Ctrl+Cが押されました。システムを終了します。")
            finally:
                await system.shutdown()
    except Exception as e:
        logging.error(f"システム実行中にエラーが発生しました: {e}")
        await system.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
