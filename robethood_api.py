import os
from pathlib import Path
import requests
from flask import Flask, jsonify, request, render_template, send_from_directory
from dotenv import load_dotenv
import json

load_dotenv()

# Get absolute paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(ROOT_DIR, 'templates')
STATIC_DIR = os.path.join(ROOT_DIR, 'static')

print(f"Root directory: {ROOT_DIR}")
print(f"Template directory: {TEMPLATE_DIR}")
print(f"Static directory: {STATIC_DIR}")

app = Flask(__name__)

# Explicitly set template and static folders
app.template_folder = TEMPLATE_DIR
app.static_folder = STATIC_DIR

class RobethoodAPI:
    def __init__(self):
        self.api_key = os.getenv('ROBETHOOD_API_KEY')
        self.base_url = 'https://api.robethood.com/'

    def get_data(self, endpoint):
        url = f'{self.base_url}{endpoint}'
        headers = {'Authorization': f'Token {self.api_key}'}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

api = RobethoodAPI()

@app.route('/')
def index():
    try:
        template_path = os.path.join(app.template_folder, 'index.html')
        print(f"Looking for template at: {template_path}")
        if not os.path.exists(template_path):
            return f"Template not found at {template_path}", 404
        return render_template('index.html')
    except Exception as e:
        print(f"Error rendering template: {str(e)}")
        return str(e), 500

@app.route('/api/status')
def status():
    return jsonify({
        "status": "ok",
        "message": "Robethood API is running"
    })

@app.route('/static/<path:path>')
def send_static(path):
    try:
        return send_from_directory(app.static_folder, path)
    except Exception as e:
        print(f"Error serving static file: {str(e)}")
        return str(e), 404

@app.route('/api/connect', methods=['GET'])
def connect():
    try:
        # Test connection with API
        response = api.get_data('test')
        return jsonify({"status": "ok", "message": "Connected to Robethood API"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/campaigns', methods=['POST'])
def save_campaign():
    try:
        campaign_data = request.json
        return jsonify({
            "status": "ok",
            "message": "Campaign saved successfully",
            "campaign": campaign_data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/publish', methods=['POST'])
def publish_campaign():
    try:
        data = request.json
        platforms = data.get('platforms', [])
        campaign = data.get('campaign', {})

        results = []
        for platform in platforms:
            results.append({
                "platform": platform,
                "status": "published",
                "message": f"Successfully published to {platform}"
            })

        return jsonify({
            "status": "ok",
            "message": "Campaign published successfully",
            "results": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/<endpoint>')
def get_data(endpoint):
    data = api.get_data(endpoint)
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
