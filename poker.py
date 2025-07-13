import pyxel
import random
from enum import Enum

# --- Core Card Game Classes ---

class Suit(Enum):
    """カードのスート（色）"""
    RED = "Red"
    BLUE = "Blue"
    GREEN = "Green"
    BLACK = "Black"

class Rank(Enum):
    """カードのランク（数字）"""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

class Card:
    """1枚のカードを表すクラス"""
    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{self.rank.name} of {self.suit.value}"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.rank, self.suit))

class Deck:
    """52枚のカードのデッキを表すクラス"""
    def __init__(self):
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.shuffle()

    def shuffle(self):
        """デッキをシャッフルする"""
        random.shuffle(self.cards)

    def deal(self, num_cards: int):
        """指定された枚数のカードを配る"""
        if len(self.cards) < num_cards:
            raise ValueError("Not enough cards in the deck to deal.")
        return [self.cards.pop() for _ in range(num_cards)]

class HandRank(Enum):
    """ポーカーの役の強さ"""
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9

class Hand:
    """プレイヤーの手札を表すクラス"""
    def __init__(self, cards: list[Card] = None):
        self.cards = sorted(cards, key=lambda card: card.rank.value) if cards else []

    def add_cards(self, new_cards: list[Card]):
        """手札にカードを追加する"""
        self.cards.extend(new_cards)
        self.cards.sort(key=lambda card: card.rank.value)

    def remove_cards(self, cards_to_remove: list[Card]):
        """手札からカードを削除する"""
        for card in cards_to_remove:
            if card in self.cards:
                self.cards.remove(card)
            else:
                raise ValueError(f"Card {card} not in hand.")

    def evaluate_hand(self) -> tuple[HandRank, list[int]]:
        """手札の役を判定し、役の強さとキッカーを返す"""
        ranks = [card.rank.value for card in self.cards]
        suits = [card.suit for card in self.cards]

        # 各ランクの出現回数をカウント
        rank_counts = {rank: ranks.count(rank) for rank in set(ranks)}
        counts = list(rank_counts.values())
        unique_ranks = sorted(list(set(ranks)), reverse=True)

        is_flush = len(set(suits)) == 1
        is_straight = False
        # ストレート判定 (A,2,3,4,5 の場合も考慮)
        if len(unique_ranks) == 5:
            if unique_ranks[0] - unique_ranks[4] == 4: # 通常のストレート
                is_straight = True
            elif set(unique_ranks) == {14, 2, 3, 4, 5}: # A,2,3,4,5 のストレート
                is_straight = True
                unique_ranks = [5, 4, 3, 2, 1] # 役の強さとしてAを5として扱う

        # 役の判定
        if is_straight and is_flush:
            if unique_ranks[0] == 14 and unique_ranks[1] == 13: # ロイヤルフラッシュ (10, J, Q, K, A)
                return HandRank.ROYAL_FLUSH, []
            return HandRank.STRAIGHT_FLUSH, unique_ranks # ストレートフラッシュ
        elif 4 in counts:
            four_of_a_kind_rank = [rank for rank, count in rank_counts.items() if count == 4][0]
            kicker = [rank for rank, count in rank_counts.items() if count == 1]
            return HandRank.FOUR_OF_A_KIND, [four_of_a_kind_rank] + kicker # フォーカード
        elif 3 in counts and 2 in counts:
            three_of_a_kind_rank = [rank for rank, count in rank_counts.items() if count == 3][0]
            pair_rank = [rank for rank, count in rank_counts.items() if count == 2][0]
            return HandRank.FULL_HOUSE, [three_of_a_kind_rank, pair_rank] # フルハウス
        elif is_flush:
            return HandRank.FLUSH, unique_ranks # フラッシュ
        elif is_straight:
            return HandRank.STRAIGHT, unique_ranks # ストレート
        elif 3 in counts:
            three_of_a_kind_rank = [rank for rank, count in rank_counts.items() if count == 3][0]
            kicker = [rank for rank, count in rank_counts.items() if count == 1]
            return HandRank.THREE_OF_A_KIND, [three_of_a_kind_rank] + kicker # スリーカード
        elif counts.count(2) == 2:
            pair_ranks = sorted([rank for rank, count in rank_counts.items() if count == 2], reverse=True)
            kicker = [rank for rank, count in rank_counts.items() if count == 1]
            return HandRank.TWO_PAIR, pair_ranks + kicker # ツーペア
        elif 2 in counts:
            pair_rank = [rank for rank, count in rank_counts.items() if count == 2][0]
            kicker = [rank for rank, count in rank_counts.items() if count == 1]
            return HandRank.ONE_PAIR, [pair_rank] + kicker # ワンペア
        else:
            return HandRank.HIGH_CARD, unique_ranks # ハイカード

class Player:
    """ポーカーゲームのプレイヤーを表すクラス"""
    def __init__(self, name: str, chips: int):
        self.name = name
        self.hand = Hand()
        self.chips = chips

    def __repr__(self):
        return f"Player(name='{self.name}', chips={self.chips}, hand={self.hand.cards})"

class GameState(Enum):
    START_SCREEN = 0
    BETTING = 1
    DEAL_INITIAL_CARDS = 2
    PLAYER_EXCHANGE = 3
    SHOWDOWN = 4
    CONTINUE_OR_END_GAME = 5
    GAME_OVER_DISPLAY = 6

# --- Main Poker Game Class ---

class App:
    def __init__(self):
        self.screen_w = 255
        self.screen_h = 127
        pyxel.init(self.screen_w, self.screen_h, title="Poker")

        # Card dimensions
        self.card_w = 42
        self.card_h = 56
        self.card_spacing = 5 # Space between cards
        pyxel.load("poker.pyxres")

        # ゲームの初期化
        self.deck = Deck()
        
        # プレイヤーの作成
        self.player = Player("You", 100)
        self.players = [self.player]

        # 選択されたカードのインデックス
        self.selected_cards_indices = []

        # ゲームの状態
        self.game_state = GameState.START_SCREEN

        # 賭け金関連
        self.current_bet = 10 # 現在の賭け金
        self.min_bet = 10     # 最小賭け金
        self.max_bet = 100    # 最大賭け金
        self.bet_step = 10    # 賭け金増減ステップ
        self.last_payout = 0  # 前のハンドでの配当を保存

        # 賭け金変更の連続入力用タイマー
        self.bet_change_timer = 0
        self.bet_change_delay = 5 # 5フレームごとに賭け金を変更

        # スタート画面用タイマー
        self.point_add_timer = 0 # ポイント加算用タイマー
        self.point_add_interval = 60 * 60 # 1分 (60フレーム/秒 * 60秒 = 3600フレーム) ごとに1ポイント加算

        # ゲームオーバー表示用タイマー
        self.game_over_timer = 0
        self.game_over_display_duration = 60 * 3 # 3秒間表示

        # 役の配当倍率 (例: 賭け金に対する倍率)
        self.payout_multipliers = {
            HandRank.ROYAL_FLUSH: 250,
            HandRank.STRAIGHT_FLUSH: 50,
            HandRank.FOUR_OF_A_KIND: 25,
            HandRank.FULL_HOUSE: 9,
            HandRank.FLUSH: 6,
            HandRank.STRAIGHT: 4,
            HandRank.THREE_OF_A_KIND: 3,
            HandRank.TWO_PAIR: 2,
            HandRank.ONE_PAIR: 1, # ワンペアは賭け金が戻る (1倍)
            HandRank.HIGH_CARD: 0  # ハイカードは配当なし
        }

        self.reset_full_game()
        pyxel.run(self.update, self.draw)

    def reset_hand(self):
        """各ハンドの開始時にゲームの状態をリセットする"""
        self.deck = Deck()
        for p in self.players:
            p.hand = Hand() # 手札をリセット
        self.selected_cards_indices = []
        # 前のハンドで配当があった場合、それを次の賭け金の初期値とする
        if self.last_payout > 0:
            self.current_bet = self.last_payout
        else:
            self.current_bet = self.min_bet # 配当がない場合は最小賭け金に
        self.game_state = GameState.BETTING # リセット後、BETTINGフェーズへ

    def reset_full_game(self):
        # ゲームの状態を初期化する処理をここに書きます
        self.deck = Deck()
        for p in self.players:
            p.hand = Hand() # 手札をリセット
        self.selected_cards_indices = []
        self.current_bet = self.min_bet # 初期化

        # チップが0の場合、ゲームオーバー状態を維持
        if self.player.chips <= 0:
            self.game_state = GameState.START_SCREEN
        else:
            self.game_state = GameState.START_SCREEN # リセット後、START_SCREENへ

    def _deal_initial_cards(self):
        """ゲーム開始時に各プレイヤーにカードを配る"""
        for p in self.players:
            p.hand.add_cards(self.deck.deal(5))

    def _draw_card(self, x, y, card=None, face_up=True, is_selected=False):
        """カードを描画するヘルパー関数 (シンプル版)"""
        # 選択されている場合は少し縦にずらす
        if is_selected:
            y -= 5

        # カードの枠
        pyxel.rect(x, y, self.card_w, self.card_h, 7) # 白い枠
        pyxel.rectb(x, y, self.card_w, self.card_h, 0) # 黒い縁

        if face_up and card:
            # カードの数字とマーク
            rank_str = str(card.rank.value) if card.rank.value <= 10 else card.rank.name[0]
            
            # スートの色を辞書でマッピング (色設定を変更)
            # スペード:黒, ハート:赤, クローバー:緑, ダイヤ:青
            suit_colors = {
                Suit.BLACK: 0,  # Spade -> Black
                Suit.RED: 8,    # Heart -> Red
                Suit.BLUE: 3,   # Clover -> Green
                Suit.GREEN: 1,  # Diamond -> Blue
            }
            suit_color = suit_colors[card.suit]

            pyxel.text(x + 2, y + 2, rank_str, suit_color)
            
            # ドット絵を描画
            # Large suit icon dimensions
            w_large, h_large = 8, 8
            # Small suit icon dimensions
            w_small, h_small = 4, 4

            # Get UV coordinates for large suit
            u_large, v_large = 0, 0 # v_large is always 0
            if card.suit == Suit.BLACK: # Spade
                u_large = 8
            elif card.suit == Suit.RED: # Heart
                u_large = 16
            elif card.suit == Suit.BLUE: # Clover
                u_large = 24
            elif card.suit == Suit.GREEN: # Diamond
                u_large = 32

            # Get UV coordinates for small suit
            u_small, v_small = 0, 0 # v_small is always 8
            if card.suit == Suit.BLACK: # Spade
                u_small = 8
                v_small = 8
            elif card.suit == Suit.RED: # Heart
                u_small = 16
                v_small = 8
            elif card.suit == Suit.BLUE: # Clover
                u_small = 24
                v_small = 8
            elif card.suit == Suit.GREEN: # Diamond
                u_small = 32
                v_small = 8

            # Define inner padding for pips
            inner_padding_x = 8 # From left/right edge of card
            inner_padding_y_top = 15 # Below rank text
            inner_padding_y_bottom = 15 # From bottom edge of card

            # Define common pip positions relative to card's (x, y)
            x_left = x + inner_padding_x
            x_right = x + self.card_w - inner_padding_x - w_small
            x_center = x + (self.card_w - w_small) // 2

            # Calculate available height for pips
            available_pip_height = self.card_h - inner_padding_y_top - inner_padding_y_bottom - h_small

            # Calculate y positions for 5 vertical sections, evenly distributed
            y_pos_1 = y + inner_padding_y_top
            y_pos_2 = y_pos_1 + available_pip_height // 4
            y_pos_3 = y_pos_1 + available_pip_height // 2
            y_pos_4 = y_pos_1 + (available_pip_height * 3) // 4
            y_pos_5 = y + self.card_h - inner_padding_y_bottom - h_small

            # Draw pips based on rank
            if 2 <= card.rank.value <= 10:
                pip_positions = []
                if card.rank.value == 2:
                    pip_positions = [(x_center, y_pos_1), (x_center, y_pos_5)]
                elif card.rank.value == 3:
                    pip_positions = [(x_center, y_pos_1), (x_center, y_pos_3), (x_center, y_pos_5)]
                elif card.rank.value == 4:
                    pip_positions = [(x_left, y_pos_1), (x_right, y_pos_1), (x_left, y_pos_5), (x_right, y_pos_5)]
                elif card.rank.value == 5:
                    pip_positions = [(x_left, y_pos_1), (x_right, y_pos_1), (x_center, y_pos_3), (x_left, y_pos_5), (x_right, y_pos_5)]
                elif card.rank.value == 6:
                    pip_positions = [(x_left, y_pos_1), (x_right, y_pos_1), (x_left, y_pos_3), (x_right, y_pos_3), (x_left, y_pos_5), (x_right, y_pos_5)]
                elif card.rank.value == 7:
                    # Dice 5 on top, two pips horizontally on bottom
                    pip_positions = [
                        (x_left, y_pos_1), (x_right, y_pos_1),
                        (x_center, y_pos_2),
                        (x_left, y_pos_3), (x_right, y_pos_3),
                        (x_left, y_pos_5), (x_right, y_pos_5)
                    ]
                elif card.rank.value == 8:
                    pip_positions = [
                        (x_left, y_pos_1), (x_right, y_pos_1),
                        (x_left, y_pos_2), (x_right, y_pos_2),
                        (x_left, y_pos_4), (x_right, y_pos_4),
                        (x_left, y_pos_5), (x_right, y_pos_5)
                    ]
                elif card.rank.value == 9:
                    # Dice 5 on top, Dice 4 on bottom
                    pip_positions = [
                        (x_left, y_pos_1), (x_right, y_pos_1),
                        (x_center, y_pos_2),
                        (x_left, y_pos_3), (x_right, y_pos_3),
                        (x_left, y_pos_4), (x_right, y_pos_4),
                        (x_left, y_pos_5), (x_right, y_pos_5)
                    ]
                elif card.rank.value == 10:
                    # Two dice 5s, one above the other
                    # Top dice 5 section
                    top_section_y_start = y + inner_padding_y_top
                    top_section_y_end = y + self.card_h // 2 - h_small // 2 - 2 # Small gap in the middle
                    
                    y_top_dice5_p1 = top_section_y_start
                    y_top_dice5_p2 = top_section_y_start + (top_section_y_end - top_section_y_start) // 2
                    y_top_dice5_p3 = top_section_y_end

                    # Bottom dice 5 section
                    bottom_section_y_start = y + self.card_h // 2 + h_small // 2 + 2 # Small gap in the middle
                    bottom_section_y_end = y + self.card_h - inner_padding_y_bottom - h_small

                    y_bottom_dice5_p1 = bottom_section_y_start
                    y_bottom_dice5_p2 = bottom_section_y_start + (bottom_section_y_end - bottom_section_y_start) // 2
                    y_bottom_dice5_p3 = bottom_section_y_end

                    pip_positions = [
                        # Top dice 5
                        (x_left, y_top_dice5_p1), (x_right, y_top_dice5_p1),
                        (x_center, y_top_dice5_p2),
                        (x_left, y_top_dice5_p3), (x_right, y_top_dice5_p3),
                        # Bottom dice 5
                        (x_left, y_bottom_dice5_p1), (x_right, y_bottom_dice5_p1),
                        (x_center, y_bottom_dice5_p2),
                        (x_left, y_bottom_dice5_p3), (x_right, y_bottom_dice5_p3)
                    ]

                for px, py in pip_positions:
                    pyxel.blt(px, py, 0, u_small, v_small, w_small, h_small, 7)
            else: # A, J, Q, K
                w_face, h_face = 0, 0
                u_face, v_face = 0, 0 # Initialize face card UV

                if card.rank == Rank.ACE:
                    # Draw large suit icon in the center for Ace
                    w_face, h_face = 8, 8
                    u_face = u_large
                    v_face = v_large
                else: # J, Q, K
                    w_face, h_face = 16, 16 # Face card image dimensions
                    # Set v_face based on rank
                    if card.rank == Rank.KING:
                        v_face = 40
                    elif card.rank == Rank.QUEEN:
                        v_face = 56
                    elif card.rank == Rank.JACK:
                        v_face = 72
                    
                    # Set u_face based on suit
                    if card.suit == Suit.BLACK: # Spade
                        u_face = 0
                    elif card.suit == Suit.RED: # Heart
                        u_face = 16
                    elif card.suit == Suit.BLUE: # Clover
                        u_face = 32
                    elif card.suit == Suit.GREEN: # Diamond
                        u_face = 48

                pyxel.blt(x + (self.card_w - w_face) // 2, y + (self.card_h - h_face) // 2, 0, u_face, v_face, w_face, h_face, 7)
        else:
            # カードの裏面
            pyxel.rect(x + 1, y + 1, self.card_w - 2, self.card_h - 2, 1) # 青い裏面
            pyxel.line(x + 2, y + 2, x + self.card_w - 3, y + self.card_h - 3, 0)
            pyxel.line(x + self.card_w - 3, y + 2, x + 2, y + self.card_h - 3, 0)

    def update(self):
        """ゲームロジックの更新"""
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        
        if self.game_state == GameState.START_SCREEN:
            self.point_add_timer += 2 # 2倍速でカウントアップ
            if self.point_add_timer >= self.point_add_interval:
                self.player.chips += 10 # 10ポイント加算
                self.point_add_timer = 0 # タイマーリセット
            
            if self.is_button_pressed(self.screen_w // 2 - 30, self.screen_h - 20, 60, 15): # START GAMEボタン
                self.reset_hand() # 手札をリセットし、BETTINGフェーズへ

        elif self.game_state == GameState.BETTING:
            # 賭け金調整ボタンの処理
            # UPボタン
            if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and self.is_button_hovered(self.screen_w // 2 + 20, self.screen_h // 2 - 30, 20, 15):
                self.bet_change_timer += 1
                if self.bet_change_timer % self.bet_change_delay == 0:
                    self.current_bet = min(self.player.chips, self.current_bet + self.bet_step)
            # DOWNボタン
            elif pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and self.is_button_hovered(self.screen_w // 2 + 20, self.screen_h // 2 + 15, 20, 15):
                self.bet_change_timer += 1
                if self.bet_change_timer % self.bet_change_delay == 0:
                    self.current_bet = max(self.min_bet, self.current_bet - self.bet_step)
            else:
                self.bet_change_timer = 0 # ボタンが離されたらタイマーをリセット
            
            # BETボタン
            if self.is_button_pressed(self.screen_w // 2 - 30, self.screen_h - 20, 60, 15):
                if self.player.chips >= self.current_bet:
                    self.player.chips -= self.current_bet # チップを減らす
                    self._deal_initial_cards() # カードを配る
                    self.game_state = GameState.PLAYER_EXCHANGE # プレイヤーの交換フェーズへ
                else:
                    self.game_state = GameState.START_SCREEN # チップが足りない場合はスタート画面へ

        elif self.game_state == GameState.PLAYER_EXCHANGE:
            # カードのクリック判定
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                player_hand_start_x = (self.screen_w - (self.card_w * 5 + self.card_spacing * 4)) // 2
                player_hand_y = (self.screen_h - self.card_h) // 2

                clicked_on_card = False
                for i in range(len(self.player.hand.cards)):
                    card_x = player_hand_start_x + i * (self.card_w + self.card_spacing)
                    card_y_for_click = player_hand_y

                    if i in self.selected_cards_indices:
                        card_y_for_click -= 5

                    if card_x <= pyxel.mouse_x <= card_x + self.card_w and \
                       card_y_for_click <= pyxel.mouse_y <= card_y_for_click + self.card_h:
                        if i in self.selected_cards_indices:
                            self.selected_cards_indices.remove(i) # 選択解除
                        else:
                            # 最大5枚まで選択可能
                            if len(self.selected_cards_indices) < 5:
                                self.selected_cards_indices.append(i) # 選択
                        clicked_on_card = True
                        break # 1回のクリックで1枚だけ選択/解除
                
            # EXCHANGEボタンの更新処理
            if self.is_button_pressed(self.screen_w // 2 - 30, self.screen_h - 20, 60, 15): # 画面下中央に配置
                print("EXCHANGE button pressed!")
                self._exchange_player_cards() # カード交換処理
                self.game_state = GameState.SHOWDOWN # AIがいないので直接SHOWDOWNへ

        elif self.game_state == GameState.SHOWDOWN:
            # ショーダウンのロジックをここに記述
            # 役の判定と勝者の決定
            player_hand_rank, player_kicker = self.player.hand.evaluate_hand()

            # 役に応じたチップの加算
            payout = self.payout_multipliers.get(player_hand_rank, 0) * self.current_bet
            self.player.chips += payout
            self.last_payout = payout # 最後の配当を保存
            print(f"Player Hand: {player_hand_rank.name}, Payout: {payout}")

            # プレイヤーのチップが0になったらゲームオーバー表示へ
            if self.player.chips <= 0:
                self.game_state = GameState.GAME_OVER_DISPLAY
                self.game_over_timer = 0 # タイマーをリセット
            else:
                self.game_state = GameState.CONTINUE_OR_END_GAME # 継続か精算か選択フェーズへ

        elif self.game_state == GameState.CONTINUE_OR_END_GAME:
            # CONTINUEボタン
            if self.is_button_pressed(self.screen_w // 2 - 60, self.screen_h - 20, 60, 15): # 左側に配置
                self.reset_hand() # 次のハンドへ
            # END GAMEボタン
            if self.is_button_pressed(self.screen_w // 2 + 10, self.screen_h - 20, 60, 15): # 右側に配置
                self.game_state = GameState.START_SCREEN # 精算してスタート画面へ

        elif self.game_state == GameState.GAME_OVER_DISPLAY:
            self.game_over_timer += 1
            if self.game_over_timer >= self.game_over_display_duration or \
               self.is_button_pressed(self.screen_w // 2 - 30, self.screen_h - 20, 60, 15): # RETURN TO STARTボタン
                self.game_state = GameState.START_SCREEN # スタート画面へ

    def _ai_exchange_cards(self, ai_player):
        """AIプレイヤーがカードを交換するロジック"""
        # ここでは非常にシンプルなAIロジックを実装
        # 例: ワンペアがあればそれ以外を交換、など
        hand_rank, kicker = ai_player.hand.evaluate_hand()
        cards_to_exchange = []

        if hand_rank == HandRank.HIGH_CARD:
            # ハイカードの場合、エース以外の4枚を交換
            for i, card in enumerate(ai_player.hand.cards):
                if card.rank != Rank.ACE:
                    cards_to_exchange.append(card)
        elif hand_rank == HandRank.ONE_PAIR:
            # ワンペアの場合、ペア以外の3枚を交換
            pair_rank = kicker[0] # ペアのランク
            for card in ai_player.hand.cards:
                if card.rank.value != pair_rank:
                    cards_to_exchange.append(card)
        # 他の役の場合も同様にロジックを追加できます

        if cards_to_exchange:
            ai_player.hand.remove_cards(cards_to_exchange)
            ai_player.hand.add_cards(self.deck.deal(len(cards_to_exchange)))

    def _exchange_player_cards(self):
        """プレイヤーが選択したカードを交換する"""
        if not self.selected_cards_indices: # 選択されたカードがない場合は何もしない
            return

        # 選択されたカードのインデックスを昇順にソート
        self.selected_cards_indices.sort()
        
        # 新しいカードを必要な枚数だけ配る
        new_cards = self.deck.deal(len(self.selected_cards_indices))

        # 選択されたインデックスのカードを新しいカードで置き換える
        for i, original_index in enumerate(self.selected_cards_indices):
            self.player.hand.cards[original_index] = new_cards[i]
        
        self.selected_cards_indices = [] # 選択状態をリセット

    def draw(self):
        """画面の描画"""
        pyxel.cls(2) # 深緑の背景
        
        # プレイヤーの名前とチップの表示
        pyxel.text(self.screen_w // 2 - 20, 5, f"{self.player.name}: {self.player.chips}", 7)

        if self.game_state == GameState.START_SCREEN:
            pyxel.text(self.screen_w // 2 - 40, self.screen_h // 2 - 20, "POKER GAME", 7)
            pyxel.text(self.screen_w // 2 - 40, self.screen_h // 2, f"Chips: {self.player.chips}", 7)
            
            # ポイント加算までのカウントダウン表示
            remaining_frames = self.point_add_interval - self.point_add_timer
            remaining_seconds = remaining_frames // 60
            pyxel.text(self.screen_w // 2 - 40, self.screen_h // 2 + 20, f"Next 10 points in: {remaining_seconds}s", 7)
            pyxel.text(self.screen_w // 2 - 40, self.screen_h // 2 + 30, "(+10 points every 60s)", 7)

            self.draw_button(self.screen_w // 2 - 30, self.screen_h - 20, 60, 15, "START GAME")
        else:
            # プレイヤーの手札 (画面中央に横に並べる)
            hand_total_width = self.card_w * 5 + self.card_spacing * 4 # 5枚のカードと4つのスペースの合計幅

            player_hand_start_x = (self.screen_w - hand_total_width) // 2
            player_hand_y = (self.screen_h - self.card_h) // 2

            # 賭け金表示とボタン
            if self.game_state == GameState.BETTING:
                pyxel.text(self.screen_w // 2 - 20, self.screen_h // 2 - 10, f"BET: {self.current_bet}", 7)
                self.draw_button(self.screen_w // 2 + 20, self.screen_h // 2 - 30, 20, 15, "UP")
                self.draw_button(self.screen_w // 2 + 20, self.screen_h // 2 + 15, 20, 15, "DOWN")
                self.draw_button(self.screen_w // 2 - 30, self.screen_h - 20, 60, 15, "BET")
            else:
                for i, card in enumerate(self.player.hand.cards):
                    is_selected = i in self.selected_cards_indices
                    card_y_offset = -5 if is_selected else 0 # 選択されている場合は上にずらす
                    self._draw_card(player_hand_start_x + i * (self.card_w + self.card_spacing), player_hand_y + card_y_offset, card, True, is_selected)

            # YOUの役をカードの下に表示
            if self.game_state == GameState.SHOWDOWN or self.game_state == GameState.CONTINUE_OR_END_GAME:
                player_hand_rank, _ = self.player.hand.evaluate_hand()
                pyxel.text(self.screen_w // 2 - 20, player_hand_y + self.card_h + 5, f"Your Hand: {player_hand_rank.name}", 7) # 表示位置を調整

            # EXCHANGEボタンの描画
            if self.game_state == GameState.PLAYER_EXCHANGE:
                self.draw_button(self.screen_w // 2 - 30, self.screen_h - 20, 60, 15, "EXCHANGE") # 画面下中央に配置

            # ゲームオーバー時にRESTARTボタンを表示
            if self.game_state == GameState.CONTINUE_OR_END_GAME:
                pyxel.text(self.screen_w // 2 - 60, self.screen_h // 2 - 40, "CONTINUE or END GAME?", 7)
                self.draw_button(self.screen_w // 2 - 60, self.screen_h - 20, 60, 15, "CONTINUE")
                self.draw_button(self.screen_w // 2 + 10, self.screen_h - 20, 60, 15, "END GAME")
            elif self.game_state == GameState.GAME_OVER_DISPLAY:
                self.draw_button(self.screen_w // 2 - 30, self.screen_h - 20, 60, 15, "RETURN TO START")

    def is_button_pressed(self, x, y, w, h):
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            if x <= pyxel.mouse_x <= x + w and y <= pyxel.mouse_y <= y + h:
                return True
        return False

    def is_button_hovered(self, x, y, w, h):
        return x <= pyxel.mouse_x <= x + w and y <= pyxel.mouse_y <= y + h

    def draw_button(self, x, y, w, h, text):
        pyxel.rect(x, y, w, h, 1) # ボタンの背景
        pyxel.rectb(x, y, w, h, 7) # ボタンの枠
        pyxel.text(x + (w - len(text) * 4) / 2, y + (h - 5) / 2, text, 7) # ボタンのテキスト

App()