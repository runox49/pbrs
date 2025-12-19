import streamlit as st
import pandas as pd
import random
from itertools import combinations

# --- UTILITY FUNCTIONS ---
def shuffle_list(l):
    temp = l.copy()
    random.shuffle(temp)
    return temp

def generate_schedule(stay_full, stay_early, total_rounds, exit_round):
    # Trackers
    game_counts = {p: 0 for p in (stay_full + stay_early)}
    consecutive_games = {p: 0 for p in (stay_full + stay_early)}
    pair_history = {frozenset(pair): 0 for pair in combinations(stay_full + stay_early, 2)}
    match_history = {} # Stores frozenset({frozenset(Team1), frozenset(Team2)})
    
    schedule = []

    for r in range(1, total_rounds + 1):
        # 1. Selection Logic
        if r <= exit_round:
            # Column B: < 6 games total AND < 3 in a row
            early_eligible = [p for p in stay_early if game_counts[p] < 6 and consecutive_games[p] < 3]
            # Column A: < 2 in a row
            full_eligible = [p for p in stay_full if consecutive_games[p] < 2]
            candidates = early_eligible + full_eligible
        else:
            # Final Hour: Only Column A, < 2 in a row
            candidates = [p for p in stay_full if consecutive_games[p] < 2]

        # Safety: If rules are too strict, take anyone not currently at limit
        if len(candidates) < 4:
            all_pool = (stay_early + stay_full) if r <= exit_round else stay_full
            candidates = sorted(all_pool, key=lambda x: (consecutive_games[x], game_counts[x]))
        
        # Pick top 4 based on fewest total games played
        candidates.sort(key=lambda x: game_counts[x])
        playing = candidates[:4]

        # 2. Matchup Optimization (Preventing Duplicate Pairs/Matches)
        # 3 possible ways to split 4 players into 2 teams
        possible_splits = [
            (frozenset([playing[0], playing[1]]), frozenset([playing[2], playing[3]])),
            (frozenset([playing[0], playing[2]]), frozenset([playing[1], playing[3]])),
            (frozenset([playing[0], playing[3]]), frozenset([playing[1], playing[2]]))
        ]

        def evaluate_split(split):
            t1, t2 = split
            p_score = pair_history[t1] + pair_history[t2]
            match_key = frozenset([t1, t2])
            m_score = match_history.get(match_key, 0)
            return p_score + (m_score * 5) # High penalty for same team vs same team

        best_split = min(possible_splits, key=evaluate_split)
        team1 = sorted(list(best_split[0]))
        team2 = sorted(list(best_split[1]))

        # 3. Record History
        pair_history[best_split[0]] += 1
        pair_history[best_split[1]] += 1
        m_key = frozenset([best_split[0], best_split[1]])
        match_history[m_key] = match_history.get(m_key, 0) + 1

        # 4. Update Player Stats
        current_pool = (stay_early + stay_full) if r <= exit_round else stay_full
        for p in current_pool:
            if p in playing:
                game_counts[p] += 1
                consecutive_games[p] += 1
            else:
                consecutive_games[p] = 0

        schedule.append({
            "Round": r,
            "Team 1": f"{team1[0]} + {team1[1]}",
            "Team 2": f"{team2[0]} + {team2[1]}",
            "Resting": ", ".join([p for p in current_pool if p not in playing])
        })

    return schedule, game_counts

# --- STREAMLIT UI ---
st.set_page_config(page_title="Pickleball Pro Scheduler", page_icon="🏓")

st.title("🏓 Pickleball Session Scheduler")
st.markdown("Balanced pairings, unique matchups, and smart rest tracking.")

with st.sidebar:
    st.header("⚙️ Session Config")
    hours = st.selectbox("Duration", [2, 3], index=1)
    
    st.subheader("👥 Players")
    col_a_text = st.text_area("Column A (Full-time)", "Shin\nRita\nCT\nDan\nKen\nMay")
    col_b_text = st.text_area("Column B (Early Exit - 2hrs)", "Lana\nZoe")
    
    stay_full = [n.strip() for n in col_a_text.split('\n') if n.strip()]
    stay_early = [n.strip() for n in col_b_text.split('\n') if n.strip()]

if st.button("Generate Smart Schedule", type="primary"):
    if len(stay_full) < 4:
        st.error("Error: Need at least 4 players in Column A to finish the 3rd hour.")
    else:
        total_rounds = 14 if hours == 3 else 9
        exit_round = 9
        
        sched_data, counts = generate_schedule(stay_full, stay_early, total_rounds, exit_round)
        
        # Display Table
        df = pd.DataFrame(sched_data)
        
        # Shading for the 3rd hour
        def highlight_transition(row):
            return ['background-color: #f8f9fa' if row.Round > 9 else '' for _ in row]
        
        st.subheader("📅 Rotation Schedule")
        st.table(df.style.apply(highlight_transition, axis=1))

        # Summary Metrics
        st.divider()
        st.subheader("📊 Session Stats")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Games per Player**")
            summary_df = pd.DataFrame(list(counts.items()), columns=['Player', 'Games'])
            st.dataframe(summary_df.sort_values(by="Games", ascending=False), hide_index=True)
            
        with col2:
            st.info("""
            **Rules Applied:**
            - Column B: Max 6 games.
            - Column B: Max 3-game streak.
            - Column A: Max 2-game streak.
            - Unique partners prioritized.
            - Unique matchups prioritized.
            """)
