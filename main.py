import datetime
import tweepy
import keys
import requests
from bs4 import BeautifulSoup
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import date


def client_create() -> tweepy.Client:
    client = tweepy.Client(consumer_key=keys.API_KEY,
                           consumer_secret=keys.API_KEY_SECRET,
                           access_token=keys.ACCESS_TOKEN,
                           access_token_secret=keys.ACCESS_TOKEN_SECRET)
    return client


def api() -> tweepy.API:
    tweepy_auth = tweepy.OAuth1UserHandler(
        "{}".format(keys.API_KEY),
        "{}".format(keys.API_KEY_SECRET),
        "{}".format(keys.ACCESS_TOKEN),
        "{}".format(keys.ACCESS_TOKEN_SECRET),
    )
    return tweepy.API(tweepy_auth)


def get_quote_data() -> str:
    driver = webdriver.Chrome()
    driver.get('https://ithinkyoushouldquote.me/')
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "randomQ")))

    button.click()
    time.sleep(1)
    html_source = driver.page_source
    data = check_valid(html_source)
    while data == "nope":
        button.click()
        time.sleep(1)
        html_source = driver.page_source
        data = check_valid(html_source)
    driver.quit()
    return data


def check_valid(html_source: str) -> str:
    soup = BeautifulSoup(html_source, 'html.parser')
    element = soup.find('ul', id='resultDiv')

    episode_full = element.find(
        'div', class_='mb-1.5 text-white').find('a')

    title = episode_full.text

    season_ep = episode_full.next_sibling.strip()
    season_ep = season_ep[2:]
    season_ep = season_ep.replace('Ep:', 'Episode')
    season_ep = season_ep.replace(':', '')

    image = element.find('a', class_='block relative').find('img')['src']
    last_dex = image.rfind('?')
    image = image[:last_dex]
    quote = element.find('h3').text
    data = {'title': title, 'season_ep': season_ep,
            'image': image.split('/')[-1], 'quote': quote}

    if len(format_quote(data)) > 280 or check_file(data):
        return "nope"
    else:
        download_image(image)
        return data


def download_image(image_string: str) -> None:
    folder_path = 'images'

    image_filename = os.path.join(folder_path, image_string.split('/')[-1])

    response = requests.get(image_string)

    with open(image_filename, 'wb') as image_file:
        image_file.write(response.content)


def check_file(data: dict) -> bool:
    duplicate = False
    quote = data['quote']
    with open('quotes.txt', mode='r') as file:
        for row in file:
            if row.rstrip() == quote:
                duplicate = True
                break
    if not duplicate:
        with open('quotes.txt', 'a') as file:
            file.write(f'{quote}\n')
    return duplicate


def format_quote(data: dict) -> str:
    tweet = f'{data["title"]}: {data["season_ep"]}\n\n{data["quote"]}\n\n#itysl'
    full = f'{date.today().strftime("%B %d, %Y")}\n\n{tweet}'
    return full


def run() -> None:
    data = get_quote_data()
    message = format_quote(data)
    path_to_file = f'images/{data["image"]}'
    t_api = api()
    t_client = client_create()
    media = t_api.media_upload(path_to_file)
    t_client.create_tweet(media_ids=[media.media_id], text=message)
    os.remove(path_to_file)
    print(
        f'Tweeted Successfully: {datetime.datetime.now()}')


if __name__ == "__main__":
    run()
