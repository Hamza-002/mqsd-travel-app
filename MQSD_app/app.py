"""
MQSD - Discover the Kingdom
A Flask web application for planning and managing trips in Saudi Arabia.
"""
import json
import os
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_file
from werkzeug.exceptions import HTTPException
import openai
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import logging
from bson.objectid import ObjectId
from dotenv import load_dotenv
import pymongo
import base64
from MQSD_app.models import User
from PIL import Image
from io import BytesIO
from werkzeug.utils import secure_filename
from flask import stream_with_context, Response
from flask_mail import Mail, Message
import random

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Configuration
app.secret_key = os.getenv('SECRET_KEY')
print("MONGO_URI =", os.getenv('MONGO_URI'))

app.config["MONGO_URI"] = os.getenv('MONGO_URI')
app.config['SESSION_PROTECTION'] = 'strong'
app.config['WTF_CSRF_ENABLED'] = False  # Temporarily disable CSRF for debugging
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME') or 'hamzajereb00@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD') or 'zwah kdlx qphx dnvq'
openai.api_key = os.getenv("OPENAI_API_KEY")

#hamza_worked on the whole website alone

# MongoDB Configuration
mongo = PyMongo(app)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create MongoDB indexes
with app.app_context():
    mongo.db.users.create_index([('email', pymongo.ASCENDING)], unique=True)
    mongo.db.trips.create_index([('user_id', pymongo.ASCENDING)])

# Flask-Mail configuration
mail = Mail(app)

# OTP utility
def generate_otp():
    return str(random.randint(100000, 999999))

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    return User(user_data) if user_data else None

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = mongo.db.users.find_one({'email': email})
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data)
            login_user(user)
            
            # If there's a trip in session, save it to the user's account
            if 'trip_data' in session:
                trip_data = session['trip_data']
                trip_data['user_id'] = ObjectId(user.id)
                trip_data['created_at'] = datetime.now()
                trip_id = mongo.db.trips.insert_one(trip_data).inserted_id
                mongo.db.users.update_one(
                    {'_id': ObjectId(user.id)},
                    {'$push': {'trips': trip_id}}
                )
                session.pop('trip_data', None)
                return redirect(url_for('trip_details', trip_id=trip_id))
            
            # If no trip in session, go to account page
            return redirect(url_for('account'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Password validation
        if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
            flash('Password must be at least 8 characters and contain a number and uppercase letter', 'error')
            return redirect(url_for('signup'))
        
        try:
            user_data = {
                'email': email,
                'password_hash': generate_password_hash(password),
                'full_name': request.form.get('full_name'),
                'location': request.form.get('location'),
                'preferred_cities': request.form.getlist('preferred_cities'),
                'interests': request.form.getlist('interests'),
                'languages': request.form.getlist('languages'),
                'trips': [],
                'created_at': datetime.now()
            }
            # OTP logic
            otp = generate_otp()
            session['otp'] = otp
            session['pending_user'] = user_data
            msg = Message('Your MQSD Verification Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Your OTP is: {otp}'  # Fallback for non-HTML clients
            logo_url = url_for('static', filename='images/logo_black_green.svg', _external=True)
            msg.html = f'''
                <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px; background: #f8f9fa; border-radius: 12px;">
                    <div style="text-align: center; margin-bottom: 24px;">
                        <img src="{logo_url}" alt="MQSD Logo" style="height: 48px;">
                    </div>
                    <h2 style="color: #00A651; text-align: center;">Email Verification</h2>
                    <p style="font-size: 1.1rem; color: #333; text-align: center;">
                        Hello,<br>
                        Thank you for signing up for <b>MQSD</b>!<br>
                        Please use the following code to verify your email address:
                    </p>
                    <div style="font-size: 2.2rem; font-weight: bold; color: #00A651; text-align: center; margin: 24px 0;">
                        {otp}
                    </div>
                    <p style="color: #555; text-align: center;">
                        This code will expire soon. If you did not request this, please ignore this email.
                    </p>
                    <div style="text-align: center; color: #aaa; font-size: 0.95rem; margin-top: 32px;">
                        &copy; 2024 MQSD. All rights reserved.
                    </div>
                </div>
            '''
            mail.send(msg)
            return redirect(url_for('verify_otp'))
        except pymongo.errors.DuplicateKeyError:
            flash('Email already exists', 'error')
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# OTP verification routes
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        if user_otp == session.get('otp'):
            user_data = session.get('pending_user')
            if user_data:
                user_id = mongo.db.users.insert_one(user_data).inserted_id
                user = User(mongo.db.users.find_one({'_id': user_id}))
                login_user(user)
                session.pop('otp', None)
                session.pop('pending_user', None)
                return redirect(url_for('account'))
            else:
                flash('Session expired. Please sign up again.', 'error')
                return redirect(url_for('signup'))
        else:
            flash('Invalid OTP. Please try again.', 'error')
    return render_template('verify_otp.html')

# Modified submit-onboarding route
@app.route('/submit-onboarding', methods=['POST'])
def submit_onboarding():
    try:
        # Get JSON data from request
        json_data = request.get_json()
        
        trip_data = {
            'location': json_data.get('location'),
            'date_in': json_data.get('date_in'),
            'date_out': json_data.get('date_out'),
            'adults': json_data.get('adults'),
            'children': json_data.get('children'),
            'trip_type': json_data.get('trip_type'),
            'budget_type': json_data.get('budget_type'),
            'preferences': json_data.get('preferences'),
            'created_at': datetime.now()
        }

        # Generate AI itinerary
        prompt = f"""
        Create a detailed {trip_data['trip_type']} travel itinerary in JSON format for a trip to {trip_data['location']} 
        from {trip_data['date_in']} to {trip_data['date_out']} ({calculate_days(trip_data['date_in'], trip_data['date_out'])} days).

        Travel party: {trip_data['adults']} adults and {trip_data['children']} children
        Budget level: {trip_data['budget_type']}
        Preferences: {trip_data.get('preferences', 'None')}

        IMPORTANT: 
        - The itinerary must cover ALL days of the trip from arrival to departure.
        - Each activity MUST include BOTH:
          1. A "google_maps_link" field like: "https://www.google.com/maps/search/?api=1&query=Activity+Name+in+City"
          2. A "coordinates" field with real geographic coordinates for the actual location

        Format requirements:
        {{
        "location": "City Name",
        "trip_duration": "X days",
        "itinerary": [
            {{
            "day_number": 1,
            "date": "YYYY-MM-DD",
            "activities": [
                {{
                "time": "08:00 AM",
                "title": "Activity name",
                "description": "Detailed description",
                "duration": "2 hours",
                "type": "sightseeing/dining/leisure",
                "coordinates": [46.6753, 24.7136],
                "google_maps_link": "https://www.google.com/maps/search/?api=1&query=Activity+Name+in+City"
                }}
            ]
            }}
        ]
        }}

        NOTES:
        - Use real coordinates for each location (example above shows Riyadh coordinates)
        - Longitude range: -180 to 180
        - Latitude range: -90 to 90
        - Each activity should have unique, accurate coordinates for its specific location
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            ai_reply = response["choices"][0]["message"]["content"]
            itinerary_data = json.loads(ai_reply)

            # Verify and handle coordinates for each activity
            for day in itinerary_data.get("itinerary", []):
                for activity in day.get("activities", []):
                    # Initialize default coordinates for Riyadh
                    default_coords = [46.6753, 24.7136]
                    
                    # Handle coordinates
                    try:
                        if "coordinates" not in activity or not activity["coordinates"]:
                            logging.warning(f"Missing coordinates for activity: {activity.get('title')}")
                            activity["coordinates"] = default_coords
                        else:
                            # Validate coordinate ranges
                            longitude, latitude = activity["coordinates"]
                            if not (isinstance(longitude, (int, float)) and isinstance(latitude, (int, float))):
                                logging.error(f"Invalid coordinate types for activity: {activity.get('title')}")
                                activity["coordinates"] = default_coords
                            elif not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                                logging.error(f"Coordinates out of range for activity: {activity.get('title')}")
                                activity["coordinates"] = default_coords
                    except (TypeError, ValueError) as e:
                        logging.error(f"Error processing coordinates for activity {activity.get('title')}: {str(e)}")
                        activity["coordinates"] = default_coords

                    # Ensure all required fields exist with defaults if needed
                    activity["title"] = activity.get("title", "Untitled Activity")
                    activity["description"] = activity.get("description", "")
                    activity["time"] = activity.get("time", "No time specified")
                    activity["duration"] = activity.get("duration", "Duration not specified")
                    activity["type"] = activity.get("type", "activity")
                    
                    # Handle Google Maps link
                    if not activity.get("google_maps_link"):
                        title = activity["title"].replace(" ", "+")
                        city = trip_data["location"].replace(" ", "+")
                        activity["google_maps_link"] = f"https://www.google.com/maps/search/?api=1&query={title}+in+{city}"

            trip_data['ai_itinerary'] = itinerary_data

        except json.JSONDecodeError as e:
            logging.error(f"Error parsing AI response: {str(e)}\nResponse: {ai_reply}")
            trip_data['ai_itinerary'] = None
            return jsonify({'success': False, 'error': 'Invalid AI response format'}), 400
        except Exception as e:
            logging.error(f"Error processing AI response: {str(e)}")
            trip_data['ai_itinerary'] = None
            return jsonify({'success': False, 'error': 'Error processing AI response'}), 400

        try:
            if current_user.is_authenticated:
                # Save to MongoDB
                trip_data['user_id'] = ObjectId(current_user.id)
                trip_id = mongo.db.trips.insert_one(trip_data).inserted_id
                mongo.db.users.update_one(
                    {'_id': ObjectId(current_user.id)},
                    {'$push': {'trips': trip_id}}
                )
                # Redirect to trip details after creation
                return jsonify({'success': True, 'redirect': url_for('trip_details', trip_id=trip_id)})
            else:
                # Store in session for non-authenticated users
                session['trip_data'] = trip_data

            # Return success response
            return jsonify({'success': True, 'redirect': url_for('trip_dashboard')})

        except Exception as e:
            logging.error(f"Error saving trip: {str(e)}")
            return jsonify({'success': False, 'error': 'Error saving trip data'}), 400

    except Exception as e:
        logging.error(f"Error saving trip: {str(e)}")
        return jsonify({'success': False, 'error': 'Error saving trip data'}), 400


def calculate_days(date_in, date_out):
    """Calculate the number of days between two dates"""
    try:
        fmt = "%Y-%m-%d"
        d1 = datetime.strptime(date_in, fmt)
        d2 = datetime.strptime(date_out, fmt)
        return abs((d2 - d1).days) + 1  # +1 to include both start and end days
    except:
        return 0
@app.route('/trip-dashboard')
def trip_dashboard():
    try:
        if current_user.is_authenticated:
            # Get user's trips from MongoDB
            user_trips = list(mongo.db.trips.find({'user_id': ObjectId(current_user.id)}))
            return render_template('trip-dashboard.html', trips=user_trips, is_authenticated=True)
        else:
            # For non-authenticated users, get trip from session
            trip = session.get('trip_data')
            if not trip:
                flash("No trip data found. Please start again.", "error")
                return redirect(url_for('index'))

            # Create AI itinerary if not already in session
            if 'ai_itinerary' not in session:
                prompt = f"""
                Create a detailed {trip['trip_type']} travel itinerary in JSON format for a trip to {trip['location']} 
                from {trip['date_in']} to {trip['date_out']} ({calculate_days(trip['date_in'], trip['date_out'])} days).
                ...
                Preferences: {trip.get('preferences', 'None')}

                IMPORTANT: 
                - The itinerary must cover ALL days of the trip from arrival to departure.
                - Each activity MUST include BOTH:
                  1. A "google_maps_link" field like: "https://www.google.com/maps/search/?api=1&query=Activity+Name+in+City"
                  2. A "coordinates" field with [longitude, latitude] for precise location

                Format:
                {{
                "location": "City Name",
                "trip_duration": "X days",
                "itinerary": [
                    {{
                    "day_number": 1,
                    "date": "YYYY-MM-DD",
                    "activities": [
                        {{
                        "time": "08:00 AM",
                        "title": "Activity name",
                        "description": "Detailed description",
                        "duration": "2 hours",
                        "type": "sightseeing/dining/leisure",
                        "coordinates": [longitude, latitude],
                        "google_maps_link": "https://www.google.com/maps/search/?api=1&query=Activity+Name+in+City"
                        }}
                    ]
                    }}
                ]
                }}
                """

                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )

                try:
                    ai_reply = response["choices"][0]["message"]["content"]
                    itinerary_data = json.loads(ai_reply)

                    # Verify and handle coordinates for each activity
                    for day in itinerary_data.get("itinerary", []):
                        for activity in day.get("activities", []):
                            # Initialize default coordinates for Riyadh
                            default_coords = [46.6753, 24.7136]
                            
                            # Handle coordinates
                            try:
                                if "coordinates" not in activity or not activity["coordinates"]:
                                    logging.warning(f"Missing coordinates for activity: {activity.get('title')}")
                                    activity["coordinates"] = default_coords
                                else:
                                    # Validate coordinate ranges
                                    longitude, latitude = activity["coordinates"]
                                    if not (isinstance(longitude, (int, float)) and isinstance(latitude, (int, float))):
                                        logging.error(f"Invalid coordinate types for activity: {activity.get('title')}")
                                        activity["coordinates"] = default_coords
                                    elif not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                                        logging.error(f"Coordinates out of range for activity: {activity.get('title')}")
                                        activity["coordinates"] = default_coords
                            except (TypeError, ValueError) as e:
                                logging.error(f"Error processing coordinates for activity {activity.get('title')}: {str(e)}")
                                activity["coordinates"] = default_coords

                            # Ensure all required fields exist with defaults if needed
                            activity["title"] = activity.get("title", "Untitled Activity")
                            activity["description"] = activity.get("description", "")
                            activity["time"] = activity.get("time", "No time specified")
                            
                            # Handle Google Maps link
                            if not activity.get("google_maps_link"):
                                title = activity["title"].replace(" ", "+")
                                city = trip_data["location"].replace(" ", "+")
                                activity["google_maps_link"] = f"https://www.google.com/maps/search/?api=1&query={title}+in+{city}"

                    session['ai_itinerary'] = itinerary_data

                except (json.JSONDecodeError, KeyError) as e:
                    logging.error(f"Error parsing AI response: {str(e)}")
                    itinerary_data = None
            else:
                itinerary_data = session.get('ai_itinerary')

            return render_template('trip-dashboard.html', 
                                trip=trip, 
                                itinerary=itinerary_data, 
                                is_authenticated=False)
    except Exception as e:
        logging.error(f"Error in trip dashboard: {str(e)}")
        flash('Error loading trip dashboard', 'error')
        return redirect(url_for('index'))

@app.route('/save-trip-file')
def save_trip_file():
    """Save trip data to JSON file for non-authenticated users."""
    try:
        trip_data = session.get('trip_data')
        if not trip_data:
            return jsonify({"error": "No trip data found"}), 404

        # Add AI itinerary if available
        trip_data['ai_itinerary'] = session.get('ai_itinerary')
        
        # Generate unique filename
        trip_id = f"trip_{int(time.time())}_{trip_data['location'].lower().replace(' ', '_')}"
        
        # Ensure temp directory exists
        if not os.path.exists('temp'):
            os.makedirs('temp')
            
        # Save to file
        filename = f"temp/{trip_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(trip_data, f, indent=2, ensure_ascii=False)
            
        return send_file(filename, 
                        as_attachment=True,
                        download_name=f"{trip_id}.json",
                        mimetype='application/json')
    except Exception as e:
        logging.error(f"Error saving trip file: {str(e)}")
        return jsonify({"error": "Failed to save trip"}), 500

# General error handler
@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    logging.error(f"Server Error: {str(e)}")
    return jsonify(error="Internal server error"), 500

# Template filters
@app.template_filter('datetime')
def parse_datetime(date_str):
    """Convert date string to datetime object"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return datetime.now()  # fallback to current date if invalid

@app.template_filter('strftime')
def format_datetime(value, format='%Y-%m-%d'):
    """Format a datetime object."""
    if value is None:
        return ""
    return value.strftime(format)

@app.template_global()
def date_range(start_date, end_date):
    """Generate a range of dates between start and end date"""
    days = []
    try:
        current_date = start_date
        while current_date <= end_date:
            days.append(current_date)
            current_date += timedelta(days=1)
    except (ValueError, TypeError):
        # Return empty list if dates are invalid
        pass
    return days

# Helper function to generate unique trip IDs
def generate_trip_id(location):
    return f"trip_{int(time.time())}_{location.lower().replace(' ', '_')}"

# Home and Search Routes
@app.route('/')
def index():
    """Render the home page with search functionality."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search form submission and redirect to onboarding."""
    try:
        # Get form data
        location = request.form.get('location')
        date_in = request.form.get('date_in')
        date_out = request.form.get('date_out')
        adults = request.form.get('adults', '1')
        children = request.form.get('children', '0')

        # Validate required fields
        if not all([location, date_in, date_out]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('index'))

        # Redirect to trip onboarding with parameters
        return redirect(url_for('trip_onboarding',
                              location=location,
                              date_in=date_in,
                              date_out=date_out,
                              adults=adults,
                              children=children))
    except Exception as e:
        flash('An error occurred during search', 'error')
        return redirect(url_for('index'))

# Trip Onboarding Routes
@app.route('/trip-onboarding')
def trip_onboarding():
    """First step - trip type selection."""
    try:
        # Get parameters from URL
        location = request.args.get('location')
        date_in = request.args.get('date_in')
        date_out = request.args.get('date_out')
        adults = request.args.get('adults', '1')
        children = request.args.get('children', '0')

        if not all([location, date_in, date_out]):
            flash('Missing trip parameters', 'error')
            return redirect(url_for('index'))

        return render_template('trip-onboarding.html',
                             location=location,
                             date_in=date_in,
                             date_out=date_out,
                             adults=adults,
                             children=children)
    except Exception as e:
        flash('Error loading onboarding', 'error')
        return redirect(url_for('index'))

@app.route('/trip-onboarding-2')
def trip_onboarding_2():
    """Second step - budget selection."""
    location = request.args.get('location')
    date_in = request.args.get('date_in')
    date_out = request.args.get('date_out')
    adults = request.args.get('adults')
    children = request.args.get('children')
    trip_type = request.args.get('trip_type')

    return render_template('trip-onboarding-2.html',
                         location=location,
                         date_in=date_in,
                         date_out=date_out,
                         adults=adults,
                         children=children,
                         trip_type=trip_type)

@app.route('/trip-onboarding-3')
def trip_onboarding_3():
    """Third step - preferences selection."""
    location = request.args.get('location')
    date_in = request.args.get('date_in')
    date_out = request.args.get('date_out')
    adults = request.args.get('adults')
    children = request.args.get('children')
    trip_type = request.args.get('trip_type')
    budget_type = request.args.get('budget_type')

    return render_template('trip-onboarding-3.html',
                         location=location,
                         date_in=date_in,
                         date_out=date_out,
                         adults=adults,
                         children=children,
                         trip_type=trip_type,
                         budget_type=budget_type)

@app.route('/trip-onboarding-4')
def trip_onboarding_4():
    """Fourth step - review and confirmation."""
    location = request.args.get('location')
    date_in = request.args.get('date_in')
    date_out = request.args.get('date_out')
    adults = request.args.get('adults')
    children = request.args.get('children')
    trip_type = request.args.get('trip_type')
    budget_type = request.args.get('budget_type')
    preferences = request.args.get('preferences')

    return render_template('trip-onboarding-4.html',
                         location=location,
                         date_in=date_in,
                         date_out=date_out,
                         adults=adults,
                         children=children,
                         trip_type=trip_type,
                         budget_type=budget_type,
                         preferences=preferences)

# Trip Saving and Management
@app.route('/save-trip', methods=['POST'])
def save_trip():
    """Save trip data to JSON file."""
    try:
        trip_data = request.json
        
        # Validate required data
        if not all(key in trip_data for key in ['location', 'date_in', 'date_out']):
            return jsonify({"status": "error", "message": "Missing required trip data"}), 400
        
        # Add metadata
        trip_data['created_at'] = datetime.now().isoformat()
        trip_id = generate_trip_id(trip_data['location'])
        trip_data['trip_id'] = trip_id
        
        # Save to JSON file
        filename = f"temp/{trip_id}.json"
        with open(filename, 'w') as f:
            json.dump(trip_data, f, indent=2)
        
        # Store in session
        session['trip_data'] = trip_data
        
        return jsonify({
            "status": "success",
            "message": "Trip saved successfully",
            "trip_id": trip_id,
            "data": trip_data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to save trip: {str(e)}"
        }), 500

@app.route('/trip-complete')
def trip_complete():
    """Display trip completion confirmation."""
    return render_template('trip-complete.html')

# Information Routes
@app.route('/cities')
def cities():
    """Display list of available cities."""
    return render_template('destinations.html')

@app.route('/city/<city_name>')
def city(city_name):
    """Display city information page."""
    # Security: Basic sanitization
    safe_city = ''.join(c for c in city_name if c.isalnum() or c in ('-', '_'))
    template_path = f'cities/{safe_city}.html'
    
    if not os.path.exists(os.path.join('templates', template_path)):
        flash('City not found', 'error')
        return redirect(url_for('cities'))
    
    return render_template(template_path)

@app.route('/about-saudi')
def about_saudi():
    """Display about Saudi Arabia page."""
    return render_template('about-saudi.html')

# User Account Routes
@app.route('/account')
@login_required
def account():
    """Display account page."""
    user_data = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    return render_template('account.html', user=user_data)


@app.route('/settings')
def settings():
    """Display settings page."""
    return render_template('settings.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        # Get form data
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        location = request.form.get('location')
        
        # Validate required fields
        if not full_name:
            return jsonify({'status': 'error', 'message': 'Full name is required'}), 400
        
        # Handle list fields by splitting comma-separated strings
        preferred_cities = [city.strip() for city in request.form.get('preferred_cities', '').split(',') if city.strip()]
        interests = [interest.strip() for interest in request.form.get('interests', '').split(',') if interest.strip()]
        languages = [language.strip() for language in request.form.get('languages', '').split(',') if language.strip()]
        
        # Update user document in MongoDB
        update_data = {
            'full_name': full_name,
            'phone': phone,
            'location': location,
            'preferred_cities': preferred_cities,
            'interests': interests,
            'languages': languages
        }
        
        # Use ObjectId for MongoDB query
        result = mongo.db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': update_data}
        )
        
        if result.modified_count == 0:
            return jsonify({'status': 'error', 'message': 'No changes were made'}), 400
        
        # Get the updated user data and refresh current_user
        user_data = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
        if user_data:
            # Update the current_user's attributes directly
            current_user._full_name = user_data.get('full_name')
            current_user._location = user_data.get('location')
            current_user._preferred_cities = user_data.get('preferred_cities', [])
            current_user._interests = user_data.get('interests', [])
            current_user._languages = user_data.get('languages', [])
        
        return jsonify({
            'status': 'success',
            'message': 'Profile updated successfully',
            'data': update_data
        })
        
    except Exception as e:
        app.logger.error(f"Error updating profile: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error updating profile: {str(e)}'
        }), 500

# Error Handling
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(file, max_size=(500, 500)):
    try:
        image = Image.open(file)
        image = image.convert('RGB')
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=85, optimize=True)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    except Exception as e:
        app.logger.error(f"Error processing image: {str(e)}")
        return None

@app.route('/upload-header-image', methods=['POST'])
@login_required
def upload_header_image():
    if 'header_image' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('account'))
    
    file = request.files['header_image']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('account'))
    
    if file and allowed_file(file.filename):
        try:
            # Open and resize image
            image = Image.open(file)
            image = image.convert('RGB')  # Convert to RGB if needed
            
            # Resize to a reasonable size for header (e.g., 1920x400)
            image.thumbnail((1920, 400), Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Update user in database
            mongo.db.users.update_one(
                {'_id': ObjectId(current_user.id)},
                {'$set': {'header_image': img_str}}
            )
            
            flash('Header image updated successfully', 'success')
        except Exception as e:
            app.logger.error(f"Error processing image: {str(e)}")
            flash('Error processing image', 'error')
    else:
        flash('Invalid file type. Please use PNG, JPG, or GIF', 'error')
    
    return redirect(url_for('account'))

@app.route('/update-theme', methods=['POST'])
@login_required
def update_theme():
    theme = request.form.get('theme')
    if theme in ['solid_blue', 'gradient_green', 'pattern_geometric']:
        try:
            mongo.db.users.update_one(
                {'_id': ObjectId(current_user.id)},
                {'$set': {'profile_theme': theme}}
            )
            flash('Theme updated successfully', 'success')
        except Exception as e:
            app.logger.error(f"Error updating theme: {str(e)}")
            flash('Error updating theme', 'error')
    else:
        flash('Invalid theme selected', 'error')
    
    return redirect(url_for('account'))

@app.route('/trip/<trip_id>')
def trip_details(trip_id):
    """View detailed itinerary for a specific trip."""
    try:
        # Get the Mapbox token from environment
        mapbox_token = os.getenv('MAPBOX_TOKEN')
        
        if current_user.is_authenticated:
            # For authenticated users, fetch trip from MongoDB
            trip = mongo.db.trips.find_one({'_id': ObjectId(trip_id)})
            if not trip:
                flash('Trip not found', 'error')
                return redirect(url_for('trip_dashboard'))
            
            # Get itinerary from trip data
            itinerary = trip.get('ai_itinerary')
        else:
            # For non-authenticated users, get trip from session
            trip = session.get('trip_data')
            itinerary = session.get('ai_itinerary')
            if not trip:
                flash('No trip data found', 'error')
                return redirect(url_for('index'))

        return render_template('trip-details.html', 
                            trip=trip, 
                            itinerary=itinerary,
                            is_authenticated=bool(current_user.is_authenticated),
                            mapbox_token=mapbox_token)
    except Exception as e:
        logging.error(f"Error viewing trip details: {str(e)}")
        flash('Error loading trip details', 'error')
        return redirect(url_for('trip_dashboard'))

@app.route('/chat')
def chat_page():
    """Serve the Travel Assistant chat page."""
    return render_template('chat.html')

@app.route('/chat/message', methods=['POST'])
def chat_message():
    user_msg = request.json.get('message', '').strip()
    if not user_msg:
        return jsonify({'error': 'No message provided'}), 400

    # Forbidden keywords for out-of-scope topics
    forbidden_keywords = ['disney', 'universal', 'eiffel', 'busch gardens', 'tokyo', 'orlando', 'london', 'paris']
    if any(word in user_msg.lower() for word in forbidden_keywords):
        return jsonify({'error': 'This assistant only supports locations within Saudi Arabia. Please ask about a Saudi destination.'}), 400

    def generate():
        # Strict, clean system prompt for formatting and focus
        system_prompt = """
You are a travel assistant specialized in Saudi Arabia tourism. Your task is to help users plan personalized travel experiences and generate clearly formatted, organized daily itineraries.

🚫 Do not mention or recommend any destinations outside of Saudi Arabia.
✅ Always format responses in an easy-to-read structure using markdown-style formatting:
- Use headings like ## or ### for sections
- Use bullet points and short, clear descriptions
- Break information into separate days

### Example Output:

## 🗓️ 3-Day Itinerary for Riyadh

### Day 1: History & Culture
- **King Abdulaziz Historical Center** – Discover Saudi heritage.
- **Al Bujairi Heritage Park** – Traditional lunch and scenic views.
- **Dinner at Najd Village** – Authentic Saudi cuisine.

### Day 2: Shopping & Architecture
- **Al-Masmak Fortress** – Historic mud-brick fort.
- **Souq Al Zal** – Traditional marketplace.
- **The Globe Restaurant** – Dining with panoramic city views.

### Day 3: Nature & Relaxation
- **Edge of the World** – Stunning desert cliffs outside Riyadh.
- **Spa afternoon** – Relax at your luxury hotel.
- **Dinner at Spazio 77** – Gourmet dining with a view.

## 🛏️ Accommodation Suggestions
- **The Ritz-Carlton, Riyadh**
- **Four Seasons Hotel Riyadh**

## 💡 Travel Tips
- Respect local customs and dress codes
- Book attractions and dining in advance
- Be mindful of prayer times

Only respond with Saudi-based destinations. If a user asks about international places, gently inform them and suggest local alternatives instead.
"""

        chat_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=chat_history,
            temperature=0.7,
            stream=True
        )

        ai_response = ""
        for chunk in response:
            delta = chunk.choices[0].delta.get('content', '')
            ai_response += delta
            yield delta

        # Post-filter: replace response if hallucinated forbidden content appears
        if any(bad in ai_response.lower() for bad in forbidden_keywords):
            yield "\n\nSorry, I can only recommend places within Saudi Arabia. Please ask about a Saudi destination."

    return Response(stream_with_context(generate()), content_type='text/plain')

@app.route("/test-openai")
def test_openai():
    try:
        import openai
        from openai import OpenAIError

        # Ensure API key is picked up
        api_key = openai.api_key or os.getenv("OPENAI_API_KEY")

        if not api_key:
            return {"status": "fail", "error": "API key not found in environment."}, 500

        # Simple request to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        )

        return {"status": "success", "response": response["choices"][0]["message"]["content"]}

    except openai.error.RateLimitError as e:
        return {"status": "fail", "error": "Rate limit exceeded", "details": str(e)}, 429

    except openai.error.AuthenticationError as e:
        return {"status": "fail", "error": "Authentication failed", "details": str(e)}, 401

    except Exception as e:
        return {"status": "fail", "error": "Unexpected error", "details": str(e)}, 500



if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host='127.0.0.1', port=5000)