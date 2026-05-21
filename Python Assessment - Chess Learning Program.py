import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import PhotoImage
from PIL import Image, ImageTk
import chess
import chess.engine

Square_Size = 60
Colors = ["#eeeed2", "#769656"]
PIECES = {'R':'♖','N':'♘','B':'♗','Q':'♕','K':'♔','P':'♙','r':'♜','n':'♞','b':'♝','q':'♛','k':'♚','p':'♟'}

root = tk.Tk()
root.geometry("600x750")

class DylanChessProgram:
    def __init__(self, root):
        self.root = root
        self.root.title("Dylan's Chess: Training & Review")
        self.board = chess.Board()
        self.history = []  # Stores (FEN, Move)
        self.review_analysis = [] # Stores analysis data
        self.selected_square = None
        self.ai_level = 0 # 0=Easy, 1=Med, 2=Hard
        self.review_index = -1

        self.container = tk.Frame(self.root, bg="#2c3e50")
        self.container.pack(fill="both", expand=True)
        self.create_menu_ui()

    def clear_screen(self):
        for window in self.container.winfo_children(): window.destroy()

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
        
        tk.Button(frame, text="Play Chess", width=25, command=lambda: self.start_game(None)).pack(pady=10)

    def start_game(self, level):
        self.ai_level = level
        self.board = chess.Board()
        self.history = []
        self.clear_screen()
        self.chess_board_ui()

    def chess_board_ui(self):
        self.canvas = tk.Canvas(self.container, width=480, height=480, highlightthickness=0)
        self.canvas.pack(pady=10)

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
                        text=PIECES[piece_position.symbol()], font="Arial")



app = DylanChessProgram(root)
root.mainloop()