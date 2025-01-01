from flask import Flask, render_template, jsonify, request, send_from_directory
import os
from dotenv import load_dotenv
from scraper import RobethoodScraper
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
scraper = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/connect', methods=['GET'])
def connect_api():
    global scraper
    try:
        if scraper is None:
            scraper = RobethoodScraper()
        
        # Test connection by trying to get ads
        result = scraper.get_ads()
        if result['status'] == 'success':
            response = {'status': 'ok', 'message': 'Successfully connected to Robethood'}
        else:
            response = {'status': 'error', 'message': result['message']}
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        response = {'status': 'error', 'message': f'Could not connect to Robethood: {str(e)}'}
    
    return jsonify(response)

@app.route('/api/ads', methods=['GET'])
def get_ads():
    global scraper
    try:
        if scraper is None:
            scraper = RobethoodScraper()
        
        result = scraper.get_ads()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting ads: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/post-ad', methods=['POST'])
def post_ad():
    data = request.json
    ad_id = data.get('ad_id')
    platforms = data.get('platforms', [])
    
    try:
        # Here you would implement the actual posting logic
        # For now, we'll just return a success message
        return jsonify({
            'status': 'success',
            'message': f'Ad {ad_id} would be posted to platforms: {", ".join(platforms)}'
        })
    except Exception as e:
        logger.error(f"Error posting ad: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)
