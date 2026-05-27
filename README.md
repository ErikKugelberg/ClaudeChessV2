This project consists of a hobby chess-engine which was, at first, developed to learn Python (bot1.py in first commit was written without AI help in 2023).

Later, in 2026, this project was continued in the quest to learn Claude Code and agentic workflows. Bot2.py is a result of this work.

Anyone reading this is free to use the software however they'd like.

## Running the Project:
# GUI viewer: watch bots play or play against bot2 interactively
python chessViewer.py

# Standard benchmark: 10 games, 0.5s per move — used for bot2 evaluations
python botFighter.py --games 10 --time-limit 0.5
