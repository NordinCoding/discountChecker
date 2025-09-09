from functools import wraps
from flask import session, redirect, url_for, render_template
import datetime
import requests
import os

BASE_URL = os.getenv("BASE_URL", "")

def login_required(f):
    '''
    Makes sure certain routes cant be accessed unless user is logged in by checking
    for user_id
    
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(f"{BASE_URL}/login")
        return f(*args, **kwargs)
    return decorated_function


def log_to_file(message, level="INFO", user_id=None):
    '''
    Log a message to a file with timestamps and log levels.
    
    '''

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Use user_id if available to identify specific users in logs
    if user_id:
        user_string = f"User ID: {user_id} - "
    else:
        user_string = f"User ID: None -"
    
    log_entry = f"{timestamp} - {level} - {user_string} {message}\n"
    
    # If log level is error, write error to both files for easier debugging.
    # Otherwise write only to the regular usage logs
    if level == "ERROR":
        with open("scraper_errors.txt", "a", encoding="utf-8") as file:
            file.write(log_entry)
    
    with open("scraper_logs.txt", "a", encoding="utf-8") as file:
        file.write(log_entry)
            
            
def validate_turnsrtile(token, secret, remoteip=None):
    url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
    
    data = {
        'secret': secret,
        'response': token
    }
    
    if remoteip:
        data['remoteip'] = remoteip
        
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log_to_file(f"Turnstile validation error: {e}")
        return {'success': False, 'error-codes': ['internal-error']}