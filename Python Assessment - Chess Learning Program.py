import tkinter as tk
from tkinter import ttk
from tkinter import *
import chess
import chess.engine

Square_Size = 60
Colors = ["#eeeed2", "#769656"]
PIECES = {'R':'♖','N':'♘','B':'♗','Q':'♕','K':'♔','P':'♙','r':'♜','n':'♞','b':'♝','q':'♛','k':'♚','p':'♟'}

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

        

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("600x750")
    app = DylanChessProgram(root)
    root.mainloop()