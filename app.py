import streamlit as st
import pandas as pd

# --- Core Scheduling Function (Hybrid Logic) ---

def generate_pickleball_schedule(playerNames):
    N = len(playerNames)
    TOTAL_ROUNDS = 14
    schedule_data = []
    game_counts = {name: 0 for name in playerNames}
    
    # 1. Input Validation
    if N < 6 or N > 8:
        return None, game_counts, "Error: Player count must be between 6 and 8."

    # 2. Hybrid Scheduling Logic
    if N == 8:
        # --- A. PERFECT N=8 SCHEDULE (Streak-Free Guarantee) ---
        
        # Map input names to fixed slots P0-P7 based on their input order
        P = {f"P{i}": playerNames[i] for i in range(8)}

        # The Verified Streak-Free Matrix (Format: [P1, P2, P3, P4] -> (P1+P2) vs (P3+P4))
        perfect_matrix = [
            [P["P0"], P["P1"], P["P2"], P["P3"]],   [P["P4"], P["P5"], P["P6"], P["P7"]],   [P["P0"], P["P2"], P["P4"], P["P6"]],   
            [P["P1"], P["P3"], P["P5"], P["P7"]],   [P["P0"], P["P4"], P["P1"], P["P5"]],   [P["P2"], P["P6"], P["P3"], P["P7"]],   
            [P["P0"], P["P3"], P["P1"], P["P7"]],   [P["P2"], P["P6"], P["P4"], P["P5"]],   [P["P0"], P["P7"], P["P2"], P["P1"]],   
            [P["P3"], P["P4"], P["P5"], P["P6"]],   [P["P0"], P["P5"], P["P3"], P["P6"]],   [P["P1"], P["P7"], P["P4"], P["P2"]],   
            [P["P0"], P["P6"], P["P1"], P["P4"]],   [P["P3"], P["P5"], P["P2"], P["P7"]]
        ]
        
        all_players_set = set(playerNames)
        
        for r in range(TOTAL_ROUNDS):
            p1, p2, p3, p4 = perfect_matrix[r]
            playing = [p1, p2, p3, p4]
            resting = sorted(list(all_players_set - set(playing)))
            
            schedule_data.append({
                'Round': r + 1, 
                'Team 1': f"{p1} + {p2}", 
                'Team 2': f"{p3} + {p4}", 
                'Resting': ', '.join(resting),
                'Playing_List': playing # Hidden for streak/count analysis
            })
            for p in playing:
                game_counts[p] += 1
            
        status_msg = "This rotation is mathematically **perfect** and guarantees **no player plays more than 2 games in a row**."

    else:
        # --- B. DYNAMIC N=6 or N=7 SCHEDULE (Simple Cycle + Streak Highlighting) ---
        
        rotation_queue = playerNames.copy()
        
        for round_num in range(1, TOTAL_ROUNDS + 1):
            playing = rotation_queue[:4]
            resting = rotation_queue[4:]
            
            team1 = playing[:2]
            team2 = playing[2:]
            
            schedule_data.append({
                'Round': round_num,
                'Team 1': f"{team1[0]} + {team1[1]}",
                'Team 2': f"{team2[0]} + {team2[1]}",
                'Resting': ', '.join(resting),
                'Playing_List': playing
            })
            
            for p in playing:
                game_counts[p] += 1
            
            # Rotation Mechanism: Cycle the 4 players who just played to the back to rest
            players_to_rest = rotation_queue[:4]
            rotation_queue = rotation_queue[4:] + players_to_rest
            
        status_msg = "**Unavoidable streaks** (3+ consecutive games) are highlighted in the schedule below. This is required to fill the court over 14 rounds with fewer than 8 players."


    schedule_df = pd.DataFrame(schedule_data)
    return schedule_df, game_counts, status_msg

# --- Streak Analysis and Highlighting Function ---

def highlight_streaks(schedule_df, playerNames):
    
    # 1. Prepare styling containers
    # We need styling applied to Team 1 and Team 2 columns only (index 1 and 2 in the df)
    style_df = pd.DataFrame('', index=schedule_df.index, columns=schedule_df.columns)
    
    # 2. Iterate through players and rounds to find streaks
    for player in playerNames:
        streak = 0
        for r in range(len(schedule_df)):
            playing_list = schedule_df.iloc[r]['Playing_List']
            
            if player in playing_list:
                streak += 1
                if streak >= 3:
                    # Streak detected: Highlight the current cell
                    # Find which column (Team 1 or Team 2) the player's name appears in
                    team_1_str = schedule_df.iloc[r]['Team 1']
                    team_2_str = schedule_df.iloc[r]['Team 2']
                    
                    if player in team_1_str:
                        style_df.iloc[r, 1] = 'background-color: #ffcccc' # Red tint for Team 1
                    elif player in team_2_str:
                        style_df.iloc[r, 2] = 'background-color: #ffcccc' # Red tint for Team 2
            else:
                streak = 0
                
    return style_df

# --- Streamlit UI Code ---

st.set_page_config(
    page_title="Hybrid Pickleball Scheduler (6-8 Players)",
    layout="wide"
)

st.title("🏓 Hybrid Pickleball Scheduler (6-8 Players)")
st.markdown("Enter 6 to 8 player names to generate a fair, 14-round (approx. 3-hour) rotation.")
st.markdown("---")

# 1. Player Input Section
st.subheader("1. Enter Player Names (6 to 8)")

input_names = []
cols = st.columns(8)
default_names = ["Shin", "Rita", "Lana", "Zoe", "CT", "KG", "Janet", "Russ"]

for i in range(8):
    # Only show 6 inputs for a cleaner starting UI, but allow more
    if i < 6:
        name = cols[i].text_input(f"Player {i+1}", value=default_names[i])
    elif i == 6:
        name = cols[i].text_input(f"Player {i+1}", value=default_names[i])
    elif i == 7:
        name = cols[i].text_input(f"Player {i+1}", value=default_names[i])
    
    if name and name.strip():
        input_names.append(name.strip())

st.markdown(f"**Current Players Entered:** {len(input_names)}")
st.markdown("---")


# 2. Schedule Generation and Display
if st.button("Generate Schedule", type="primary"):
    
    unique_names = list(set(input_names))
    
    if 6 <= len(unique_names) <= 8:
        
        schedule_df, game_counts, status_msg = generate_pickleball_schedule(unique_names)
        
        # Remove the hidden analysis column before display
        schedule_display_df = schedule_df.drop(columns=['Playing_List'])
        
        st.subheader("2. Court Rotation Schedule (14 Rounds)")
        st.info(status_msg)
        
        # Apply highlighting if N < 8
        if len(unique_names) < 8:
            styles = highlight_streaks(schedule_df, unique_names)
            st.dataframe(schedule_display_df.style.apply(lambda x: styles, axis=None), use_container_width=True)
        else:
            st.dataframe(schedule_display_df, use_container_width=True)

        st.markdown("---")
        
        # 3. Game Count Summary Display
        st.subheader("3. Total Games Played")
        
        analysis_data = pd.DataFrame({
            'Player': list(game_counts.keys()),
            'Total Games': list(game_counts.values())
        })
        
        # Sorting by Total Games to easily see the fairest distribution
        analysis_data = analysis_data.sort_values(by='Total Games', ascending=False).reset_index(drop=True)
        
        st.dataframe(analysis_data, use_container_width=True)
        
        st.success("✅ Schedule generated successfully!")
        
    else:
        st.error("Please enter a number of players between 6 and 8, ensuring all names are unique.")

# Display installation instructions for clarity
st.sidebar.markdown("### ⚙️ How to Run This App")
st.sidebar.markdown("""
1.  **Install Streamlit and Pandas:**
    ```bash
    pip install streamlit pandas
    ```
2.  **Save the code:** Save the code above into a file named `app.py`.
3.  **Run the app:**
    ```bash
    streamlit run app.py
    ```
""")