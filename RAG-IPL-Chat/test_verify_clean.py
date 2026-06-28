import os
import shutil
import glob
import json
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Load env
load_dotenv('../.env')
if not os.getenv("OPENAI_API_KEY"):
    load_dotenv()

def get_season_year(season_str):
    season_str = str(season_str)
    mapping = {
        "2007/08": "2008",
        "2009/10": "2010",
        "2020/21": "2020"
    }
    return mapping.get(season_str, season_str)

def get_sort_key(item):
    filepath, data = item
    info = data.get('info', {})
    dates = info.get('dates', [])
    date_str = dates[0] if dates else '9999-12-31'
    event = info.get('event', {})
    match_num = event.get('match_number', 999)
    if isinstance(match_num, str):
        if 'final' in match_num.lower():
            match_num_val = 200
        elif 'semi' in match_num.lower():
            match_num_val = 190
        elif 'qualifier' in match_num.lower():
            match_num_val = 180
        elif 'eliminator' in match_num.lower():
            match_num_val = 175
        else:
            match_num_val = 150
    else:
        match_num_val = int(match_num) if match_num is not None else 999
    filename = filepath.split('/')[-1]
    return (date_str, match_num_val, filename)

def get_team_abbr(team_name):
    abbrev_map = {
        "Kolkata Knight Riders": "KKR",
        "Royal Challengers Bangalore": "RCB",
        "Royal Challengers Bengaluru": "RCB",
        "Chennai Super Kings": "CSK",
        "Mumbai Indians": "MI",
        "Rajasthan Royals": "RR",
        "Kings XI Punjab": "KXIP",
        "Punjab Kings": "PBKS",
        "Delhi Capitals": "DC",
        "Delhi Daredevils": "DD",
        "Deccan Chargers": "DC",
        "Sunrisers Hyderabad": "SRH",
        "Pune Warriors": "PWI",
        "Kochi Tuskers Kerala": "KTK",
        "Gujarat Lions": "GL",
        "Rising Pune Supergiant": "RPS",
        "Rising Pune Supergiants": "RPS",
        "Lucknow Super Giants": "LSG",
        "Gujarat Titans": "GT"
    }
    if team_name in abbrev_map:
        return abbrev_map[team_name]
    words = team_name.replace("Supergiant", "Super giant").split()
    return "".join(word[0].upper() for word in words if word[0].isalnum())

def get_ordinal(n):
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def calculate_overs(overs_list):
    if not overs_list:
        return 0.0
    last_over = overs_list[-1]
    over_num = last_over.get('over', 0)
    legal_balls = 0
    for d in last_over.get('deliveries', []):
        extras = d.get('extras', {})
        if 'wides' not in extras and 'noballs' not in extras:
            legal_balls += 1
    if legal_balls >= 6:
        return float(over_num + 1)
    else:
        return over_num + (legal_balls / 10.0)

def make_match_summary_text(info, winner, win_by_runs, win_by_wickets, match_id):
    season = info.get('season')
    season_year = get_season_year(season)
    date = info.get('dates', [None])[0]
    venue = info.get('venue')
    city = info.get('city', info.get('venue', 'Unknown').split(',')[0])
    teams = info.get('teams', [])
    toss_winner = info.get('toss', {}).get('winner')
    toss_decision = info.get('toss', {}).get('decision')
    pom = info.get('player_of_match', [''])[0]
    summary_parts = [
        f"IPL {season_year} match (ID: {match_id}) was played on {date} at {venue}, {city} between {teams[0]} and {teams[1]}.",
        f"{toss_winner} won the toss and elected to {toss_decision}."
    ]
    if winner == 'No Result':
        summary_parts.append("The match ended in a No Result.")
    elif winner:
        margin_str = f"by {win_by_runs} runs" if win_by_runs else (f"by {win_by_wickets} wickets" if win_by_wickets else "via Super Over")
        summary_parts.append(f"{winner} defeated {teams[0] if winner == teams[1] else teams[1]} {margin_str}.")
    if pom:
        summary_parts.append(f"{pom} was named Player of the Match.")
    return " ".join(summary_parts)

def make_match_narrative(info, winner, win_by_runs, win_by_wickets, match_id, innings_summaries):
    season = info.get('season')
    season_year = get_season_year(season)
    venue = info.get('venue')
    city = info.get('city', info.get('venue', 'Unknown').split(',')[0])
    teams = info.get('teams', [])
    toss_winner = info.get('toss', {}).get('winner')
    toss_decision = info.get('toss', {}).get('decision')
    pom = info.get('player_of_match', [''])[0]
    narrative_parts = [
        f"IPL {season_year} match was played at {venue}, {city} between {teams[0]} and {teams[1]}.",
        f"{toss_winner} won the toss and elected to {toss_decision}."
    ]
    for i_summary in innings_summaries:
        team_name = i_summary['team']
        runs = i_summary['runs']
        wickets = i_summary['wickets']
        overs = i_summary['overs']
        top_scorers = i_summary['top_scorers']
        top_scorer_part = f" thanks to {top_scorers[0]['player']}'s score of {top_scorers[0]['runs']}" if top_scorers else ""
        narrative_parts.append(f"{team_name} scored {runs}/{wickets} in {overs} overs{top_scorer_part}.")
    if winner == 'No Result':
        narrative_parts.append("The match ended in a No Result.")
    elif winner:
        margin_str = f"by {win_by_runs} runs" if win_by_runs else (f"by {win_by_wickets} wickets" if win_by_wickets else "via Super Over")
        narrative_parts.append(f"{winner} won the match {margin_str}.")
    if pom:
        narrative_parts.append(f"{pom} was named Player of the Match.")
    return " ".join(narrative_parts)

def generate_match_chunks(file_path, match_id):
    with open(file_path, 'r') as f:
        data = json.load(f)
    info = data.get('info', {})
    season = info.get('season', 'Unknown')
    season_year = get_season_year(season)
    dates = info.get('dates', [])
    date_str = dates[0] if dates else 'Unknown'
    year_val = int(date_str.split('-')[0]) if dates else 0
    venue = info.get('venue', 'Unknown')
    city = info.get('city', info.get('venue', 'Unknown').split(',')[0])
    teams = info.get('teams', [])
    if len(teams) < 2: return []
    team1, team2 = teams[0], teams[1]
    team1_abbr = get_team_abbr(team1)
    team2_abbr = get_team_abbr(team2)
    toss = info.get('toss', {})
    toss_winner = toss.get('winner', 'Unknown')
    toss_decision = toss.get('decision', 'Unknown').capitalize()
    outcome = info.get('outcome', {})
    winner = outcome.get('winner') or outcome.get('eliminator')
    winner_abbr = get_team_abbr(winner) if winner else ('No Result' if outcome.get('result') == 'no result' else 'Draw')
    outcome_by = outcome.get('by', {})
    win_by_runs = outcome_by.get('runs', 0)
    win_by_wickets = outcome_by.get('wickets', 0)
    poms = info.get('player_of_match', [])
    player_of_match = poms[0] if poms else 'None'
    metadata = {
        "match_id": match_id, "season": str(season), "year": year_val,
        "team1": team1_abbr, "team2": team2_abbr, "venue": venue, "city": city,
        "winner": winner_abbr, "player_of_match": player_of_match
    }
    chunks = []
    win_str = f"win_by_runs: {win_by_runs}" if win_by_runs else (f"win_by_wickets: {win_by_wickets}" if win_by_wickets else "win_by: Super Over / Tie")
    match_summary_text = make_match_summary_text(info, winner, win_by_runs, win_by_wickets, match_id)
    match_summary_doc = f"""[Match Summary]
Match ID: {match_id}
Season: {season}
Date: {date_str}
Venue: {venue}, {city}
Teams: {team1} vs {team2}
Toss: {toss_winner} won the toss and elected to {toss_decision}
Winner: {winner} ({win_str})
Player of the Match: {player_of_match}
Summary: {match_summary_text}"""
    m_meta = metadata.copy()
    m_meta["chunk_type"] = "match_summary"
    chunks.append({"id": f"{match_id}_match_summary", "document": match_summary_doc, "metadata": m_meta})
    
    innings_data = data.get('innings', [])
    innings_summaries = []
    batting_stats = {}
    bowling_stats = {}
    match_partnerships = []
    match_milestones = []
    match_wickets = []
    
    for inning_idx, inning in enumerate(innings_data):
        batting_team = inning.get('team')
        bowling_team = team2 if batting_team == team1 else team1
        batting_team_abbr = get_team_abbr(batting_team)
        bowling_team_abbr = get_team_abbr(bowling_team)
        inning_num = inning_idx + 1
        overs_list = inning.get('overs', [])
        inning_runs = 0
        inning_wickets_count = 0
        current_partnership_batsmen = None
        part_runs = 0
        part_balls = 0
        reached_50 = set()
        reached_100 = set()
        reached_150 = set()
        bowler_wickets_in_innings = {}
        reached_3w = set()
        reached_5w = set()
        
        for over_obj in overs_list:
            over_index = over_obj.get('over', 0)
            deliveries = over_obj.get('deliveries', [])
            legal_balls = 0
            for delivery in deliveries:
                striker = delivery['batter']
                non_striker = delivery['non_striker']
                bowler = delivery['bowler']
                runs_dict = delivery.get('runs', {})
                batter_runs = runs_dict.get('batter', 0)
                total_runs = runs_dict.get('total', 0)
                extras = delivery.get('extras', {})
                is_wide = 'wides' in extras
                is_noball = 'noballs' in extras
                is_legal = not is_wide and not is_noball
                if is_legal: legal_balls += 1
                ball_display = legal_balls if is_legal else (legal_balls + 1)
                over_val = over_index + (ball_display / 10.0)
                inning_runs += total_runs
                if striker not in batting_stats:
                    batting_stats[striker] = {
                        "runs": 0, "balls": 0, "fours": 0, "sixes": 0,
                        "team": batting_team, "opposing_team": bowling_team,
                        "dismissed": False, "how_out": "not out", "bowler": None, "fielder": None
                    }
                if non_striker not in batting_stats:
                    batting_stats[non_striker] = {
                        "runs": 0, "balls": 0, "fours": 0, "sixes": 0,
                        "team": batting_team, "opposing_team": bowling_team,
                        "dismissed": False, "how_out": "not out", "bowler": None, "fielder": None
                    }
                if bowler not in bowling_stats:
                    bowling_stats[bowler] = {
                        "wickets": 0, "runs_conceded": 0, "balls_bowled": 0,
                        "team": bowling_team, "opposing_team": batting_team
                    }
                batting_stats[striker]["runs"] += batter_runs
                if is_legal: batting_stats[striker]["balls"] += 1
                if batter_runs == 4: batting_stats[striker]["fours"] += 1
                elif batter_runs == 6: batting_stats[striker]["sixes"] += 1
                conceded = total_runs - extras.get('byes', 0) - extras.get('legbyes', 0) - extras.get('penalty', 0)
                bowling_stats[bowler]["runs_conceded"] += max(0, conceded)
                if is_legal: bowling_stats[bowler]["balls_bowled"] += 1
                if current_partnership_batsmen is None:
                    current_partnership_batsmen = [striker, non_striker]
                    part_runs = 0
                    part_balls = 0
                part_runs += total_runs
                if is_legal: part_balls += 1
                current_batsman_runs = batting_stats[striker]["runs"]
                current_batsman_balls = batting_stats[striker]["balls"]
                if current_batsman_runs >= 50 and striker not in reached_50:
                    reached_50.add(striker)
                    match_milestones.append({"player": striker, "milestone": "Half-Century", "runs": 50, "over": over_val, "summary": f"{striker} reached his half-century in {current_batsman_balls} balls."})
                if current_batsman_runs >= 100 and striker not in reached_100:
                    reached_100.add(striker)
                    match_milestones.append({"player": striker, "milestone": "Century", "runs": 100, "over": over_val, "summary": f"{striker} reached his century in {current_batsman_balls} balls."})
                wickets_list = delivery.get('wickets', [])
                if wickets_list:
                    for w in wickets_list:
                        player_out = w.get('player_out')
                        dismissal_kind = w.get('kind', 'out')
                        fielders_names = [fld.get('name') for fld in w.get('fielders', []) if fld.get('name')]
                        fielders_str = " and ".join(fielders_names) if fielders_names else None
                        inning_wickets_count += 1
                        if player_out in batting_stats:
                            batting_stats[player_out]["dismissed"] = True
                            batting_stats[player_out]["how_out"] = dismissal_kind
                            batting_stats[player_out]["bowler"] = bowler
                            batting_stats[player_out]["fielder"] = fielders_str
                        if dismissal_kind in ['caught', 'bowled', 'lbw', 'stumped', 'caught and bowled', 'hit wicket']:
                            bowling_stats[bowler]["wickets"] += 1
                            bowler_wickets_in_innings[bowler] = bowler_wickets_in_innings.get(bowler, 0) + 1
                            current_w = bowler_wickets_in_innings[bowler]
                            if current_w == 3 and bowler not in reached_3w:
                                reached_3w.add(bowler)
                                match_milestones.append({"player": bowler, "milestone": "3 Wicket Haul", "runs": 3, "over": over_val, "summary": f"{bowler} completed a 3-wicket haul at {over_val} overs."})
                        match_wickets.append({"over": over_val, "batsman": player_out, "bowler": bowler, "dismissal": dismissal_kind, "fielder": fielders_str, "inning_num": inning_num, "batting_team": batting_team})
                        p_label = "Opening" if inning_wickets_count == 1 else f"{get_ordinal(inning_wickets_count)} wicket"
                        match_partnerships.append({"players": list(current_partnership_batsmen), "runs": part_runs, "wicket": inning_wickets_count, "unbroken": False, "summary": f"{p_label} partnership between {current_partnership_batsmen[0]} and {current_partnership_batsmen[1]} added {part_runs} runs.", "team": batting_team, "inning_num": inning_num})
                        current_partnership_batsmen = None
                        part_runs = 0
                        part_balls = 0
        if current_partnership_batsmen is not None:
            match_partnerships.append({"players": list(current_partnership_batsmen), "runs": part_runs, "wicket": inning_wickets_count + 1, "unbroken": True, "summary": f"Unbroken partnership of {part_runs} runs between {current_partnership_batsmen[0]} and {current_partnership_batsmen[1]}.", "team": batting_team, "inning_num": inning_num})
        overs_bowled = calculate_overs(overs_list)
        inning_batsmen = {p: stats for p, stats in batting_stats.items() if stats["team"] == batting_team}
        top_scorers = [{"player": p, "runs": stats["runs"]} for p, stats in sorted(inning_batsmen.items(), key=lambda x: x[1]["runs"], reverse=True)[:2]]
        top_scorer_part = f" {top_scorers[0]['player']} remained unbeaten on {top_scorers[0]['runs']} runs." if top_scorers and not batting_stats[top_scorers[0]['player']]['dismissed'] else (f" {top_scorers[0]['player']} scored {top_scorers[0]['runs']} runs." if top_scorers else "")
        innings_summary_text = f"{batting_team_abbr} scored {inning_runs}/{inning_wickets_count} in {overs_bowled} overs.{top_scorer_part}"
        innings_summaries.append({"innings": inning_num, "team": batting_team, "runs": inning_runs, "wickets": inning_wickets_count, "overs": overs_bowled, "top_scorers": top_scorers, "summary": innings_summary_text})
        
        inning_summary_doc = f"""[Team Innings Summary]
Match ID: {match_id}
Season/Year: {season_year}
Date: {date_str}
Venue: {venue}, {city}
Teams: {team1} vs {team2}
Team: {batting_team}
Innings: {inning_num}
Score: {inning_runs}/{inning_wickets_count} in {overs_bowled} overs
Top Scorers:
""" + "\n".join([f"- {ts['player']}: {ts['runs']} runs" for ts in top_scorers]) + f"\nSummary: {innings_summary_text} (Match played between {team1} and {team2} on {date_str})"
        in_meta = metadata.copy()
        in_meta["chunk_type"] = "innings_summary"
        chunks.append({"id": f"{match_id}_innings_{inning_num}", "document": inning_summary_doc, "metadata": in_meta})

    for player, stats in batting_stats.items():
        runs, balls, fours, sixes, team, opp_team, dismissed = stats["runs"], stats["balls"], stats["fours"], stats["sixes"], stats["team"], stats["opposing_team"], stats["dismissed"]
        sr = round((runs / balls * 100), 1) if balls > 0 else 0.0
        status_suffix = "not out" if not dismissed else "out"
        how_out_text = f"dismissed ({stats['how_out']})" if dismissed else "not out"
        player_batting_text = f"{player} scored {runs} {status_suffix} off {balls} balls against {opp_team} in IPL {season_year}."
        doc = f"""[Player Batting Performance]
Match ID: {match_id}
Season/Year: {season_year}
Date: {date_str}
Venue: {venue}, {city}
Teams: {team1} vs {team2}
Player: {player}
Team: {team}
Opponent: {opp_team}
Runs: {runs} | Balls: {balls} | Fours: {fours} | Sixes: {sixes} | SR: {sr}
Status: {how_out_text}
Summary: {player_batting_text}"""
        p_meta = metadata.copy()
        p_meta["chunk_type"] = "player_batting"
        chunks.append({"id": f"{match_id}_batting_{player.replace(' ', '_')}", "document": doc, "metadata": p_meta})

    for player, stats in bowling_stats.items():
        wickets, conceded, balls_bowled, team, opp_team = stats["wickets"], stats["runs_conceded"], stats["balls_bowled"], stats["team"], stats["opposing_team"]
        overs_str = f"{balls_bowled // 6}" if balls_bowled % 6 == 0 else f"{balls_bowled // 6}.{balls_bowled % 6}"
        economy = round(conceded / (balls_bowled / 6.0), 2) if balls_bowled > 0 else 0.0
        player_bowling_text = f"{player} took {wickets} wickets conceding {conceded} runs in {overs_str} overs (economy {economy}) against {opp_team} in IPL {season_year}."
        doc = f"""[Player Bowling Performance]
Match ID: {match_id}
Season/Year: {season_year}
Date: {date_str}
Venue: {venue}, {city}
Teams: {team1} vs {team2}
Player: {player}
Team: {team}
Opponent: {opp_team}
Overs: {overs_str} | Wickets: {wickets} | Runs Conceded: {conceded} | Economy: {economy}
Summary: {player_bowling_text}"""
        pb_meta = metadata.copy()
        pb_meta["chunk_type"] = "player_bowling"
        chunks.append({"id": f"{match_id}_bowling_{player.replace(' ', '_')}", "document": doc, "metadata": pb_meta})

    for part_idx, part in enumerate(match_partnerships):
        doc = f"""[Partnership]
Match ID: {match_id}
Season/Year: {season_year}
Date: {date_str}
Venue: {venue}, {city}
Teams: {team1} vs {team2}
Team: {part['team']}
Innings: {part['inning_num']}
Players: {part['players'][0]} & {part['players'][1]}
Wicket: {part['wicket']}
Runs: {part['runs']}
Summary: {part['summary']} (Match played between {team1} and {team2} on {date_str})"""
        pt_meta = metadata.copy()
        pt_meta["chunk_type"] = "partnership"
        chunks.append({"id": f"{match_id}_partnership_inning{part['inning_num']}_{part_idx}", "document": doc, "metadata": pt_meta})

    for wicket_idx, w_evt in enumerate(match_wickets):
        over_val, batsman, bowler, dismissal, fielder, inning_num, bat_team = w_evt["over"], w_evt["batsman"], w_evt["bowler"], w_evt["dismissal"], w_evt["fielder"], w_evt["inning_num"], w_evt["batting_team"]
        f_part = f" caught by {fielder}" if fielder and dismissal == "caught" else (" caught" if dismissal == "caught" else (f" stumped by {fielder}" if dismissal == "stumped" else ""))
        summary_text = f"{batsman} was bowled by {bowler} at {over_val} overs." if dismissal == "bowled" else (f"{batsman} was{f_part} off {bowler} at {over_val} overs." if dismissal in ["caught", "stumped"] else (f"{batsman} was out LBW off {bowler} at {over_val} overs." if dismissal == "lbw" else (f"{batsman} was run out at {over_val} overs." if dismissal == "run out" else f"{batsman} was dismissed ({dismissal}) off {bowler} at {over_val} overs.")))
        doc = f"""[Wicket Event]
Match ID: {match_id}
Season/Year: {season_year}
Date: {date_str}
Venue: {venue}, {city}
Teams: {team1} vs {team2}
Innings: {inning_num}
Batting Team: {bat_team}
Batsman Dismissed: {batsman}
Bowler: {bowler}
Dismissal Type: {dismissal}
Fielder: {fielder or 'N/A'}
Over: {over_val}
Summary: {summary_text} (Match played between {team1} and {team2} on {date_str})"""
        w_meta = metadata.copy()
        w_meta["chunk_type"] = "wicket_event"
        chunks.append({"id": f"{match_id}_wicket_{inning_num}_{wicket_idx}", "document": doc, "metadata": w_meta})

    for milestone_idx, ms in enumerate(match_milestones):
        player, ms_name, runs_val, over_val = ms["player"], ms["milestone"], ms["runs"], ms["over"]
        doc = f"""[Milestone]
Match ID: {match_id}
Season/Year: {season_year}
Date: {date_str}
Venue: {venue}, {city}
Teams: {team1} vs {team2}
Player: {player}
Milestone: {ms_name}
Value: {runs_val}
Over: {over_val}
Summary: {ms['summary']} (Match played between {team1} and {team2} on {date_str})"""
        ms_meta = metadata.copy()
        ms_meta["chunk_type"] = "milestone"
        chunks.append({"id": f"{match_id}_milestone_{milestone_idx}", "document": doc, "metadata": ms_meta})

    narrative_text = make_match_narrative(info, winner, win_by_runs, win_by_wickets, match_id, innings_summaries)
    narrative_doc = f"""[Match Narrative]
Match ID: {match_id}
Narrative: {narrative_text}"""
    n_meta = metadata.copy()
    n_meta["chunk_type"] = "match_narrative"
    chunks.append({"id": f"{match_id}_narrative", "document": narrative_doc, "metadata": n_meta})
    return chunks

def main():
    # 1. Clean delete of chroma_db directory to fix index corruption
    db_dir = "./chroma_db"
    if os.path.exists(db_dir):
        print("Deleting corrupted chroma_db directory to start fresh...")
        shutil.rmtree(db_dir)
        
    # Gather matches in ipl-2008 (matching user configuration)
    json_files = glob.glob('ipl-2008/*.json')
    all_matches = []
    for f in json_files:
        with open(f, 'r') as file:
            data = json.load(file)
            all_matches.append((f, data))
            
    all_matches.sort(key=get_sort_key)
    
    # Assign logical IDs
    filepath_to_id = {}
    for idx, (filepath, data) in enumerate(all_matches):
        match_id = f"IPL_2008_{idx+1:03d}"
        filepath_to_id[filepath] = match_id
        
    print(f"Loaded and sorted {len(filepath_to_id)} matches from ipl-2008.")
    
    # Extract all chunks
    all_chunks = []
    for filepath, match_id in filepath_to_id.items():
        all_chunks.extend(generate_match_chunks(filepath, match_id))
    print(f"Total chunks extracted: {len(all_chunks)}")
    
    # Ingest fresh
    client = chromadb.PersistentClient(path="./chroma_db")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-large"
    )
    collection_name = "ipl_enhanced_chunks_openai"
    collection = client.create_collection(name=collection_name, embedding_function=openai_ef)
    
    # Ingest in batches of 1000
    batch_size = 1000
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        collection.add(
            documents=[c['document'] for c in batch],
            metadatas=[c['metadata'] for c in batch],
            ids=[c['id'] for c in batch]
        )
        print(f"Ingested {min(i+batch_size, len(all_chunks))} of {len(all_chunks)}...")
        
    # Test query with metadata filter to verify it works now
    print("\nRunning verification queries with where filter...")
    res = collection.query(
        query_texts=["KKR won in Bangalore"],
        n_results=2,
        where={"chunk_type": "match_summary"}
    )
    print("Verification Query succeeded! Found IDs:", res['ids'])

if __name__ == "__main__":
    main()
