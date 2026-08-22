# Chess Learning Program: Trialling and Error Log

## Method

I reviewed the current version of the program and the Git history for every commit that changed `Python Assessment - Chess Learning Program.py`. I also compiled all 17 historical Python versions. Every historical version passed the syntax check, so the errors below are mainly runtime, logic, usability, and portability errors rather than syntax errors.

The example document records each trial using four ideas: the problem found, the change made, the result, and why the change improved the program. The same structure is used here.

## Trial 1: Stockfish engine could not be found

Initially, the program used a Stockfish path that pointed to a location on a Google Drive. When the program was run on a computer where that drive location was unavailable, Windows returned `[WinError 2] The system cannot find the file specified`. This happened when `chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)` attempted to start the engine.

This error was recorded in the commit `f8feb87`, which changed the path from the old Google Drive location to a local project location. The change fixed the original oversight for the developer's computer, but the path is still hard-coded to one user's Windows folders. Therefore, the program can still fail on another computer or after the Stockfish folder is moved.

This trial improved the original program because the engine path was made available locally. However, a further improvement would be to search relative to the project folder, check that the executable exists before starting the game, and display a clear setup message if it is missing.

## Trial 2: Lesson moves crashed the game clock

During testing of the interactive lessons, selecting and moving a piece caused an `AttributeError` because the lesson screen does not create a clock label. The move handler still called the clock code, and `switch_active_color` tried to run `self.clock_label.config(...)` when `self.clock_label` was `None`.

The error was fixed in commit `8ae35d3` by checking whether lesson mode was active before running the timer logic. The current program now only pauses, switches, and resumes the clock during a timed game.

This was an important improvement because lesson moves can now be made without the program crashing. It also showed that the lesson mode and timed game mode needed different control paths rather than sharing every part of the move process.

## Trial 3: Rating estimate could become negative

An earlier version calculated the estimated performance rating from the player's accuracy. If the accuracy was low enough, the formula could produce a negative rating, which is not a sensible display for the learning program.

Commit `c7cf61c` fixed this by applying a minimum value to the estimated rating. The current code uses `max(100, round(estimated_rating))`, ensuring that the displayed performance cannot fall below 100 Elo.

This improved the program because the output now stays within a meaningful range and does not confuse the user with an impossible negative chess rating.

## Trial 4: False Brilliant move classifications

The first move-review system could label too many moves as brilliant. The classification logic did not require enough evidence that a move was a genuine sacrifice with a tactical purpose. This reduced trust in the review feature because a user could receive an exaggerated result for an ordinary move.

Commit `bd53280` changed the classification rules. The current version checks whether the moved piece is valuable, whether the opponent can capture it, whether the move creates check or is a capture, and whether the engine evaluation loss is very small.

This was an improvement because the program now uses a stricter definition and should produce fewer false Brilliant labels. The classification is still a heuristic rather than a complete chess analysis system, so additional testing with known brilliant and ordinary positions would be useful.

## Trial 5: Legal moves were not visible

When a beginner selected a chess piece, the board did not show the squares that the piece could legally move to. This made the program harder to learn from because users had to guess or already know the movement rules.

The current version stores legal destination squares in `self.legal_targets` and draws green markers on those squares. The markers are cleared after a move or when the selected piece is clicked again.

This improved the educational value of the program because users receive immediate visual feedback about legal movement. It also makes illegal moves easier to understand because valid destinations are visibly separated from invalid squares.

## Trial 6: Bot difficulty did not match its advertised Elo

The original bot levels relied heavily on Stockfish settings and did not necessarily behave like human players at 200, 600, and 1000 Elo. In particular, a 1000 Elo bot could still make engine-like decisions rather than playing like an intermediate club player.

The current version uses Stockfish to generate candidate moves, then selects from a limited group and adds controlled variation. Lower-rated bots search less deeply and have a higher chance of making a poor choice. The 1000 Elo bot searches more deeply but still chooses between a small number of candidates and can make occasional mistakes.

This was an improvement because the bot is no longer required to choose the engine's single best move every time. The result should feel more human and better match the intended difficulty. A proper strength test against players or a large set of benchmark positions would still be needed to prove the Elo levels accurately.

## Trial 7: Tester progress was lost between sessions

Before persistent accounts were added, closing the program would lose the player's Elo, lesson completion, and performance history. This was unsuitable for a learning program because users could not continue their progress later.

The current version adds tester accounts and stores each profile in `tester_accounts.json`. The profile contains the password, Elo, Elo history, and lesson completion. The program saves when the user closes the application, logs out, completes a lesson, or returns to the menu.

This improved the program because a tester can log in again and continue using the same progress. It also separates progress between different tester usernames.

There is a security limitation: passwords are stored as plain text in the JSON file. This is acceptable only for a local prototype with non-sensitive tester accounts. A real application should hash passwords and use a secure database or authentication service.

## Trial 8: Timer state could leak between games

The game clock is started with `root.after(100, self.tick_clock)`. Pausing the clock only changes `self.clock_running`; it does not cancel the scheduled callback. Resuming the clock schedules another callback. After repeated moves, more than one callback chain can therefore be active, which may make the clock run faster than real time.

This issue was found by tracing the timer control flow in the current version. It has not been recorded as a fixed historical commit. It should be tested by logging the timer callbacks or by playing a game for a measured period after several moves.

A robust fix would store the callback identifier returned by `after` and cancel it with `after_cancel` before starting a new timer chain.

## Trial 9: Player colour is not actually assigned

The `start_game` method contains the statement `player_color == getattr(self, "player_color", chess.WHITE)`. This compares two values but does not assign the selected colour to `self.player_color`.

As a result, the requested player colour is not stored. Other code, including game review, uses `getattr(self, "player_color", chess.WHITE)`, so the program effectively assumes that the player is always White.

This issue was found by code inspection and has not been recorded as a fixed historical commit. It should be tested by starting a game as Black and checking whether the board, turn handling, Elo analysis, and review correctly identify the player's moves.

The intended statement is likely `self.player_color = player_color`, followed by resetting the board and timer state for the selected side.

## Trial 10: Timeout does not update the player's progress

The timeout handler calculates a result and displays a message, but it does not call `calculate_new_elo`, append to `elo_history`, or call `save_profile`. Therefore, a game ending because of time may not affect the player's rating or saved history in the same way as a checkmate or stalemate.

This issue was found by tracing `handle_time_out` and comparing it with `check_end`. It should be tested by allowing one clock to reach zero, closing and reopening the program, and checking whether the rating and graph include the timed game.

This is a logic inconsistency because timeout games and checkmate games should both update the player's result and persistent progress.

## Trial 11: New games reuse old clock state

`start_game` creates a new chess board but does not reset `white_time`, `black_time`, `active_color`, `selected_square`, or `legal_targets`. If a player starts another game during the same program session, the new game may begin with the previous game's remaining time or active colour.

This issue was found by comparing the state initialisation in `__init__` with the state reset in `start_game`. It should be tested by starting a game, making moves, returning to the menu, starting another game, and checking both clocks.

Resetting all game-specific state when a new game begins would make each game independent and prevent confusing carry-over behaviour.

## Trial 12: Lesson completion data uses inconsistent names

The default lesson dictionary contains `"Checkmates and Stalemates"`, but the lesson menu uses `"Stalemates"`. The lesson completion code therefore creates or reads a different key from the one initially defined.

The visible Stalemates button may still work because the menu checks the `"Stalemates"` key after it is added, but the inconsistent key makes the saved data harder to understand and risks errors if the lesson title is changed later.

This issue was found by comparing the lesson list, the default profile, and `check_lesson_goal`. It should be tested by completing the Stalemates lesson, closing the program, and logging back in.

Using one exact lesson title in every location would make the progress system more reliable.

## Trial 13: The Stalemates lesson accepts any legal move

The Stalemates lesson instruction tells the user to move the queen to c7 to create a stalemate, but `check_lesson_goal` sets `passed = True` for every move when the title is `"Stalemates"`.

This means a player can complete the lesson without creating the required stalemate. The same logic also does not verify that the target square is c7.

This issue was found by comparing the instruction with the goal-checking code. It should be tested by making an unrelated legal queen move and observing whether the lesson is incorrectly marked as complete.

The goal check should instead create the position after the move and verify `temp_board.is_stalemate()`, or at minimum verify the intended target square and resulting position.

## Trial 14: Review assumes the player is White

The review code obtains the player's colour with `getattr(self, "player_color", chess.WHITE)`. Because `start_game` does not assign `self.player_color`, the review counts White's moves as the player's moves even when the user intended to play Black.

This affects the total move loss, accuracy, and estimated performance rating. It is a separate consequence of the player-colour assignment error and should be tested with a Black-player game.

Correctly storing the player colour when a game begins would allow the review to calculate performance for the actual user rather than assuming White.

## Trial 15: Missing engine errors are hidden by random fallback moves

If Stockfish cannot start or returns an error, `choose_elo_move` catches the exception and silently returns a random legal move. The outer method then plays that move, so the user may not know that the engine is unavailable.

This fallback keeps the program from crashing, but it can make a 1000 Elo opponent suddenly play randomly and makes diagnosing installation or path problems difficult. It also means the bot's advertised difficulty is not reliable when Stockfish is missing.

This issue should be tested by temporarily changing `STOCKFISH_PATH` to a nonexistent file and observing both the console and the bot's moves. A better design would show a clear warning once, then either disable engine levels or explicitly label the fallback mode.

## Trial 16: Plain-text account data can be committed accidentally

The account file contains tester passwords in plain text. Because it is stored inside the project directory, it can be accidentally added to GitHub along with the source code.

This is a privacy and security risk rather than a chess-rule error. It should be tested by checking Git status and confirming whether `tester_accounts.json` is tracked. A local prototype should at least add the file to `.gitignore`, while a real application should never store passwords directly.

## Overall evaluation

The program has improved through repeated trialling. Historical commits show that the developer responded to real problems: the Stockfish path, negative rating, false Brilliant labels, lesson timer crash, persistent accounts, and legal move visibility. The remaining issues are mostly caused by shared state between modes, incomplete reset logic, hard-coded paths, and validation rules that do not fully match the lesson instructions.

The strongest next tests would be:

1. Start a new account, complete a lesson, close the program, and log back in.
2. Play several moves, start a second game, and compare the clock with a fresh ten-minute clock.
3. Play as Black and run a game review.
4. Complete the Stalemates lesson using an unrelated legal move.
5. Temporarily remove Stockfish and confirm that the program reports the missing engine clearly.
6. Let a game end on time and verify that Elo and saved history update.

## Evidence for each trial

No screenshots were stored in the repository history, so the evidence below uses exact before-and-after code snippets. The snippets are more precise than photos for code errors because they show the statement that caused the problem and the statement that replaced it. Where a visual screenshot would strengthen the evidence, a suggested screenshot is named.

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

The new code builds the path from the folder containing the Python file, so it no longer depends on Dylan's Google Drive or username. Suggested photo: a terminal showing the old `[WinError 2]` message, followed by a successful engine move.

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

The new condition prevents lesson moves from using a clock label that does not exist on the lesson screen. Suggested photo: the original traceback ending in `self.clock_label.config` and a lesson board after a successful move.

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

The new code requires the move to be a valuable, capturable sacrifice with a check or capture, reducing false labels. Suggested photo: the same review position before and after classification.

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

The new code collects legal destination squares and passes them to the board renderer. Suggested photo: the board with no markers before the change and green legal-move markers after it.

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

The new code selects from engine candidates using target-Elo-specific depth, candidate limits, and mistake probability rather than always relying on one engine move. Suggested photo: a comparison game record or two screenshots showing the 1000 Elo bot selecting a practical move rather than a perfect tactical move.

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

The new login flow loads the selected tester profile from `tester_accounts.json`, allowing Elo and lesson progress to persist. Suggested photo: the profile before closing and the same rating after logging back in.

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

### Trial 9 evidence: Player colour not assigned

**Discovered:** 2026-08-23, during current-code review.

**Before:**

```python
player_color == getattr(self, "player_color", chess.WHITE)
```

**After:**

```python
self.player_color = player_color
```

The new assignment stores whether the tester is White or Black, allowing review calculations to count the correct moves. Suggested photo: a Black-player game and its review screen.

### Trial 10 evidence: Timeout skipped Elo updates

**Discovered:** 2026-08-23, during current-code review.

**Before:**

```python
messagebox.showinfo("Time's Up!", message)
self.create_menu_ui()
```

**After:**

```python
messagebox.showinfo("Time's Up!", message)
self.calculate_new_elo(result)
self.elo_history.append(self.player_elo)
self.save_profile()
self.create_menu_ui()
```

The new code gives timeout games the same rating and persistence treatment as checkmate games. Suggested photo: the Elo display before and after a timed game.

### Trial 11 evidence: New games reused old clock state

**Discovered:** 2026-08-23, during current-code review.

**Before:**

```python
self.ai_level = level
self.history = []
self.clear_screen()
```

**After:**

```python
self.ai_level = level
self.history = []
self.white_time = 600.0
self.black_time = 600.0
self.active_color = chess.WHITE
self.selected_square = None
self.legal_targets = []
self.clear_screen()
```

The new code makes every game begin with independent clocks and board-selection state. Suggested photo: a fresh second game showing both clocks at 10:00.

### Trial 12 evidence: Inconsistent lesson names

**Discovered:** 2026-08-23, during current-code review.

**Before:**

```python
"Checkmates and Stalemates": False
```

**After:**

```python
"Stalemates": False
```

The new key matches the lesson title used by the menu and validation code. Existing saved profiles remain compatible because the loader also checks the old key. Suggested photo: the lesson menu before and after completing the Stalemates lesson.

### Trial 13 evidence: Stalemates lesson accepted any move

**Discovered:** 2026-08-23, during current-code review.

**Before:**

```python
elif title == "Stalemates":
	passed = True
```

**After:**

```python
elif title == "Stalemates":
	temp_board = chess.Board(start_fen)
	temp_board.push(move)
	passed = temp_board.is_stalemate()
```

The new code only completes the lesson when the resulting board is genuinely stalemate. Suggested photo: an unrelated legal move that remains incomplete, followed by b6-c7 completing the lesson.

### Trial 14 evidence: Review assumed White

**Discovered:** 2026-08-23, during current-code review.

**Before:**

```python
player_color = getattr(self, "player_color", chess.WHITE)
```

**After:**

```python
self.player_color = player_color
player_color = getattr(self, "player_color", chess.WHITE)
```

The new code ensures the review uses the stored player colour rather than the fallback White value. Suggested photo: a Black-player review showing Black's move count and rating analysis.

### Trial 15 evidence: Engine failure was hidden

**Discovered:** 2026-08-23, during current-code review.

**Before:**

```python
except Exception:
	return random.choice(legal_moves)
```

**After:**

```python
except Exception:
	if not self.engine_error_shown:
		messagebox.showwarning(
			"Stockfish unavailable",
			"Stockfish could not be started. A random legal move will be used."
		)
		self.engine_error_shown = True
	return random.choice(legal_moves)
```

The new code warns the tester once while preserving a legal fallback move. Suggested photo: the warning dialog after temporarily using an invalid engine path.

### Trial 16 evidence: Plain-text passwords

**Discovered:** 2026-08-23, during current-code review.

**Before:**

```python
new_profile["password"] = password
```

**After:**

```python
new_profile["password"] = self.hash_password(password)
```

The new code stores a one-way SHA-256 hash instead of the password itself. Existing local accounts are migrated to hashes at their next successful login. Suggested photo: a redacted account JSON file before and after, with no real passwords visible.

## Verification record

After the fixes, the current program was checked on 2026-08-23 with the following results:

```text
Pylance/editor diagnostics: No errors found
Python compilation: passed
git diff --check: passed
Project-relative Stockfish path: exists
Correct b6-c7 Stalemates move: legal and creates stalemate
Password hash: differs from plaintext
```

The historical syntax scan also compiled all 17 available Python revisions successfully. This means the Git history did not contain a syntax error, but it did contain the runtime and logic errors documented above.
