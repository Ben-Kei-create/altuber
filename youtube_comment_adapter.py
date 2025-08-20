import pytchat
import json
import logging
import asyncio
import time

class YouTubeCommentAdapter:
    def __init__(self, video_id: str):
        self.video_id = video_id
        self.chat = None
        self.last_comment_ids = set()  # 重複コメント防止用
        self.comment_count = 0
        self.error_count = 0
        logging.info(f"YouTubeCommentAdapter インスタンス化 (Video ID: {video_id})")

    async def __aenter__(self):
        """
        非同期コンテキストマネージャーの開始時にpytchatオブジェクトを作成します。
        """
        logging.info("pytchatオブジェクトを作成中...")
        try:
            # pytchat.create()は signal handlers を設定するため、メインスレッドで実行する必要がある
            self.chat = pytchat.create(video_id=self.video_id)
            logging.info("pytchat オブジェクト作成成功")
            
            # 接続テスト
            if hasattr(self.chat, 'is_alive'):
                is_live = self.chat.is_alive()
                logging.info(f"ライブ配信状態: {is_live}")
                if not is_live:
                    logging.warning("ライブ配信が検出されていません。コメントは取得できない可能性があります。")
            
        except Exception as e:
            logging.error(f"エラー: pytchat オブジェクトの作成に失敗しました: {e}")
            logging.error("Video IDが正しいか、ライブ配信中か確認してください。")
            self.chat = None
            raise
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        非同期コンテキストマネージャーの終了時にリソースを解放します。
        """
        if self.chat and hasattr(self.chat, 'terminate'):
            try:
                self.chat.terminate()
                logging.info("pytchat オブジェクトを終了しました")
            except Exception as e:
                logging.warning(f"pytchat終了時にエラーが発生しました: {e}")
        
        logging.info(f"セッション終了統計: 取得コメント数={self.comment_count}, エラー数={self.error_count}")

    async def __get_comments(self):
        """
        pytchatからコメント一覧を非同期で取得し、JSON形式で返します。
        """
        if self.chat is None:
            logging.debug("pytchat オブジェクトが初期化されていません。")
            return None

        try:
            # 配信状態をチェック
            if hasattr(self.chat, 'is_alive') and not self.chat.is_alive():
                logging.debug("ライブ配信が終了しているか、まだ開始されていません。")
                return None

            # コメントを取得（タイムアウト付き）
            try:
                comments_data = await asyncio.wait_for(
                    asyncio.to_thread(self.chat.get),
                    timeout=3.0  # タイムアウトを3秒に延長
                )
            except asyncio.TimeoutError:
                logging.debug("コメント取得がタイムアウトしました")
                return None
            
            # コメントデータの解析
            comments_list = self._parse_comments_data(comments_data)
            
            if comments_list:
                logging.debug(f"取得したコメント数: {len(comments_list)}")
                # 最初のコメントの詳細をログ出力
                if len(comments_list) > 0:
                    first_comment = comments_list[0]
                    logging.debug(f"最初のコメント詳細: {type(first_comment)} -> {first_comment}")
            else:
                logging.debug("新しいコメントはありません。")
            
            return comments_list

        except Exception as e:
            self.error_count += 1
            logging.error(f"コメント取得中にエラーが発生しました: {e}")
            logging.error(f"エラー詳細: {type(e).__name__}")
            return None

    def _parse_comments_data(self, comments_data):
        """
        コメントデータを解析してリスト形式で返す
        """
        try:
            logging.debug(f"コメントデータの型: {type(comments_data)}")
            
            # comments_dataがChatdataオブジェクトまたは類似のオブジェクトの場合
            if hasattr(comments_data, 'items'):
                logging.debug("itemsプロパティを使用してコメントを取得")
                comments_list = list(comments_data.items)
            elif hasattr(comments_data, 'json'):
                logging.debug("json()メソッドを使用してコメントを取得")
                comments_list = comments_data.json()
            elif isinstance(comments_data, list):
                logging.debug("既にリスト形式")
                comments_list = comments_data
            else:
                # その他の場合、イテレート可能か確認
                try:
                    comments_list = list(comments_data)
                    logging.debug("イテレーション結果をリストに変換")
                except (TypeError, AttributeError):
                    logging.debug("データ形式が不明、そのままリストとして扱う")
                    comments_list = [comments_data] if comments_data else []

            # デバッグ情報の追加
            if comments_list:
                logging.debug(f"解析結果: {len(comments_list)}個のコメント")
                for i, comment in enumerate(comments_list[:3]):  # 最初の3個のコメントをチェック
                    logging.debug(f"コメント{i}: 型={type(comment)}, 内容={str(comment)[:100]}")
            
            return comments_list if comments_list else None

        except Exception as e:
            logging.error(f"コメントデータの解析に失敗しました: {e}")
            return None

    async def get_comment(self):
        """
        最新の未処理コメントを取得します。
        """
        try:
            comments = await self.__get_comments()
            if not comments:
                return None

            # 新しいコメントのみを処理（重複防止）
            new_comments = []
            for comment in comments:
                comment_id = self._extract_comment_id(comment)
                if comment_id and comment_id not in self.last_comment_ids:
                    new_comments.append(comment)
                    self.last_comment_ids.add(comment_id)

            if not new_comments:
                logging.debug("新しいコメントは見つかりませんでした。")
                return None

            # 最新のコメントを処理
            latest_comment = new_comments[-1]  # 最後のコメントが最新
            parsed_comment = self._parse_single_comment(latest_comment)
            
            if parsed_comment:
                self.comment_count += 1
                logging.info(f"新しいコメント取得成功 #{self.comment_count}")
                logging.info(f"内容: {parsed_comment['message'][:50]}...")
                logging.info(f"投稿者: {parsed_comment['author']['name']}")
            
            return parsed_comment

        except Exception as e:
            self.error_count += 1
            logging.error(f"get_comment()でエラーが発生しました: {e}")
            return None

    def _extract_comment_id(self, comment):
        """
        コメントからIDを抽出（重複防止用）
        """
        try:
            if hasattr(comment, 'id'):
                return comment.id
            elif hasattr(comment, '__dict__') and 'id' in comment.__dict__:
                return comment.__dict__['id']
            elif isinstance(comment, dict) and 'id' in comment:
                return comment['id']
            else:
                # IDが取得できない場合、メッセージと投稿者名でハッシュを作成
                message = str(comment)[:50]  # 最初の50文字
                return hash(message + str(time.time()))
        except:
            return None

    def _parse_single_comment(self, comment):
        """
        単一のコメントを解析して統一フォーマットで返す
        """
        try:
            message = ""
            author_name = "Unknown"
            
            logging.debug(f"コメント解析開始: 型={type(comment)}")
            
            if isinstance(comment, str):
                # コメントが文字列の場合
                message = comment
                author_name = "Unknown"
                logging.debug("文字列形式のコメント")
                
            elif hasattr(comment, 'message') and hasattr(comment, 'author'):
                # pytchatのコメントオブジェクトの場合
                message = str(comment.message)
                if hasattr(comment.author, 'name'):
                    author_name = str(comment.author.name)
                else:
                    author_name = str(comment.author)
                logging.debug("pytchatオブジェクト形式のコメント")
                
            elif hasattr(comment, '__dict__'):
                # その他のオブジェクト
                comment_dict = comment.__dict__
                message = str(comment_dict.get('message',
                                            comment_dict.get('text',
                                                           comment_dict.get('content', str(comment)))))
                
                # 投稿者情報の取得
                author_info = comment_dict.get('author', {})
                if hasattr(author_info, 'name'):
                    author_name = str(author_info.name)
                elif hasattr(author_info, '__dict__') and 'name' in author_info.__dict__:
                    author_name = str(author_info.__dict__['name'])
                elif isinstance(author_info, dict) and 'name' in author_info:
                    author_name = str(author_info['name'])
                elif author_info:
                    author_name = str(author_info)
                logging.debug("オブジェクト属性形式のコメント")
                
            elif isinstance(comment, dict):
                # 辞書形式の場合
                message = comment.get('message',
                                    comment.get('text',
                                              comment.get('content', str(comment))))
                author_info = comment.get('author', {})
                if isinstance(author_info, dict):
                    author_name = author_info.get('name', 'Unknown')
                else:
                    author_name = str(author_info) if author_info else "Unknown"
                logging.debug("辞書形式のコメント")
                
            else:
                # その他の場合は文字列に変換
                message = str(comment)
                author_name = "Unknown"
                logging.debug("その他形式のコメント（文字列変換）")
                
            # メッセージの検証
            if not message or message.strip() == "" or message == "None":
                logging.debug("メッセージが空のためスキップ")
                return None
            
            # 結果をログ出力
            logging.debug(f"解析結果 - メッセージ: '{message[:100]}...', 投稿者: '{author_name}'")
            
            return {
                'message': message.strip(),
                'author': {'name': author_name}
            }
            
        except Exception as e:
            logging.error(f"コメント解析中にエラーが発生しました: {e}")
            logging.error(f"コメントデータ: {comment}")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("YouTubeCommentAdapterのテストを開始します。")
    
    # テスト用のYouTube LiveのVideo IDを設定してください
    test_video_id = "8E5Dehlo2M0"  # .envからの値を使用

    async def test_adapter():
        try:
            async with YouTubeCommentAdapter(test_video_id) as adapter:
                logging.info("コメント取得テストを開始します。")
                logging.info("ライブ配信中であることを確認してください。")
                
                # 30秒間コメントを監視
                start_time = time.time()
                test_duration = 30  # 30秒間テスト
                
                while time.time() - start_time < test_duration:
                    logging.info(f"--- 試行 {int(time.time() - start_time) + 1}秒目 ---")
                    
                    comment = await adapter.get_comment()
                    if comment:
                        message = comment.get('message', '')
                        author = comment.get('author', {}).get('name', 'Unknown')
                        logging.info(f"✓ 取得コメント: {message}")
                        logging.info(f"✓ 投稿者: {author}")
                        logging.info("=" * 50)
                    else:
                        logging.debug("新しいコメントはありません。")
                    
                    await asyncio.sleep(2)  # 2秒間隔
                
                logging.info(f"テスト完了。統計: コメント={adapter.comment_count}, エラー={adapter.error_count}")
                
        except Exception as e:
            logging.error(f"テスト中にエラーが発生しました: {e}")

    asyncio.run(test_adapter())
