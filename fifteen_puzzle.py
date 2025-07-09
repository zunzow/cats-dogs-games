import pyxel
import random

# --- 定数 ---
SCREEN_WIDTH = 200
SCREEN_HEIGHT = 220
BOARD_SIZE = 4
TILE_SIZE = 48
# リソースファイル (fifteen_puzzle.pyxres) には、
# 48x48ピクセルのタイル画像を4x4のグリッド状に配置してください。
# 全体で192x192ピクセル (48*4 x 48*4) の画像が必要です。
BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_SIZE * TILE_SIZE) // 2
BOARD_OFFSET_Y = (SCREEN_HEIGHT - BOARD_SIZE * TILE_SIZE) // 2 + 10 # タイトル用に少し下げる

class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="15 Puzzle", fps=30)
        pyxel.load("fifteen_puzzle.pyxres")
        pyxel.mouse(False)
        self.image_bank = 0 # 使用する画像バンク
        self.reset()
        pyxel.run(self.update, self.draw)

    def get_inversion_count(self, arr):
        """リストの転置数を計算する"""
        inversions = 0
        # 0は無視する
        flat_list = [i for i in arr if i != 0]
        for i in range(len(flat_list)):
            for j in range(i + 1, len(flat_list)):
                if flat_list[i] > flat_list[j]:
                    inversions += 1
        return inversions

    def reset(self):
        """ゲームの状態を初期化する"""
        self.image_bank = random.randint(0, 2) # IMAGE 0, 1, 2 からランダムに選択
        self.is_cleared = False
        self.restart_sequence_count = 0
        
        # 1から15までの数字リストを作成
        tiles = list(range(1, BOARD_SIZE * BOARD_SIZE))
        
        # 解ける配置になるまでシャッフルを繰り返す
        while True:
            random.shuffle(tiles)
            inversions = self.get_inversion_count(tiles)
            # 4x4パズルの場合、転置数が偶数なら可解 (空きマスが右下にあると仮定するため)
            if inversions % 2 == 0:
                break
        
        # 盤面に配置し、最後に空きマス(0)を追加
        tiles.append(0)
        self.board = []
        for i in range(BOARD_SIZE):
            row = tiles[i * BOARD_SIZE : (i + 1) * BOARD_SIZE]
            self.board.append(row)
        
        # 空きマスの位置を記録
        self.empty_pos = [BOARD_SIZE - 1, BOARD_SIZE - 1]

    def update(self):
        """ゲームのロジックを更新する"""
        if pyxel.btnp(pyxel.KEY_R):
            self.reset()

        if self.is_cleared:
            # クリア後、1から15まで順番にクリックされたらリスタートする
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                mouse_x, mouse_y = pyxel.mouse_x, pyxel.mouse_y
                tx = (mouse_x - BOARD_OFFSET_X) // TILE_SIZE
                ty = (mouse_y - BOARD_OFFSET_Y) // TILE_SIZE

                if 0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE:
                    clicked_num = self.board[ty][tx]
                    if clicked_num == self.restart_sequence_count + 1:
                        self.restart_sequence_count += 1
                        if self.restart_sequence_count == 15:
                            self.reset()
                    # 違うタイルをクリックしたらリセット
                    elif clicked_num != 0:
                        self.restart_sequence_count = 0
            return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            mouse_x, mouse_y = pyxel.mouse_x, pyxel.mouse_y
            
            # クリックされたタイル座標を計算
            tx = (mouse_x - BOARD_OFFSET_X) // TILE_SIZE
            ty = (mouse_y - BOARD_OFFSET_Y) // TILE_SIZE

            if 0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE:
                ex, ey = self.empty_pos
                # 空きマスと隣接しているかチェック
                if (abs(tx - ex) == 1 and ty == ey) or (tx == ex and abs(ty - ey) == 1):
                    # タイルを入れ替え
                    self.board[ey][ex] = self.board[ty][tx]
                    self.board[ty][tx] = 0
                    self.empty_pos = [tx, ty]
                    
                    # クリアチェック
                    self.check_clear()

    def draw(self):
        """画面を描画する"""
        pyxel.cls(1) # 背景色: 濃い青
        pyxel.text(SCREEN_WIDTH // 2 - 24, 5, "15 PUZZLE", 7)

        # 1行あたりのタイル数を4に設定
        TILES_PER_ROW = 4

        # 盤面を描画
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                tile_num = self.board[y][x]
                draw_x = BOARD_OFFSET_X + x * TILE_SIZE
                draw_y = BOARD_OFFSET_Y + y * TILE_SIZE

                if tile_num > 0:
                    # リソースファイル上のタイルの位置(u, v)を計算 (4x4グリッド配置を想定)
                    tile_index = tile_num - 1 # 0-15
                    u = (tile_index % TILES_PER_ROW) * TILE_SIZE
                    v = (tile_index // TILES_PER_ROW) * TILE_SIZE
                    # 画像を描画 (ランダムに選択された画像バンクを使用)
                    pyxel.blt(draw_x, draw_y, self.image_bank, u, v, TILE_SIZE, TILE_SIZE, 0)
                    
                    # 画像の上に白い文字で数字を右下に描画
                    num_str = str(tile_num)
                    text_w = len(num_str) * 4
                    text_x = draw_x + TILE_SIZE - text_w - 2 # 右端から2px内側
                    text_y = draw_y + TILE_SIZE - 6 - 2      # 下端から2px内側
                    # 黒い影をつけて見やすくする
                    pyxel.text(text_x + 1, text_y + 1, num_str, 0)
                    pyxel.text(text_x, text_y, num_str, 7) # 7は白
        
        # クリアメッセージ
        if self.is_cleared:
            # 最後のマスに16番目の絵柄を表示
            ex, ey = self.empty_pos
            draw_x = BOARD_OFFSET_X + ex * TILE_SIZE
            draw_y = BOARD_OFFSET_Y + ey * TILE_SIZE
            
            tile_index = BOARD_SIZE * BOARD_SIZE - 1 # 15
            u = (tile_index % TILES_PER_ROW) * TILE_SIZE
            v = (tile_index // TILES_PER_ROW) * TILE_SIZE
            pyxel.blt(draw_x, draw_y, self.image_bank, u, v, TILE_SIZE, TILE_SIZE, 0)

            # リスタート指示文を盤面の上部中央に配置
            restart_msg = "TAP 1-15 IN ORDER TO RESTART"
            restart_x = SCREEN_WIDTH // 2 - (len(restart_msg) * 4) // 2
            restart_y = BOARD_OFFSET_Y - 10 # 盤面の上から10px上
            pyxel.text(restart_x, restart_y, restart_msg, 7)

    def check_clear(self):
        """クリアしたかどうかをチェックする"""
        expected_num = 1
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                # 最後のマスは空きマス(0)のはず
                if y == BOARD_SIZE - 1 and x == BOARD_SIZE - 1:
                    if self.board[y][x] == 0:
                        continue
                    else:
                        self.is_cleared = False
                        return
                
                if self.board[y][x] != expected_num:
                    self.is_cleared = False
                    return
                expected_num += 1
        
        # すべてのタイルが正しければクリア
        self.is_cleared = True

App()