from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, session
import os
from dotenv import load_dotenv
from scraper import RobethoodScraper
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Setze einen geheimen Schlüssel
scraper = None

# Facebook OAuth-Konfiguration
FACEBOOK_CLIENT_ID = os.getenv('FACEBOOK_CLIENT_ID')
FACEBOOK_CLIENT_SECRET = os.getenv('FACEBOOK_CLIENT_SECRET')
FACEBOOK_REDIRECT_URI = os.getenv('FACEBOOK_REDIRECT_URI')

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

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/facebook_login')
def facebook_login():
    # Redirect to Facebook for authentication
    return redirect(f"https://www.facebook.com/v10.0/dialog/oauth?client_id={FACEBOOK_CLIENT_ID}&redirect_uri={FACEBOOK_REDIRECT_URI}&scope=email")

@app.route('/facebook_callback')
def facebook_callback():
    code = request.args.get('code')
    # Exchange the code for an access token
    token_response = requests.get(f"https://graph.facebook.com/v10.0/oauth/access_token?client_id={FACEBOOK_CLIENT_ID}&redirect_uri={FACEBOOK_REDIRECT_URI}&client_secret={FACEBOOK_CLIENT_SECRET}&code={code}")
    token_info = token_response.json()
    access_token = token_info.get('access_token')

    # Use the access token to get user info
    user_info_response = requests.get(f"https://graph.facebook.com/me?access_token={access_token}&fields=id,name,email")
    user_info = user_info_response.json()

    # Save user info in session or database
    session['user'] = user_info

    return redirect(url_for('dashboard'))  # Redirect to the dashboard or another page

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return f"Willkommen, {session['user']['name']}!"
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)
