import streamlit as st

# --- constants ---
PLAYER_1_PITS = ('A', 'B', 'C', 'D', 'E', 'F')
PLAYER_2_PITS = ('G', 'H', 'I', 'J', 'K', 'L')
OPPOSITE_PIT = {
    'A': 'G', 'B': 'H', 'C': 'I', 'D': 'J', 'E': 'K', 'F': 'L',
    'G': 'A', 'H': 'B', 'I': 'C', 'J': 'D', 'K': 'E', 'L': 'F'
}
NEXT_PIT = {
    'A': 'B', 'B': 'C', 'C': 'D', 'D': 'E', 'E': 'F', 'F': '1',
    '1': 'L', 'L': 'K', 'K': 'J', 'J': 'I', 'I': 'H', 'H': 'G',
    'G': '2', '2': 'A'
}

@st.cache_data
def get_new_board(starting_seeds=4):
    board = {'1': 0, '2': 0}
    for pit in PLAYER_1_PITS + PLAYER_2_PITS:
        board[pit] = starting_seeds  # set seeds per pit based on sidebar input
    return board

@st.cache_data
def stone_text(n, with_word=False):
    return f"{n}" + (" stone" if with_word else "") if n == 1 else f"{n} stones" if with_word else str(n)

# --- game logic ---
def make_move(board, player, pit):
    # sow seeds from pit
    seeds = board[pit]
    board[pit] = 0
    while seeds:
        pit = NEXT_PIT[pit]
        if (player == '1' and pit == '2') or (player == '2' and pit == '1'):
            continue  # skip opponent's mancala
        board[pit] += 1
        seeds -= 1
    # extra turn if landing in own mancala
    if pit == player:
        return player
    # capture move if landing in empty own pit and opposite pit has seeds
    if player == '1' and pit in PLAYER_1_PITS and board[pit] == 1 and board[OPPOSITE_PIT[pit]] > 0:
        board['1'] += board[OPPOSITE_PIT[pit]] + 1
        board[pit] = board[OPPOSITE_PIT[pit]] = 0
    elif player == '2' and pit in PLAYER_2_PITS and board[pit] == 1 and board[OPPOSITE_PIT[pit]] > 0:
        board['2'] += board[OPPOSITE_PIT[pit]] + 1
        board[pit] = board[OPPOSITE_PIT[pit]] = 0
    return '2' if player == '1' else '1'

def check_winner(board):
    total = sum(board[p] for p in ['1', '2'] + list(PLAYER_1_PITS) + list(PLAYER_2_PITS))
    if board['1'] > total / 2:
        return "Player 1 wins!"
    if board['2'] > total / 2:
        return "Player 2 wins!"
    p1_total = sum(board[p] for p in PLAYER_1_PITS)
    p2_total = sum(board[p] for p in PLAYER_2_PITS)
    if p1_total == 0:
        board['2'] += p2_total
        for p in PLAYER_2_PITS:
            board[p] = 0
    elif p2_total == 0:
        board['1'] += p1_total
        for p in PLAYER_1_PITS:
            board[p] = 0
    else:
        return None
    return "Player 1 wins!" if board['1'] > board['2'] else "Player 2 wins!" if board['2'] > board['1'] else "Tie game!"

def evaluate_board(board):
    return (board['2'] + sum(board[p] for p in PLAYER_2_PITS)) - (board['1'] + sum(board[p] for p in PLAYER_1_PITS))

def minimax(board, depth=-1, alpha=-float('inf'), beta=float('inf'), player=None):
    if depth is not None and depth < 0:
        return (0, None)
    board_copy = board.copy()
    result = check_winner(board_copy)
    if result is not None:
        if result == "Player 2 wins!":
            return (1000, None)
        if result == "Player 1 wins!":
            return (-1000, None)
        return (0, None)
    if depth == 0:
        return (evaluate_board(board), None)
    if player == '2':  # maximizing
        max_eval, best_move = -float('inf'), None
        moves = [p for p in PLAYER_2_PITS if board[p] > 0]
        if not moves:
            return (evaluate_board(board), None)
        for move in moves:
            new_board = board.copy()
            new_player = make_move(new_board, player, move)
            eval_val, _ = minimax(new_board, depth - 1 if depth is not None else None, alpha, beta, new_player)
            if eval_val > max_eval:
                max_eval, best_move = eval_val, move
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return (max_eval, best_move)
    else:  # minimizing
        min_eval, best_move = float('inf'), None
        moves = [p for p in PLAYER_1_PITS if board[p] > 0]
        if not moves:
            return (evaluate_board(board), None)
        for move in moves:
            new_board = board.copy()
            new_player = make_move(new_board, player, move)
            eval_val, _ = minimax(new_board, depth - 1 if depth is not None else None, alpha, beta, new_player)
            if eval_val < min_eval:
                min_eval, best_move = eval_val, move
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return (min_eval, best_move)

# --- callbacks ---
def ai_move_callback(depth):
    eval_val, best_move = minimax(st.session_state.board.copy(), depth, -float('inf'), float('inf'), '2')
    if best_move:
        idx = PLAYER_2_PITS.index(best_move) + 1
        st.write(f"AI chooses pit {idx}")
        st.session_state.playerTurn = make_move(st.session_state.board, '2', best_move)
        if (winner := check_winner(st.session_state.board)):
            st.session_state.winner = winner
    # force re-run if ai still has turn and game isn't over
    if st.session_state.playerTurn == '2' and st.session_state.winner is None:
        st.rerun()

def human_move_callback(player, pit):
    st.session_state.playerTurn = make_move(st.session_state.board, player, pit)
    if (winner := check_winner(st.session_state.board)):
        st.session_state.winner = winner

def new_game_callback():
    seeds = st.session_state.starting_seeds  # get starting seeds from sidebar
    first = st.session_state.first_move      # get first move selection from sidebar
    st.session_state.board = get_new_board(seeds)
    st.session_state.playerTurn = '1' if first == "Player 1" else '2'
    st.session_state.winner = None

# --- ui rendering ---
def render_styles():
    st.markdown("""
        <style>
        div.stButton > button {
            width: 80px;
            height: 80px;
            font-size: 24px;
        }
        .mancala-container {
            height: 180px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        </style>
    """, unsafe_allow_html=True)

def render_board(depth, hints, opponent):
    col_left, col_center, col_right = st.columns([1, 6, 1])
    # left mancala (player2)
    with col_left:
        st.markdown('<div class="mancala-container">', unsafe_allow_html=True)
        store_val = st.session_state.board['2']
        disp = "•" * store_val if store_val else ""
        st.button(f"{disp}\n\n{stone_text(store_val)}", key="store_player2", disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)
    # center board rows
    with col_center:
        st.markdown("#### Top Row (Player 2)")
        top_cols = st.columns(6)
        for i, pit in enumerate("GHIJKL"):
            stones = st.session_state.board[pit]
            disp = "•" * stones if stones else ""
            # disable click if opponent is AI
            clickable = (opponent == "Human" and st.session_state.playerTurn == '2' and stones > 0)
            hint_str = ""
            if hints and clickable:
                board_copy = st.session_state.board.copy()
                new_player = make_move(board_copy, '2', pit)
                eval_val, _ = minimax(board_copy, depth - 1 if depth is not None else None, -float('inf'), float('inf'), new_player)
                if abs(eval_val) == 1000:
                    hint_str = "🟢 (W)" if eval_val > 0 else "🔴 (L)"
                else:
                    hint_str = f"({eval_val:+d})"
            with top_cols[i]:
                st.button(disp + (f"\n\n{hint_str}" if hint_str else ""),
                          key=f"pit_{pit}_top", disabled=not clickable,
                          on_click=human_move_callback, args=('2', pit))
                st.write(stone_text(st.session_state.board[pit], True))
        st.markdown("---")
        st.markdown("#### Bottom Row (Player 1)")
        bottom_cols = st.columns(6)
        for i, pit in enumerate("ABCDEF"):
            stones = st.session_state.board[pit]
            disp = "•" * stones if stones else ""
            clickable = st.session_state.playerTurn == '1' and stones > 0
            hint_str = ""
            if hints and clickable:
                board_copy = st.session_state.board.copy()
                new_player = make_move(board_copy, '1', pit)
                eval_val, _ = minimax(board_copy, depth - 1 if depth is not None else None, -float('inf'), float('inf'), new_player)
                perspective = -eval_val  # invert for player1
                if abs(perspective) == 1000:
                    hint_str = "🟢 (W)" if perspective > 0 else "🔴 (L)"
                else:
                    hint_str = f"({perspective:+d})"
            with bottom_cols[i]:
                st.button(disp + (f"\n\n{hint_str}" if hint_str else ""),
                          key=f"pit_{pit}_bottom", disabled=not clickable,
                          on_click=human_move_callback, args=('1', pit))
                st.write(stone_text(st.session_state.board[pit], True))
    # right mancala (player1)
    with col_right:
        st.markdown('<div class="mancala-container">', unsafe_allow_html=True)
        store_val = st.session_state.board['1']
        disp = "•" * store_val if store_val else ""
        st.button(f"{disp}\n\n{stone_text(store_val)}", key="store_player1", disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    render_styles()
    st.title("Mancala")
    st.sidebar.button("New Game", on_click=new_game_callback)
    opponent = st.sidebar.radio("Opponent", ["Human", "AI"])
    search_depth = st.sidebar.number_input("AI Search Depth (0 for unlimited)", min_value=0, value=10, step=1)
    hints = st.sidebar.checkbox("Hints", value=False)
    depth = None if search_depth == 0 else int(search_depth)

    st.sidebar.number_input("Number of starting seeds", min_value=1, value=4, step=1, key="starting_seeds")
    st.sidebar.radio("Who goes first?", ["Player 1", "Player 2"], key="first_move")
    
    if 'board' not in st.session_state:
        st.session_state.board = get_new_board()
    if 'playerTurn' not in st.session_state:
        st.session_state.playerTurn = '1'
    if 'winner' not in st.session_state:
        st.session_state.winner = None

    if opponent == "AI" and st.session_state.playerTurn == '2':
        ai_move_callback(depth)

    render_board(depth, hints, opponent)
    
    if st.session_state.winner:
        st.success(st.session_state.winner)
    else:
        st.markdown(f"**Player {st.session_state.playerTurn}'s turn**")

if __name__ == '__main__':
    main()
