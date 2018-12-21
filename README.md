# Twitter Live Data Collector

Uses the Twitter API to collect and store  profile and tweet data for the specified keywords. Data will be stored inside the data directory. 

Data will be stored in the following format:

**Tweet Data:**

| ID | Tweet | Time | User | Likes | Replies | Retweets | in_response_to | response_type
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: 
| The ID of the tweet | The tweet text. Contains retweeted and quoted information too if they exist | Unix timestamp of the tweet in UTC Time | Username of the use who posted the tweet | Total number of likes the tweet received. It will be zero  as  we are collecting live | Same as likes | Same as likes | ID of tweet in whose response the current tweet was made. None if it's a parent tweet | "tweet" or "retweet" or "quoted_retweet"

**Profile Data:**

| username | created | location | has_location | is_verified | total_tweets | total_following | total_followers | total_likes | has_avatar | has_background | is_protected | profile_modified
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---:  | :---: | :---: | :---: | :---: 
| Username of the use who posted the tweet | The date the profile was created in on YYYY-MM-DD format | Profile Location | 1 if profile has a location 0 if it dosen't | 1  if profile is verified 0 if it isn't  | Total number of tweets created by the user | Total accounts following | Total Followers | Total likes the user has received | 1 if account  has an avatar 0 if it dosen't  | 1 if account has an background 0 if it dosen't | 1 if account is protected 0 if it isn't | 1 if profile is  modified. 0 if it isn't

Live tweet data will be stored inside "data/tweet/category_name/live" while will be moved to live_storage folder later.
Profile data will be stored in "data/profile"

## Instructions:

1) Open the keywords.json file. Replace the title (manual, house and senate) with a category that you will remeber. You can place this anything you want. Modify the start_date to the current date. They add keywords or hastags for that category in the keywords section. You can remove or add any number of categories.

2) Add your API credentials in data/static/api.json

3) Run the live data collection:

`python3 run_live.py`

After wards you can clean the data and convert them into a single file using notebooks in "Data Cleaning" folder

4) If you wish to update the number of likes and retweets later you can use this repository:
https://github.com/warproxxx/Tweet-Details-Scraper