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
        self.is_demo_mode = False # Trueの場合、コンピュータ同士の対戦

        self.cat_wins = 0 # 黒猫の勝数
        self.dog_wins = 0 # 白犬の勝数

        # アニメーション関連
        self.flipping_stones = [] # ひっくり返す石のリスト
        self.flip_index = 0       # 現在ひっくり返している石のインデックス
        self.flip_delay = 5       # 各石がひっくり返るまでのフレーム数

        # ゲーム終了時のアニメーション
        self.game_over_animation_timer = 0
        self.game_over_animation_count = 0
        self.show_special_face = False # 特殊な表情を表示するか

        # サウンドの定義
        pyxel.sounds[0].set('g4c4b3a3g4c4b3a3g4f4e4d4c4', 't', '4', 'n', 10) # 犬が勝った時 (白)
        pyxel.sounds[1].set('c4g4c4g4c4g4c4g4', 's', '3', 'n', 15) # 猫が勝った時 (黒)
        pyxel.sounds[2].set('c4', 't', '3', 'n', 10) # 石がひっくり返る音 (猫: 黒)
        pyxel.sounds[3].set('g4', 't', '3', 'n', 10) # 石がひっくり返る音 (犬: 白)
        pyxel.sounds[4].set('c3', 'p', '4', 'n', 10) # 無効な手のエラー音

        pyxel.run(self.update, self.draw)

    def reset(self):
        """ゲームの状態を初期化する"""
        self.board = [[0] * self.board_size for _ in range(self.board_size)]
        self.setup_board()
        self.current_player = 1  # 1: 黒, -1: 白
        self.game_over = False
        self.winner = 0 # 0: 引き分け, 1: 黒の勝ち, -1: 白の勝ち
        self.game_state = GameState.PLAYING
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
            button_w, button_h = 60, 30
            button_x = self.screen_size // 2 - 30
            black_button_y = 100
            white_button_y = black_button_y + button_h + 20
            demo_button_x, demo_button_y, demo_button_w, demo_button_h = self.screen_size // 2 - 30, self.screen_size + 5, 60, 15

            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                # 黒選択ボタンのクリック検出
                if button_x <= pyxel.mouse_x <= button_x + button_w and black_button_y <= pyxel.mouse_y <= black_button_y + button_h:
                    self.player_color, self.is_demo_mode = 1, False
                    self.reset()
                # 白選択ボタンのクリック検出
                elif button_x <= pyxel.mouse_x <= button_x + button_w and white_button_y <= pyxel.mouse_y <= white_button_y + button_h:
                    self.player_color, self.is_demo_mode = -1, False
                    self.reset()
                # DEMOボタンのクリック検出
                elif demo_button_x <= pyxel.mouse_x <= demo_button_x + demo_button_w and demo_button_y <= pyxel.mouse_y <= demo_button_y + demo_button_h:
                    self.is_demo_mode, self.player_color = True, 0
                    self.reset()
            return

        # ゲーム中またはゲームオーバー時のRESTARTボタン処理
        if self.game_state in [GameState.PLAYING, GameState.GAME_OVER]:
            button_x, button_y, button_w, button_h = self.screen_size // 2 - 30, self.screen_size + 5, 60, 15
            if pyxel.btnp(pyxel.KEY_R) or (pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and \
               button_x <= pyxel.mouse_x <= button_x + button_w and \
               button_y <= pyxel.mouse_y <= button_y + button_h):
                self.game_state, self.is_demo_mode = GameState.TITLE, False # タイトルに戻りデモモード解除
            
            # ゲームオーバー時のアニメーション更新
            if self.game_state == GameState.GAME_OVER:
                if self.winner != 0 and self.game_over_animation_count < 4:
                    self.game_over_animation_timer += 1
                    if self.game_over_animation_timer > 15: # 0.5秒ごとに表情を切り替え
                        self.game_over_animation_timer = 0
                        self.show_special_face = not self.show_special_face
                        self.game_over_animation_count += 1
                return

        if self.game_state == GameState.PLAYING:
            # 石をひっくり返すアニメーション中
            if self.flipping_stones:
                if pyxel.frame_count % self.flip_delay == 0:
                    if self.flip_index < len(self.flipping_stones):
                        r, c = self.flipping_stones[self.flip_index]
                        self.board[r][c] = self.current_player
                        pyxel.play(1, 2 if self.current_player == 1 else 3) # ひっくり返す音
                        self.flip_index += 1
                    else:
                        # アニメーション終了
                        self.flipping_stones, self.flip_index = [], 0
                        self.current_player *= -1 # プレイヤー交代
                        self.check_game_over()
                return # アニメーション中は他の入力を受け付けない

            # コンピュータのターンか判定
            is_computer_turn = self.is_demo_mode or self.current_player != self.player_color
            if is_computer_turn:
                if pyxel.frame_count % 15 == 0: # 少し待ってから手を打つ
                    self._computer_move()
            # プレイヤーのターン
            elif pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                offset, board_size = 20, self.board_size * self.cell_size
                if offset <= pyxel.mouse_x < offset + board_size and offset <= pyxel.mouse_y < offset + board_size:
                    c, r = (pyxel.mouse_x - offset) // self.cell_size, (pyxel.mouse_y - offset) // self.cell_size
                    stones_to_flip = self.is_valid_move(r, c)
                    if stones_to_flip:
                        self.board[r][c] = self.current_player # 石を置く
                        self.flip_stones(stones_to_flip) # 裏返す石をセット
                    else:
                        pyxel.play(2, 4) # 無効な手のエラー音

    def is_valid_move(self, r, c):
        """指定されたマスに石を置けるか、裏返せる石のリストを返す"""
        if self.board[r][c] != 0: return []
        stones_to_flip = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                temp_flip, nr, nc = [], r + dr, c + dc
                while 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if self.board[nr][nc] == -self.current_player:
                        temp_flip.append((nr, nc))
                    elif self.board[nr][nc] == self.current_player:
                        temp_flip.sort(key=lambda p: abs(p[0] - r) + abs(p[1] - c))
                        stones_to_flip.extend(temp_flip)
                        break
                    else: break # 空白マス
                    nr, nc = nr + dr, nc + dc
        return stones_to_flip

    def flip_stones(self, stones_to_flip):
        """指定された石を裏返すアニメーションの準備"""
        self.flipping_stones, self.flip_index = stones_to_flip, 0

    def check_game_over(self):
        """ゲームの終了をチェックする"""
        if not self.has_valid_moves(self.current_player):
            self.current_player *= -1 # パス
            if not self.has_valid_moves(self.current_player):
                self.game_over, self.game_state = True, GameState.GAME_OVER
                self.calculate_winner()

    def has_valid_moves(self, player):
        """指定されたプレイヤーが石を置ける場所があるか"""
        return any(self.is_valid_move(r, c) for r in range(self.board_size) for c in range(self.board_size))

    def _computer_move(self):
        """コンピューターの思考ロジック"""
        best_moves, max_score = [], -float('inf')
        for r in range(self.board_size):
            for c in range(self.board_size):
                stones = self.is_valid_move(r, c)
                if stones:
                    # スコア計算: ひっくり返せる石の数 + マスの重み
                    score = len(stones) + self._board_weights[r][c]
                    if score > max_score:
                        max_score, best_moves = score, [(r, c, stones)]
                    elif score == max_score:
                        best_moves.append((r, c, stones))
        if best_moves:
            import random
            r, c, stones = random.choice(best_moves)
            self.board[r][c] = self.current_player
            self.flip_stones(stones)
        else:
            # 有効な手がない場合はパス
            self.current_player *= -1
            self.check_game_over()

    def start_game_over_animation(self):
        """ゲーム終了時のアニメーションを開始する"""
        self.game_over_animation_timer, self.game_over_animation_count, self.show_special_face = 0, 0, True

    def calculate_winner(self):
        """勝者を計算する"""
        black = sum(row.count(1) for row in self.board)
        white = sum(row.count(-1) for row in self.board)
        if black > white:
            self.winner, self.cat_wins = 1, self.cat_wins + 1
            pyxel.play(0, 1) # 猫の勝利音
        elif white > black:
            self.winner, self.dog_wins = -1, self.dog_wins + 1
            pyxel.play(0, 0) # 犬の勝利音
        else: self.winner = 0
        if self.winner != 0: self.start_game_over_animation()

    def draw(self):
        """画面を描画する"""
        pyxel.cls(3) # 背景色
        if self.game_state == GameState.TITLE:
            self._draw_title_text()
            pyxel.text(self.screen_size // 2 - 40, 70, "SELECT YOUR COLOR", 7)
            
            # 色選択ボタン
            button_w, button_h = 60, 30
            button_x = self.screen_size // 2 - 30
            black_button_y = 100
            pyxel.rect(button_x, black_button_y, button_w, button_h, 0)
            pyxel.text(button_x + 18, black_button_y + 12, "BLACK", 7)
            white_button_y = black_button_y + button_h + 20
            pyxel.rect(button_x, white_button_y, button_w, button_h, 7)
            pyxel.text(button_x + 18, white_button_y + 12, "WHITE", 0)

            # DEMOボタン
            demo_x, demo_y, demo_w, demo_h = self.screen_size // 2 - 30, self.screen_size + 5, 60, 15
            pyxel.rect(demo_x, demo_y, demo_w, demo_h, 1)
            pyxel.text(demo_x + 18, demo_y + 4, "DEMO", 7)
            return

        # 盤面の描画
        offset, board_size = 20, self.board_size * self.cell_size
        for i in range(self.board_size + 1):
            pyxel.line(offset + i * self.cell_size, offset, offset + i * self.cell_size, offset + board_size, 7)
            pyxel.line(offset, offset + i * self.cell_size, offset + board_size, offset + i * self.cell_size, 7)

        # 石の描画
        for r in range(self.board_size):
            for c in range(self.board_size):
                stone = self.board[r][c]
                if stone == 0: continue
                x, y, radius = offset + c * self.cell_size + 11, offset + r * self.cell_size + 11, self.cell_size // 2 - 3
                win, lose = False, False
                if self.game_state == GameState.GAME_OVER and self.winner != 0 and self.show_special_face:
                    win, lose = (self.winner == stone), (self.winner == -stone)
                if stone == 1: self._draw_black_cat(x, y, radius, win, lose)
                else: self._draw_white_dog(x, y, radius, win, lose)

        # メッセージの表示
        if self.game_state == GameState.GAME_OVER:
            msg = "DRAW!" if self.winner == 0 else ("BLACK CAT WINS!" if self.winner == 1 else "WHITE DOG WINS!")
            pyxel.text(self.screen_size // 2 - len(msg) * 2, self.screen_size - 15, msg, 7)
        else:
            player = "BLACK CAT" if self.current_player == 1 else "WHITE DOG"
            player_text = f"{player}'s Turn" if not self.is_demo_mode else "DEMO MODE"
            pyxel.text(25, self.screen_size - 15, player_text, 7)

        # RESTARTボタンの描画
        if self.game_state in [GameState.PLAYING, GameState.GAME_OVER]:
            x, y, w, h = self.screen_size // 2 - 30, self.screen_size + 5, 60, 15
            pyxel.rect(x, y, w, h, 1); pyxel.text(x + 8, y + 4, "RESTART", 7)

    def _draw_black_cat(self, x, y, radius, winning_face=False, losing_face=False):
        # 顔と耳
        pyxel.circ(x, y, radius, 0)
        pyxel.tri(x - radius*0.7, y - radius*0.7, x - radius*0.2, y - radius*0.7, x - radius*0.45, y - radius*1.2, 0)
        pyxel.tri(x + radius*0.2, y - radius*0.7, x + radius*0.7, y - radius*0.7, x + radius*0.45, y - radius*1.2, 0)
        
        # 目
        eye_r, eye_ox, eye_oy = radius * 0.15, radius * 0.3, radius * 0.2
        pyxel.circ(x - eye_ox, y - eye_oy, eye_r, 14)
        pyxel.circ(x + eye_ox, y - eye_oy, eye_r, 14)

        # 表情
        if winning_face:
            # にっこりした口
            mouth_y = y + radius * 0.4
            pyxel.line(x - 4, mouth_y, x - 2, mouth_y + 2, 8); pyxel.line(x - 2, mouth_y + 2, x + 2, mouth_y + 2, 8); pyxel.line(x + 2, mouth_y + 2, x + 4, mouth_y, 8)
        elif losing_face:
            # 口を丸く開ける
            pyxel.circ(x, y + radius * 0.5, radius * 0.3, 8)

    def _draw_white_dog(self, x, y, radius, winning_face=False, losing_face=False):
        # 顔と耳
        pyxel.circ(x, y, radius, 7)
        pyxel.tri(x - radius*0.7, y - radius*0.7, x - radius*0.2, y - radius*0.7, x - radius*0.45, y - radius*1.2, 7)
        pyxel.tri(x + radius*0.2, y - radius*0.7, x + radius*0.7, y - radius*0.7, x + radius*0.45, y - radius*1.2, 7)

        # 目と鼻
        eye_r, eye_ox, eye_oy = radius * 0.15, radius * 0.3, radius * 0.2
        pyxel.circ(x - eye_ox, y - eye_oy, eye_r, 0)
        pyxel.circ(x + eye_ox, y - eye_oy, eye_r, 0)
        pyxel.circ(x, y + radius * 0.3, radius * 0.2, 0) # 鼻は常に表示

        # 表情
        if winning_face:
            # にっこりした口
            mouth_y = y + radius * 0.4
            pyxel.line(x - 4, mouth_y, x - 2, mouth_y + 2, 8); pyxel.line(x - 2, mouth_y + 2, x + 2, mouth_y + 2, 8); pyxel.line(x + 2, mouth_y + 2, x + 4, mouth_y, 8)
        elif losing_face:
            # 舌を出す
            pyxel.rect(x - radius*0.2, y + radius*0.6, radius*0.4, radius*0.6, 8)

    def _draw_title_text(self):
        """タイトル画面のキャラクターと勝数を描画"""
        y, r = 30, 20
        cat_x, dog_x = self.screen_size // 2 - 60, self.screen_size // 2 + 60
        self._draw_black_cat(cat_x, y, r)
        pyxel.text(cat_x + r + 5, y, str(self.cat_wins), 7)
        pyxel.line(self.screen_size//2 - 15, y, self.screen_size//2 + 15, y, 7)
        self._draw_white_dog(dog_x, y, r)
        pyxel.text(dog_x + r + 5, y, str(self.dog_wins), 7)

Reversi()
