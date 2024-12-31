import os
import requests
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

class RobethoodAPI:
    def __init__(self):
        self.api_key = os.getenv('ROBETHOOD_API_KEY')
        self.base_url = 'https://api.robethood.com/'

    def get_data(self, endpoint):
        url = f'{self.base_url}{endpoint}'
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers=headers)
        return response.json()

api = RobethoodAPI()

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Robethood API is running"})

@app.route('/api/<endpoint>')
def get_data(endpoint):
    data = api.get_data(endpoint)
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
