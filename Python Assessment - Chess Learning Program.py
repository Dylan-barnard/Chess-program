import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import *
from tkinter import PhotoImage
from PIL import Image, ImageTk
import chess
import chess.engine
import chess.pgn
import chess.variant
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import glob
import io
import os

Square_Size = 60
Colors = ["#eeeed2", "#769656"]
PIECES = {'R':'♖','N':'♘','B':'♗','Q':'♕','K':'♔','P':'♙','r':'♜','n':'♞','b':'♝','q':'♛','k':'♚','p':'♟'}
STOCKFISH_PATH = (r"G:\My Drive\Level 3 NCEA\L3DTSD\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe")
OPENING_FOLDER = (r"G:\My Drive\Level 3 NCEA\L3DTSD\chess-openings-master\chess-openings-master")

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
        self.opening_database = self.load_opening_database()

        self.player_elo = 200 # Starting elo
        self.elo_history = [200]

        # Track Lesson Progress
        self.completed_lessons = {
            "Piece Movements": False,
            "Checks and Captures": False,
            "Checkmates and Stalemates": False
        }

        self.container = tk.Frame(self.root, bg="#2c3e50")
        self.container.pack(fill="both", expand=True)
        self.create_menu_ui()

    def load_opening_database(self):
        opening_database = {}

        for filename in glob.glob(os.path.join(OPENING_FOLDER, "*.tsv")):
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    reader = csv.DictReader(file, delimiter="\t")

                    for row in reader:
                        eco = row.get("eco", "").strip()
                        name = row.get("name", "").strip()
                        pgn_text = row.get("pgn", "").strip()

                        if not pgn_text or not name:
                            continue

                        try:
                            game = chess.pgn.read_game(io.StringIO(pgn_text))

                            if game is None:
                                continue

                            board = game.board()

                            # Store every position in the opening line.
                            for move in game.mainline_moves():
                                position_key = board.epd(en_passant="fen")
                                opening_database[position_key] = {
                                    "eco": eco,
                                    "name": name
                                }
                                board.push(move)

                            # Also store the final position.
                            opening_database[board.epd(en_passant="fen")] = {
                                "eco": eco,
                                "name": name
                            }



                        except Exception as error:
                            print(f"Could not read opening line: {error}")

            except FileNotFoundError:
                print(f"Opening file not found: {filename}")

        print("Opening folder:", OPENING_FOLDER)
        print("Folder exists:", os.path.isdir(OPENING_FOLDER))
        print("TSV files:", glob.glob(os.path.join(OPENING_FOLDER, "*.tsv")))
        print("Opening positions loaded:", len(opening_database))
        return opening_database

    def get_opening_name(self, board):
        position_key = board.epd(en_passant="fen")
        return self.opening_database.get(position_key)

    def clear_screen(self):
        for window in self.container.winfo_children(): window.destroy()

    def on_closing(self):
        if messagebox.askokcancel("Exit the program",
                              "Are you sure you want to exit?"):
            self.root.destroy()




    def create_menu_ui(self):
        self.clear_screen()
        self.review_index = -1
        self.lesson_mode = False
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

        tk.Button(frame, text="Learn Chess (Interactive)", width=25, command=self.show_lesson_menu).pack(pady=5)

        if len(self.elo_history) > 1:
            self.show_performance_graph(frame)

        if self.history:
            tk.Button(frame, text="Review Last Game", width=25, command=lambda: self.run_game_review()).pack(pady=10)

        exit_button = tk.Button(frame, text="Exit", width=25, command=self.on_closing)
        exit_button.pack(pady=10)

    def show_lesson_menu(self):
        self.clear_screen()
        frame = tk.Frame(self.container, bg="#2c3e50")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="Mandatory Lessons", fg="white", bg="#2c3e50", font=("Arial", 24, "bold")).pack(pady=20)

        lessons = [
        ("Piece Movements", "1k6/1p6/8/8/4Q3/8/8/6K1 w - - 0 1", "PRACTICE: Move the Queen to any square. The Queen moves horizontally, vertically, and diagonally."),
        ("Checks and Captures", "k7/8/8/8/8/2n5/1P6/1K6 w - - 0 1", "PRACTICE: The Knight is attacking your King (Check!). Use your Pawn to capture it."),
        ("Stalemates", "k7/8/1Q6/8/8/8/8/4K3 w - - 0 1", "PRACTICE: Move your Queen to c7 to create a Stalemate. A stalemate happens when your opponent has no legal moves but is not in check.")
        ]

        for title, fen, instruction in lessons:
            status = "✓ " if self.completed_lessons.get(title) else ""
            btn_color = "#27ae60" if self.completed_lessons.get(title) else "SystemButtonFace"
            tk.Button(frame, text=f"{status}{title}", width=30, height=2, bg=btn_color, 
                      command=lambda t=title, f=fen, i=instruction: self.start_interactive_lessons(t, f, i)).pack(pady=10)

        tk.Button(frame, text="Return to Main Menu", width=20, bg="#e74c3c", fg="white",
            command=self.create_menu_ui).pack(pady=30)

    def start_interactive_lessons(self, title, fen, instruction):
        self.clear_screen()
        self.lesson_mode = True
        self.current_lesson_title = title
        self.ai_level = None
        self.board = chess.Board(fen)

        header = tk.Frame(self.container, bg="#34495e", pady=10)
        header.pack(fill="x")
        tk.Label(header, text=title, fg="#f1c40f", bg="#34495e", font=("Arial", 16, "bold")).pack()

        self.lesson_instr_label = tk.Label(self.container, text=instruction, fg="white", bg="#2c3e50", 
                                      font=("Arial", 11, "italic"), wraplength=500, pady=10)
        self.lesson_instr_label.pack()
        tk.Button(self.container, text="Show Hint", command=self.show_lesson_hint, 
              bg="#f39c12", fg="white").pack(pady=5)
        self.canvas = tk.Canvas(self.container, width=480, height=480, highlightthickness=0)
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.handle_click)
    
        self.draw_board()

        tk.Button(self.container, text="Back to Lessons", width=20, 
                command=self.show_lesson_menu).pack(pady=10)

    def show_lesson_hint(self):
        target_square = None
        if self.current_lesson_title == "Checks and Captures":
            target_square = chess.C3
        elif self.current_lesson_title == "Stalemates":
            target_square = chess.C7

        if target_square is not None:
            c = chess.square_file(target_square)
            r = 7 - chess.square_rank(target_square)
            self.canvas.create_rectangle(c*60, r*60, (c+1)*60, (r+1)*60, outline = "#e74c3c", width = 5)
            messagebox.showinfo("Hint!", "Focus on the highlighted square.")
        else:
            messagebox.showinfo("Hint!", "Move to any legal square to complete this lesson.")

    def check_lesson_goal(self, title, start_fen, move):
        passed = False
        if title == "Piece Movements":
            passed = True
        elif title == "Checks and Captures":
            temp_board = chess.Board(start_fen)
            captured_piece = temp_board.piece_at(move.to_square)

            if captured_piece and captured_piece.piece_type == chess.KNIGHT:
                passed = True
        elif title == "Stalemates":
            passed = True

        if passed:
            self.completed_lessons[title] = True
            messagebox.showinfo("Success", f"Lesson'{title}' completed!")
            self.show_lesson_menu()

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
        
    def start_game(self, level, player_color=chess.WHITE):
        self.board = chess.Board()
        self.game_settings.destroy()
        self.ai_level = level
        player_color == getattr(self, "player_color", chess.WHITE)
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
        final_move = None

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

            if final_move:
                    start_fen = self.board.fen()
                    self.history.append((start_fen, final_move))
                    self.board.push(final_move)
                    self.selected_square = None
                    self.draw_board()

                    if not getattr(self, 'lesson_mode', False):
                        if self.ai_level is not None and not self.board.is_game_over():
                            self.root.after(500, self.make_ai_move)
                        else:
                            self.check_end()
                    else:
                        self.check_lesson_goal(getattr(self, 'current_lesson_title', ""), start_fen, final_move)
                        
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
                    if self.ai_level == 5:
                        skill_level = 5
                        engine.configure({"Skill Level": skill_level})
                        engine_move = engine.play(self.board, chess.engine.Limit(time=0.1))
                        self.execute_bot_move(engine_move.move)
                        return

            else:
                with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                    if self.ai_level == 10:
                        skill_level = 15
                        engine.configure({"Skill Level": skill_level})
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


            if not getattr(self, 'lesson_mode', False):
                elo_update = self.calculate_new_elo(result_str)
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
        bot_rating = Bot_ratings.get(self.ai_level, 200)
        k_factor = 32

        # Calculate expected score
        expected_score = 1 / (1 + 10 ** ((bot_rating - player_rating) / 400))

        #calulate elo change
        rating_change = k_factor * (actual_score - expected_score)

        #change user's elo
        self.player_elo += rating_change
        if self.player_elo < 100:
            self.player_elo = 100
        
        return rating_change

    def run_game_review(self):
        self.clear_screen()
        tk.Label(self.container, text="Stockfish is analysing your performance...",
                fg="white", bg="#2c3e50", font=("Arial", 14)).pack(pady=10)
        self.root.update()
        current_total_loss = 0
        current_moves_count = 0
        self.review_analysis_data = []
        player_color = self.player_color

        try:
            with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                for move_number, (fen, move) in enumerate(self.history):
                    board_before = chess.Board(fen)
                    current_turn = board_before.turn

                    # Use multiple principal variations so the reviewer can identify
                    # theoretical and alternative strong moves.
                    analysis = engine.analyse(
                        board_before,
                        chess.engine.Limit(time=0.3),
                        multipv=1
                    )

                    if not analysis:
                        continue

                    best_info = analysis[0]
                    best_move = best_info["pv"][0]
                    best_score = best_info["score"].pov(current_turn).score(mate_score=10000)

                    # Evaluate the move that was actually played.
                    board_after = board_before.copy()
                    board_after.push(move)
                    after_info = engine.analyse(
                        board_after,
                        chess.engine.Limit(time=0.2)
                    )
                    actual_score = after_info["score"].pov(current_turn).score(mate_score=10000)

                    loss = max(0, best_score - actual_score)

                    # Check the opening database first.
                    opening = self.get_opening_name(board_before)

                    if opening is not None:
                    # Theoretical takes priority over all other classifications.
                        opening_name = opening["name"]
                        opening_eco = opening["eco"]
                        quality = "Theoretical"

                        explanation = (
                            f"{board_before.san(move)} follows the theoretical line "
                            f"of {opening_name} ({opening_eco})."
                        )
                    else:
                        opening_name = "Opening not recognised"
                        opening_eco = ""

                        quality, explanation = self.get_move_classification(board_before, move, best_move, best_score, actual_score, loss, move_number)

                    # Only use the player's moves for performance rating.
                    if current_turn == player_color:
                        current_total_loss += loss
                        current_moves_count += 1

                    self.review_analysis_data.append({"fen": fen, "move": move, "best_move": best_move, "quality": quality, "exp": explanation, "loss": loss, "opening_name": opening_name, "opening_eco": opening_eco})

            if current_moves_count > 0:
                acpl = current_total_loss / current_moves_count
                accuracy = max(0, min(100, 100 * (1 - acpl / 300)))
                opponent_rating = Bot_ratings.get(self.ai_level, 200)
                estimated_rating = opponent_rating + ((accuracy - 50) * 8)
                self.performance_rating = max(100, round(estimated_rating))
            else:
                self.performance_rating = 100

        except Exception as e:
            messagebox.showerror("Error", f"Analysis Failed: {e}")
            self.create_menu_ui()
            return

        self.review_index = 0
        self.show_review_ui()

    def get_move_classification(self, board, move, best_move, best_score, actual_score, loss, move_number):
        """Classifies a move using engine loss and simple tactical heuristics."""

        move_text = board.san(move)
        best_text = board.san(best_move)
        is_capture = board.is_capture(move)
        is_best = move == best_move

        # A sacrifice that keeps approximately the engine's best evaluation is
        # treated as brilliant. This is a heuristic, not a formal chess label.
        moving_piece = board.piece_at(move.from_square)

        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000}

        moved_value = (
                piece_values.get(moving_piece.piece_type, 0)
                if moving_piece else 0
            )

        # Look at the position after the move.
        board_after = board.copy()
        board_after.push(move)

        # Check whether the opponent can capture the piece that just moved.
        piece_can_be_captured = any(
            opponent_move.to_square == move.to_square
            for opponent_move in board_after.legal_moves
        )

        creates_check = board_after.is_check()

        # Only valuable pieces can normally be sacrificed.
        valuable_piece = moved_value >= piece_values[chess.KNIGHT]

        # Strict definition to reduce false Brilliant labels.
        is_sacrifice = (
            valuable_piece
            and piece_can_be_captured
            and (creates_check or is_capture)
        )

        if is_sacrifice and loss <= 5:
            return ("Brilliant", f"Brilliant idea! {move_text} offers material "
        "for a strong tactical advantage."
    )

        if is_best and loss <= 10:
            return "Great", f"Great move! {move_text} is Stockfish's top choice."

        # A miss means a strong opportunity was available but not played.
        if best_score >= 100 and loss >= 60:
            return "Miss", f"You missed a strong opportunity. {best_text} was better than {move_text}."

        if loss <= 30:
            return "Great", f"Strong move. {move_text} keeps the position healthy."
        if loss <= 80:
            return "Inaccuracy", f"Inaccuracy: {move_text} loses a small amount compared with {best_text}."
        if loss <= 250:
            return "Mistake", f"Mistake: {best_text} was better than {move_text}."
        return "Blunder", f"Blunder: {move_text} loses significant evaluation. Consider {best_text}."

# Keep this method if other parts of your program still call it.
    def get_explanation(self, loss, move, best):
        if loss <= 10:
            return "Great", f"{move} was one of the engine's strongest moves."
        if loss <= 80:
            return "Inaccuracy", f"{move} was playable, but {best} was more accurate."
        if loss <= 250:
            return "Mistake", f"{best} was better than {move}."
        return "Blunder", f"{move} lost significant evaluation; consider {best}."

    def show_review_ui(self):
        self.clear_screen()
        perf_header = tk.Frame(self.container, bg="#34495e", pady=10)
        perf_header.pack(fill="x")
        tk.Label(perf_header, text=f"Estimated Performance: {round(self.performance_rating)} Elo", fg="#f1c40f",
                bg="#34495e", font=("Arial", 14, "bold")).pack()

        self.canvas = tk.Canvas(self.container, width=480, height=480, highlightthickness=0)
        self.canvas.pack(pady=10)

        self.exp_label = tk.Label(self.container, text="", fg="white", bg="#2c3e50",
                                    font=("Arial", 11, "italic"), wraplength=450, height=5)
        self.exp_label.pack(fill="x", padx=20)

        self.opening_label = tk.Label(self.container, text="Opening: Not recognised", fg="#3498db", bg="#2c3e50", font=("Arial", 12, "bold"))
        self.opening_label.pack(pady=5)

        nav_frame = tk.Frame(self.container, bg="#2c3e50")
        nav_frame.pack(pady=10)

        tk.Button(nav_frame, text="<< Previous", command=self.prev_move).pack(side="left", padx=10)
        tk.Button(nav_frame, text="Next >>", command=self.next_move).pack(side="left", padx=10)
        tk.Button(nav_frame, text="Finish Review", command=self.create_menu_ui).pack(side="left", padx=10)

        self.update_review_display()

    def update_review_display(self):
        data = self.review_analysis_data[self.review_index]
        temp_board = chess.Board(data["fen"])
        self.draw_board(temp_board)

        move = data["move"]
        f_c, f_r = chess.square_file(move.from_square), 7 - chess.square_rank(move.from_square)
        t_c, t_r = chess.square_file(move.to_square), 7 - chess.square_rank(move.to_square)

        self.canvas.create_rectangle(f_c * 60, f_r * 60, (f_c + 1) * 60, 
                                    (f_r + 1) * 60, outline="Blue", width=3)
        self.canvas.create_rectangle(t_c * 60, t_r * 60, (t_c + 1) * 60, 
                                    (t_r + 1) * 60, outline="Blue", width=3)

        color_map = {
            "Theoretical": "#836135",
            "Brilliant": "#00bcd4",
            "Great": "#27ae60",
            "Good": "#2ecc71",
            "Inaccuracy": "#f1c40f",
            "Miss": "#e67e22",
            "Mistake": "#e67e22",
            "Blunder": "#e74c3c"
        }

        best_move = data.get("best_move")
        best_text = ""
        if best_move is not None:
            best_text = f"Engine suggestion: {temp_board.san(best_move)}"
        opening_name = data.get(
            "opening_name",
            "Opening not recognised")

        opening_eco = data.get(
            "opening_eco",
            "")

        if opening_eco:
            self.opening_label.config(text=f"Opening: {opening_name} ({opening_eco})")
        else:
            self.opening_label.config(text=f"Opening: {opening_name}")

        self.exp_label.config(text=(
        f"Move {self.review_index + 1}: {data['quality']}\n"
        f"{data['exp']}{best_text}"
        ),fg=color_map.get(data["quality"], "white"))

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
