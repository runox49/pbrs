import streamlit as st
import random
import pandas as pd

def shuffle_list(l):
    temp = l.copy()
    random.shuffle(temp)
    return temp

st.set_page_config(page_title="Pickleball Scheduler", layout="wide")
st.title("🏓 Pickleball Session Scheduler")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Setup Session")
total_hours = st.sidebar.selectbox("Total Meetup Duration", [2, 3], index=1)
total_rounds = 14 if total_hours == 3 else 9
exit_round = 9

st.sidebar.subheader("Players")
col_a_input = st.sidebar.text_area("Column A: Full-time (3 hrs)", "Shin\nRita\nCT\nDan").split('\n')
col_b_input = st.sidebar.text_area("Column B: Early Exit (2 hrs)", "Lana\nZoe").split('\n')

stay_full = [name.strip() for name in col_a_input if name.strip()]
stay_early = [name.strip() for name in col_b_input if name.strip()]

if st.button("Generate Mixed Schedule"):
    if len(stay_full) < 4:
        st.error("Need at least 4 players in Column A to finish the session.")
    else:
        # --- INITIALIZE TRACKERS ---
        game_counts = {name: 0 for name in (stay_full + stay_early)}
        consecutive_games = {name: 0 for name in (stay_full + stay_early)}
        schedule = []

        # --- GENERATION LOOP ---
        for r in range(1, total_rounds + 1):
            if r <= exit_round:
                # Filter Col B: Max 6 total AND Max 3 in a row
                early_eligible = [p for p in stay_early if game_counts[p] < 6 and consecutive_games[p] < 3]
                early_eligible.sort(key=lambda x: game_counts[x])
                
                # Filter Col A: Max 2 in a row
                full_eligible = [p for p in stay_full if consecutive_games[p] < 2]
                full_eligible.sort(key=lambda x: game_counts[x])
                
                # Selection
                playing = early_eligible[:4]
                if len(playing) < 4:
                    needed = 4 - len(playing)
                    playing += full_eligible[:needed]
                
                # Emergency Backup: If streaks prevent a game, take longest rested
                if len(playing) < 4:
                    rested_backup = [p for p in (stay_early + stay_full) if p not in playing]
                    rested_backup.sort(key=lambda x: consecutive_games[x])
                    playing += rested_backup[:(4 - len(playing))]
            else:
                # Rounds 10-14: Column A only, Max 2 in a row
                stay_full.sort(key=lambda x: (consecutive_games[x] >= 2, game_counts[x]))
                playing = stay_full[:4]

            # Update stats
            current_available = (stay_early + stay_full) if r <= exit_round else stay_full
            resting = [p for p in current_available if p not in playing]
            
            for p in current_available:
                if p in playing:
                    game_counts[p] += 1
                    consecutive_games[p] += 1
                else:
                    consecutive_games[p] = 0

            # Shuffle playing for team variety
            shuffled_playing = shuffle_list(playing)
            while len(shuffled_playing) < 4: shuffled_playing.append("N/A")
            
            schedule.append({
                "Round": r,
                "Team 1": f"{shuffled_playing[0]} + {shuffled_playing[1]}",
                "Team 2": f"{shuffled_playing[2]} + {shuffled_playing[3]}",
                "Resting": ", ".join(resting)
            })

        # --- DISPLAY RESULTS ---
        df = pd.DataFrame(schedule)
        
        # Styling for 3rd hour
        def highlight_rows(row):
            return ['background-color: #f0f0f0' if row.Round > 9 else '' for _ in row]

        st.table(df.style.apply(highlight_rows, axis=1))

        # --- SUMMARY ---
        st.subheader("📊 Games Played Summary")
        summary_df = pd.DataFrame(list(game_counts.items()), columns=['Player', 'Games'])
        st.dataframe(summary_df.sort_values(by="Games", ascending=False))
