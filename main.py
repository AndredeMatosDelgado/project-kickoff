# %%
#!pip install lyricsgenius pandas
#!pip install tqdm
#!pip install pandas
#!pip install requests
#!pip install beautifulsoup4
#!pip install tqdm
#!pip install curl-cffi
#!pip install matplotlib
#!pip install seaborn
#!pip install python-dotenv

# %%
import lyricsgenius
import pandas as pd
import numpy as np
import requests
import ast
import re
import time
import random
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns

from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests as cffi_requests

# %%
load_dotenv()
tqdm.pandas()  # Initialize tqdm for pandas

# %%
# Genius Token and Checkpoint File
GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_API_KEY")
CHECKPOINT_FILE = "genius_lyrics.json"

# %%
# ------------------------------------------------------FUNCTIONS START HERE---------------------------------------------------------

# %%
# This function will clean the genre list by converting it to a list of strings, takes care of the null values or strings "nan"
def clean_genre_list(val): 
    if pd.isna(val) or str(val).lower() == "nan":
        return []
    try:
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        return []

# %%
# This function will convert subgenres to main genres based on the mapping

def convert_subgenres_to_main_genre(genres):
    assigned_genres = []
    for genre in genres:
        if "hip hop" in genre or "rap" in genre or "trap" in genre or "gangsta rap" in genre or "conscious hip hop" in genre or "boom bap" in genre or "drill" in genre:
            assigned_genres.append("Hip Hop/Rap")
        elif "pop" in genre or "dance pop" in genre or "synthpop" in genre or "electropop" in genre:
            assigned_genres.append("Pop")
        elif "rock" in genre or "metal" in genre or "punk" in genre or "alternative" in genre:
            assigned_genres.append("Rock")
        elif "country" in genre:
            assigned_genres.append("Country")
        elif "r&b" in genre or "soul" in genre:
            assigned_genres.append("R&B/Soul")
        elif "electronic" in genre or "dance" in genre or "edm" in genre or "house" in genre or "techno" in genre or "trance" in genre or "dubstep" in genre or "drum and bass" in genre or "trap" in genre:
            assigned_genres.append("Electronic/Dance")
        elif "jazz" in genre:
            assigned_genres.append("Jazz")
        elif "classical" in genre:
            assigned_genres.append("Classical")
        elif "reggae" in genre:
            assigned_genres.append("Reggae")
        elif "blues" in genre:
            assigned_genres.append("Blues")
        elif "folk" in genre or "acoustic" in genre or "indie" in genre:
            assigned_genres.append("Folk")
        elif "latin" in genre or "salsa" in genre or "merengue" in genre or "bachata" in genre or "reggaeton" in genre:
            assigned_genres.append("Latin")
        else:
            assigned_genres.append("Other")
    return list(set(assigned_genres))  # Return unique main genres    

# %%
# This function removes extra text like feat, remixes, or brackets from the title when scraping the lyrics from Genius.
# This is to ensure that the title matches the one on Genius.

def clean_song_title(title):
    title_str = str(title)
    title_str = re.sub(r'\s*[\(\[][^\]\)]*[\)\]]', '', title_str)
    title_str = re.sub(r'\s+(feat\.?|ft\.?|with)\s+.*', '', title_str, flags=re.IGNORECASE)
    title_str = re.sub(r'\b(Deluxe|Remix|Version|Edit)\b', '', title_str, flags=re.IGNORECASE)
    return title_str.strip()

# %%
# Searches Genius API for the correct path of the URL and then with that URL scrapes the song lyrics.

def get_lyrics(artist_name, song_title, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    search_url = f"https://api.genius.com/search?q={artist_name} {song_title}"

        # "cffi_requests" is used to make the request importing "requests" from a library called "curl_cffi"
        # which is a library that allows you to request like a browser, and it is faster than the requests library
        # "impersonate="chrome" impersonates a Chrome browser to avoid being blocked by Genius.
        
    try:
        response = cffi_requests.get(search_url, headers=headers, impersonate="chrome", timeout=10)
        
        if response.status_code != 200: # If the response is not OK (error 404 or 403), return "Empty"
            return "Empty"
            
        data = response.json() # Converts raw string data to a Python dictionary using the json() method.
        
        # hits is a list of dictionaries,
        #each representing a song that matches the search query.
        hits = data.get("response", {}).get("hits", []) 

        # If there are no matches, return "Empty" avoiding an IndexError
        if not hits:
            return "Empty"

        # This creates the URL for the song's lyrics page on Genius by extracting the path from the first hit "index[0]" in the search results.
        song_path = hits[0]["result"]["path"]
        lyrics_url = f"https://genius.com{song_path}"

        # "impersonate="chrome" impersonates a Chrome browser again to avoid being blocked by Genius.
        page_response = cffi_requests.get(lyrics_url, headers=headers, impersonate="chrome", timeout=10)

        if page_response.status_code != 200: # If the response is not OK (error 404 or 403), return "Empty"
            return "Empty"

        # This tranforms the HTML content of the lyrics page into a BeautifulSoup object,
        # which allows for easy parsing and extraction of the lyrics.  
        soup = BeautifulSoup(page_response.text, 'html.parser')

        # all div elements from Genius have the attribute data-lyrics-container="true" and the lyrics are inside these divs.
        # e.g. <div data-lyrics-container="true" class="Lyrics__Container-sc-12f9e8d3-1 jhVhlB">
        lyrics_containers = soup.select('div[data-lyrics-container="true"]') 
        
        if not lyrics_containers:
            return "Empty" # Avoids an IndexError if no lyrics containers are found, returning "Empty" instead of crashing.
            
        lyrics_list = [] # Creates a empty list to store the lyrics from each container

        for container in lyrics_containers: # Loops through the containers and extract the lyrics text,
            for br in container.find_all("br"):
                br.replace_with("\n") # Replaces all <br> tags with a line breaker to preserve the format of the lyrics
            lyrics_list.append(container.get_text()) # Appends the extracted lyrics text to the lyrics_list
            
        full_lyrics = "\n".join(lyrics_list).strip() # Joins all the lyrics from the list into a single string, preserves the format and removes extra spaces
        return full_lyrics if full_lyrics else "Empty" # # Avoids an IndexError if full lyrics are empty, returning "Empty" instead of crashing.
        
    except:
        return "Empty" # Avoids an IndexError if any error occurs during the process, returning "Empty" instead of crashing.

# %%
# This function saves the current progress safely during the scraping into a temporary JSON file.
# To avoid data loss and starting from zero if it crashes 

def save_progress(data):
    temp_file = CHECKPOINT_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
        os.rename(temp_file, CHECKPOINT_FILE)
    except Exception as error:
        print(f"Could not save progress: {error}")

# %%
# Loads the progress saved previously during the scraping,
# because the data is very long like 3000 lyrics to pull.

def load_saved_data():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

# %%
def download_lyrics(): # Check if the billboard dataset is loaded in Jupyter
    if 'billboard' not in globals():
        print("Error: The 'billboard' dataframe was not found")
        return

    # Filter songs between 2020 and 2026
    billboard_copy = billboard.copy() # creates a copy of the original to avoid direct modifications
    billboard_copy['year_numeric'] = pd.to_numeric(billboard_copy['year'], errors='coerce') # converts "year" column to numeric, coercing errors to NaN
    filtered_billboard = billboard_copy[(billboard_copy['year_numeric'] >= 2020) & (billboard_copy['year_numeric'] <= 2026)] # filters "year" to be between 2020 and 2026
    filtered_df = filtered_billboard.drop_duplicates(subset=['performer', 'song']) # removes duplicate entries based on artist and song name

    # Saves the lyrics that have already been downloaded into a variable called "saved_lyrics".
    saved_lyrics = load_saved_data()
    
    # Create a simple lowercase lookup for already downloaded songs, removes spaces and converts to lowercase for consistent comparison.
    saved_lowercase = {key.strip().lower(): value for key, value in saved_lyrics.items()}
    
    # Find songs that still need to be downloaded
    pending_songs = [] # Creates a list to store the songs that need to be downloaded avoiding downloading duplicates or already downloaded songs.
    for index, row in filtered_billboard.iterrows(): # Loops through the Dataframe rows and columns to extract artist"performer" and song "song".
        artist = str(row.get("performer", "")).strip()
        song = str(row.get("song", "")).strip()
        
        if not artist or not song or artist == "nan" or song == "nan": # Avoids processing rows with missing or invalid artist or song names
            continue
            
        unique_key = f"{artist} - {song}" # Uses the artist and song name as a primary key
        normalized_key = unique_key.strip().lower()

        # Checks if the song has already been downloaded and is not empty, to avoid downloading duplicates or empty lyrics.
        already_downloaded = normalized_key in saved_lowercase and saved_lowercase[normalized_key] != "Empty"

        # If the song has not been downloaded yet, add it to the pending_songs list for processing.
        if not already_downloaded:
            pending_songs.append({
                "artist": artist,
                "song": song,
                "key": unique_key
            })

    # Checks how many songs are still pending to download and prints the number of songs remaining to download.
    total_pending = len(pending_songs)
    print(f"Songs remaining to download: {total_pending}\n")

    # If there are no pending songs, print a message and exit the function.
    if total_pending == 0:
        print("All songs have already been downloaded!")
        return

    # Prints a message indicating that the lyrics download process is starting.
    print("Starting lyrics download...\n")

    # Loops through the pending songs and downloads the lyrics for each song, saving progress after each download.
    for i, item in enumerate(pending_songs, 1):
        artist = item["artist"]
        original_song = item["song"]
        unique_key = item["key"]
        clean_title = clean_song_title(original_song)

        # Prints number of songs remaining to download and the current song being downloaded, including the artist and cleaned title.
        print(f"[{i}/{total_pending}] Downloading: '{clean_title}' by {artist}...")

        # Gets the lyrics for the artist "performer", song "clean_title" using the Genius API Token
        lyrics = get_lyrics(artist, clean_title, GENIUS_ACCESS_TOKEN)
        saved_lyrics[unique_key] = lyrics # Unique keys are called lyrics and are stored in the saved_lyrics dictionary for later use.

        # Checks if lyrics are found or not, printing a "Lyrics found" or "Lyrics not found" message accordingly.
        if lyrics != "Empty":
            print("Lyrics found")
        else:
            print("Lyrics not found")
            
        # Save progress after each song
        save_progress(saved_lyrics)
        
        # Wait a random short time between requests to be safe to avoid blocks by Genius API
        time.sleep(random.uniform(0.4, 0.8))

    print("\nProcess finished successfully!")

# %%
def seperate_lyrics_into_words(raw_lyrics):
    if not raw_lyrics or raw_lyrics == "Empty":
        return[]

    # Removes any text within square brackets (like [Chorus], [Verse 1], etc.) and converts the lyrics to lowercase for uniformity.
    text = re.sub(r'\[.*?\]','',raw_lyrics).lower()

    # Uses a regular expression to find all words in the lyrics, including contractions and hyphenated words, and returns them as a list.
    words = re.findall(r"\b[\w']+\b", text) 
    # \b is a word boundary , starts at the beggining of a word and ends before a space or punctiuation
    # \w represents alphanumerical including ( ' ) .
    # and + to match one or more of the preceding letters/words, so it will match words like "don't" or "mother-in-law"
    

    return words

# %%
def convert_lyrics_to_list(val): # converts the lyrics column into a real list
    if isinstance(val,list):
        return val
    if isinstance(val, str) and val.strip().startswith('['):
        try:
            return ast.literal_eval(val)
        except:
            return[]
    return[]

# %%
def assign_musical_era(year): # This function associates years to each musical era
    year = int(year)
    if 1958 <= year <= 1979:
        return "Golden Rock/Soul Era"
    elif 1980 <= year <= 1999:
        return "MTV/Synth-Pop Era"
    elif 2000 <= year <= 2018:
        return "Digital Streaming Era"
    elif 2019 <= year <= 2026:
        return "Short-Form Era"
    else:
        return "Other"

# %%
# --------------------------------------------------------FUNCTIONS END HERE----------------------------------------------------------

# %%
# -----------------------------------------------------DATA CLEANING STARTS HERE------------------------------------------------------

# %%
dataset = "billboard_hot_100.csv"

billboard = pd.read_csv(dataset)
billboard


# %%
print(billboard.shape)
print(billboard.columns)
print(billboard.dtypes)
print(billboard.info)
print(billboard.describe)

# %%
print(billboard.duplicated().sum())
display(billboard.isna().sum())

# %%
print("Spotify Genre Counts:", billboard["spotify_genre"].value_counts())

# %%
genres = billboard["spotify_genre"].explode().dropna().unique()

print(genres)

# %%
# Applies the "clean_genre_list" by converting it to a list of strings, takes care of the null values or strings "nan"
billboard["spotify_genre"] = billboard["spotify_genre"].apply(clean_genre_list)

# %%
print(billboard["spotify_genre"].head())

# %%
# Applies the "convert_subgenres_to_main_genre" function to convert subgenres to main genres based on the mapping
billboard["spotify_genre"] = billboard["spotify_genre"].apply(convert_subgenres_to_main_genre)

# %%
billboard.columns

# %%
# Drops unnecessary columns in regards to our analysis
billboard = billboard.drop(columns = ['cot_rationale',
                                        'valence',
                                        'liveness',
                                        'loudness',
                                        'mode',
                                        'speechiness',
                                        'instrumentalness',
                                        'spotify_track_explicit',
                                        'spotify_track_id',
                                        'spotify_track_preview_url',
                                        'evidence_span',
                                        'acoustic_mood_cluster',
                                        'danceability',
                                        'energy',
                                        'spotify_track_album',
                                        'hit_longevity_profile',
                                        'confidence_score',
                                        'song_id',
                                        'time_signature'
                                        ])

# %%
# Renames the columns to remove "spotify" keywords and make it more precise
billboard = billboard.rename(columns={"spotify_track_duration_ms": "duration",
                                        "spotify_genre": "genre",
                                        "spotify_track_popularity": "track_popularity",
                                        "peak_position": "chart_position"
                                        })

# %%
# Converts numerical columns into type "Int64"
billboard["chart_position"] = billboard["chart_position"].astype("Int64")
billboard["weeks_on_chart"] = billboard["weeks_on_chart"].astype("Int64")
billboard["track_popularity"] = billboard["track_popularity"].astype("Int64")

# %%
billboard.columns
billboard

# %%
#This converts the duration from milliseconds to a more readable format of minutes and seconds,
#and handles any non-numeric values by coercing them to NaN. It then creates two new columns for minutes and seconds
#formats them as strings, and combines them into a single 'duration' column in the format "MM:SS".

duration_to_numeric = pd.to_numeric(billboard["duration"], errors="coerce")

minutes = (duration_to_numeric // 60000).astype("Int64")
seconds = ((duration_to_numeric // 1000) % 60).astype("Int64")

billboard['duration'] = minutes.astype(str) + ":" + seconds.astype(str).str.zfill(2)

# %%
# Checks the names for the 4 unique eras of music
billboard["musical_era"].unique()

# %%
# Changes the name of the "musical_era" values into capitalized names
billboard["musical_era"] = billboard["musical_era"].replace({"digital_streaming_explosion" : "Digital Streaming Era",
                                                             "mtv_synth_pop_boom" : "MTV/Synth-Pop Era",
                                                             "golden_rock_soul_era" : "Golden Rock/Soul Era",
                                                             "hyper_streaming_short_form_era" : "Short-Form Era"})

# %%
# Keeps the string indexed 0 (YYYY-MM-DD) from the column "first_week" to extract to a new column "year"
billboard["year"] = billboard["first_week"].str.split("-").str[0]

# %%
# Groups the songs regarding their corresponding year to their musical era
era_by_years = (billboard.groupby("musical_era")["year"].unique())

# %%
# Drops all null values
billboard = billboard.dropna()

# %%
# checks if there are still null values
billboard.isna().any(axis=1).sum()

# %%
# Billboard Dataframe is now cleaned and ready for analysis. The next steps involve cleaning the lyrics and notes and merge them

# %%
# Start clean hot_100 dataset

# %%
hot_100 = pd.read_csv("hot100.csv")

# %%
# Standardizes the hot_100 dataset columns
hot_100.columns = (
hot_100.columns
.str.strip()
.str.lower()
.str.replace(' ', '_'))

# %%
# Standardizes the colums headers to merge later with the billboard dataset
hot_100 = hot_100.rename(columns={"title": "song","artist": "performer"})

# %%
# Clean titles safely using .loc to remove parentheses/translations
billboard.loc[:, 'clean_song'] = billboard['song'].str.replace(r'(.?)|[.?]', '', regex=True).str.lower().str.strip()
hot_100.loc[:, 'clean_song'] = hot_100['song'].str.replace(r'(.?)|[.?]', '', regex=True).str.lower().str.strip()

# Merge datasets
billboard_merged = billboard.merge(hot_100[['clean_song', 'lyrics']], on='clean_song', how='left')
print("Missing lyrics:", billboard_merged['lyrics'].isna().sum())

# %%
# End clean hot_100 dataset

# %%
# Start clean lyrics dataset

# %%
lyrics = pd.read_csv("billboard_top_100_1946_2022_lyrics.csv")

# %%
# Standardizes the lyrics dataset columns
lyrics.columns = (
lyrics.columns
.str.strip()
.str.lower()
.str.replace(' ', '_'))

# %%
# Standardizes the colums headers to merge later with the billboard dataset
lyrics = lyrics.rename(columns={"artist_names": "performer"})

# %%
# End clean lyrics dataset

# %%
#1. Clean billboard song column using .loc
billboard.loc[:, 'clean_song'] = billboard['song'].astype(str).str.lower().str.strip()

#2. Clean lyrics song column using .loc
lyrics.loc[:, 'clean_song'] = lyrics['song'].astype(str).str.lower().str.strip()

#3. Merge based on the clean song title
billboard_merged = billboard.merge(
lyrics[['clean_song', 'lyrics']],
on='clean_song',
how='left'
)

# %%
#1. Disable pandas row truncation
pd.set_option('display.max_rows', None)

#2. Get the full year-by-year count of matched songs and print as a full string
temporal_dist = billboard_merged[billboard_merged['lyrics'].notna()]['year'].value_counts().sort_index()
print(temporal_dist.to_string())

# %%
# Here begins the Download process of the Genius Lyrics

# %%
# Calls the "download_lyrics" function to start the lyrics download process
"""if __name__ == "__main__":
    download_lyrics()"""

# %%
# Clean Genius Lyrics Dataset starts here

# %%
genius_lyrics = "genius_lyrics.json"

# %%
with open("genius_lyrics.json", "r", encoding="utf-8") as f:
    genius_lyrics = json.loads(f.read())

# %%
genius_list = []

for key, raw_lyrics in genius_lyrics.items():
    # Seperates the performer from the song and put them into a dictionary with the lyrics so it can be merged with the Billboard dataset later.
    parts = re.split(r'\s+-+\s+', key)
    if len(parts) == 2:
        song_name = parts[0].strip()
        performer_name = parts[1].strip()
    else:
        song_name = key
        performer_name = "Unknown"
        
    # Applies the function to separate the lyrics into a list of words, removing any extra text like [Chorus] or [Verse 1].
    words_list = seperate_lyrics_into_words(raw_lyrics)
    
    # Saves the song name, performer name, raw lyrics, list of words, and word count into a dictionary and appends it to the genius_list.
    genius_list.append({
        "song": song_name,
        "performer": performer_name,
        "lyrics": words_list
    })

#Creates a Dataframe ready to merge with billboard dataset, with the song name, performer name, and lyrics as a list of words."
genius_dataframe = pd.DataFrame(genius_list)

# %%
billboard_merged = billboard_merged.merge( # Creates a new column with the lyrics by matching the "performer" and "song"
    genius_dataframe[['song', 'performer', 'lyrics']],
    on=['song', 'performer'],
    how='left',
    suffixes=('', '_genius')
)

# %%
# if billboard column lyrics already has lyrics in it do nothing and fill out only the ones that are missing
billboard_merged['lyrics'] = billboard_merged['lyrics'].fillna(billboard_merged['lyrics_genius'])

# %%
billboard_merged = billboard_merged.drop(columns=['lyrics_genius', # removes unnecessary columns
                                                  'clean_song',
                                                  'chart_success_tier',
                                                  'first_week',
                                                  'last_week',
                                                  'weeks_on_chart',
                                                  'key',
                                                  'track_popularity'])

# %%
billboard_merged = billboard_merged.dropna(subset=['lyrics']) # cleans rows without lyrics to avoid errors in the next steps

# %%
billboard_merged['lyrics'] = billboard_merged['lyrics'].apply(convert_lyrics_to_list) # Calls the function and converts lyrics column into a true list

# %%
billboard_merged['total_words'] = billboard_merged['lyrics'].apply(len) # Calculates the total of words in lyrics

# %%
billboard_merged['unique_words'] = billboard_merged['lyrics'].apply(lambda words: len(set(words))) # Calculates the total unique words in lyrics

# %%
billboard_merged['diversity_words'] = billboard_merged['unique_words'] / billboard_merged['total_words'] # Calculates the total diversity of words

# %%
billboard_merged['complexity_words'] = billboard_merged['lyrics'].apply(lambda words: sum(len(w) for w in words) / len(words) if len(words) > 0 else 0) # Calculates word complexity 

# %%
billboard_merged = billboard_merged.drop(columns = ["lyrics"]) # Drops "lyrics" column due to "Copyright" Protection

# %%
billboard_merged["diversity_words"] = billboard_merged["diversity_words"].round(3)
billboard_merged["complexity_words"] = billboard_merged["complexity_words"].round(3)

# %%
billboard_merged['genre'] = billboard_merged['genre'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x)) # Converts the column list into strings united by ","

# %%
metric_cols = ['total_words', 'unique_words', 'diversity_words', 'complexity_words']# Replaces 0 or negative values with NaN
for col in metric_cols:
    if col in billboard_merged.columns:
        billboard_merged[col] = pd.to_numeric(billboard_merged[col], errors='coerce')
        billboard_merged[col] = billboard_merged[col].replace(0, np.nan)

# %%
if 'complexity_words' in billboard_merged.columns: # Checks and removes outliers in the complexity_words column by keeping NaN values
    billboard_merged = billboard_merged[
        (billboard_merged['complexity_words'].isna()) | 
        ((billboard_merged['complexity_words'] >= 1.0) & (billboard_merged['complexity_words'] <= 5.0))
    ]

# %%
if 'total_words' in billboard_merged.columns: # Checks for outliers in the total_words column by also keeping the NaN values
    billboard_merged = billboard_merged[
        (billboard_merged['total_words'].isna()) | 
        (billboard_merged['total_words'] <= 2500)
    ]

# %%
if 'unique_words' in billboard_merged.columns and 'total_words' in billboard_merged.columns: # Calculates diversity_words by dividing unique_words by total_words
    billboard_merged['diversity_words'] = (billboard_merged['unique_words'] / billboard_merged['total_words']).round(3)

# %%
# Converts back the now cleaned genre column from a list to a string divided by separating them with a ","
billboard_merged['genre'] = billboard_merged['genre'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))

# %%
billboard_merged = ( # This will split the genre column into a seperate string instead of a list
    billboard_merged.assign(
        genre=lambda df: df['genre'].astype(str).str.split(',')
    )
    .explode('genre')
    .assign(genre=lambda df: df['genre'].str.strip())
)

billboard_merged = billboard_merged[
    billboard_merged['genre'].notna()
    & (billboard_merged['genre'] != '')
    & (billboard_merged['genre'] != 'nan')
    & (billboard_merged['genre'] != 'None')
]

# %%
# Applies the "assign_musical_era" function to check where the songs fit in each era
billboard_merged['musical_era'] = billboard_merged['year'].apply(assign_musical_era)

# %%
# -------------------------------------------------------DATA CLEANING ENDS HERE-------------------------------------------------------

# %%
# -------------------------------------------------------MUSIC EDA STARTS HERE---------------------------------------------------------

# %%
# Checks the current distribuition of songs by year
temporal_dist = billboard_merged[billboard_merged['song'].notna()]['year'].value_counts().sort_index()
print(temporal_dist.to_string())

# %%
print(billboard_merged.columns)

# %%
metrics = ['total_words', 'unique_words', 'complexity_words', 'diversity_words', 'acousticness']

# %%
for metric in metrics: # This will create pivot table by musical era with genres as columns
    if metric in billboard_merged.columns:
        table_era_genre = billboard_merged.pivot_table(
            index="musical_era", 
            columns="genre", 
            values=metric, 
            aggfunc="mean"
        ).round(3)

        filename = f"{metric}_by_musical_era_and_genre.csv"
        table_era_genre.to_csv(filename)

# %%
for metric in metrics: # This will create pivot table by year with genres as columns
    if metric in billboard_merged.columns:
        table_year_genre = billboard_merged.pivot_table(
            index="year", 
            columns="genre", 
            values=metric, 
            aggfunc="mean"
        ).round(3)

        filename = f"{metric}_by_year_and_genre.csv"
        table_year_genre.to_csv(filename)

# %%
# ---------------------------------------------------------MUSIC EDA ENDS HERE---------------------------------------------------------

# %%
# -------------------------------------------------------AI DATA CLEANING STARTS HERE--------------------------------------------------

# %%
# 1. LOAD THE DATASET

file = "computation-used-to-train-notable-artificial-intelligence-systems.csv"

print(f"Loading dataset from '{file}'...")
df = pd.read_csv(file)

# Display basic information about the structure
print("\nDataset Shape (Rows, Columns):", df.shape)
print("\nFirst 5 rows:")
print(df.head())
print("\nAvailable Columns:")
print(df.columns)

# %%
# 2. DATA CLEANING AND PREPARATION

# Drop rows with missing values in key columns (Entity/Year/Compute)
df = df.dropna(subset=[df.columns[0], df.columns[1], df.columns[-1]])

# Identify the relevant columns dynamically based on standard OWID format
entity_col = df.columns[0]  # Usually System Name
year_col = df.columns[1]  # Date / Year
compute_col = df.columns[
    -1
]  # Usually the compute metric

# Rename columns for clarity
df = df.rename(
    columns={
        entity_col: "System",
        year_col: "Year",
        compute_col: "Compute_FLOPs",
    }
)

# Clean year column to extract just the year number if it's a full date
df["Year"] = pd.to_numeric(
    df["Year"].astype(str).str.slice(0, 4), errors="coerce"
)
df = df.dropna(subset=["Year"])
df["Year"] = df["Year"].astype(int)

print(f"Total valid rows after cleaning: {len(df)}")

# %%
# 3. SAVE CLEANED DATASET

output_cleaned = "ai_compute_cleaned.csv"
df.to_csv(output_cleaned, index=False)
print(f"\nCleaned dataset successfully saved as '{output_cleaned}'!")

# %%
# -------------------------------------------------------AI DATA CLEANING ENDS HERE--------------------------------------------------

# %%
# --------------------------------------------------AI DATA VISUALIZATION STARTS HERE--------------------------------------------------

# %%
# 4. VISUALIZATION (LOG SCALE FOR AI COMPUTE)

plt.figure(figsize=(12, 7))

plt.scatter(
    df["Year"],
    df["Compute_FLOPs"],
    color="#1f77b4",
    alpha=0.7,
    edgecolors="k",
    s=50,
)

# Use logarithmic scale on the y-axis because AI compute growth is exponential
plt.yscale("log")

plt.title(
    "Exponential Growth of Computation Used to Train Notable AI Systems",
    fontsize=14,
    fontweight="bold",
)
plt.xlabel("Year", fontsize=12)
plt.ylabel("Training Computation (FLOPs - Log Scale)", fontsize=12)
plt.grid(True, which="both", linestyle="--", alpha=0.5)

# Save the plot
plot_filename = "ai_compute_growth_plot.png"
plt.savefig(plot_filename, dpi=300, bbox_inches="tight")
print(f"Visualization successfully saved as '{plot_filename}'!")

plt.show()

# %%
# Get the top 10 models with the highest compute
top_10_models = df.sort_values(by="Compute_FLOPs", ascending=False).head(10)

# Set the visualization theme
sns.set_theme(style="whitegrid")
plt.figure(figsize=(12, 6))

# Create a horizontal bar chart for clear readability
sns.barplot(
    x="Compute_FLOPs", 
    y="System", 
    data=top_10_models, 
    palette="flare"
)

# Apply logarithmic scale to handle massive variations in compute
plt.xscale("log")

# Labeling and styling
plt.title("Top 10 Most Computationally Expensive AI Systems", fontsize=16, fontweight="bold", pad=20)
plt.xlabel("Total Training Compute (FLOPs - Log Scale)", fontsize=12, fontweight="bold")
plt.ylabel("AI System Name", fontsize=12, fontweight="bold")

# Save and show this secondary chart
plt.savefig("top_10_ai_compute_bar_plot.png", dpi=300, bbox_inches="tight")
plt.show()


# %%
music_ai_html = """
<table>
    <tr><th>Music AI System</th><th>Release Year</th><th>Compute (FLOPs)</th><th>Impact on Music</th></tr>
    <tr><td>Spotify RecSys (Early)</td><td>2015</td><td>5.0e15</td><td>Standardized playlists</td></tr>
    <tr><td>NSynth (Google)</td><td>2017</td><td>8.0e17</td><td>Algorithmic sound synthesis</td></tr>
    <tr><td>Jukebox (OpenAI)</td><td>2020</td><td>1.2e22</td><td>Full raw audio generation</td></tr>
    <tr><td>MusicLM (Google)</td><td>2023</td><td>5.5e23</td><td>Text-to-music high fidelity</td></tr>
    <tr><td>Suno AI / Udio</td><td>2024</td><td>2.0e24</td><td>Mass production of pop tracks</td></tr>
</table>
"""

print("[1/2] Scraping Music AI Model metrics using BeautifulSoup...")
soup_music = BeautifulSoup(music_ai_html, "html.parser")
rows = soup_music.find_all("tr")

music_ai_list = []
for row in rows[1:]:
    cols = row.find_all("td")
    if len(cols) == 4:
        music_ai_list.append({
            "Music_AI_System": cols[0].text.strip(),
            "Year": int(cols[1].text.strip()),
            "Compute_FLOPs": float(cols[2].text.strip()),
            "Impact": cols[3].text.strip()
        })

df_music_ai = pd.DataFrame(music_ai_list)

# 2. ULTRA-SHARP VISUALIZATION: Bar Plot of Music AI Evolution
%config InlineBackend.figure_format = 'svg'
plt.figure(figsize=(11, 5), dpi=300)

# Create a clean horizontal bar chart with high contrast
sns.barplot(
    x="Compute_FLOPs",
    y="Music_AI_System",
    data=df_music_ai,
    palette="cool",
    edgecolor="#000000",
    linewidth=1.5
)

plt.xscale("log")
plt.title("The Exponential Growth of AI Models in the Music Industry", fontsize=14, fontweight="bold", pad=20)
plt.xlabel("Training Compute (FLOPs - Log Scale)", fontsize=11, fontweight="bold")
plt.ylabel("Music AI Model", fontsize=11, fontweight="bold")

plt.savefig("music_ai_growth_chart.png", dpi=300, bbox_inches="tight")
plt.show()

# Print text insight for your presentation slides
print("\n" + "-"*65)
print("-"*65)
for _, row in df_music_ai.iterrows():
    print(f"-> {row['Music_AI_System']} ({row['Year']}): Required {row['Compute_FLOPs']:.1e} FLOPs.")
    print(f"   Real-world Impact: {row['Impact']}\n")
print("="*65)

# %%
top_music_ai = pd.read_csv("ai_compute_cleaned.csv")

# Filter for audio/music models
audio_keywords = ["AudioGen", "AudioLM", "MUSIC perceptron", "Whisper", "wave2vec"]
music_df = top_music_ai[
    top_music_ai["System"].str.contains("|".join(audio_keywords), case=False, na=False)
].copy()

# Sort by compute requirement
music_df = music_df.sort_values(by="Compute_FLOPs", ascending=False)

# Export for Flourish
music_df.to_csv("top_music_ai.csv", index=False)


