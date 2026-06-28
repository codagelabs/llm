"""
Chunk generation logic for IPL match JSON files.

Generates 7 specialized chunk types per match:
  1. match_summary
  2. innings_summary (x2)
  3. player_batting (per batsman per innings)
  4. player_bowling (per bowler per innings)
  5. partnership (per wicket fall)
  6. wicket_event (per wicket)
  7. milestone (centuries / half-centuries / 5-wicket hauls)
  8. match_narrative
"""

import json
from src.utils import (
    get_season_year,
    get_team_abbr,
    get_ordinal,
    calculate_overs,
)


# ---------------------------------------------------------------------------
# Text builders
# ---------------------------------------------------------------------------

def _make_match_summary_text(info: dict, winner: str, win_by_runs, win_by_wickets, match_id: str) -> str:
    season = info.get("season")
    season_year = get_season_year(season)
    date = info.get("dates", [None])[0]
    venue = info.get("venue")
    city = info.get("city", info.get("venue", "Unknown").split(",")[0])
    teams = info.get("teams", [])
    toss_winner = info.get("toss", {}).get("winner")
    toss_decision = info.get("toss", {}).get("decision")
    pom = info.get("player_of_match", [""])[0]

    match_num = info.get("event", {}).get("match_number")
    match_num_str = f"Match {match_num}" if match_num else "Match"  # noqa: F841

    parts = [
        f"IPL {season_year} match (ID: {match_id}) was played on {date} at {venue}, {city}"
        f" between {teams[0]} and {teams[1]}."
    ]
    if toss_winner and toss_decision:
        parts.append(f"{toss_winner} won the toss and elected to {toss_decision}.")
    if winner == "No Result":
        parts.append("The match ended in a No Result.")
    elif winner:
        if win_by_runs:
            margin = f"by {win_by_runs} runs"
        elif win_by_wickets:
            margin = f"by {win_by_wickets} wickets"
        else:
            margin = "via Super Over"
        opponent = teams[0] if winner == teams[1] else teams[1]
        parts.append(f"{winner} defeated {opponent} {margin}.")
    if pom:
        parts.append(f"{pom} was named Player of the Match.")
    return " ".join(parts)


def _make_match_narrative(
    info: dict,
    winner: str,
    win_by_runs,
    win_by_wickets,
    match_id: str,
    innings_summaries: list,
) -> str:
    season = info.get("season")
    season_year = get_season_year(season)
    venue = info.get("venue")
    city = info.get("city", info.get("venue", "Unknown").split(",")[0])
    teams = info.get("teams", [])
    toss_winner = info.get("toss", {}).get("winner")
    toss_decision = info.get("toss", {}).get("decision")
    pom = info.get("player_of_match", [""])[0]
    match_num = info.get("event", {}).get("match_number")
    match_num_str = f"Match {match_num}" if match_num else "Match"

    parts = [
        f"IPL {season_year} {match_num_str} was played at {venue}, {city}"
        f" between {teams[0]} and {teams[1]}."
    ]
    if toss_winner and toss_decision:
        parts.append(f"{toss_winner} won the toss and elected to {toss_decision}.")

    for i_summary in innings_summaries:
        team_name = i_summary["team"]
        runs = i_summary["runs"]
        wickets = i_summary["wickets"]
        overs = i_summary["overs"]
        top_scorers = i_summary["top_scorers"]
        team_action = "posted" if i_summary["innings"] == 1 else "scored"
        top_scorer_part = ""
        if top_scorers:
            top_scorer_part = f" thanks to {top_scorers[0]['player']}'s score of {top_scorers[0]['runs']}"
        parts.append(f"{team_name} {team_action} {runs}/{wickets} in {overs} overs{top_scorer_part}.")

    if winner == "No Result":
        parts.append("The match ended in a No Result.")
    elif winner:
        if win_by_runs:
            margin = f"by {win_by_runs} runs"
        elif win_by_wickets:
            margin = f"by {win_by_wickets} wickets"
        else:
            margin = "via Super Over"
        parts.append(f"{winner} won the match {margin}.")
    if pom:
        parts.append(f"{pom} was named Player of the Match.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main chunk generator
# ---------------------------------------------------------------------------

def generate_match_chunks(file_path: str, match_id: str) -> list[dict]:
    """
    Parse a single IPL match JSON file and return a list of chunk dicts.
    Each chunk has keys: 'id', 'document', 'metadata'.
    """
    with open(file_path, "r") as f:
        data = json.load(f)

    info = data.get("info", {})
    season = info.get("season", "Unknown")
    season_year = get_season_year(season)

    dates = info.get("dates", [])
    date_str = dates[0] if dates else "Unknown"
    year_val = int(date_str.split("-")[0]) if dates else 0

    venue = info.get("venue", "Unknown")
    city = info.get("city", info.get("venue", "Unknown").split(",")[0])

    teams = info.get("teams", [])
    if len(teams) < 2:
        return []

    team1, team2 = teams[0], teams[1]
    team1_abbr = get_team_abbr(team1)
    team2_abbr = get_team_abbr(team2)

    toss = info.get("toss", {})
    toss_winner = toss.get("winner", "")
    toss_decision = toss.get("decision", "").capitalize()

    outcome = info.get("outcome", {})
    winner = outcome.get("winner", "No Result")
    win_by = outcome.get("by", {})
    win_by_runs = win_by.get("runs")
    win_by_wickets = win_by.get("wickets")

    pom_list = info.get("player_of_match", [])
    pom = pom_list[0] if pom_list else ""

    winner_abbr = get_team_abbr(winner) if winner and winner != "No Result" else "NR"

    # Shared metadata for all chunks in this match
    metadata = {
        "match_id": match_id,
        "season": season,
        "year": year_val,
        "venue": venue,
        "city": city,
        "team1": team1_abbr,
        "team2": team2_abbr,
        "winner": winner_abbr,
        "player_of_match": pom,
    }

    chunks: list[dict] = []
    innings_summaries: list[dict] = []

    # ---- Per-innings processing -----------------------------------------
    for inning_idx, inning in enumerate(data.get("innings", [])):
        inning_num = inning_idx + 1
        bat_team = inning.get("team", "")
        bowl_team = team2 if bat_team == team1 else team1
        bat_team_abbr = get_team_abbr(bat_team)

        overs_list = inning.get("overs", [])
        total_overs = calculate_overs(overs_list)

        # Accumulate batting/bowling stats
        batter_stats: dict[str, dict] = {}  # player -> {runs, balls, fours, sixes, dismissed, how}
        bowler_stats: dict[str, dict] = {}  # player -> {overs_count, wickets, runs_conceded}
        match_wickets: list[dict] = []
        match_milestones: list[dict] = []
        partnerships: list[dict] = []

        # Partnership tracking
        current_batters: list[str] = []
        partnership_runs: dict[str, int] = {}  # frozen-pair-key -> runs
        wicket_count = 0

        total_runs = 0
        total_wickets = 0

        for over_obj in overs_list:
            over_num_base = over_obj.get("over", 0)
            deliveries = over_obj.get("deliveries", [])
            legal_ball_in_over = 0

            for delivery in deliveries:
                batter = delivery.get("batter", "")
                bowler = delivery.get("bowler", "")
                non_striker = delivery.get("non_striker", "")
                runs_obj = delivery.get("runs", {})
                batter_runs = runs_obj.get("batter", 0)
                extras = delivery.get("extras", {})
                total_delivery_runs = runs_obj.get("total", 0)

                is_wide = "wides" in extras
                is_noball = "noballs" in extras
                is_legal = not is_wide

                # --- Batter stats ---
                if batter not in batter_stats:
                    batter_stats[batter] = {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "dismissed": False, "how": "not out"}
                batter_stats[batter]["runs"] += batter_runs
                if is_legal:
                    batter_stats[batter]["balls"] += 1
                if batter_runs == 4:
                    batter_stats[batter]["fours"] += 1
                if batter_runs == 6:
                    batter_stats[batter]["sixes"] += 1

                # Milestone tracking (50 / 100)
                old_runs = batter_stats[batter]["runs"] - batter_runs
                for milestone_val, milestone_name in [(100, "Century"), (50, "Half-Century")]:
                    if old_runs < milestone_val <= batter_stats[batter]["runs"]:
                        over_val = round(over_num_base + (legal_ball_in_over + 1) / 10, 1)
                        match_milestones.append({
                            "player": batter,
                            "milestone": milestone_name,
                            "runs": batter_stats[batter]["runs"],
                            "over": over_val,
                            "summary": (
                                f"{batter} scored a {milestone_name} ({batter_stats[batter]['runs']} runs)"
                                f" in innings {inning_num} against {bowl_team} in IPL {season_year}."
                            ),
                        })

                # --- Bowler stats ---
                if bowler not in bowler_stats:
                    bowler_stats[bowler] = {"legal_balls": 0, "wickets": 0, "runs_conceded": 0}
                if is_legal:
                    bowler_stats[bowler]["legal_balls"] += 1
                bowler_stats[bowler]["runs_conceded"] += total_delivery_runs

                # --- Partnership tracking ---
                pair = tuple(sorted([batter, non_striker]))
                pair_key = f"{pair[0]}&{pair[1]}"
                if pair_key not in partnership_runs:
                    partnership_runs[pair_key] = 0
                partnership_runs[pair_key] += total_delivery_runs

                if is_legal:
                    legal_ball_in_over += 1

                total_runs += total_delivery_runs

                # --- Wicket processing ---
                wickets = delivery.get("wickets", [])
                for w in wickets:
                    player_out = w.get("player_out", "")
                    kind = w.get("kind", "")
                    fielders = w.get("fielders", [])
                    fielder_name = fielders[0].get("name", "") if fielders else ""

                    if kind not in ["run out"]:
                        bowler_stats[bowler]["wickets"] += 1

                    if player_out in batter_stats:
                        batter_stats[player_out]["dismissed"] = True
                        batter_stats[player_out]["how"] = kind

                    over_val = round(over_num_base + legal_ball_in_over / 10, 1)

                    match_wickets.append({
                        "over": over_val,
                        "batsman": player_out,
                        "bowler": bowler,
                        "dismissal": kind,
                        "fielder": fielder_name,
                        "inning_num": inning_num,
                        "batting_team": bat_team,
                    })
                    total_wickets += 1
                    wicket_count += 1

                    # Record partnership that just ended
                    pair_runs = partnership_runs.get(pair_key, 0)
                    is_unbroken = False
                    partnerships.append({
                        "wicket": wicket_count,
                        "players": (batter, non_striker),
                        "runs": pair_runs,
                        "inning": inning_num,
                        "is_unbroken": is_unbroken,
                    })
                    # Reset partnership runs for next pair
                    partnership_runs = {}

        # Unbroken final partnership
        if total_wickets < 10 and batter_stats:
            active_batters = [b for b, s in batter_stats.items() if not s["dismissed"]]
            if len(active_batters) >= 2:
                pair = tuple(sorted(active_batters[:2]))
                pair_key = f"{pair[0]}&{pair[1]}"
                pair_runs = partnership_runs.get(pair_key, 0)
                partnerships.append({
                    "wicket": wicket_count + 1,
                    "players": (active_batters[0], active_batters[1]),
                    "runs": pair_runs,
                    "inning": inning_num,
                    "is_unbroken": True,
                })

        # --- 5-wicket haul milestones ---
        for bowler_name, bs in bowler_stats.items():
            if bs["wickets"] >= 5:
                match_milestones.append({
                    "player": bowler_name,
                    "milestone": "5-Wicket Haul",
                    "runs": bs["wickets"],
                    "over": total_overs,
                    "summary": (
                        f"{bowler_name} took {bs['wickets']} wickets"
                        f" in innings {inning_num} against {bat_team} in IPL {season_year}."
                    ),
                })

        # Top scorers for this innings
        sorted_batters = sorted(batter_stats.items(), key=lambda x: x[1]["runs"], reverse=True)
        top_scorers = [{"player": p, "runs": s["runs"]} for p, s in sorted_batters[:3] if s["runs"] > 0]

        # Innings summary for narrative
        innings_summaries.append({
            "innings": inning_num,
            "team": bat_team,
            "runs": total_runs,
            "wickets": total_wickets,
            "overs": total_overs,
            "top_scorers": top_scorers,
        })

        # --- Innings Summary Chunk ---
        top_scorer_lines = "\n".join(f"- {s['player']}: {s['runs']} runs" for s in top_scorers) or "- None"
        last_not_out = next(
            (p for p, s in sorted_batters if not s["dismissed"]),
            sorted_batters[0][0] if sorted_batters else "N/A",
        )
        last_not_out_runs = batter_stats.get(last_not_out, {}).get("runs", 0) if last_not_out != "N/A" else 0
        innings_doc = (
            f"[Team Innings Summary]\n"
            f"Match ID: {match_id}\n"
            f"Season/Year: {season_year}\n"
            f"Date: {date_str}\n"
            f"Venue: {venue}, {city}\n"
            f"Teams: {team1} vs {team2}\n"
            f"Team: {bat_team}\n"
            f"Innings: {inning_num}\n"
            f"Score: {total_runs}/{total_wickets} in {total_overs} overs\n"
            f"Top Scorers:\n{top_scorer_lines}\n"
            f"Summary: {bat_team_abbr} scored {total_runs}/{total_wickets} in {total_overs} overs."
            f" {last_not_out} remained unbeaten on {last_not_out_runs} runs."
            f" (Match played between {team1} and {team2} on {date_str})"
        )
        innings_meta = metadata.copy()
        innings_meta["chunk_type"] = "innings_summary"
        innings_meta["innings"] = inning_num
        innings_meta["batting_team"] = bat_team_abbr
        chunks.append({
            "id": f"{match_id}_innings_{inning_num}",
            "document": innings_doc,
            "metadata": innings_meta,
        })

        # --- Player Batting Chunks ---
        for batter_name, bs in batter_stats.items():
            sr = round(bs["runs"] / bs["balls"] * 100, 1) if bs["balls"] > 0 else 0.0
            status_str = f"dismissed ({bs['how']})" if bs["dismissed"] else "not out"
            not_out_str = "" if bs["dismissed"] else " not"
            bat_doc = (
                f"[Player Batting Performance]\n"
                f"Match ID: {match_id}\n"
                f"Season/Year: {season_year}\n"
                f"Date: {date_str}\n"
                f"Venue: {venue}, {city}\n"
                f"Teams: {team1} vs {team2}\n"
                f"Player: {batter_name}\n"
                f"Team: {bat_team}\n"
                f"Opponent: {bowl_team}\n"
                f"Runs: {bs['runs']} | Balls: {bs['balls']} | Fours: {bs['fours']} | Sixes: {bs['sixes']} | SR: {sr}\n"
                f"Status: {status_str}\n"
                f"Summary: {batter_name} scored {bs['runs']}{not_out_str} out off {bs['balls']} balls"
                f" against {bowl_team} in IPL {season_year}."
            )
            bat_meta = metadata.copy()
            bat_meta["chunk_type"] = "player_batting"
            bat_meta["player"] = batter_name
            bat_meta["innings"] = inning_num
            chunks.append({
                "id": f"{match_id}_bat_{inning_num}_{batter_name.replace(' ', '_')}",
                "document": bat_doc,
                "metadata": bat_meta,
            })

        # --- Player Bowling Chunks ---
        for bowler_name, bs in bowler_stats.items():
            overs_bowled = bs["legal_balls"] // 6 + (bs["legal_balls"] % 6) / 10
            economy = round(bs["runs_conceded"] / (bs["legal_balls"] / 6), 2) if bs["legal_balls"] > 0 else 0.0
            bowl_doc = (
                f"[Player Bowling Performance]\n"
                f"Match ID: {match_id}\n"
                f"Season/Year: {season_year}\n"
                f"Date: {date_str}\n"
                f"Venue: {venue}, {city}\n"
                f"Teams: {team1} vs {team2}\n"
                f"Player: {bowler_name}\n"
                f"Team: {bowl_team}\n"
                f"Opponent: {bat_team}\n"
                f"Overs: {overs_bowled} | Wickets: {bs['wickets']} | Runs Conceded: {bs['runs_conceded']} | Economy: {economy}\n"
                f"Summary: {bowler_name} took {bs['wickets']} wickets conceding {bs['runs_conceded']} runs"
                f" in {overs_bowled} overs (economy {economy}) against {bat_team} in IPL {season_year}."
            )
            bowl_meta = metadata.copy()
            bowl_meta["chunk_type"] = "player_bowling"
            bowl_meta["player"] = bowler_name
            bowl_meta["innings"] = inning_num
            chunks.append({
                "id": f"{match_id}_bowl_{inning_num}_{bowler_name.replace(' ', '_')}",
                "document": bowl_doc,
                "metadata": bowl_meta,
            })

        # --- Partnership Chunks ---
        for part in partnerships:
            w_num = part["wicket"]
            players = part["players"]
            runs_added = part["runs"]
            is_unbroken = part["is_unbroken"]

            if w_num == 1:
                part_desc = f"Opening partnership between {players[0]} and {players[1]} added {runs_added} runs."
            elif is_unbroken:
                part_desc = f"Unbroken partnership of {runs_added} runs between {players[0]} and {players[1]}."
            else:
                part_desc = f"{get_ordinal(w_num)} wicket partnership between {players[0]} and {players[1]} added {runs_added} runs."

            part_doc = (
                f"[Partnership]\n"
                f"Match ID: {match_id}\n"
                f"Season/Year: {season_year}\n"
                f"Date: {date_str}\n"
                f"Venue: {venue}, {city}\n"
                f"Teams: {team1} vs {team2}\n"
                f"Team: {bat_team}\n"
                f"Innings: {inning_num}\n"
                f"Players: {players[0]} & {players[1]}\n"
                f"Wicket: {w_num}\n"
                f"Runs: {runs_added}\n"
                f"Summary: {part_desc} (Match played between {team1} and {team2} on {date_str})"
            )
            part_meta = metadata.copy()
            part_meta["chunk_type"] = "partnership"
            chunks.append({
                "id": f"{match_id}_partnership_{inning_num}_{w_num}",
                "document": part_doc,
                "metadata": part_meta,
            })

        # --- Wicket Event Chunks ---
        for wicket_idx, w_evt in enumerate(match_wickets):
            over_val = w_evt["over"]
            batsman = w_evt["batsman"]
            bowler_name = w_evt["bowler"]
            dismissal = w_evt["dismissal"]
            fielder = w_evt["fielder"]
            w_inning_num = w_evt["inning_num"]
            bat_team_wk = w_evt["batting_team"]

            if dismissal == "caught" and fielder:
                fielder_part = f" caught by {fielder}"
            elif dismissal == "caught":
                fielder_part = " caught"
            elif dismissal == "stumped" and fielder:
                fielder_part = f" stumped by {fielder}"
            else:
                fielder_part = ""

            if dismissal == "bowled":
                summary_text = f"{batsman} was bowled by {bowler_name} at {over_val} overs."
            elif dismissal in ("caught", "stumped"):
                summary_text = f"{batsman} was{fielder_part} off {bowler_name} at {over_val} overs."
            elif dismissal == "lbw":
                summary_text = f"{batsman} was out LBW off {bowler_name} at {over_val} overs."
            elif dismissal == "run out":
                fielder_info = f" by {fielder}" if fielder else ""
                summary_text = f"{batsman} was run out{fielder_info} at {over_val} overs."
            else:
                summary_text = f"{batsman} was dismissed ({dismissal}) off {bowler_name} at {over_val} overs."

            wicket_doc = (
                f"[Wicket Event]\n"
                f"Match ID: {match_id}\n"
                f"Season/Year: {season_year}\n"
                f"Date: {date_str}\n"
                f"Venue: {venue}, {city}\n"
                f"Teams: {team1} vs {team2}\n"
                f"Innings: {w_inning_num}\n"
                f"Batting Team: {bat_team_wk}\n"
                f"Batsman Dismissed: {batsman}\n"
                f"Bowler: {bowler_name}\n"
                f"Dismissal Type: {dismissal}\n"
                f"Fielder: {fielder or 'N/A'}\n"
                f"Over: {over_val}\n"
                f"Summary: {summary_text} (Match played between {team1} and {team2} on {date_str})"
            )
            wicket_meta = metadata.copy()
            wicket_meta["chunk_type"] = "wicket_event"
            chunks.append({
                "id": f"{match_id}_wicket_{w_inning_num}_{wicket_idx}",
                "document": wicket_doc,
                "metadata": wicket_meta,
            })

        # --- Milestone Chunks ---
        for milestone_idx, ms in enumerate(match_milestones):
            ms_doc = (
                f"[Milestone]\n"
                f"Match ID: {match_id}\n"
                f"Season/Year: {season_year}\n"
                f"Date: {date_str}\n"
                f"Venue: {venue}, {city}\n"
                f"Teams: {team1} vs {team2}\n"
                f"Player: {ms['player']}\n"
                f"Milestone: {ms['milestone']}\n"
                f"Value: {ms['runs']}\n"
                f"Over: {ms['over']}\n"
                f"Summary: {ms['summary']} (Match played between {team1} and {team2} on {date_str})"
            )
            ms_meta = metadata.copy()
            ms_meta["chunk_type"] = "milestone"
            chunks.append({
                "id": f"{match_id}_milestone_{milestone_idx}",
                "document": ms_doc,
                "metadata": ms_meta,
            })

    # --- Match Summary Chunk ---
    summary_text = _make_match_summary_text(info, winner, win_by_runs, win_by_wickets, match_id)
    toss_winner_val = toss.get("winner", "")
    toss_decision_str = toss.get("decision", "").capitalize()
    win_meta_str = f"win_by_runs: {win_by_runs}" if win_by_runs else f"win_by_wickets: {win_by_wickets}"
    summary_doc = (
        f"[Match Summary]\n"
        f"Match ID: {match_id}\n"
        f"Season: {season}\n"
        f"Date: {date_str}\n"
        f"Venue: {venue}, {city}\n"
        f"Teams: {team1} vs {team2}\n"
        f"Toss: {toss_winner_val} won the toss and elected to {toss_decision_str}\n"
        f"Winner: {winner} ({win_meta_str})\n"
        f"Player of the Match: {pom}\n"
        f"Summary: {summary_text}"
    )
    summary_meta = metadata.copy()
    summary_meta["chunk_type"] = "match_summary"
    chunks.append({
        "id": f"{match_id}_match_summary",
        "document": summary_doc,
        "metadata": summary_meta,
    })

    # --- Match Narrative Chunk ---
    narrative_text = _make_match_narrative(info, winner, win_by_runs, win_by_wickets, match_id, innings_summaries)
    narrative_doc = f"[Match Narrative]\nMatch ID: {match_id}\nNarrative: {narrative_text}"
    narrative_meta = metadata.copy()
    narrative_meta["chunk_type"] = "match_narrative"
    chunks.append({
        "id": f"{match_id}_narrative",
        "document": narrative_doc,
        "metadata": narrative_meta,
    })

    return chunks
