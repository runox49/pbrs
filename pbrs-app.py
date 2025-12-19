import streamlit as st
import random
import pandas as pd
from itertools import combinations

def generate_mixed_schedule(stay_full, stay_early, total_rounds, exit_round):
    # --- TRACKERS ---
    game_counts = {p: 0 for p in (stay_full + stay_early)}
    consecutive_games = {p: 0 for p in (stay_full + stay_early)}
    
    # Track Partnership History: {PlayerA, PlayerB}
    pair_history = {frozenset(pair): 0 for pair in combinations(stay_full + stay_early, 2)}
    
    # Track Matchup History: {frozenset({P1, P2}), frozenset({P3, P4})}
    match_history = {}

    schedule = []

    for r in range(1, total_rounds + 1):
        # 1. Pick 4 players based on your existing rules (Capped B, Balanced A)
        if r <= exit_round:
            candidates = [p for p in stay_early if game_counts[p] < 6 and consecutive_games[p] < 3]
            # Fill remaining with A players (max 2 in a row)
            if len(candidates) < 4:
                full_eligible = [p for p in stay_full if consecutive_games[p] < 2]
                candidates += full_eligible
        else:
            candidates = [p for p in stay_full if consecutive_games[p] < 2]

        # Safety: If rules are too strict to find 4, take longest rested
        if len(candidates) < 4:
            all_avail = (stay_early + stay_full) if r <= exit_round else stay_full
            candidates = sorted(all_avail, key=lambda x: (consecutive_games[x], game_counts[x]))
            
        # Prioritize those with fewest total games
        candidates.sort(key=lambda x: game_counts[x])
        playing = candidates[:4]

        # 2. Find the best Team Split among these 4 players
        # There are only 3 ways to split 4 people into 2 teams
        possible_splits = [
            (frozenset([playing[0], playing[1]]), frozenset([playing[2], playing[3]])),
            (frozenset([playing[0], playing[2]]), frozenset([playing[1], playing[3]])),
            (frozenset([playing[0], playing[3]]), frozenset([playing[1], playing[2]]))
        ]

        # Score each split based on history
        def score_split(split):
            t1, t2 = split
            # Penalty for repeat partners
            p_score = pair_history[t1] + pair_history[t2]
            # Penalty for repeat matchup (A+B vs C+D)
            matchup_key = frozenset([t1, t2])
            m_score = match_history.get(matchup_key, 0)
            return p_score + (m_score * 2) # Heavily penalize repeat matches

        best_split = min(possible_splits, key=score_split)
        team1, team2 = list(best_split[0]), list(best_split[1])
        
        # 3. Update Histories
        pair_history[best_split[0]] += 1
        pair_history[best_split[1]] += 1
        match_key = frozenset([best_split[0], best_split[1]])
        match_history[match_key] = match_history.get(match_key, 0) + 1

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

    return schedule
