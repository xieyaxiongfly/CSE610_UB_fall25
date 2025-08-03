from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import yaml
import os
from datetime import datetime
from functools import wraps
import hashlib

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production

# Configuration
SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SITE_ROOT, '_data')
CONFIG_FILE = os.path.join(SITE_ROOT, '_config.yml')

# Simple authentication (replace with proper auth in production)
ADMIN_PASSWORD = "admin123"  # Change this!

def load_yaml_file(filename):
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return {}

def save_yaml_file(filename, data):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return {}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in request.cookies:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@require_auth
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            response = redirect(url_for('index'))
            response.set_cookie('authenticated', 'true', max_age=3600*24)  # 24 hours
            flash('Login successful!', 'success')
            return response
        else:
            flash('Invalid password!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    response = redirect(url_for('login'))
    response.set_cookie('authenticated', '', expires=0)
    flash('Logged out successfully!', 'success')
    return response

@app.route('/schedule')
@require_auth
def schedule():
    schedule_data = load_yaml_file('course_schedule.yml')
    return render_template('schedule.html', schedule=schedule_data)

@app.route('/schedule/add_lecture', methods=['POST'])
@require_auth
def add_lecture():
    week = int(request.form['week'])
    day = request.form['day']
    topic = request.form['topic']
    
    schedule_data = load_yaml_file('course_schedule.yml')
    
    if 'lectures' not in schedule_data:
        schedule_data['lectures'] = []
    
    # Find or create week entry
    week_entry = None
    for lecture in schedule_data['lectures']:
        if lecture.get('week') == week:
            week_entry = lecture
            break
    
    if week_entry is None:
        week_entry = {'week': week}
        schedule_data['lectures'].append(week_entry)
    
    # Add lecture for the day
    week_entry[day] = {
        'topic': topic,
        'materials': []
    }
    
    save_yaml_file('course_schedule.yml', schedule_data)
    flash(f'Added lecture for Week {week}, {day.title()}!', 'success')
    return redirect(url_for('schedule'))

@app.route('/schedule/add_material', methods=['POST'])
@require_auth
def add_material():
    week = int(request.form['week'])
    day = request.form['day']
    material_name = request.form['material_name']
    material_url = request.form['material_url']
    
    schedule_data = load_yaml_file('course_schedule.yml')
    
    # Find the lecture
    for lecture in schedule_data.get('lectures', []):
        if lecture.get('week') == week and day in lecture:
            if 'materials' not in lecture[day]:
                lecture[day]['materials'] = []
            lecture[day]['materials'].append({
                'name': material_name,
                'url': material_url
            })
            break
    
    save_yaml_file('course_schedule.yml', schedule_data)
    flash(f'Added material to Week {week}, {day.title()}!', 'success')
    return redirect(url_for('schedule'))

@app.route('/people')
@require_auth
def people():
    people_data = load_yaml_file('people.yml')
    return render_template('people.html', people=people_data)

@app.route('/people/add_instructor', methods=['POST'])
@require_auth
def add_instructor():
    instructor_data = {
        'name': request.form['name'],
        'title': request.form['title'],
        'email': request.form['email'],
        'office': request.form['office'],
        'office_hours': request.form['office_hours'],
        'webpage': request.form['webpage'],
        'profile_pic': request.form['profile_pic']
    }
    
    people_data = load_yaml_file('people.yml')
    if 'instructors' not in people_data:
        people_data['instructors'] = []
    
    people_data['instructors'].append(instructor_data)
    save_yaml_file('people.yml', people_data)
    flash('Instructor added successfully!', 'success')
    return redirect(url_for('people'))

@app.route('/people/add_ta', methods=['POST'])
@require_auth
def add_ta():
    ta_data = {
        'name': request.form['name'],
        'email': request.form['email'],
        'office_hours': request.form['office_hours'],
        'profile_pic': request.form.get('profile_pic', ''),
        'webpage': request.form.get('webpage', ''),
        'bio': request.form.get('bio', '')
    }
    
    people_data = load_yaml_file('people.yml')
    if 'teaching_assistants' not in people_data:
        people_data['teaching_assistants'] = []
    
    people_data['teaching_assistants'].append(ta_data)
    save_yaml_file('people.yml', people_data)
    flash('Teaching Assistant added successfully!', 'success')
    return redirect(url_for('people'))

@app.route('/config')
@require_auth
def config():
    config_data = load_config()
    return render_template('config.html', config=config_data)

@app.route('/config/update', methods=['POST'])
@require_auth
def update_config():
    config_data = load_config()
    
    config_data['course_name'] = request.form['course_name']
    config_data['course_description'] = request.form['course_description']
    config_data['course_semester'] = request.form['course_semester']
    config_data['baseurl'] = request.form['baseurl']
    config_data['url'] = request.form['url']
    config_data['schoolname'] = request.form['schoolname']
    config_data['schoolurl'] = request.form['schoolurl']
    config_data['logo_path'] = request.form.get('logo_path', '/_images/logo.png')
    config_data['logo_width'] = int(request.form.get('logo_width', 75))
    
    save_config(config_data)
    flash('Configuration updated successfully!', 'success')
    return redirect(url_for('config'))

@app.route('/schedule/delete_lecture', methods=['POST'])
@require_auth
def delete_lecture():
    week = int(request.form['week'])
    day = request.form['day']
    
    schedule_data = load_yaml_file('course_schedule.yml')
    
    for lecture in schedule_data.get('lectures', []):
        if lecture.get('week') == week and day in lecture:
            del lecture[day]
            # Remove week entry if it's empty
            if len(lecture) == 1:  # Only 'week' key remains
                schedule_data['lectures'].remove(lecture)
            break
    
    save_yaml_file('course_schedule.yml', schedule_data)
    flash(f'Deleted lecture for Week {week}, {day.title()}!', 'success')
    return redirect(url_for('schedule'))

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=8080)