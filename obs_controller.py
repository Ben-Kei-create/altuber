import obsws_python as obs

class OBSController:
    def __init__(self, host='localhost', port=4444, password=''):
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        print(f"--- デバッグ情報: OBSController インスタンス化 (ホスト: {host}, ポート: {port}) ---")

    def connect(self):
        """
        OBS WebSocketサーバーに接続します。
        """
        print("--- デバッグ情報: OBSに接続中... ---")
        try:
            self.ws = obs.ReqClient(host=self.host, port=self.port, password=self.password)
            print("--- デバッグ情報: OBSに接続しました。 ---")
            return True
        except Exception as e:
            print(f"エラー: OBSへの接続に失敗しました: {e}")
            print("--- デバッグ情報: OBS接続エラー ---")
            self.ws = None
            return False

    def disconnect(self):
        """
        OBS WebSocketサーバーから切断します。
        """
        if self.ws:
            print("--- デバッグ情報: OBSから切断中... ---")
            self.ws.close()
            self.ws = None
            print("--- デバッグ情報: OBSから切断しました。 ---")

    def get_current_scene(self):
        """
        現在のOBSシーン名を取得します。
        """
        if not self.ws:
            print("エラー: OBSに接続されていません。")
            return None
        try:
            response = self.ws.get_current_program_scene()
            print(f"--- デバッグ情報: 現在のシーン -> {response.current_program_scene_name} ---")
            return response.current_program_scene_name
        except Exception as e:
            print(f"エラー: 現在のシーンの取得に失敗しました: {e}")
            return None

    def set_current_scene(self, scene_name: str):
        """
        OBSのシーンを切り替えます。
        """
        if not self.ws:
            print("エラー: OBSに接続されていません。")
            return False
        try:
            self.ws.set_current_program_scene(scene_name)
            print(f"--- デバッグ情報: シーンを '{scene_name}' に切り替えました。 ---")
            return True
        except Exception as e:
            print(f"エラー: シーン '{scene_name}' への切り替えに失敗しました: {e}")
            return False

    def set_source_visibility(self, scene_name: str, source_name: str, visible: bool):
        """
        指定されたシーン内のソースの表示/非表示を切り替えます。
        """
        if not self.ws:
            print("エラー: OBSに接続されていません。")
            return False
        try:
            self.ws.set_scene_item_enabled(scene_name, source_name, visible)
            print(f"--- デバッグ情報: シーン '{scene_name}' のソース '{source_name}' を {'表示' if visible else '非表示'} に設定しました。 ---")
            return True
        except Exception as e:
            print(f"エラー: ソース '{source_name}' の表示/非表示設定に失敗しました: {e}")
            return False

if __name__ == "__main__":
    print("OBSControllerのテストを開始します。")
    # OBSのWebSocket設定に合わせてホスト、ポート、パスワードを設定してください
    # パスワードを設定していない場合は空文字列のまま
    obs_host = 'localhost'
    obs_port = 4444
    obs_password = 'YOUR_OBS_WEBSOCKET_PASSWORD' # OBSで設定したパスワード

    controller = OBSController(obs_host, obs_port, obs_password)

    if controller.connect():
        # 現在のシーン名を取得
        current_scene = controller.get_current_scene()
        if current_scene:
            print(f"現在のシーン: {current_scene}")

            # シーンを切り替えるテスト (存在しないシーン名だとエラーになります)
            # test_scene_name = "新しいシーン名"
            # if controller.set_current_scene(test_scene_name):
            #     print(f"シーンが {test_scene_name} に切り替わりました。")
            # else:
            #     print(f"シーン {test_scene_name} への切り替えに失敗しました。")

            # ソースの表示/非表示を切り替えるテスト (存在しないソース名だとエラーになります)
            # test_source_name = "テキスト"
            # if controller.set_source_visibility(current_scene, test_source_name, False):
            #     print(f"ソース '{test_source_name}' を非表示にしました。")
            # else:
            #     print(f"ソース '{test_source_name}' の非表示設定に失敗しました。")

        controller.disconnect()
    else:
        print("OBSへの接続に失敗したため、テストをスキップします。")

    print("OBSControllerのテストが完了しました。")
