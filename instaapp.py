import os
from dotenv import load_dotenv
import requests
# Lade die Umgebungsvariablen
load_dotenv()

# Zugriff auf die Umgebungsvariablen
INSTAGRAM_APP_ID = os.getenv('INSTAGRAM_APP_ID')
INSTAGRAM_APP_SECRET = os.getenv('INSTAGRAM_APP_SECRET')
INSTAGRAM_REDIRECT_URI = os.getenv('INSTAGRAM_REDIRECT_URI')

import base64
from datetime import datetime, timedelta
from functools import wraps
import io
import json
import logging
import os
import secrets
import time

from PIL import Image
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
    jsonify
)
from openai import RateLimitError
from werkzeug.utils import secure_filename

from transformers import pipeline


# Load environment variables from .env file
load_dotenv()
print("OpenAI API Key:", os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a secure random key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Session expires after 1 day
app.config['DEBUG'] = False  # Disable debug mode in production
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size for videos
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login_with_api():  # Ändere den Namen hier
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Benutzername und Passwort sind erforderlich', 'error')
            return redirect(url_for('index'))

        # Instagram API-Integration
        access_token_url = 'https://api.instagram.com/oauth/access_token'  # Definiere die URL hier
        payload = {
            'client_id': INSTAGRAM_APP_ID,
            'client_secret': INSTAGRAM_APP_SECRET,
            'grant_type': 'password',
            'username': username,
            'password': password,
            'redirect_uri': INSTAGRAM_REDIRECT_URI
        }

        response = requests.post(access_token_url, data=payload)
        data = response.json()

        print("Response from Instagram API:", data)  # Debugging-Log

        if response.status_code == 200 and 'access_token' in data:
            session['user_info'] = data  # Speichere die Benutzerinformationen in der Sitzung
            flash('Erfolgreich eingeloggt!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Ungültige Anmeldedaten!', 'error')
            return redirect(url_for('index'))

    return render_template('login.html')

# File Upload Configuration
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a'}

def allowed_file(filename, filetype):
    if not filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if filetype == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif filetype == 'video':
        return ext in ALLOWED_VIDEO_EXTENSIONS
    elif filetype == 'audio':
        return ext in ALLOWED_AUDIO_EXTENSIONS
    return False

# Post Configuration
POST_FORMATS = {
    'feed': {
        'name': 'Feed Post',
        'allowed_media': ['image', 'video'],
        'max_duration': 60, # seconds for video
        'aspect_ratios': ['1:1', '4:5', '16:9']
    },
    'reel': {
        'name': 'Reel',
        'allowed_media': ['video'],
        'max_duration': 90, # seconds
        'aspect_ratio': '9:16'
    },
    'story': {
        'name': 'Story',
        'allowed_media': ['image', 'video'],
        'max_duration': 15, # seconds for video
        'aspect_ratio': '9:16'
    },
    'carousel': {
        'name': 'Carousel',
        'allowed_media': ['image', 'video'],
        'max_items': 10,
        'aspect_ratios': ['1:1', '4:5', '16:9']
    }
}

# Fake user profile for testing
FAKE_PROFILE = {
    'username': 'test_user',
    'full_name': 'Test User',
    'profile_picture_url': 'https://via.placeholder.com/150',
    'bio': 'This is a test profile for local development',
    'media_count': 0,
    'media': {'data': []}
}

def validate_schedule_time(schedule_time):
    try:
        schedule_dt = datetime.fromisoformat(schedule_time)
        now = datetime.now()
        if schedule_dt <= now:
            return False, "Schedule time must be in the future"
        if schedule_dt > now + timedelta(days=30):
            return False, "Cannot schedule posts more than 30 days in advance"
        return True, None
    except ValueError:
        return False, "Invalid datetime format"

def calculate_statistics(posts):
    now = datetime.now()
    stats = {
        'total_posts': len(posts),
        'scheduled_posts': 0,
        'posts_this_month': 0,
        'posts_by_format': {
            'feed': 0,
            'reel': 0,
            'story': 0,
            'carousel': 0
        },
        'posts_by_type': {
            'IMAGE': 0,
            'VIDEO': 0
        },
        'upcoming_posts': [],
        'most_active_day': None,
        'posts_by_weekday': {
            'Montag': 0, 'Dienstag': 0, 'Mittwoch': 0,
            'Donnerstag': 0, 'Freitag': 0, 'Samstag': 0, 'Sonntag': 0
        }
    }

    if not posts:
        return stats

    # Posts by date for finding most active day
    posts_by_date = {}
    weekday_names = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

    for post in posts:
        post_time = datetime.fromisoformat(post['timestamp'])
        
        # Count scheduled posts
        if post_time > now:
            stats['scheduled_posts'] += 1
            if len(stats['upcoming_posts']) < 5:  # Keep only next 5 upcoming posts
                stats['upcoming_posts'].append({
                    'timestamp': post_time,
                    'format': post['post_format'],
                    'type': post['media_type']
                })

        # Count posts this month
        if post_time.year == now.year and post_time.month == now.month:
            stats['posts_this_month'] += 1

        # Count by format
        stats['posts_by_format'][post['post_format']] += 1

        # Count by type
        stats['posts_by_type'][post['media_type']] += 1

        # Track posts by date for most active day
        date_key = post_time.date()
        posts_by_date[date_key] = posts_by_date.get(date_key, 0) + 1

        # Count posts by weekday
        weekday_name = weekday_names[post_time.weekday()]
        stats['posts_by_weekday'][weekday_name] += 1

    # Find most active day
    if posts_by_date:
        most_active_date = max(posts_by_date.items(), key=lambda x: x[1])[0]
        stats['most_active_day'] = {
            'date': most_active_date.strftime('%d.%m.%Y'),
            'count': posts_by_date[most_active_date]
        }

    # Sort upcoming posts by date
    stats['upcoming_posts'].sort(key=lambda x: x['timestamp'])

    return stats

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_info' not in session:
            flash('Bitte melden Sie sich zuerst an', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Funktion zur Generierung von Inhalten mit Hugging Face

def generate_content_with_huggingface(prompt):
    generator = pipeline('text-generation', model='gpt2')  # Beispielmodell, ersetze es durch das gewünschte Modell
    try:
        response = generator(prompt, max_length=100, num_return_sequences=1)
        return response[0]['generated_text']
    except Exception as e:
        print(f'Error generating content: {e}')
        return None

@app.route('/generate_post', methods=['GET', 'POST'])
def generate_post_function():
    if request.method == 'POST':
        prompt = request.form.get('prompt')
        
        for attempt in range(10):  # Try 3 times
            try:
                response = generate_content_with_huggingface(prompt)
                generated_post = response
                return render_template('generate_post.html', generated_post=generated_post)
            except Exception as e:
                return render_template('generate_post.html', error=f"An error occurred: {str(e)}")
    
    return render_template('generate_post.html')

@app.route('/')
def index():
    if 'user_info' not in session:
        session['user_info'] = FAKE_PROFILE.copy()
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    user_info = session.get('user_info', FAKE_PROFILE.copy())
    posts = user_info.get('media', {}).get('data', [])
    
    # Calculate statistics
    statistics = calculate_statistics(posts)
    
    # Pass statistics to the template
    return render_template('dashboard.html', statistics=statistics)

@app.route('/scheduler')
@login_required
def scheduler():
    return render_template('scheduler.html')

@app.route('/schedule_posts', methods=['POST'])
@login_required
def schedule_posts():
    try:
        if 'user_info' not in session:
            flash('Bitte melden Sie sich zuerst an', 'error')
            return redirect(url_for('index'))

        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        captions = request.form.getlist('captions[]')
        schedules = request.form.getlist('schedules[]')
        post_types = request.form.getlist('post_types[]')
        post_formats = request.form.getlist('post_formats[]')
        media_files = request.files.getlist('media[]')
        audio_files = request.files.getlist('audio[]')

        if not all([captions, schedules, post_types, post_formats, media_files]):
            flash('Bitte füllen Sie alle erforderlichen Felder aus', 'error')
            return redirect(url_for('scheduler'))

        if len(captions) != len(schedules) or len(captions) != len(media_files) or len(captions) != len(post_types):
            flash('Ungültige Anzahl von Medien, Bildunterschriften oder Zeitpunkten', 'error')
            return redirect(url_for('scheduler'))

        user_info = session.get('user_info', FAKE_PROFILE.copy())
        if 'media' not in user_info:
            user_info['media'] = {'data': []}

        successful_posts = 0
        for caption, schedule, post_type, post_format, media_file, audio_file in zip(captions, schedules, post_types, post_formats, media_files, audio_files):
            try:
                # Validate schedule time
                schedule_dt = datetime.fromisoformat(schedule)
                now = datetime.now()
                if schedule_dt <= now:
                    flash(f'Zeitpunkt muss in der Zukunft liegen: {schedule}', 'error')
                    continue

                # Validate post format and media type combination
                if post_format not in POST_FORMATS:
                    flash(f'Ungültiges Post-Format: {post_format}', 'error')
                    continue

                format_config = POST_FORMATS[post_format]
                if post_type not in format_config['allowed_media']:
                    flash(f'{format_config["name"]} unterstützt keine {post_type}-Dateien', 'error')
                    continue

                # Validate and save media file
                if not media_file or not allowed_file(media_file.filename, post_type):
                    allowed_types = {
                        'image': ', '.join(ALLOWED_IMAGE_EXTENSIONS),
                        'video': ', '.join(ALLOWED_VIDEO_EXTENSIONS)
                    }
                    flash(f'Ungültiges Dateiformat für {post_type}. Erlaubte Formate: {allowed_types.get(post_type)}', 'error')
                    continue

                # Save media file
                if media_file and media_file.filename:
                    media_filename = secure_filename(media_file.filename)
                    media_filepath = os.path.join(app.config['UPLOAD_FOLDER'], media_filename)
                    try:
                        media_file.save(media_filepath)
                    except Exception as e:
                        logger.error(f'Fehler beim Speichern der Mediendatei: {str(e)}')
                        flash(f'Fehler beim Speichern der Mediendatei: {media_file.filename}', 'error')
                        continue

                # Handle audio file if present
                audio_url = None
                if audio_file and audio_file.filename:
                    if not allowed_file(audio_file.filename, 'audio'):
                        flash(f'Ungültiges Audio-Format. Erlaubte Formate: {", ".join(ALLOWED_AUDIO_EXTENSIONS)}', 'error')
                        continue
                    
                    audio_filename = secure_filename(audio_file.filename)
                    audio_filepath = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
                    try:
                        audio_file.save(audio_filepath)
                        audio_url = url_for('static', filename=f'uploads/{audio_filename}')
                    except Exception as e:
                        logger.error(f'Fehler beim Speichern der Audiodatei: {str(e)}')
                        flash(f'Fehler beim Speichern der Audiodatei: {audio_file.filename}', 'error')
                        continue

                # Add to user media
                new_post = {
                    'id': str(len(user_info['media']['data']) + 1),
                    'caption': caption,
                    'media_type': post_type.upper(),
                    'post_format': post_format,
                    'media_url': url_for('static', filename=f'uploads/{media_filename}'),
                    'thumbnail_url': url_for('static', filename=f'uploads/{media_filename}'),
                    'audio_url': audio_url,
                    'permalink': '#',
                    'timestamp': schedule
                }

                user_info['media']['data'].append(new_post)
                successful_posts += 1

            except Exception as e:
                logger.error(f'Fehler beim Verarbeiten des Posts: {str(e)}')
                flash(f'Fehler beim Verarbeiten eines Posts: {str(e)}', 'error')
                continue

        if successful_posts > 0:
            user_info['media_count'] = len(user_info['media']['data'])
            session['user_info'] = user_info
            flash(f'{successful_posts} {"Post wurde" if successful_posts == 1 else "Posts wurden"} erfolgreich geplant', 'success')
        else:
            flash('Keine Posts konnten geplant werden', 'error')

        return redirect(url_for('dashboard'))

    except Exception as e:
        logger.error(f'Fehler beim Planen der Posts: {str(e)}')
        flash(f'Fehler beim Planen der Posts: {str(e)}', 'error')
        return redirect(url_for('scheduler'))

@app.route('/schedule_post', methods=['POST'])
def schedule_post():
    try:
        logger.debug('Received schedule_post request')
        logger.debug(f'Form data: {request.form}')
        logger.debug(f'Files: {request.files}')
        
        if 'image' not in request.files:
            flash('Kein Bild hochgeladen', 'error')
            return redirect(url_for('scheduler'))

        file = request.files['image']
        if file.filename == '':
            flash('Keine Datei ausgewählt', 'error')
            return redirect(url_for('scheduler'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logger.debug(f'Saving image to: {filepath}')
            file.save(filepath)
            
            if 'user_info' not in session:
                session['user_info'] = FAKE_PROFILE.copy()
            user_info = session['user_info']
            
            # Initialisiere media Dictionary falls es noch nicht existiert
            if 'media' not in user_info:
                user_info['media'] = {'data': []}
            
            caption = request.form.get('caption', '')
            schedule_time = request.form.get('schedule')
            
            # Validate schedule time
            is_valid, error_msg = validate_schedule_time(schedule_time)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('scheduler'))
            
            new_post = {
                'id': str(len(user_info['media']['data']) + 1),
                'caption': caption,
                'media_type': 'IMAGE',
                'media_url': url_for('static', filename=f'uploads/{filename}'),
                'thumbnail_url': url_for('static', filename=f'uploads/{filename}'),
                'permalink': '#',
                'timestamp': schedule_time
            }
            
            user_info['media']['data'].append(new_post)
            user_info['media_count'] = len(user_info['media']['data'])
            session['user_info'] = user_info
            logger.debug('Post added to user_info')

            flash('Beitrag erfolgreich geplant!', 'success')
            return redirect(url_for('dashboard'))

        flash('Ungültiger Dateityp', 'error')
        return redirect(url_for('scheduler'))
        
    except Exception as e:
        logger.error(f'Error in schedule_post: {str(e)}', exc_info=True)
        flash(f'Fehler beim Planen des Beitrags: {str(e)}', 'error')
        return redirect(url_for('scheduler'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Benutzername und Passwort sind erforderlich', 'error')
            return redirect(url_for('index'))

        # Hier sollte die API-Integration zur Überprüfung der Anmeldedaten erfolgen
        # Beispiel: response = requests.post('https://api.instagram.com/oauth/access_token', data={...})
        # Überprüfen, ob die Anmeldedaten gültig sind
        valid_credentials = True  # Platzhalter für die API-Integration
        if valid_credentials:
            session['user_info'] = FAKE_PROFILE.copy()
            flash('Erfolgreich eingeloggt!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Ungültige Anmeldedaten!', 'error')
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sie wurden erfolgreich abgemeldet', 'success')
    return redirect(url_for('login'))

@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum size is 100MB.', 'error')
    return redirect(url_for('scheduler'))

@app.errorhandler(500)
def internal_error(e):
    logger.error(f'Internal Server Error: {str(e)}')
    flash('An internal error occurred. Please try again later.', 'error')
    return redirect(url_for('index'))

@app.route('/data-deletion')
def data_deletion():
    return render_template('data_deletion.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/calendar')
@login_required
def calendar():
    user_info = session.get('user_info', FAKE_PROFILE.copy())
    posts = user_info.get('media', {}).get('data', [])
    
    # Group posts by date for calendar view
    posts_by_date = {}
    for post in posts:
        schedule_time = datetime.fromisoformat(post['timestamp'])
        date_key = schedule_time.date().isoformat()
        if date_key not in posts_by_date:
            posts_by_date[date_key] = []
        posts_by_date[date_key].append({
            **post,
            'time': schedule_time.strftime('%H:%M'),
            'format_name': POST_FORMATS[post['post_format']]['name']
        })

    return render_template('calendar.html', 
                         user_info=user_info,
                         posts_by_date=posts_by_date,
                         current_month=datetime.now().strftime('%Y-%m'))

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/targeting')
@login_required
def targeting():
    return render_template('targeting.html')

@app.route('/api/generate-content', methods=['POST'])
@login_required
def generate_content():
    data = request.json
    
    try:
        # Generate image prompt based on interests and content type
        image_prompt = generate_image_prompt(data)
        
        # Generate image using DALL-E
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # Get the image URL
        image_url = image_response.data[0].url
        
        # Generate caption and hashtags
        content = generate_text_content(data)
        
        return jsonify({
            'imageUrl': image_url,
            'caption': content['caption'],
            'hashtags': content['hashtags']
        })
        
    except Exception as e:
        app.logger.error(f"Error generating content: {str(e)}")
        return jsonify({'error': 'Content generation failed'}), 500

def generate_image_prompt(data):
    # Create a prompt for DALL-E based on user preferences
    prompt_template = f"""Create an engaging Instagram-worthy image for a {data['contentType']} post 
    targeting {data['ageRange']} year olds interested in {', '.join(data['interests'])}.
    The image should be {data['tone']} in style."""
    
    # Get prompt from GPT-4
    response = generate_content_with_huggingface(prompt_template)
    
    return response

def generate_text_content(data):
    # Create engaging caption and hashtags using GPT-4
    prompt = f"""Create an Instagram post caption and hashtags for a {data['contentType']} post 
    targeting {data['ageRange']} year olds interested in {', '.join(data['interests'])}.
    The tone should be {data['tone']}.
    
    Format the response as JSON with two fields:
    1. caption: The main post text
    2. hashtags: An array of relevant hashtags (without the # symbol)"""
    
    response = generate_content_with_huggingface(prompt)
    
    return json.loads(response)

@app.route('/instagram_data')
def instagram_data():
    # Simulierte Instagram-Daten
    instagram_info = {
        'username': 'dein_username',
        'followers': 150,
        'following': 75,
        'posts': 30
    }
    return render_template('instagram_data.html', data=instagram_info)

if __name__ == '__main__':
    app.run(debug=True, port=5001)