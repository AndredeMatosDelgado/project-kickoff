# Music & AI Evolution : From Appreciation to Al Co-Creation
[![View Presentation](https://via.placeholder.com/800x450.png?text=Click+to+View+Presentation)](https://canva.link/6exh8v4h4lnd59n)


This project is an exploratory data analysis pipeline examining how popular music lyrics have evolved across historical eras alongside the exponential growth of computational power used to train notable audio and AI systems.

Lyrical Evolution (1958–2026):

Scrapes song lyrics via the Genius API

cleans and merges them with Billboard Hot 100 chart metadata

Maps granular Spotify subgenres into 13 core parent genres, and categorizes songs into four musical eras:
-Golden Rock/Soul Era
-MTV/Synth-Pop Era
-Digital Streaming Era
-and Short-Form Era

It engineers four linguistic features aggregated in pivot tables before dropping raw lyric text for copyright compliance:
-Total Words
-Unique Words
-Word Diversity
-Word Complexity

AI Compute & Audio Models:
Processes historical AI training compute data (measured in FLOPs) to visualize exponential scaling trends on a logarithmic

Audio and music Generation Models:
-Spotify RecSys
-NSynth 
-Jukebox
-MusicLM
-Suno AI / Udio

Visualization regarding exponential growth for the models


---------------------------------------------------------------------------------------------------------------------------------


# 1. How to Install It

git clone https://github.com/AndredeMatosDelgado/project-kickoff.git
cd project-kickoff.git


# 2. Install Dependencies

pip install pandas numpy requests beautifulsoup4 tqdm curl-cffi matplotlib seaborn python-dotenv lyricsgenius


# 3. Configure Environment Variables

GENIUS_API_KEY=your_genius_access_token_here


---------------------------------------------------------------------------------------------------------------------------------


# Example Usage


# 1. Running the full pipeline

This executes the data cleaning, engeneering, filter, pivots and exports with compute AI visualizations

python main.py

# 2. Scraping Missing Lyrics via Genius API´

To scrape lyrics for songs between 2020 and 2026 with automatic crash-safe JSON checkpointing (genius_lyrics.json), ->uncomment<- the download_lyrics() block in your script.

from main_script import download_lyrics

Automatically resumes from genius_lyrics.json and skips already-downloaded tracks
download_lyrics()

# 3. Outputs

Era & Genre Pivot CSVs:
metrics - (total_words, unique_words, complexity_words, diversity_words, and acousticness)
{metric}_by_musical_era_and_genre.csv
{metric}_by_year_and_genre.csv

AI Compute Datasets & Charts: ai_compute_cleaned.csv, top_music_ai.csv, and ai_compute_growth_plot.png.


---------------------------------------------------------------------------------------------------------------------------------


# How to Set Up the Dev Environment

# 1. Create virtual environment

Create virtual environment
python -m venv venv

Activate on Mac/Linux
source venv/bin/activate

Activate on Windows
venv\Scripts\activate


# 2. Install development packages & Jupyter kernel:

pip install pandas numpy requests beautifulsoup4 tqdm curl-cffi matplotlib seaborn python-dotenv lyricsgenius ipykernel


# 3. Verify .gitignore protection:
Confirm that .env, genius_lyrics.json, and raw lyric CSVs are ignored before making edits:

git status


---------------------------------------------------------------------------------------------------------------------------------


# How to Ship a Change

# 1. Create a new branch from main:

git checkout -b feature/your-feature-name


# 2. Make your edits and verify security:
Run the pipeline locally to verify there are no errors, and run git status to ensure no .env files or copyrighted lyric datasets are tracked.


# 3. Commit and push your branch:
Navigate to your repository on GitHub, open a Pull Request from your feature branch into main, review the changes, and merge.


---------------------------------------------------------------------------------------------------------------------------------


# Change Log

[1.0.0] - 2026-11-14

Added: Billboard Hot 100 cleaning, subgenre-to-parent-genre mapping, and 4-era classification pipeline.
Added: Genius API scraper with browser impersonation (curl_cffi) and crash-safe .tmp JSON checkpointing.
Added: Linguistic metric calculations (total_words, unique_words, diversity_words, complexity_words) and automated removal of raw lyrics prior to export.
Added: AI compute log-scale visualization and filtering for notable audio/music AI models (top_music_ai.csv).

Security: Migrated API credentials to .env and configured .gitignore to exclude sensitive tokens and lyric datasets.


---------------------------------------------------------------------------------------------------------------------------------


# License and Author Info

Authors:
[André Delgado] — [GitHub Profile](https://github.com/AndredeMatosDelgado)
[Gert Xani] — [GitHub Profile](https://github.com/gertxani2-cmyk)

Program: Ironhack Data Analytics Bootcamp (2026)

License: This project's source code is licensed under the MIT License — see the LICENSE file for full details.

Data Disclaimer: Third-party datasets (Billboard Hot 100 metadata and AI compute benchmarks) belong to their respective publishers. Raw song lyrics fetched via the Genius API are excluded from this repository and remain the sole property of their respective copyright holders.