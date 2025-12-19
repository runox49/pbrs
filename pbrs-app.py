import streamlit as st
import pandas as pd
import random
from itertools import combinations

# --- CORE LOGIC ---
def generate_schedule(stay_full, stay_early, total_rounds, exit_round):
    # Initialize trackers
    game_counts = {p: 0 for p in (stay_full + stay_early)}
    consecutive_games = {p: 0 for p in (stay_full + stay_early)}
    pair_history = {frozenset(pair): 0 for pair in combinations(stay_full + stay_early, 2)}
    match_history = {} 
    
    schedule = []

    for r in range(1, total_rounds + 1):
        # SHUFFLE available players to ensure different results every run
        shuff_full = random.sample(stay_full, len(stay_full))
        shuff_early = random.sample(stay_early, len(stay_early))

        if r <= exit_round:
            # Rules: Col B < 6 total & < 3 streak | Col A < 2 streak
            early_eligible = [p for p in shuff_early if game_counts[p] < 6 and consecutive_games[p] < 3]
            full_eligible = [p for p in shuff_full if consecutive_games[p] < 2]
            candidates = early_eligible + full_eligible
        else:
            candidates = [p for p in shuff_full if consecutive_games[p] < 2]

        # Safety: If constraints are too tight, relax and pick by least consecutive
        if len(candidates) < 4:
            pool = (shuff_early + shuff_full) if r <= exit_round else shuff_full
            candidates = sorted(pool, key=lambda x: (consecutive_games[x], game_counts[x]))
        
        # Sort by total games (shuffle handles the ties)
        candidates.sort(key=lambda x: game_counts[x])
        playing = candidates[:4]

        # Optimize Matchup (Unique pairs and teams)
        possible_splits = [
            (frozenset([playing[0], playing[1]]), frozenset([playing[2], playing[3]])),
            (frozenset([playing[0], playing[2]]), frozenset([playing[1], playing[3]])),
            (frozenset([playing[0], playing[3]]), frozenset([playing[1], playing[2]]))
        ]

        def evaluate_split(split):
            t1, t2 = split
            p_score = pair_history[t1] + pair_history[t2]
            m_score = match_history.get(frozenset([t1, t2]), 0)
            return p_score + (m_score * 5)

        best_split = min(possible_splits, key=evaluate_split)
        team1, team2 = sorted(list(best_split[0])), sorted(list(best_split[1]))

        # Update History
        pair_history[best_split[0]] += 1
        pair_history[best_split[1]] += 1
        match_history[frozenset([best_split[0], best_split[1]])] = match_history.get(frozenset([best_split[0], best_split[1]]), 0) + 1

        # Update Player Stats
        current_pool = (stay_early + stay_full) if r <= exit_round else stay_full
        for p in current_pool:
            if p in playing:
                game_counts[p] += 1
                consecutive_games[p] += 1
            else:
                consecutive_games[p] = 0

        schedule.append({
            "Round": r, "Team 1": f"{team1[0]} + {team1[1]}", 
            "Team 2": f"{team2[0]} + {team2[1]}", 
            "Resting": ", ".join([p for p in current_pool if p not in playing])
        })

    return schedule, game_counts

# --- UI ---
st.set_page_config(page_title="Pickleball Pro", page_icon="🏓", layout="wide")
st.title("🏓 Smart Pickleball Scheduler")

with st.sidebar:
    st.header("Settings")
    hours = st.selectbox("Duration", [2, 3], index=1)
    col_a_text = st.text_area("Column A (Full-time)", "Shin")
    col_b_text = st.text_area("Column B (Early Exit)", "")
    
    stay_full = [n.strip() for n in col_a_text.split('\n') if n.strip()]
    stay_early = [n.strip() for n in col_b_text.split('\n') if n.strip()]

if st.button("Generate Randomized Schedule", type="primary"):
    if len(stay_full) < 4:
        st.error("Need 4+ players in Column A.")
    else:
        res, counts = generate_schedule(stay_full, stay_early, 14 if hours == 3 else 9, 9)
        st.table(pd.DataFrame(res))
        st.subheader("📊 Stats")
        st.dataframe(pd.DataFrame(list(counts.items()), columns=['Player', 'Games']).sort_values(by="Games", ascending=False), hide_index=True)
