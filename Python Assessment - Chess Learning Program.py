import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import *
from tkinter import PhotoImage
from PIL import Image, ImageTk
import chess
import chess.engine

Square_Size = 60
Colors = ["#eeeed2", "#769656"]
PIECES = {'R':'♖','N':'♘','B':'♗','Q':'♕','K':'♔','P':'♙','r':'♜','n':'♞','b':'♝','q':'♛','k':'♚','p':'♟'}
STOCKFISH_PATH = "G:\\My Drive\\Level 3 NCEA\\L3DTSD\\stockfish-windows-x86-64-avx2\\stockfish\\stockfish-windows-x86-64-avx2.exe"

Bot_ratings = {
    0: 200,
    5: 600,
    10: 1000
}

root = tk.Tk()
root.geometry("600x750")

class DylanChessProgram:
    def __init__(self, root):
        self.root = root
        self.root.title("Dylan's Chess: Training & Review")

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.board = chess.Board()
        self.history = []  # Stores (FEN, Move)
        self.review_analysis = [] # Stores analysis data
        self.selected_square = None
        self.ai_level = 0 # 0=Easy, 1=Med, 2=Hard
        self.review_index = -1

        self.player_elo = 200 # Starting elo

        self.container = tk.Frame(self.root, bg="#2c3e50")
        self.container.pack(fill="both", expand=True)
        self.create_menu_ui()

    def clear_screen(self):
        for window in self.container.winfo_children(): window.destroy()

    def on_closing(self):
        if messagebox.askokcancel("Exit the program",
                              "Are you sure you want to exit?"):
            self.root.destroy()




    def create_menu_ui(self):
        self.clear_screen()
        self.review_index = -1
        frame = tk.Frame(self.container, bg="#2c3e50")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        logo_image = Image.open(r"G:\My Drive\Level 3 NCEA\L3DTSD\Chess-program\chess learning website assets\Logo.png") 
        logo_image = logo_image.resize((325, 175))
        self.logo_tk = ImageTk.PhotoImage(logo_image) # Stored to self to prevent garbage collection
        
        logo_label = tk.Label(frame, image=self.logo_tk, bg="#2c3e50")
        logo_label.pack(pady=10)

        tk.Label(frame, text="Dylan's Chess", fg="white", 
                 bg="#2c3e50", font=("Courier", 32, "bold")).pack(pady=10)

        tk.Label(frame, text=f"Your Rating: {round(self.player_elo)} Elo", fg="#1abc9c", bg="#2c3e50", 
                 font=("Arial", 16, "bold")).pack(pady=10)
        
        tk.Button(frame, text="Play Chess", width=25, command=lambda: self.start_game(0)).pack(pady=10)
        exit_button = tk.Button(frame, text="Exit", width=25, command=self.on_closing)
        exit_button.pack(pady=10)

    def start_game(self, level):
        self.ai_level = level
        self.board = chess.Board()
        self.history = []
        self.clear_screen()
        self.chess_board_ui()

    def chess_board_ui(self):
        self.canvas = tk.Canvas(self.container, width=480, height=480, highlightthickness=0)
        self.canvas.pack(pady=10)

        self.canvas.bind("<Button-1>", self.handle_click)
        self.elo_label = tk.Label(self.container, text=f"Your Elo: {round(self.player_elo)}  |  Opponent Elo: {Bot_ratings[self.ai_level]}",
        fg="white", bg="#2c3e50", font=("Arial", 14, "bold"))
        self.elo_label.pack(pady=5)
        self.draw_board()

    def draw_board(self,
    current_board=None):
        if current_board is None:
            current_board = self.board
        self.canvas.delete("all")
        for r in range(8):
            for c in range(8):
                x1, y1, x2, y2 = c*60, r*60, (c+1)*60, (r+1)*60
                color = Colors[(r+c)%2]

                if self.selected_square is not None:
                        if r == 7-chess.square_rank(self.selected_square
                        ) and c == chess.square_file(self.selected_square):
                            color = "#f7f769"

                self.canvas.create_rectangle(x1, y1, x2, 
                                                 y2, fill=color, outline="")
                chess_square = chess.square(c, 7-r)
                piece_position = current_board.piece_at(chess_square)
                if piece_position:
                        self.canvas.create_text(x1+30, y1+30, 
                        text=PIECES[piece_position.symbol()], font=("Arial", 36))
                        
    def handle_click(self, event):
        column, row = event.x//60, 7-(event.y//60)
        square = chess.square(column, row)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn: 
                self.selected_square = square
                self.draw_board()
        else:
            move = chess.Move(self.selected_square, square)

                #Handling promotion
            promotion = chess.Move(self.selected_square, square, chess.QUEEN)

            if move in self.board.legal_moves:
                    final_move = move
            elif promotion in self.board.legal_moves:
                    final_move = promotion
            else:
                    final_move = None

            if final_move:
                    self.history.append((self.board.fen(), final_move))
                    self.board.push(final_move)
                    self.selected_square = None
                    self.draw_board()

                    if self.ai_level is not None and not self.board.is_game_over():
                        self.root.after(500, self.make_ai_move)

                    else:
                        self.check_end()
                        
            else:
                self.selected_square = None
                self.draw_board()

    def make_ai_move(self):
        try:
            with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                target_elo = max(1350, Bot_ratings[self.ai_level])
                engine.configure({
                    "UCI_LimitStrength": True, 
                    "UCI_Elo": target_elo, 
                    "Skill Level": self.ai_level
                })

                if self.ai_level == 0:
                    limit = chess.engine.Limit(depth=1, time=0.05)
                else:
                    limit = chess.engine.Limit(time=0.1)
                engine_move = engine.play(self.board, limit)

                if engine_move.move:
                    self.history.append((self.board.fen(), engine_move.move))
                    self.board.push(engine_move.move)
                    self.draw_board()
                    self.check_end()
        except Exception as e:
            print(f"Stockfish Error: {e}")

    def check_end(self):
        if self.board.is_game_over():
            messagebox.showinfo("Game Over", f"Result: {self.board.result()}")
            result_str = self.board.result()
            elo_update = self.calculate_new_elo(result_str)
            direction = "+" if elo_update >= 0 else ""

            self.create_menu_ui()

    def calculate_new_elo(self, game_result):
        if game_result == "1-0":
            actual_score = 1.0
        elif game_result == "0-1":
            actual_score = 0.0
        else:
            actual_score = 0.5
        
        player_rating = self.player_elo
        bot_rating = Bot_ratings[self.ai_level]
        k_factor = 32

        # Calculate expected score
        expected_score = 1 / (1 + 10 ** ((bot_rating - player_rating) / 400))

        #calulate elo change
        rating_change = k_factor * (actual_score - expected_score)

        #change user's elo
        self.player_elo += rating_change
        return rating_change

app = DylanChessProgram(root)
root.mainloop()
