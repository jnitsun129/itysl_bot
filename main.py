import os
from datetime import date, datetime

import tweepy
from keys import ACCESS_TOKEN, ACCESS_TOKEN_SECRET, API_KEY, API_KEY_SECRET
from utils import DataHandler

def client_create() -> tweepy.Client:
    """Create and return a Tweepy Client instance."""
    return tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_KEY_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )


def tweepy_api_create() -> tweepy.API:
    """Create and return a Tweepy API instance."""
    tweepy_auth = tweepy.OAuth1UserHandler(
        API_KEY,
        API_KEY_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET,
    )
    return tweepy.API(tweepy_auth)

def format_quote(data: dict) -> str:
    """Format quote data into tweet text."""
    tweet = f'{data["title"]}: {data["season_ep"]}\n\n{data["quote"]}\n\n#itysl'
    return f'{date.today().strftime("%B %d, %Y")}\n\n{tweet}'


def run() -> None:
    """Main function to run the tweet process."""
    data_handler = DataHandler()
    
    data = data_handler.run()
    
    message = format_quote(data)
    t_api = tweepy_api_create()
    t_client = client_create()
    
    media = t_api.media_upload(data["image_path"])
    t_client.create_tweet(media_ids=[media.media_id], text=message)
    
    os.remove(data["image_path"])
    print(f'Tweeted Successfully: {datetime.now()}')


if __name__ == "__main__":
    run()