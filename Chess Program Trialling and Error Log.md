Chess Learning Program: Trialling and Error Log

Method

I examined the program’s current state and Git repository commits to identify relevant changes. I reviewed the current Python file and all previous versions of it. All 17 historical versions of the Python file parsed successfully, suggesting that any errors were not present in syntax but rather in execution, logic, usability, and portability.

The example document demonstrates each trial in four sections: the problem, the changes, the result, and why the change was an improvement. Each trial follows the same format.

Trial 1: Stockfish engine could not be found

The main issue was that the path to the Stockfish engine was incorrectly set to a Google Drive folder. When run on a computer where this folder was unavailable, Windows raised the error “[WinError 2] The system cannot find the file specified.” This occurred at the line “chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH).”

This error was fixed in “commit f8feb87”, which updated the path to a local project folder. This change fixed the error for the committer, who used Windows, but the path is still hardcoded to their machine.

The trial shows an improvement, as the engine path is now available locally. However, STOCKFISH_PATH should be resolved relative to the project folder, and the program should check if the file exists before attempting to launch the game.

Trial 2: Lesson moves crashed the game clock

The error occurred when testing the lesson mode. Trying to move a piece raised an AttributeError because the clock label was not generated in the lesson. The crash occurred at the line “self.clock_label.config(text=elapsed_formatted)” because switch_active_color tried to access self.clock_label, which was None.

The fix was to detect lesson mode and skip clock-switching logic, implemented in “commit 8ae35d3.”

This was an important change because lessons now have a separate logic branch. 

A possible further improvement is that it could be helpful to implement similar changes for other modes, for example, remove Elo calculation code for clocks in lesson mode.

Trial 3: Rating estimate could become negative

The estimated rating based on accuracy had no lower bound. It was possible for the rating to become negative if the player’s accuracy was sufficiently low.

This was fixed in “commit c7cf61c.” The commit sets the lower bound to 100, preventing the rating from going below this value.

It was a necessary change because the rating estimate rarely made sense below 100 Elo, and 100 Elo is globally accepted as the lowest level, and a negative rating would have been confusing to the user.

Trial 4: False Brilliant move classifications

The move review system classified many moves as brilliant. This occurred because the logic for doing so did not require the move to be a sacrifice with a tactical justification.

The problem was fixed in “commit bd53280,” which added several conditions. The commit made it so that a brilliant move had to involve a valuable piece, be captured or give a check, and have a negligible engine evaluation loss.

The change was an improvement because it reduced the number of false positives. The change is still an approximation because the move review system is not designed to perfectly categorise moves. 

Further improvement could involve testing with example positions with a more experienced chess player for assistance.

Trial 5: Legal moves were not visible

When clicking on a chess piece, the legal moves were not indicated on the board. This made it harder to learn how pieces moved.

The current implementation stores legal destination squares in self.legal_targets and highlights them in green. After making a move or clicking on another piece, the legal moves are removed.

It is now clearer what moves are available, which improves the learning experience. It also becomes easier to see illegal moves, as they are distinguished from legal moves.

Further improvement could involve highlighting the last move made or perhaps using the arrow system from chess.com.

Trial 6: Bot difficulty did not match its Elo

The bot difficulty levels did not scale consistently with their Elo rating. A bot with an Elo rating of 1000 was almost identical to Stockfish but used a smaller search window.

The current implementation uses Stockfish to find candidate moves but limits the number of moves considered and makes it select between them with a biased probability distribution. Lower-rated bots have a smaller search window and a higher chance of making a mistake. The 1000 Elo bot searches deeper but still picks between a few candidate moves and can make occasional errors.

It was an important change because the bot no longer tries to play perfectly every move, which would be unrealistic for lower-rated opponents. 
In order to further increase the accuracy of the 1000 Elo bot, a stress test against human players or standard Elo-rated positions could be a means of further improving the bot.

Trial 7: Tester progress was lost between sessions

Before this change, testers could not retain their Elo rating, lesson progress, and Elo history upon closing the application. It made the app unsuitable for serious study because testers could only track their progress within a single session.

The change added tester accounts, which are stored in tester_accounts.json. Each account saves the password, Elo rating, Elo history, and lesson progress. The application saves progress when it is closed, logged out of, a lesson is finished, or the app returns to the menu.

It was a critical change because testers could now resume their progress after closing the app. It became possible to distinguish between different testers. Another important observation was that, for security reasons, passwords should be salted and stored in a secure location rather than project files.

Trial 11: New games reuse old clock state

When starting a new game, the clock states such as white_time, black_time, active_color, selected_square, and legal_targets are not reset. As a result, a player could launch a new game with the same settings as the previous one midway through.

The bug was verified by comparing the __init__ variables and the start_game function.
It was fixed by adding code that zeroes these values when a new game starts. It would make new games more consistent by resetting each value rather than carrying over the previous game’s state.

### Trial 1 evidence: Stockfish path

**Discovered:** 2026-08-22, recorded in commit `f8feb87`.

**Before:**

```python
STOCKFISH_PATH = "G:\\My Drive\\Level 3 NCEA\\L3DTSD\\stockfish-windows-x86-64-avx2\\stockfish\\stockfish-windows-x86-64-avx2.exe"
```

**After:**

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOCKFISH_PATH = os.path.join(
	BASE_DIR,
	"stockfish-windows-x86-64-avx2-20260821T230608Z-1-001",
	"stockfish-windows-x86-64-avx2",
	"stockfish",
	"stockfish-windows-x86-64-avx2.exe"
)
```

The new code builds the path from the folder containing the Python file, so it no longer depends on my Google Drive or username.

### Trial 2 evidence: Lesson timer crash

**Discovered:** 2026-08-22, recorded in commit `8ae35d3`.

**Before:**

```python
self.pause_game_clock()
self.switch_active_color()
self.resume_game_clock()
```

**After:**

```python
if not getattr(self, 'lesson_mode', False):
	self.pause_game_clock()
	self.switch_active_color()
	self.resume_game_clock()
```

The new condition prevents lesson moves from using a clock label that does not exist on the lesson screen.

### Trial 3 evidence: Negative rating

**Discovered:** 2026-07-30, recorded in commit `c7cf61c`.

**Before:**

```python
self.performance_rating = round(estimated_rating)
```

**After:**

```python
self.performance_rating = max(100, round(estimated_rating))
```

The minimum prevents an impossible negative displayed rating. Suggested photo: the review screen showing the old negative result and the corrected screen showing the minimum of 100 Elo.

### Trial 4 evidence: False Brilliant classifications

**Discovered:** 2026-08-13, recorded in commit `bd53280`.

**Before:**

```python
if is_sacrifice and loss <= 5:
	return "Brilliant", "Brilliant idea!"
```

**After:**

```python
valuable_piece = moved_value >= piece_values[chess.KNIGHT]
is_sacrifice = (
	valuable_piece
	and piece_can_be_captured
	and (creates_check or is_capture)
)
if is_sacrifice and loss <= 5:
	return ("Brilliant", f"Brilliant idea! {move_text} offers material "
			"for a strong tactical advantage.")
```

The new code requires the move to be a valuable, capturable sacrifice with a check or capture, reducing false labels.

### Trial 5 evidence: Legal moves not visible

**Discovered:** 2026-08-23, during current-code review.

**Before:**

```python
if piece and piece.color == self.board.turn:
	self.selected_square = square
	self.draw_board()
```

**After:**

```python
if piece and piece.color == self.board.turn:
	self.selected_square = square
	self.legal_targets = [
		move.to_square for move in self.board.legal_moves
		if move.from_square == square
	]
	self.draw_board()
```

The new code collects legal destination squares and passes them to the board renderer and creates cyan dots.

### Trial 6 evidence: Unrealistic bot difficulty

**Discovered:** 2026-08-23, during current-code review.

**Before:**

```python
engine.configure({"Skill Level": 15})
engine_move = engine.play(self.board, chess.engine.Limit(time=0.1))
```

**After:**

```python
target_elo = Bot_ratings.get(self.ai_level, 200)
chosen_move = self.choose_elo_move(self.board, target_elo)
```

The new code selects from engine candidates using target-Elo-specific depth, candidate limits, and mistake probability rather than always relying on one engine move.

### Trial 7 evidence: Progress lost between sessions

**Discovered:** 2026-08-22, recorded in commit `b0a8d2c`.

**Before:**

```python
self.player_elo = 200
self.elo_history = [200]
self.create_menu_ui()
```

**After:**

```python
self.accounts = self.load_accounts()
self.create_login_ui()
```

The new login flow loads the selected tester profile from `tester_accounts.json`, allowing Elo and lesson progress to persist.

### Trial 8 evidence: Timer callbacks multiplying

**Discovered:** 2026-08-23, during current-code review.

**Before:**

```python
self.root.after(100, self.tick_clock)
```

**After:**

```python
self.clock_job = self.root.after(100, self.tick_clock)

def pause_game_clock(self):
	self.clock_running = False
	if self.clock_job is not None:
		self.root.after_cancel(self.clock_job)
		self.clock_job = None
```

The new code stores the scheduled callback and cancels it before restarting the clock, preventing multiple timer loops. Suggested photo: a timed game after repeated moves, with a recorded wall-clock comparison before and after the fix.

## Verification record

After the fixes, the current program was checked on 2026-08-23 with the following results:

```text
Pylance/editor diagnostics: No errors found
Python compilation: passed
git diff --check: passed
Project-relative Stockfish path: exists
```

The historical syntax scan also compiled all 17 available Python revisions successfully. This means the Git history did not contain a syntax error, but it did contain the runtime and logic errors documented above.
