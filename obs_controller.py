import obsws_python as obs
import logging
import asyncio
import random
from dotenv import load_dotenv
import os

class OBSController:
    def __init__(self, host='localhost', port=4455, password=''):  # デフォルトポートを4455に変更
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        self.connection_attempts = 0
        logging.info(f"OBSController初期化 (ホスト: {host}, ポート: {port})")

    async def __aenter__(self):
        """
        非同期コンテキストマネージャーの開始時にOBS WebSocketサーバーに接続します。
        """
        logging.info("OBSに接続中...")
        return await self.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        非同期コンテキストマネージャーの終了時にOBS WebSocketサーバーから切断します。
        """
        await self.disconnect()

    async def connect(self):
        """OBS WebSocketサーバーに接続します。"""
        self.connection_attempts += 1
        logging.info(f"OBS接続試行 #{self.connection_attempts}")
        
        try:
            # ReqClientは内部で接続と認証を処理
            self.ws = obs.ReqClient(
                host=self.host,
                port=self.port,
                password=self.password,
                subs=0,  # サブスクリプション無効
                timeout=None
            )
            logging.info("OBSに接続しました。")
            
            # 接続テスト
            try:
                version_info = await asyncio.to_thread(self.ws.get_version)
                logging.info(f"OBSバージョン情報: {version_info}")
            except Exception as e:
                logging.warning(f"バージョン情報の取得に失敗: {e}")
            
            return self
            
        except ConnectionRefusedError:
            logging.error("OBS WebSocketサーバーに接続できません。OBSが起動しているか、WebSocketプラグインが有効か確認してください。")
            self.ws = None
            raise
        except Exception as e:
            logging.error(f"OBSへの接続に失敗しました: {e}")
            logging.error(f"接続設定: ホスト={self.host}, ポート={self.port}")
            self.ws = None
            raise

    async def disconnect(self):
        """OBS WebSocketサーバーから切断します。"""
        if self.ws:
            try:
                logging.info("OBSから切断中...")
                # obsws-pythonのReqClientは自動的にクローズされるため、明示的な処理は不要
                self.ws = None
                logging.info("OBSから切断しました。")
            except Exception as e:
                logging.warning(f"OBS切断時にエラーが発生しました: {e}")

    async def get_current_scene(self):
        """現在のOBSシーン名を取得します。"""
        if not self.ws:
            logging.error("OBSに接続されていません。")
            return None
            
        try:
            response = await asyncio.to_thread(self.ws.get_current_program_scene)
            scene_name = response.current_program_scene_name
            logging.debug(f"現在のシーン: {scene_name}")
            return scene_name
        except Exception as e:
            logging.error(f"現在のシーンの取得に失敗しました: {e}")
            return None

    async def set_current_scene(self, scene_name: str):
        """OBSのシーンを切り替えます。"""
        if not self.ws:
            logging.error("OBSに接続されていません。")
            return False
            
        try:
            await asyncio.to_thread(self.ws.set_current_program_scene, scene_name)
            logging.info(f"シーンを '{scene_name}' に切り替えました。")
            return True
        except Exception as e:
            logging.error(f"シーン '{scene_name}' への切り替えに失敗しました: {e}")
            return False

    async def set_source_visibility(self, scene_name: str, source_name: str, visible: bool):
        """指定されたシーン内のソースの表示/非表示を切り替えます。"""
        if not self.ws:
            logging.error("OBSに接続されていません。")
            return False
            
        try:
            await asyncio.to_thread(self.ws.set_scene_item_enabled, scene_name, source_name, visible)
            status = '表示' if visible else '非表示'
            logging.info(f"シーン '{scene_name}' のソース '{source_name}' を {status} に設定しました。")
            return True
        except Exception as e:
            logging.error(f"ソース '{source_name}' の表示/非表示設定に失敗しました: {e}")
            return False

    async def set_text_source_text(self, source_name: str, text: str):
        """指定されたテキストソースのテキストを設定します。"""
        if not self.ws:
            logging.error("OBSに接続されていません。")
            return False
            
        try:
            # テキストの長さ制限（OBSの制限を考慮）
            if len(text) > 1000:
                text = text[:997] + "..."
                logging.warning("テキストが長すぎるため、1000文字に切り詰めました。")
            
            # 入力設定を更新
            settings = {"text": text}
            await asyncio.to_thread(self.ws.set_input_settings, source_name, settings, True)
            
            logging.info(f"テキストソース '{source_name}' を更新しました。")
            logging.debug(f"設定内容: {text[:100]}{'...' if len(text) > 100 else ''}")
            return True
            
        except Exception as e:
            logging.error(f"テキストソース '{source_name}' への設定に失敗しました: {e}")
            logging.error(f"ソース名が正しいか、テキストソースとして設定されているか確認してください。")
            
            # より詳細なエラー情報を提供
            try:
                # ソース一覧を取得してデバッグ情報を提供
                inputs = await asyncio.to_thread(self.ws.get_input_list)
                logging.debug("利用可能な入力ソース一覧:")
                for input_item in inputs.inputs:
                    logging.debug(f"  - {input_item['inputName']} ({input_item['inputKind']})")
            except Exception as debug_e:
                logging.debug(f"ソース一覧の取得に失敗: {debug_e}")
                
            return False

    async def get_scene_list(self):
        """OBSのシーン一覧を取得します。"""
        if not self.ws:
            logging.error("OBSに接続されていません。")
            return None
            
        try:
            response = await asyncio.to_thread(self.ws.get_scene_list)
            scenes = [scene['sceneName'] for scene in response.scenes]
            logging.debug(f"利用可能なシーン: {scenes}")
            return scenes
        except Exception as e:
            logging.error(f"シーン一覧の取得に失敗しました: {e}")
            return None

    async def get_input_list(self):
        """OBSの入力ソース一覧を取得します。"""
        if not self.ws:
            logging.error("OBSに接続されていません。")
            return None
            
        try:
            response = await asyncio.to_thread(self.ws.get_input_list)
            inputs = [(item['inputName'], item['inputKind']) for item in response.inputs]
            logging.debug(f"利用可能な入力ソース数: {len(inputs)}")
            return inputs
        except Exception as e:
            logging.error(f"入力ソース一覧の取得に失敗しました: {e}")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("OBSControllerのテストを開始します。")

    # .envファイルから環境変数を読み込む
    load_dotenv()

    obs_host = os.getenv("OBS_HOST", 'localhost')
    obs_port = int(os.getenv("OBS_PORT", 4455))
    obs_password = os.getenv("OBS_PASSWORD", '')

    async def test_obs_controller():
        try:
            async with OBSController(obs_host, obs_port, obs_password) as controller:
                logging.info("=== OBS接続テスト開始 ===")
                
                # シーン情報の取得
                current_scene = await controller.get_current_scene()
                if current_scene:
                    logging.info(f"現在のシーン: {current_scene}")
                
                # シーン一覧の取得
                scenes = await controller.get_scene_list()
                if scenes:
                    logging.info(f"利用可能なシーン数: {len(scenes)}")
                
                # 入力ソース一覧の取得
                inputs = await controller.get_input_list()
                if inputs:
                    logging.info(f"利用可能な入力ソース数: {len(inputs)}")
                    logging.info("テキストソースを探しています...")
                    text_sources = [name for name, kind in inputs if 'text' in kind.lower()]
                    logging.info(f"テキストソース: {text_sources}")
                
                # テキストソーステスト
                test_sources = ["Answer", "Question"]  # テスト対象のソース名
                
                for source_name in test_sources:
                    logging.info(f"=== {source_name} ソーステスト ===")
                    test_text = f"テスト中... ({source_name}) - {random.randint(1, 100)}"
                    
                    success = await controller.set_text_source_text(source_name, test_text)
                    if success:
                        logging.info(f"✓ {source_name} の設定に成功しました。")
                    else:
                        logging.error(f"✗ {source_name} の設定に失敗しました。")
                    
                    await asyncio.sleep(2)  # 2秒待機
                
                logging.info("=== OBS接続テスト完了 ===")
                
        except Exception as e:
            logging.error(f"OBSControllerのテスト中にエラーが発生しました: {e}")

    asyncio.run(test_obs_controller())
