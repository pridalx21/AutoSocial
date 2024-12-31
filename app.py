from flask import Flask, render_template, jsonify, request, send_from_directory, make_response
import os
import requests
from insta_poster import InstagramPoster
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment
ROBETHOOD_API_KEY = os.getenv('ROBETHOOD_API_KEY')
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')
ROBETHOOD_API_URL = os.getenv('ROBETHOOD_API_URL', 'https://api.robethood.com')

logger.debug(f"API URL: {ROBETHOOD_API_URL}")
logger.debug(f"API Key: {ROBETHOOD_API_KEY[:5]}...")  # Only log first 5 characters for security

app = Flask(__name__)

# Instagram API Integration
instagram = InstagramPoster(INSTAGRAM_ACCESS_TOKEN)

def post_to_robethood(campaign_data):
    headers = {
        'Authorization': f'Bearer {ROBETHOOD_API_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        logger.debug(f"Attempting to post to Robethood API: {ROBETHOOD_API_URL}/api/campaigns")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Data: {campaign_data}")
        
        response = requests.post(
            f'{ROBETHOOD_API_URL}/api/campaigns',
            json=campaign_data,
            headers=headers
        )
        
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response content: {response.text}")
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def get_robethood_ads():
    """Hole verfügbare Werbeanzeigen von robethood.com"""
    headers = {
        'Authorization': f'Bearer {ROBETHOOD_API_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        logger.debug(f"Attempting to get ads from Robethood API: {ROBETHOOD_API_URL}/api/ads")
        logger.debug(f"Headers: {headers}")
        
        response = requests.get(
            f'{ROBETHOOD_API_URL}/api/ads',
            headers=headers,
            verify=False  # Deaktiviere SSL-Verifizierung für Entwicklung
        )
        
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response content: {response.text}")
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def post_to_instagram(ad_data):
    """Poste eine Werbeanzeige auf Instagram"""
    try:
        logger.debug(f"Attempting to post to Instagram: {ad_data['image_url']}")
        logger.debug(f"Data: {ad_data}")
        
        return instagram.post_image(
            ad_data['image_url'],
            ad_data['description']
        )
    except Exception as e:
        logger.error(f"Instagram posting error: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/platforms', methods=['GET'])
def get_platforms():
    response = jsonify({
        'platforms': [
            {'id': 'facebook', 'name': 'Facebook'},
            {'id': 'instagram', 'name': 'Instagram'},
            {'id': 'google', 'name': 'Google Ads'}
        ]
    })
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/api/connect', methods=['GET'])
def connect_api():
    try:
        # Test connection to Robethood API
        url = f'{ROBETHOOD_API_URL}/api/status'
        headers = {'Authorization': f'Bearer {ROBETHOOD_API_KEY}'}
        
        logger.debug(f"Attempting to connect to: {url}")
        logger.debug(f"Headers: {headers}")
        
        response = requests.get(
            url,
            headers=headers,
            verify=False,  # Deaktiviere SSL-Verifizierung für Entwicklung
            timeout=10  # Timeout nach 10 Sekunden
        )
        
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response content: {response.text}")
        
        if response.status_code == 200:
            response_data = {'status': 'ok', 'message': 'Successfully connected to Robethood API'}
        else:
            response_data = {
                'status': 'error',
                'message': f'Failed to connect to Robethood API. Status code: {response.status_code}'
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error: {str(e)}")
        response_data = {
            'status': 'error',
            'message': f'Could not connect to Robethood API: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        response_data = {
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }
    
    response = jsonify(response_data)
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/api/campaign', methods=['POST'])
def create_campaign():
    data = request.json
    
    # Post to Robethood
    robethood_response = post_to_robethood(data)
    
    # If Instagram is selected, post to Instagram
    if 'instagram' in data.get('platforms', []):
        try:
            instagram_response = post_to_instagram({
                'image_url': data.get('mediaUrl', ''),
                'description': data.get('adDescription', '')
            })
            if instagram_response.get('status') == 'error':
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to post to Instagram',
                    'details': instagram_response
                })
        except Exception as e:
            logger.error(f"Instagram posting error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Instagram posting error: {str(e)}'
            })
    
    response = jsonify({
        'status': 'success',
        'message': 'Campaign created successfully',
        'data': {
            'robethood': robethood_response,
            'campaign': data
        }
    })
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/api/robethood/ads', methods=['GET'])
def get_ads():
    """API-Endpunkt zum Abrufen der verfügbaren Werbeanzeigen"""
    ads = get_robethood_ads()
    response = jsonify(ads)
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/api/post-ad', methods=['POST'])
def post_ad():
    """API-Endpunkt zum Posten einer ausgewählten Werbeanzeige"""
    data = request.json
    ad_id = data.get('ad_id')
    platforms = data.get('platforms', [])
    
    # Hole die Details der ausgewählten Werbeanzeige
    headers = {
        'Authorization': f'Bearer {ROBETHOOD_API_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        logger.debug(f"Attempting to get ad from Robethood API: {ROBETHOOD_API_URL}/api/ads/{ad_id}")
        logger.debug(f"Headers: {headers}")
        
        ad_response = requests.get(
            f'{ROBETHOOD_API_URL}/api/ads/{ad_id}',
            headers=headers
        )
        
        logger.debug(f"Response status code: {ad_response.status_code}")
        logger.debug(f"Response content: {ad_response.text}")
        
        ad_data = ad_response.json()
        
        results = {'status': 'success', 'platforms': {}}
        
        # Poste auf den ausgewählten Plattformen
        if 'instagram' in platforms:
            instagram_result = post_to_instagram(ad_data)
            results['platforms']['instagram'] = instagram_result
            
        response = jsonify(results)
        response.headers['Content-Type'] = 'application/json'
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error: {str(e)}")
        response = jsonify({'status': 'error', 'message': str(e)})
        response.headers['Content-Type'] = 'application/json'
        return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)
