
import os
import random

import redis
import requests

from const import BASE_API_URL, FOLDER_PATH, IMAGE_API_URL
from keys import REDIS_URL


class DataHandler:
    
    session = requests.Session()
    data = {}
    
    def __init__(self):
        random_num_generator = RandomNumberGenerator()
        self.random_num = random_num_generator.get_next_number()
    
    def get_quote_data(self) -> dict:
        """Fetch quote data from Sanity API."""
        api_url = f"{BASE_API_URL}[{self.random_num}]"
        response = self.session.get(api_url)
        
        data = response.json()["result"]
        
        self.data = {
            "title": data["sketch"],
            "season_ep": f"Season {data['season']}, Episode {data['episode']}",
            "image": data["characterimage"]["asset"]["_ref"],
            "quote": data["quote"]
        }
    
    def format_image_url(self, image_ref: str) -> str:
        image_ref = self.data["image"].replace("image-", "").replace("-jpg", ".jpg")
        image_url = f"{IMAGE_API_URL}/{image_ref}?w=700"
        self.data["image"] = image_url        
    
    def download_image(self) -> str:
        """Download image and return its path."""
        self.format_image_url(self.data["image"])
        
        os.makedirs(FOLDER_PATH, exist_ok=True)
        image_filename = os.path.join(FOLDER_PATH, f"{self.random_num}.jpg")

        image_response = self.session.get(self.data["image"])
        if image_response.status_code == 200:
            with open(image_filename, "wb") as f:
                f.write(image_response.content)
            print("Image downloaded successfully")
        else:
            print(f"Failed to download image: {image_response.status_code}")
        
        return image_filename

    def run(self) -> str:
        self.get_quote_data()
        self.data["image_path"] = self.download_image()
        return self.data


class RandomNumberGenerator:
    def __init__(self, min_value: int = 0, max_value: int = 879, key_name: str = "used_numbers"):
        """
        Initialize the RandomNumberGenerator.
        
        Args:
            min_value: The minimum random number (inclusive)
            max_value: The maximum random number (inclusive)
            key_name: The Redis key to use for tracking used numbers
        """
        self.min_value = min_value
        self.max_value = max_value
        self.key_name = key_name
        self.redis_url = REDIS_URL
        self.redis_client = self._get_redis_client()
    
    def _get_redis_client(self) -> redis.Redis:
        """Create and return a Redis client."""
        if not self.redis_url:
            raise ValueError("REDIS_URL environment variable not set. Add the Redis add-on to your Heroku app.")
        
        return redis.from_url(self.redis_url, ssl_cert_reqs=None)
    
    def get_used_numbers(self) -> set[int]:
        """
        Retrieve the set of numbers that have already been used.
        
        Returns:
            A set of integers representing previously used numbers
        """
        used_numbers = self.redis_client.smembers(self.key_name)
        return {int(num) for num in used_numbers}
    
    def add_used_number(self, number: int) -> bool:
        """
        Add a number to the set of used numbers.
        
        Args:
            number: The number to mark as used
            
        Returns:
            True if the number was newly added, False if it was already in the set
        """
        return bool(self.redis_client.sadd(self.key_name, number))
    
    def is_number_used(self, number: int) -> bool:
        """
        Check if a specific number has been used.
        
        Args:
            number: The number to check
            
        Returns:
            True if the number has been used, False otherwise
        """
        return bool(self.redis_client.sismember(self.key_name, number))
    
    def count_used_numbers(self) -> int:
        """
        Count how many numbers have been used so far.
        
        Returns:
            The count of used numbers
        """
        return self.redis_client.scard(self.key_name)
    
    def clear_used_numbers(self) -> bool:
        """
        Clear all used numbers from the tracking set.
        
        Returns:
            True if the operation was successful
        """
        return bool(self.redis_client.delete(self.key_name))
    
    def reset_if_all_used(self) -> bool:
        """
        Check if all possible numbers in the range have been used and reset if so.
        
        Returns:
            True if a reset was performed, False otherwise
        """
        total_possible = self.max_value - self.min_value + 1
        if self.count_used_numbers() >= total_possible:
            self.clear_used_numbers()
            return True
        return False
    
    def get_next_number(self) -> int:
        """
        Get the next unique random number that hasn't been used.
        
        If all possible numbers have been used, the tracking is reset 
        and any number may be returned.
        
        Returns:
            A random integer within the specified range that hasn't been used before
        """
        self.reset_if_all_used()
        
        while True:
            num = random.randint(self.min_value, self.max_value)
            if not self.is_number_used(num):
                self.add_used_number(num)
                return num
    
    def get_multiple_numbers(self, count: int) -> list:
        """
        Get multiple unique random numbers that haven't been used.
        
        Args:
            count: The number of unique random numbers to generate
            
        Returns:
            A list of unique random integers
        """
        result = []
        for _ in range(count):
            # Check if we need to reset before getting the next number
            self.reset_if_all_used()
            result.append(self.get_next_number())
        return result