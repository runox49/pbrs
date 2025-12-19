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
    match_history = {} 
    
    schedule = []

    for r in range(1, total_rounds + 1):
        # 1. Selection Logic
        if r <= exit_round:
            early_eligible = [p for p in stay_early if game_counts[p] < 6 and consecutive_games[p] < 3]
            full_eligible = [p for p in stay_full if consecutive_games[p] < 2]
            candidates = early_eligible + full_eligible
        else:
            candidates = [p for p in stay_full if consecutive_games[p] < 2]

        if len(candidates) < 4:
            all_pool = (stay_early + stay_full) if r <= exit_round else stay_full
            candidates = sorted(all_pool, key=lambda x: (consecutive_games[x], game_counts[x]))
        
        candidates.sort(key=lambda x: game_counts[x])
        playing = candidates[:4]

        # 2. Matchup Optimization
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
            return p_score + (m_score * 5)

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
st.set_page_config(page_title="Pickleball Pro Scheduler", page_icon="🏓", layout="wide")

st.title("🏓 Pickleball Session Scheduler")

with st.sidebar:
    st.header("⚙️ Session Config")
    hours = st.selectbox("Duration", [2, 3], index=1)
    
    st.subheader("👥 Players")
    # UPDATED: Only Shin as default, Column B is empty
    col_a_default = "Shin"
    col_b_default = ""
    
    col_a_text = st.text_area("Column A (Full-time)", col_a_default, help="Enter one name per line.")
    col_b_text = st.text_area("Column B (Early Exit - 2hrs)", col_b_default, help="Enter one name per line.")
    
    stay_full = [n.strip() for n in col_a_text.split('\n') if n.strip()]
    stay_early = [n.strip() for n in col_b_text.split('\n') if n.strip()]
    
    if st.button("Clear / Reset Names"):
        st.rerun()

if st.button("Generate Smart Schedule", type="primary"):
    if len(stay_full) < 4:
        st.error("Error: You need at least 4 players in Column A to finish the session.")
    else:
        total_rounds = 14 if hours == 3 else 9
        exit_round = 9
        
        sched_data, counts = generate_schedule(stay_full, stay_early, total_rounds, exit_round)
        
        df = pd.DataFrame(sched_data)
        
        # 3rd Hour Visual Shading
        def highlight_transition(row):
            return ['background-color: #f1f3f5' if row.Round > 9 else '' for _ in row]
        
        st.subheader("📅 Rotation Schedule")
        st.table(df.style.apply(highlight_transition, axis=1))

        # Summary
        st.divider()
        st.subheader("📊 Session Stats")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Final Game Counts**")
            summary_df = pd.DataFrame(list(counts.items()), columns=['Player', 'Games'])
            st.dataframe(summary_df.sort_values(by="Games", ascending=False), hide_index=True)
            
        with col2:
            st.info("""
            **Rules Applied:**
            - **Column B Cap:** 6 games max.
            - **Column B Streak:** No more than 3 in a row.
            - **Column A Streak:** No more than 2 in a row.
            - **Variety:** Prevents duplicate partners and matchups.
            """)
