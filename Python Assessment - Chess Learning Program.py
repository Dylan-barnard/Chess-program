import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import *
from tkinter import PhotoImage
from PIL import Image, ImageTk
import chess
import chess.engine
import chess.variant
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
        self.review_analysis_data = [] # Stores analysis data
        self.selected_square = None
        self.ai_level = 0 # 0=Easy, 1=Med, 2=Hard
        self.review_index = -1

        self.player_elo = 200 # Starting elo
        self.elo_history = [200]  # MISSING: Initialize history with starting Elo

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
        
        tk.Button(frame, text="Play Chess", width=25, command=lambda: self.open_mode_selection()).pack(pady=10)

        if len(self.elo_history) > 1:
            self.show_performance_graph(frame)

        if self.history:
            tk.Button(frame, text="Review Last Game", width=25, command=lambda: self.run_game_review()).pack(pady=10)

        exit_button = tk.Button(frame, text="Exit", width=25, command=self.on_closing)
        exit_button.pack(pady=10)

    def show_performance_graph(self, parent_frame):
        figure, ax =  plt.subplots(figsize=(4,2), dpi=100)
        figure.patch.set_facecolor('#2c3e50')
        ax.patch.set_facecolor('#34495e')

        ax.plot(self.elo_history, marker='o', color='#1abc9c', linewidth=2, markersize=4)

        ax.set_title('Elo Performance', color='white', fontsize=10)
        ax.tick_params(axis='x', colors='white', labelsize=8)
        ax.tick_params(axis='y', colors='white', labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('white')

        canvas = FigureCanvasTkAgg(figure, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10)

    def open_mode_selection(self):
        self.game_settings = tk.Toplevel(root)
        self.game_settings.title("Select your Game specifications")
        self.game_settings.geometry("600x750")
        self.game_settings.config(bg="#2c3e50")

        tk.Button(self.game_settings, text="Player vs AI Level 1(200 Elo)", width=25, command=lambda: self.start_game(0)).pack(pady=10)
        tk.Button(self.game_settings, text="Player vs AI Level 2(600 Elo)", width=25, command=lambda: self.start_game(5)).pack(pady=10)
        tk.Button(self.game_settings, text="Player vs AI Level 3(1000 Elo)", width=25, command=lambda: self.start_game(10)).pack(pady=10)
        
    def start_game(self, level):
        self.board = chess.Board()
        self.game_settings.destroy()
        self.ai_level = level
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
            # STEP 1: If playing the 200 Elo bot, implement Martin's handicap logic from chess.com
            if self.ai_level == 0:
                legal_moves = list(self.board.legal_moves)
            
                # Spin a roulette wheel (0.0 to 1.0) to decide how the 200 elo handles this turn
                roll = random.random()

                # 35% Chance: Play a completely random move (Absolute Blunder)
                if roll < 0.35:
                    final_move = random.choice(legal_moves)
                    self.execute_bot_move(final_move)
                    return

                # 65% Chance: Use Stockfish, but degrade its choice
                with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                # Ask Stockfish to evaluate the top 5 multi-PV variants at an ultra-low depth
                    analysis = engine.analyse(self.board, chess.engine.Limit(depth=2), multipv=5)
                
                    # Extract the moves found by the engine
                    ranked_moves = [info.get("pv")[0] for info in analysis if info.get("pv")]

                    if ranked_moves:
                    # 40% Chance: 200 elo bot plays a mediocre, suboptimal move (3rd to 5th choice)
                        if roll < 0.75 and len(ranked_moves) >= 3:
                            final_move = random.choice(ranked_moves[2:])
                            self.execute_bot_move(final_move)
                    # 25% Chance: 200 elo bot spots a decent move (1st or 2nd choice)
                        else:
                            final_move = random.choice(ranked_moves[:2])
                        
                            self.execute_bot_move(final_move)
                            return

            elif self.ai_level == 5:
                legal_moves = list(self.board.legal_moves)

                if random.random() < 0.15:
                    self.execute_bot_move(random.choice(legal_moves))
                    return
                
                with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                    engine.configure({"Skill Level": 0})
                    engine_move = engine.play(self.board, chess.engine.Limit(time=0.1))
                    self.execute_bot_move(engine_move.move)
                    return

            else:
                with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                    engine.configure({"Skill Level": 0})
                    engine_move = engine.play(self.board, chess.engine.Limit(time=0.1))
                    self.execute_bot_move(engine_move.move)

        except Exception as e:
            print(f"Engine Error: {e}")
            # Emergency backup: Make a random legal move if the engine fails
            if not self.board.is_game_over():
                self.execute_bot_move(random.choice(list(self.board.legal_moves)))

    def execute_bot_move(self, move):
            self.history.append((self.board.fen(), move))
            self.board.push(move)
            self.draw_board()
            self.check_end()

    def check_end(self):
        if self.board.is_game_over():
            messagebox.showinfo("Game Over", f"Result: {self.board.result()}")
            result_str = self.board.result()
            elo_update = self.calculate_new_elo(result_str)
            direction = "+" if elo_update >= 0 else ""
            self.elo_history.append(self.player_elo)

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

    def run_game_review(self):
        self.clear_screen()
        tk.Label(self.container, text="Stockfish is analysing your performance...", fg="white", bg="#2c3e50", font=("Arial", 14)).pack(pady=10)
        self.root.update()
        self.total_loss = 0
        self.moves_count = 0
        self.review_analysis_data = []

        try:
            with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                for fen, move in self.history:
                    board = chess.Board(fen)

                    info = engine.analyse(board, chess.engine.Limit(time=0.2))
                    best_move = info["pv"][0]
                    best_score = info["score"].relative.score(mate_score=10000)

                    board.push(move)
                    info_after = engine.analyse(board, chess.engine.Limit(time=0.2))
                    actual_score = -info_after["score"].relative.score(mate_score=10000)

                    loss = max(0, best_score - actual_score)
                    if board.turn == chess.BLACK:
                        self.total_loss += loss
                        self.moves_count += 1

                    quality, explanation = self.get_explanation(loss, move, best_move)
                    self.review_analysis_data.append({'fen': fen, 'move': move, 'quality': quality, 'exp': explanation})

                    if self.moves_count > 0:
                        acpl = self.total_loss/self.moves_count
                        accuracy = max(0, 100-(acpl*0.4))
                        self.performance_rating = round(Bot_ratings[self.ai_level]+(accuracy-50)*12)
                    else:
                        self.performance_rating = 0

        except Exception as e:
            messagebox.showerror("Error", f"Analysis Failed:{e}")
            self.create_menu_ui()
            return

        self.review_index = 0
        self.show_review_ui()

    #Explanation for moves
    def get_explanation(self, loss, move, best):
        if loss < 20: return "Best", f"Excellent! {move} was the strongest move."
        if loss < 60: return "Good", f"Solid move. {move} keeps the pressure on."
        if loss < 150: return "Inaccuracy", f"Inaccuracy. You played {move}, but {best} was slightly better for development."
        if loss < 350: return "Mistake", f"Mistake. {move} allows your opponent to improve. {best} was necessary."
        return "Blunder", f"Blunder! {move} loses significant material or position. You should have played {best}."

    def show_review_ui(self):
        self.clear_screen()

        #Performance Header
        perf_header = tk.Frame(self.container, bg="#34495e", pady=10)
        perf_header.pack(fill="x")
        tk.Label(perf_header, text=f"Estimated Performance: {self.performance_rating} Elo", fg="#f1c40f", bg="#34495e", font=("Arial", 14, "bold")).pack()

        #Board
        self.canvas = tk.Canvas(self.container, width=480, height=480, highlightthickness=0)
        self.canvas.pack(pady=10)

        #Explanation Area
        self.exp_label = tk.Label(self.container, text="", fg="white", bg="#2c3e50", font=
        ("Arial", 11, "italic"), wraplength=400, height=4)
        self.exp_label.pack(fill="x", padx=20)

        #General Navigation
        nav_frame = tk.Frame(self.container, bg="#2c3e50")
        nav_frame.pack(pady=10)

        tk.Button(nav_frame, text="<< Previous", command=self.prev_move).pack(side="left", padx=10)
        tk.Button(nav_frame, text="Next >>", command=self.next_move).pack(side="left", padx=10)
        tk.Button(nav_frame, text="Finish Review", command=self.create_menu_ui).pack(side="left", padx=10)

        self.update_review_display()

    def update_review_display(self):
        data = self.review_analysis_data[self.review_index]
        temp_board = chess.Board(data['fen'])

        #Update Piece Placement
        self.draw_board(temp_board)

        #Highlight the move made during the review
        move = data['move']
        f_c, f_r = chess.square_file(move.from_square), 7-chess.square_rank(move.from_square)
        t_c, t_r = chess.square_file(move.to_square), 7-chess.square_rank(move.to_square)

        self.canvas.create_rectangle(f_c*60, f_r*60, (f_c+1)*60, (f_r+1)*60, outline = "Blue", width= 3)
        self.canvas.create_rectangle(t_c*60, t_r*60, (t_c+1)*60, (t_r+1)*60, outline = "Blue", width= 3)

        #Update Text
        color_map = {"Best": "#27ae60", "Good": "#2ecc71", "Inaccuracy": "#f1c40f", "Mistake": "#e67e22", "Blunder": "#e74c3c"}
        self.exp_label.config(text=f"Move{self.review_index + 1}: {data['quality']}\n{data['exp']}", fg=color_map.get(data['quality'], "white"))

    def next_move(self):
        if self.review_index < len(self.review_analysis_data) - 1:
            self.review_index += 1
            self.update_review_display()

    def prev_move(self):
        if self.review_index > 0:
            self.review_index -= 1
            self.update_review_display()

app = DylanChessProgram(root)
root.mainloop()
