import os
import requests

class RobethoodAPI:
    def __init__(self):
        self.api_key = os.getenv('ROBETHOOD_API_KEY')
        self.base_url = 'https://api.robethood.com/'

    def get_data(self, endpoint):
        url = f'{self.base_url}{endpoint}'
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers=headers)
        return response.json()

# Beispielverwendung:
# api = RobethoodAPI()
# data = api.get_data('dein_endpoint')
# print(data)
