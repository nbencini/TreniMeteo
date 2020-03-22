# Train Delay Analysis Project

This project analyzes the relationship between train delays, user complaints on Twitter, and weather conditions in Lombardy, Italy. It combines data from the ViaggiaTreno API, Twitter, and weather sensors to create an integrated dataset for analysis.

## Components

1. `01_etl_trains.py`: Extracts train delay data from the ViaggiaTreno API.
2. `00_stream_tweets.py`: Streams and stores tweets related to train services.
3. `02_etl_weather.py`: Collects weather data from Lombardy's open data portal.
4. `03_data_integration.py`: Integrates data from all sources into a single dataset.
5. `START_TWEETS.sh`: Bash script to start the tweet streaming process.

## Setup

1. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

2. Set up your database connections and Twitter API credentials in `config.py`.

## Usage

1. Start the tweet streaming process:
   ```
   ./START_TWEETS.sh
   ```

2. Run the ETL scripts in order:
   ```
   python 01_etl_trains.py
   python 02_etl_weather.py
   ```

3. Integrate the data:
   ```
   python 03_data_integration.py
   ```

The final integrated dataset will be saved as a CSV file in `/mnt/volume_fra1_01/dati_integrati.csv`.

## Data Sources

- Train data: ViaggiaTreno API
- Weather data: Lombardy Open Data Portal
- User complaints: Twitter streaming API

## Output

The project generates an integrated dataset containing hourly information on:
- Average train delays
- Number of trains
- Number of tweets and "disagio" (discomfort) mentions
- Rainfall amount

This dataset can be used for further analysis or visualization in tools like Tableau.