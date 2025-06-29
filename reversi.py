import pyxel
from enum import Enum

class GameState(Enum):
    TITLE = 0
    PLAYING = 1
    GAME_OVER = 2

class Reversi:
    _board_weights = [
        [100, -20, 10, 5, 5, 10, -20, 100],
        [-20, -50, -2, -2, -2, -2, -50, -20],
        [10, -2, 1, 1, 1, 1, -2, 10],
        [5, -2, 1, 1, 1, 1, -2, 5],
        [5, -2, 1, 1, 1, 1, -2, 5],
        [10, -2, 1, 1, 1, 1, -2, 10],
        [-20, -50, -2, -2, -2, -2, -50, -20],
        [100, -20, 10, 5, 5, 10, -20, 100]
    ]

    def __init__(self):
        # 盤面のサイズ (8x8) とセルのサイズ
        self.board_size = 8
        self.cell_size = 22
        self.screen_size = self.board_size * self.cell_size + 40
        pyxel.init(self.screen_size, self.screen_size + 20, title="Reversi", fps=30)
        pyxel.mouse(False) # マウスカーソルを非表示

        self.game_state = GameState.TITLE
        self.player_color = 0 # 1: 黒, -1: 白 (プレイヤーが選択)

        self.cat_wins = 0 # 黒猫の勝数
        self.dog_wins = 0 # 白犬の勝数

        # アニメーション関連
        self.flipping_stones = [] # ひっくり返す石のリスト
        self.flip_index = 0       # 現在ひっくり返している石のインデックス
        self.flip_delay = 5       # 各石がひっくり返るまでのフレーム数

        # 勝者アニメーション
        self.win_animation_timer = 0
        self.win_animation_count = 0
        self.show_win_face = False

        # サウンドの定義
        # 犬が勝った時 (白)
        pyxel.sounds[0].set(
            notes='g4c4b3a3g4c4b3a3g4f4e4d4c4', # オクターブを調整
            tones='t',
            volumes='4',
            effects='n',
            speed=10
        )
        # 猫が勝った時 (黒)
        pyxel.sounds[1].set(
            notes='c4g4c4g4c4g4c4g4', # オクターブを2つ上げる
            tones='s',
            volumes='3',
            effects='n',
            speed=15
        )
        # 石がひっくり返る音 (猫: 黒)
        pyxel.sounds[2].set(
            notes='c4', # オクターfブを2つ上げる
            tones='t',
            volumes='3',
            effects='n',
            speed=10
        )
        # 石がひっくり返る音 (犬: 白)
        pyxel.sounds[3].set(
            notes='g4', # オクターブを2つ上げる
            tones='t',
            volumes='3',
            effects='n',
            speed=10
        )
        # 無効な手のエラー音
        pyxel.sounds[4].set(
            notes='c3', # オクターブを3つ上げる
            tones='p',
            volumes='4',
            effects='n',
            speed=10
        )

        pyxel.run(self.update, self.draw)

    def reset(self):
        """ゲームの状態を初期化する"""
        self.board = [[0] * self.board_size for _ in range(self.board_size)]
        self.setup_board()
        self.current_player = 1  # 1: 黒, -1: 白
        self.game_over = False
        self.winner = 0 # 0: 引き分け, 1: 黒の勝ち, -1: 白の勝ち
        self.game_state = GameState.PLAYING # ゲーム開始状態に設定
        pyxel.stop() # サウンドを停止

        self.flipping_stones = []
        self.flip_index = 0

    def setup_board(self):
        """中央に4つの石を初期配置する"""
        center = self.board_size // 2
        self.board[center - 1][center - 1] = -1  # 白
        self.board[center - 1][center] = 1      # 黒
        self.board[center][center - 1] = 1      # 黒
        self.board[center][center] = -1      # 白

    def update(self):
        """ゲームのロジックを更新する"""
        if self.game_state == GameState.TITLE:
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                # 黒を選択
                if 50 <= pyxel.mouse_x <= 150 and 100 <= pyxel.mouse_y <= 150:
                    self.player_color = 1
                    self.reset()
                # 白を選択
                elif 50 <= pyxel.mouse_x <= 150 and 170 <= pyxel.mouse_y <= 220:
                    self.player_color = -1
                    self.reset()
            return

        if self.game_state == GameState.PLAYING or self.game_state == GameState.GAME_OVER:
            # RESTARTボタンのクリック検出
            button_x = self.screen_size // 2 - 30
            button_y = self.screen_size + 5
            button_width = 60
            button_height = 15
            if pyxel.btnp(pyxel.KEY_R) or (pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and \
               button_x <= pyxel.mouse_x <= button_x + button_width and \
               button_y <= pyxel.mouse_y <= button_y + button_height):
                self.game_state = GameState.TITLE # タイトル画面に戻る
            if self.game_state == GameState.GAME_OVER:
                # 勝者アニメーションの更新
                if self.winner != 0 and self.win_animation_count < 4: # 2回表情を変える (通常→特殊→通常→特殊)
                    self.win_animation_timer += 1
                    if self.win_animation_timer > 15: # 0.5秒ごとに表情を切り替え
                        self.win_animation_timer = 0
                        self.show_win_face = not self.show_win_face
                        self.win_animation_count += 1
                return

        if self.game_state == GameState.PLAYING:
            # 石をひっくり返すアニメーション中
            if self.flipping_stones:
                if pyxel.frame_count % self.flip_delay == 0:
                    if self.flip_index < len(self.flipping_stones):
                        r, c = self.flipping_stones[self.flip_index]
                        self.board[r][c] = self.current_player
                        # ひっくり返す音を再生
                        if self.current_player == 1: # 黒猫
                            pyxel.play(1, 2) # チャンネル1でサウンド2を再生
                        else: # 白犬
                            pyxel.play(1, 3) # チャンネル1でサウンド3を再生
                        self.flip_index += 1
                    else:
                        # アニメーション終了
                        self.flipping_stones = []
                        self.flip_index = 0
                        self.current_player *= -1 # プレイヤーを交代
                        self.check_game_over()
                return # アニメーション中は他の入力を受け付けない

            # プレイヤーのターン
            if self.current_player == self.player_color:
                if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                    offset = 20
                    board_pixel_size = self.board_size * self.cell_size
                    mouse_x = pyxel.mouse_x
                    mouse_y = pyxel.mouse_y

                    # 盤面の内側かチェック
                    if offset <= mouse_x < offset + board_pixel_size and offset <= mouse_y < offset + board_pixel_size:
                        c = (mouse_x - offset) // self.cell_size
                        r = (mouse_y - offset) // self.cell_size
                        
                        stones_to_flip = self.is_valid_move(r, c)
                        if stones_to_flip:
                            self.board[r][c] = self.current_player # 置いた石は即座に表示
                            self.flip_stones(stones_to_flip) # ひっくり返す石をセット
                            # プレイヤー交代とゲームオーバーチェックはアニメーション終了後に行う
                        else:
                            pyxel.play(2, 4) # 無効な手のエラー音
            # コンピューターのターン
            else:
                # 少し待ってから手を打つ (UXのため)
                if pyxel.frame_count % 30 == 0: # 1秒に1回程度
                    self._computer_move()

    def is_valid_move(self, r, c):
        """指定されたマスに石を置けるか、裏返せる石のリストを返す"""
        if self.board[r][c] != 0:
            return []

        stones_to_flip = []
        # 8方向をチェック
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue

                temp_flip = []
                nr, nc = r + dr, c + dc

                while 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if self.board[nr][nc] == -self.current_player:
                        temp_flip.append((nr, nc))
                    elif self.board[nr][nc] == self.current_player:
                        # ここでtemp_flipをソートして追加
                        # 置いた場所からの距離でソート
                        temp_flip.sort(key=lambda x: abs(x[0] - r) + abs(x[1] - c))
                        stones_to_flip.extend(temp_flip)
                        break
                    else: # 空白マス
                        break
                    nr += dr
                    nc += dc
        return stones_to_flip

    def flip_stones(self, stones_to_flip):
        """指定された石を裏返す (アニメーション用) """
        # 置いた石からの距離でソート
        # (r, c) は置いた石の座標
        # stones_to_flip は (nr, nc) のリスト
        # ここでは、stones_to_flip がすでに適切な順序で渡されることを期待する
        self.flipping_stones = stones_to_flip
        self.flip_index = 0

    def check_game_over(self):
        """ゲームの終了をチェックする"""
        if not self.has_valid_moves(self.current_player):
            self.current_player *= -1 # パス
            if not self.has_valid_moves(self.current_player):
                self.game_over = True
                self.calculate_winner()
                self.game_state = GameState.GAME_OVER # ゲーム終了状態に設定

    def has_valid_moves(self, player):
        """指定されたプレイヤーが石を置ける場所があるか"""
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.is_valid_move(r, c):
                    return True
        return False

    def _computer_move(self):
        """コンピューターの思考ロジック"""
        best_moves = []
        max_score = -float('inf')

        for r in range(self.board_size):
            for c in range(self.board_size):
                stones_to_flip = self.is_valid_move(r, c)
                if stones_to_flip:
                    # スコア計算: ひっくり返せる石の数 + マスの重み
                    score = len(stones_to_flip) + self._board_weights[r][c]

                    if score > max_score:
                        max_score = score
                        best_moves = [(r, c, stones_to_flip)]
                    elif score == max_score:
                        best_moves.append((r, c, stones_to_flip))
        
        if best_moves:
            import random
            r, c, stones_to_flip = random.choice(best_moves)
            self.board[r][c] = self.current_player # 置いた石は即座に表示
            self.flip_stones(stones_to_flip) # ひっくり返す石をセット
        else:
            # 有効な手がない場合、パス
            self.current_player *= -1
            self.check_game_over()

    def start_win_animation(self):
        """勝者アニメーションを開始する"""
        self.win_animation_timer = 0
        self.win_animation_count = 0
        self.show_win_face = True # 最初は特殊な顔から

    def calculate_winner(self):
        """勝者を計算する"""
        black_stones = sum(row.count(1) for row in self.board)
        white_stones = sum(row.count(-1) for row in self.board)
        if black_stones > white_stones:
            self.winner = 1
            self.cat_wins += 1
            pyxel.play(0, 1) # 猫が勝ったテーマ
            self.start_win_animation()
        elif white_stones > black_stones:
            self.winner = -1
            self.dog_wins += 1
            pyxel.play(0, 0) # 犬が勝ったテーマ
            self.start_win_animation()
        else:
            self.winner = 0

    def draw(self):
        """画面を描画する"""
        pyxel.cls(3)  # 背景を緑色にする

        if self.game_state == GameState.TITLE:
            self._draw_title_text()
            pyxel.text(self.screen_size // 2 - 40, 70, "SELECT YOUR COLOR", 7)
            pyxel.rect(50, 100, 100, 50, 0) # 黒の選択ボタン
            pyxel.text(75, 115, "BLACK", 7)
            pyxel.rect(50, 170, 100, 50, 7) # 白の選択ボタン
            pyxel.text(75, 185, "WHITE", 0)
            return

        # 盤面の線を描画
        board_pixel_size = self.board_size * self.cell_size
        offset = 20
        for i in range(self.board_size + 1):
            # 縦線
            pyxel.line(offset + i * self.cell_size, offset, offset + i * self.cell_size, offset + board_pixel_size, 7)
            # 横線
            pyxel.line(offset, offset + i * self.cell_size, offset + board_pixel_size, offset + i * self.cell_size, 7)

        # 石を描画
        for r in range(self.board_size):
            for c in range(self.board_size):
                x = offset + c * self.cell_size + self.cell_size // 2
                y = offset + r * self.cell_size + self.cell_size // 2
                radius = self.cell_size // 2 - 3

                stone_player = self.board[r][c]
                is_winner_stone = (self.game_state == GameState.GAME_OVER and self.winner == stone_player)
                show_special_face = is_winner_stone and self.show_win_face

                if stone_player == 1:  # 黒い石
                    self._draw_black_cat(x, y, radius, show_special_face)
                elif stone_player == -1:  # 白い石
                    self._draw_white_dog(x, y, radius, show_special_face)

        # ひっくり返るアニメーション中の石を描画
        if self.flipping_stones:
            for i, (r, c) in enumerate(self.flipping_stones):
                if i >= self.flip_index:
                    break # まだひっくり返っていない石は描画しない
                x = offset + c * self.cell_size + self.cell_size // 2
                y = offset + r * self.cell_size + self.cell_size // 2
                radius = self.cell_size // 2 - 3
                
                # ひっくり返った後の色で描画
                if self.current_player == 1: # 次のプレイヤーが黒なら、ひっくり返った石は黒
                    self._draw_black_cat(x, y, radius, False)
                else: # 次のプレイヤーが白なら、ひっくり返った石は白
                    self._draw_white_dog(x, y, radius, False)
        
        # メッセージを表示
        if self.game_state == GameState.GAME_OVER:
            if self.winner == 1:
                msg = "BLACK CAT WINS!"
            elif self.winner == -1:
                msg = "WHITE DOG WINS!"
            else:
                msg = "DRAW!"
            pyxel.text(self.screen_size // 2 - 20, self.screen_size - 15, msg, 7)
        else:
            player_text = "BLACK CAT's Turn" if self.current_player == 1 else "WHITE DOG's Turn"
            pyxel.text(25, self.screen_size - 15, player_text, 7)

        # RESTARTボタンを描画
        if self.game_state == GameState.PLAYING or self.game_state == GameState.GAME_OVER:
            button_x = self.screen_size // 2 - 30
            button_y = self.screen_size + 5
            button_width = 60
            button_height = 15
            pyxel.rect(button_x, button_y, button_width, button_height, 1) # ボタンの背景 (青)
            pyxel.text(button_x + 8, button_y + 4, "RESTART", 7) # ボタンのテキスト (白)


    def _draw_black_cat(self, x, y, radius, winning_face=False):
        # 黒猫の顔 (円)
        pyxel.circ(x, y, radius, 0) # 黒

        # 耳 (三角形) - 非常にシンプルに
        # 顔の円の上部に配置
        pyxel.tri(x - radius * 0.7, y - radius * 0.7,
                  x - radius * 0.2, y - radius * 0.7,
                  x - radius * 0.45, y - radius * 1.2, 0)
        pyxel.tri(x + radius * 0.2, y - radius * 0.7,
                  x + radius * 0.7, y - radius * 0.7,
                  x + radius * 0.45, y - radius * 1.2, 0)

        # 目 (小さな円)
        eye_radius = radius * 0.15
        eye_offset_x = radius * 0.3
        eye_offset_y = radius * 0.2
        pyxel.circ(x - eye_offset_x, y - eye_offset_y, eye_radius, 14) # 目
        pyxel.circ(x + eye_offset_x, y - eye_offset_y, eye_radius, 14) # 目

        if winning_face:
            # 口を丸く開ける
            mouth_radius = radius * 0.3
            pyxel.circ(x, y + radius * 0.5, mouth_radius, 8) # 赤い口

    def _draw_white_dog(self, x, y, radius, winning_face=False):
        # 白犬の顔 (円)
        pyxel.circ(x, y, radius, 7) # 白

        # 耳 (三角形) - 非常にシンプルに
        pyxel.tri(x - radius * 0.7, y - radius * 0.7,
                  x - radius * 0.2, y - radius * 0.7,
                  x - radius * 0.45, y - radius * 1.2, 7) # 白
        pyxel.tri(x + radius * 0.2, y - radius * 0.7,
                  x + radius * 0.7, y - radius * 0.7,
                  x + radius * 0.45, y - radius * 1.2, 7) # 白

        # 鼻 (小さな黒い円)
        pyxel.circ(x, y + radius * 0.3, radius * 0.2, 0) # 黒

        # 目 (小さな黒い円)
        eye_radius = radius * 0.15
        eye_offset_x = radius * 0.3
        eye_offset_y = radius * 0.2
        pyxel.circ(x - eye_offset_x, y - eye_offset_y, eye_radius, 0) # 目
        pyxel.circ(x + eye_offset_x, y - eye_offset_y, eye_radius, 0) # 目

        if winning_face:
            # 舌をペロッと出す
            tongue_x = x
            tongue_y = y + radius * 0.6 # 舌の位置を少し下げる
            tongue_w = radius * 0.4
            tongue_h = radius * 0.6
            pyxel.rect(tongue_x - tongue_w / 2, tongue_y, tongue_w, tongue_h, 8) # ピンクの舌

    def _draw_title_text(self):
        # "Cats + Dogs" を図形で描画
        title_y = 30
        piece_radius = 20 # タイトル用の駒のサイズ
        line_color = 7 # 白

        # 黒猫の駒を描画
        cat_x = self.screen_size // 2 - 60
        cat_y = title_y
        self._draw_black_cat(cat_x, cat_y, piece_radius, False)
        # 黒猫の勝数を表示
        pyxel.text(cat_x + piece_radius + 5, cat_y, str(self.cat_wins), 7)

        # 横棒を描画
        line_x1 = self.screen_size // 2 - 15
        line_x2 = self.screen_size // 2 + 15
        line_y = title_y
        pyxel.line(line_x1, line_y, line_x2, line_y, line_color)

        # 白犬の駒を描画
        dog_x = self.screen_size // 2 + 60
        dog_y = title_y
        self._draw_white_dog(dog_x, dog_y, piece_radius, False)
        # 白犬の勝数を表示
        pyxel.text(dog_x + piece_radius + 5, dog_y, str(self.dog_wins), 7)

Reversi()