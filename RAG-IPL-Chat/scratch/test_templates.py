import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv('../.env')

df = pd.read_csv('dataset/ipl_matches_2026.csv')
df['total_runs'] = df['team1_runs'] + df['team2_runs']
max_total_runs = df['total_runs'].max()
max_single_runs = max(df['team1_runs'].max(), df['team2_runs'].max())

def get_text_for_template(row, template_type):
    total_runs = row['team1_runs'] + row['team2_runs']
    max_score = max(row['team1_runs'], row['team2_runs'])
    
    is_max_total = (total_runs == max_total_runs)
    is_max_single = (row['team1_runs'] == max_single_runs or row['team2_runs'] == max_single_runs)
    
    facts = []
    keywords = [
        f"total runs: {total_runs}",
        f"total runs in match: {total_runs}",
        f"innings high score: {max_score}",
        f"max runs in an innings: {max_score}"
    ]
    
    if is_max_total:
        facts.append("This match has the absolute highest total runs scored in a single match (maximum runs in one match) in the entire season.")
        keywords.extend([
            "highest scoring match",
            "maximum runs in one match",
            "max runs in one match",
            "match with maximum runs",
            "match with most runs",
            "most runs in a match",
            "highest total runs match"
        ])
    if is_max_single:
        facts.append("This match contains the highest individual team innings score (maximum runs by a single team) in the season.")
        keywords.extend([
            "highest team score",
            "maximum runs by a team",
            "max score by a team"
        ])
        
    facts_str = "\n".join([f"* {f}" for f in facts])
    keywords_str = ", ".join(keywords)
    
    text = f"""Match Summary

Date: {row['date']}
Season: IPL {row['season']}

Venue:
{row['venue']}
City: {row['city']}

Teams:
{row['team1']} vs {row['team2']}

First Innings:
{row['team1']} scored {row['team1_runs']} runs for {row['team1_wickets']} wickets.

Second Innings:
{row['team2']} scored {row['team2_runs']} runs for {row['team2_wickets']} wickets.

Match Result:
{row['winner']} won the match.

Winning Margin:
* Runs: {row['win_by_runs']}
* Wickets: {row['win_by_wickets']}

Total Match Runs: {total_runs}
Max Innings Score: {max_score}

Match Facts:
* Total runs scored: {total_runs}
* Highest innings score: {max_score}
{facts_str}

Search Keywords:
{row['team1']}, {row['team2']}, {row['winner']}, {row['player_of_match']}, {row['city']}, {row['venue']}, IPL {row['season']}, {keywords_str}"""
    return text

client = chromadb.EphemeralClient()
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv('OPENAI_API_KEY'),
    model_name='text-embedding-3-large'
)

collection = client.create_collection(name="test_advanced", embedding_function=openai_ef)
documents = [get_text_for_template(row, 'advanced') for _, row in df.iterrows()]
ids = [f"match_{i}" for i in range(len(df))]
collection.add(documents=documents, ids=ids)

queries = [
    "find the match with max runs in one match",
    "match with maximum runs",
    "highest scoring match",
    "maximum runs in one match",
    "max runs in one match"
]

for q in queries:
    res = collection.query(query_texts=[q], n_results=3)
    print(f"\nQuery: '{q}'")
    for i in range(len(res['ids'][0])):
        doc = res['documents'][0][i]
        dist = res['distances'][0][i]
        is_target = "2026-04-25" in doc
        print(f"  Result {i+1} (Dist: {dist:.4f}, Max runs match? {is_target})")
        if is_target:
            print("    [MATCH FOUND!]")
