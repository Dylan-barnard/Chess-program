"""This file creates a chess learning program designed to assist beginner players."""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import *
from tkinter import PhotoImage
from PIL import Image, ImageTk
import chess
import chess.engine
import chess.pgn
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import glob
import hashlib
import io
import json
import os
import time

SQUARE_SIZE = 60
COLORS = ["#eeeed2", "#769656"]
PIECES = {
     'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
     'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟'
    }
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOCKFISH_PATH = os.path.join(
    BASE_DIR,
    "stockfish-windows-x86-64-avx2-20260821T230608Z-1-001",
    "stockfish-windows-x86-64-avx2",
    "stockfish",
    "stockfish-windows-x86-64-avx2.exe"
)
OPENING_FOLDER = os.path.join(
    BASE_DIR,
    "chess learning website assets",
    "chess openings"
)
ACCOUNT_FILE = os.path.join(BASE_DIR, "tester_accounts.json")
MIN_PASSWORD_LENGTH = 6

Bot_ratings = {
    0: 200,
    5: 600,
    10: 1000
}

root = tk.Tk()
root.geometry("800x950")


class DylanChessProgram:
    """Represents my chess program."""

    def __init__(self, root):
        """Create the base window."""
        self.root = root
        self.root.title("Dylan's Chess: Training & Review")

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.board = chess.Board()
        self.history = []  # Stores (FEN, Move)
        self.review_analysis_data = []  # Stores analysis data
        self.selected_square = None
        self.legal_targets = []
        self.ai_level = 0  # 0=Easy, 1=Med, 2=Hard
        self.review_index = -1
        self.opening_database = self.load_opening_database()
        self.graduation_shown = False
        self.current_user = None
        self.accounts = self.load_accounts()
        self.engine_error_shown = False

        self.player_elo = 200  # Starting elo
        self.elo_history = [200]
        self.white_time = 600.0
        self.black_time = 600.0
        self.active_color = chess.WHITE
        self.clock_running = False
        self.last_tick = None
        self.clock_label = None
        self.clock_job = None

        # Track Lesson Progress
        self.completed_lessons = {
            "Piece Movements": False,
            "Checks and Captures": False,
            "Checkmates and Stalemates": False
        }

        self.container = tk.Frame(self.root, bg="#2c3e50")
        self.container.pack(fill="both", expand=True)
        self.create_login_ui()

    def load_accounts(self):
        """Load all tester accounts from the local JSON file."""
        if not os.path.exists(ACCOUNT_FILE):
            return {}

        try:
            with open(ACCOUNT_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def save_accounts(self):
        """Save the current account dictionary to disk."""
        with open(ACCOUNT_FILE, "w", encoding="utf-8") as file:
            json.dump(self.accounts, file, indent=2)

    def get_default_profile(self):
        """Return a fresh account profile for a new tester."""
        return {
            "password": "",
            "player_elo": 200,
            "elo_history": [200],
            "completed_lessons": {
                "Piece Movements": False,
                "Checks and Captures": False,
                "Stalemates": False
            }
        }

    def apply_profile_to_session(self, username):
        """Load the saved profile for the chosen tester into the app state."""
        profile = self.accounts.get(username, self.get_default_profile())
        self.current_user = username
        self.player_elo = profile.get("player_elo", 200)
        self.elo_history = profile.get("elo_history", [self.player_elo])
        self.completed_lessons = {
            "Piece Movements": profile.get("completed_lessons", {}).get("Piece Movements", False),
            "Checks and Captures": profile.get("completed_lessons", {}).get("Checks and Captures", False),
            "Stalemates": (
                profile.get("completed_lessons", {}).get("Stalemates", False)
                or profile.get("completed_lessons", {}).get("Checkmates and Stalemates", False)
            )
        }
        self.graduation_shown = self.player_elo >= 1000

    def hash_password(self, password):
        """Create a one-way hash for a tester password."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def save_profile(self):
        """Write the current tester's progress to the account file."""
        if self.current_user is None:
            return

        profile = self.accounts.setdefault(self.current_user, self.get_default_profile())
        profile["player_elo"] = round(self.player_elo)
        profile["elo_history"] = self.elo_history
        profile["completed_lessons"] = self.completed_lessons
        self.save_accounts()

    def create_login_ui(self):
        """Create the login and sign-up screen for tester accounts."""
        self.clear_screen()

        frame = tk.Frame(self.container, bg="#2c3e50")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="Tester Login", fg="white", bg="#2c3e50",
                 font=("Arial", 28, "bold")).pack(pady=(0, 20))

        tk.Label(frame, text="Username", fg="white", bg="#2c3e50").pack(anchor="w", padx=30)
        self.username_entry = tk.Entry(frame, width=30)
        self.username_entry.pack(pady=(0, 10), padx=30)

        tk.Label(frame, text="Password", fg="white", bg="#2c3e50").pack(anchor="w", padx=30)
        self.password_entry = tk.Entry(frame, width=30, show="*")
        self.password_entry.pack(pady=(0, 20), padx=30)

        btn_frame = tk.Frame(frame, bg="#2c3e50")
        btn_frame.pack()
        tk.Button(btn_frame, text="Login", width=12, command=self.login_user_action).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Create Account", width=12, command=self.create_account_action).pack(side="left", padx=10)

    def login_user_action(self):
        """Log in an existing tester by username and password."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username:
            messagebox.showerror("Login failed", "Please enter a username.")
            return

        if username not in self.accounts:
            messagebox.showerror("Login failed", "No account exists for that tester.")
            return

        account_password = self.accounts[username].get("password", "")
        password_matches = account_password == self.hash_password(password)

        if not password_matches and account_password == password:
            password_matches = True
            self.accounts[username]["password"] = self.hash_password(password)
            self.save_accounts()

        if not password_matches:
            messagebox.showerror("Login failed", "Incorrect password.")
            return

        self.apply_profile_to_session(username)
        self.create_menu_ui()

    def create_account_action(self):
        """Create a new tester account and save it."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username:
            messagebox.showerror("Account failed", "Please enter a username.")
            return

        if username in self.accounts:
            messagebox.showerror("Account failed", "That tester name already exists.")
            return

        if not password:
            messagebox.showerror("Account failed", "Please enter a password.")
            return

        if len(password) < MIN_PASSWORD_LENGTH:
            messagebox.showerror(
                "Account failed",
                f"Password must be at least "
                f"{MIN_PASSWORD_LENGTH} characters long."
            )
            return

        new_profile = self.get_default_profile()
        new_profile["password"] = self.hash_password(password)
        self.accounts[username] = new_profile
        self.save_accounts()
        self.apply_profile_to_session(username)
        self.create_menu_ui()

    def load_opening_database(self):
        """Load the opening Database."""
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
        """Get the name of the opening."""
        position_key = board.epd(en_passant="fen")
        return self.opening_database.get(position_key)

    def clear_screen(self):
        """Clear the screen."""
        for window in self.container.winfo_children():
            window.destroy()

    def on_closing(self):
        """Asks whether you want to leave before closing the program."""
        if messagebox.askokcancel("Exit the program",
                                  "Are you sure you want to exit?"):
            self.save_profile()
            self.root.destroy()

    def create_menu_ui(self):
        """Create the UI for the menu."""
        self.pause_game_clock()
        self.save_profile()
        self.clear_screen()
        self.review_index = -1
        self.lesson_mode = False
        frame = tk.Frame(self.container, bg="#2c3e50")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        logo_image = Image.open(r"C:\Users\dylan\OneDrive\Desktop\Chess-program\chess learning website assets\Logo.png")
        logo_image = logo_image.resize((325, 175))
        self.logo_tk = ImageTk.PhotoImage(logo_image)  # Stored to self to prevent garbage collection

        logo_label = tk.Label(frame, image=self.logo_tk, bg="#2c3e50")
        logo_label.pack(pady=10)

        tk.Label(frame, text="Dylan's Chess", fg="white",
                 bg="#2c3e50", font=("Courier", 32, "bold")).pack(pady=10)

        if self.current_user:
            tk.Label(frame, text=f"Tester: {self.current_user}", fg="#f1c40f", bg="#2c3e50",
                     font=("Arial", 12, "bold")).pack(pady=(0, 5))

        tk.Label(frame, text=f"Your Rating: {round(self.player_elo)} Elo", fg="#1abc9c", bg="#2c3e50",
                 font=("Arial", 16, "bold")).pack(pady=10)

        tk.Button(frame, text="Play Chess", width=25, command=lambda: self.open_mode_selection()).pack(pady=10)

        tk.Button(frame, text="Learn Chess (Interactive)", width=25, command=self.show_lesson_menu).pack(pady=5)

        if len(self.elo_history) > 1:
            self.show_performance_graph(frame)

        if self.history:
            tk.Button(frame, text="Review Last Game", width=25, command=lambda: self.run_game_review()).pack(pady=10)

        tk.Button(frame, text="Logout", width=25, command=self.logout_user).pack(pady=5)

        exit_button = tk.Button(frame, text="Exit", width=25, command=self.on_closing)
        exit_button.pack(pady=10)

    def logout_user(self):
        """Log out the current tester and return to the login screen."""
        self.save_profile()
        self.current_user = None
        self.create_login_ui()

    def show_lesson_menu(self):
        """Show the menu for lessons."""
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
        """Start each lesson."""
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
        """Show a hint to complete the lesson."""

        target_square = None

        if self.current_lesson_title == "Checks and Captures":
            target_square = chess.C3

        elif self.current_lesson_title == "Stalemates":
            target_square = chess.C7

        if target_square is not None:
            # Redraw the board first so old hints are removed.
            self.draw_board()

            column = chess.square_file(target_square)
            row = 7 - chess.square_rank(target_square)

            # The empty fill keeps the chessboard visible.
            self.canvas.create_rectangle(column * 60, row * 60,
                                         (column + 1) * 60,
                                         (row + 1) * 60,
                                         outline="#e74c3c", width=3)

            messagebox.showinfo("Hint!", "Focus on the highlighted square.")

        else:
            messagebox.showinfo("Hint!", "Move to any legal square to complete this lesson.")

    def check_lesson_goal(self, title, start_fen, move):
        """Check whether the required lesson objective was completed."""

        passed = False

        if title == "Piece Movements":
            # Any legal move completes this lesson.
            passed = True

        elif title == "Checks and Captures":
            temp_board = chess.Board(start_fen)
            captured_piece = temp_board.piece_at(move.to_square)

            # The required move must capture the knight on c3.
            passed = (
                move.to_square == chess.C3
                and captured_piece is not None
                and captured_piece.piece_type == chess.KNIGHT
            )

            if not passed:
                # Reset the position if this method is called with an
                # incorrect move.
                self.board = chess.Board(start_fen)
                self.selected_square = None
                self.legal_targets = []
                self.draw_board()

                messagebox.showinfo(
                    "Try again",
                    "You must capture the knight on c3 to complete this lesson.",
                )
                return

        elif title == "Stalemates":
            temp_board = chess.Board(start_fen)
            temp_board.push(move)
            passed = temp_board.is_stalemate()

        if passed:
            self.completed_lessons[title] = True
            self.save_profile()
            messagebox.showinfo(
                "Success",
                f"Lesson '{title}' completed!",
            )
            self.show_lesson_menu()

    def show_performance_graph(self, parent_frame):
        figure, ax = plt.subplots(figsize=(4, 2), dpi=100)
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
        self.pause_game_clock()
        self.board = chess.Board()
        self.game_settings.destroy()
        self.ai_level = level
        self.player_color = player_color
        self.history = []
        self.selected_square = None
        self.legal_targets = []
        self.white_time = 600.0
        self.black_time = 600.0
        self.active_color = chess.WHITE
        self.clock_running = False
        self.last_tick = None
        self.clock_job = None
        self.clear_screen()
        self.chess_board_ui()

    def chess_board_ui(self):
        self.canvas = tk.Canvas(self.container, width=480, height=480, highlightthickness=0)
        self.canvas.pack(pady=10)

        self.canvas.bind("<Button-1>", self.handle_click)
        self.elo_label = tk.Label(self.container, text=f"Your Elo: {round(self.player_elo)}  |  Opponent Elo: {Bot_ratings[self.ai_level]}",
                                  fg="white", bg="#2c3e50", font=("Arial", 14, "bold"))
        self.elo_label.pack(pady=5)

        self.clock_label = tk.Label(self.container, text=self.format_clock(self.white_time, self.black_time),
                                    fg="#f1c40f", bg="#2c3e50", font=("Arial", 16, "bold"))
        self.clock_label.pack(pady=5)

        self.start_game_clock()
        self.draw_board()

    def format_clock(self, white_time, black_time):
        """Format the clock display."""
        white_mins = int(white_time // 60)
        white_secs = int(white_time % 60)
        black_mins = int(black_time // 60)
        black_secs = int(black_time % 60)

        return (
            f"White: {white_mins:02d}:{white_secs:02d} "
            f"Black: {black_mins:02d}:{black_secs:02d}"
            )

    def start_game_clock(self):
        """Start the active players clock."""
        if self.board.is_game_over() or self.clock_label is None or self.clock_job is not None:
            return

        self.clock_running = True
        self.last_tick = time.monotonic()
        self.clock_job = self.root.after(100, self.tick_clock)

    def tick_clock(self):
        """reduce the active players remaining time"""
        self.clock_job = None
        if not self.clock_running or self.board.is_game_over():
            return

        now = time.monotonic()
        elapsed = now - self.last_tick
        self.last_tick = now

        if self.active_color == chess.WHITE:
            self.white_time = max(0.0, self.white_time - elapsed)
        else:
            self.black_time = max(0.0, self.black_time - elapsed)

        if self.clock_label is None:
            self.clock_running = False
            return

        self.clock_label.config(text=self.format_clock(self.white_time, self.black_time))

        if self.white_time <= 0 or self.black_time <= 0:
            self.clock_running = False
            self.handle_time_out()
            return

        self.clock_job = self.root.after(100, self.tick_clock)

    def pause_game_clock(self):
        """Pause the game clock."""
        self.clock_running = False
        if self.clock_job is not None:
            self.root.after_cancel(self.clock_job)
            self.clock_job = None

    def resume_game_clock(self):
        """Resume the game clock."""
        if not self.board.is_game_over():
            self.start_game_clock()

    def switch_active_color(self):
        """Switch the active color after a move."""
        self.active_color = chess.BLACK if self.active_color == chess.WHITE else chess.WHITE
        self.last_tick = time.monotonic()
        if self.clock_label is not None:
            self.clock_label.config(text=self.format_clock(self.white_time, self.black_time))

    def draw_board(self, current_board=None):
        if current_board is None:
            current_board = self.board
        self.canvas.delete("all")
        for r in range(8):
            for c in range(8):
                x1, y1, x2, y2 = c*60, r*60, (c+1)*60, (r+1)*60
                color = COLORS[(r+c) % 2]

                if self.selected_square is not None:
                    if r == 7-chess.square_rank(self.selected_square) and c == chess.square_file(self.selected_square):
                        color = "#f7f769"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                chess_square = chess.square(c, 7-r)
                piece_position = current_board.piece_at(chess_square)
                if piece_position:
                    self.canvas.create_text(x1+30, y1+30, text=PIECES[piece_position.symbol()], font=("Arial", 36))

        if self.selected_square is not None:
            for target_square in self.legal_targets:
                col = chess.square_file(target_square)
                row = 7 - chess.square_rank(target_square)
                x = col * 60 + 30
                y = row * 60 + 30
                self.canvas.create_oval(x - 12, y - 12, x + 12, y + 12, fill="#2ecc71", outline="#27ae60", width=2)

    def handle_click(self, event):
        """Handle selecting and moving chess pieces on the board."""

        column = event.x // 60
        row = 7 - (event.y // 60)
        square = chess.square(column, row)

        final_move = None

        if self.selected_square is None:
            piece = self.board.piece_at(square)

            if piece and piece.color == self.board.turn:
                self.selected_square = square

                self.legal_targets = [move.to_square for move in self.board.legal_moves if move.from_square == square]
                self.draw_board()

        else:
            # Clicking the selected piece again cancels the selection.
            if square == self.selected_square:
                self.selected_square = None
                self.legal_targets = []
                self.draw_board()
                return

            move = chess.Move(self.selected_square, square)

            # Automatically promote pawns to queens.
            promotion = chess.Move(self.selected_square, square, chess.QUEEN)

            if move in self.board.legal_moves:
                final_move = move

            elif promotion in self.board.legal_moves:
                final_move = promotion

            if final_move:
                # Validate the Checks and Captures lesson before changing
                # the board or switching the turn.
                if (
                    getattr(self, "lesson_mode", False)
                    and getattr(self, "current_lesson_title", "")
                    == "Checks and Captures"
                ):
                    captured_piece = self.board.piece_at(final_move.to_square)

                    correct_capture = (
                        final_move.to_square == chess.C3
                        and captured_piece is not None
                        and captured_piece.piece_type == chess.KNIGHT
                    )

                    if not correct_capture:
                        self.selected_square = None
                        self.legal_targets = []
                        self.draw_board()

                        messagebox.showinfo(
                            "Try again",
                            "That move is not part of this lesson. Capture the knight on c3.",
                        )
                        return

                start_fen = self.board.fen()

                self.history.append((start_fen, final_move))
                self.board.push(final_move)

                self.selected_square = None
                self.legal_targets = []

                self.draw_board()

                if not getattr(self, "lesson_mode", False):
                    self.pause_game_clock()
                    self.switch_active_color()
                    self.resume_game_clock()

                if not getattr(self, "lesson_mode", False):
                    if (self.ai_level is not None and not self.board.is_game_over()):
                        self.root.after(500, self.make_ai_move)
                    else:
                        self.check_end()

                else:
                    self.check_lesson_goal(getattr(self, "current_lesson_title", ""), start_fen, final_move)

            else:
                # The selected move was illegal.
                self.selected_square = None
                self.legal_targets = []
                self.draw_board()

    def choose_elo_move(self, board, target_elo):
        """Pick a move that resembles a human player around the target Elo."""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        if target_elo <= 200:
            depth = 1
            blunder_chance = 0.35
            candidate_limit = 4
            score_variation = 220
        elif target_elo <= 600:
            depth = 2
            blunder_chance = 0.18
            candidate_limit = 3
            score_variation = 140
        else:
            depth = 3
            blunder_chance = 0.08
            candidate_limit = 2
            score_variation = 90

        try:
            with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                analysis = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=8)
                scored_moves = []

                for info in analysis:
                    pv = info.get("pv", [])
                    if not pv:
                        continue

                    move = pv[0]
                    if move not in legal_moves:
                        continue

                    score = info["score"].pov(board.turn).score(mate_score=10000)

                    if random.random() < blunder_chance:
                        score -= random.randint(150, 500)
                    else:
                        score += random.randint(-50, 120)

                    if board.is_capture(move):
                        score += 20

                    scored_moves.append((move, score))

                if not scored_moves:
                    return random.choice(legal_moves)

                scored_moves.sort(key=lambda item: item[1], reverse=True)
                pool = scored_moves[:candidate_limit]
                return random.choice(pool)[0]

        except Exception:
            if not self.engine_error_shown:
                messagebox.showwarning(
                    "Stockfish unavailable",
                    "Stockfish could not be started. A random legal move will be used."
                )
                self.engine_error_shown = True
            return random.choice(legal_moves)

    def make_ai_move(self):
        try:
            target_elo = Bot_ratings.get(self.ai_level, 200)
            chosen_move = self.choose_elo_move(self.board, target_elo)

            if chosen_move is not None:
                self.execute_bot_move(chosen_move)
                return

            if not self.board.is_game_over():
                self.execute_bot_move(random.choice(list(self.board.legal_moves)))

        except Exception as e:
            print(f"Engine Error: {e}")
            if not self.board.is_game_over():
                self.execute_bot_move(random.choice(list(self.board.legal_moves)))

    def execute_bot_move(self, move):
        self.history.append((self.board.fen(), move))
        self.board.push(move)
        self.draw_board()

        self.pause_game_clock()
        self.switch_active_color()
        self.resume_game_clock()

        self.check_end()

    def handle_time_out(self):
        """Handle the situation when a player's time runs out."""
        if self.active_color == chess.WHITE:
            result = "0-1"  # Black wins
            message = ("Time's Up!", "White's time has run out. Black wins!")
        else:
            result = "1-0"  # White wins
            message = ("Time's Up!", "Black's time has run out. White wins!")

        messagebox.showinfo("Time's Up!", message)
        if not getattr(self, 'lesson_mode', False):
            self.calculate_new_elo(result)
            self.elo_history.append(self.player_elo)
            self.save_profile()
        self.create_menu_ui()

    def check_end(self):
        if self.board.is_game_over():
            messagebox.showinfo("Game Over", f"Result: {self.board.result()}")
            result_str = self.board.result()

            if not getattr(self, 'lesson_mode', False):
                elo_update = self.calculate_new_elo(result_str)
                self.elo_history.append(self.player_elo)
                self.save_profile()
                if self.player_elo >= 1000:
                    self.show_graduation_screen()

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

        # calulate elo change
        rating_change = k_factor * (actual_score - expected_score)

        # change user's elo
        self.player_elo += rating_change
        if self.player_elo < 100:
            self.player_elo = 100

        return rating_change

    def show_graduation_screen(self):
        """Show the graduation celebration once the player reaches 1000 Elo."""
        if self.graduation_shown:
            return

        self.graduation_shown = True
        popup = tk.Toplevel(self.root)
        popup.title("Graduation! 🎉")
        popup.geometry("500x260")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(
            popup,
            text="Congratulations!",
            fg="#f1c40f",
            bg="#2c3e50",
            font=("Arial", 26, "bold")
        ).pack(pady=(20, 10))

        tk.Label(
            popup,
            text="You have graduated from the training program\nwith a rating of 1000 Elo!",
            fg="white",
            bg="#2c3e50",
            font=("Arial", 16),
            justify="center"
        ).pack(pady=10)

        tk.Label(
            popup,
            text="Your chess journey is off to a strong start.",
            fg="#1abc9c",
            bg="#2c3e50",
            font=("Arial", 12, "italic")
        ).pack(pady=10)

        tk.Button(
            popup,
            text="Return to Menu",
            width=20,
            command=lambda: [popup.destroy(), self.create_menu_ui()]
        ).pack(pady=20)

    def run_game_review(self):
        self.clear_screen()
        tk.Label(self.container, text="Stockfish is analysing your performance...",
                 fg="white", bg="#2c3e50", font=("Arial", 14)).pack(pady=10)
        self.root.update()
        current_total_loss = 0
        current_moves_count = 0
        self.review_analysis_data = []
        player_color = getattr(self, "player_color", chess.WHITE)

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
                    "for a strong tactical advantage.")

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
            "Miss": "#e64922",
            "Mistake": "#da843a",
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

        self.exp_label.config(text=(f"Move {self.review_index + 1}: {data['quality']}\n"
                                    f"{data['exp']}{best_text}"), fg=color_map.get(data["quality"], "white"))

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
