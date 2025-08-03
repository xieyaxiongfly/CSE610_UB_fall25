from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import yaml
import os
from datetime import datetime
from functools import wraps
import hashlib
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production

# Configuration
SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SITE_ROOT, '_data')
CONFIG_FILE = os.path.join(SITE_ROOT, '_config.yml')
UPLOAD_DIR = os.path.join(SITE_ROOT, 'static_files', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx', 'doc', 'docx', 'txt', 'jpg', 'png', 'gif'}

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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    additional_events_data = load_yaml_file('additional_events.yml')
    
    # Merge the data for the template
    merged_data = schedule_data.copy()
    merged_data['additional_events'] = additional_events_data.get('additional_events', [])
    
    return render_template('schedule.html', schedule=merged_data)

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

@app.route('/schedule/update_settings', methods=['POST'])
@require_auth
def update_schedule_settings():
    schedule_data = load_yaml_file('course_schedule.yml')
    
    # Get current class days to check for changes
    current_days = []
    if 'course_schedule' in schedule_data and 'class_days' in schedule_data['course_schedule']:
        current_days = [day['day'] for day in schedule_data['course_schedule']['class_days']]
    
    # Update basic settings
    if 'course_schedule' not in schedule_data:
        schedule_data['course_schedule'] = {}
    
    schedule_data['course_schedule']['semester_start'] = request.form['semester_start']
    schedule_data['course_schedule']['semester_end'] = request.form['semester_end']
    
    # Update class days
    class_days = []
    days = request.form.getlist('class_days_day[]')
    times = request.form.getlist('class_days_time[]')
    
    new_days = []
    for day, time in zip(days, times):
        if day and time:
            class_days.append({
                'day': day,
                'time': time
            })
            new_days.append(day)
    
    schedule_data['course_schedule']['class_days'] = class_days
    
    # Handle changes in class days
    current_days_set = set(current_days)
    new_days_set = set(new_days)
    
    removed_days = current_days_set - new_days_set
    added_days = new_days_set - current_days_set
    
    messages = []
    auto_manage = 'auto_manage_lectures' in request.form
    
    # Process lectures if there are changes in class days
    if (removed_days or added_days) and 'lectures' in schedule_data and auto_manage:
        # Handle removed days
        if removed_days:
            lectures_to_redistribute = []
            lectures_updated = 0
            
            for lecture in schedule_data['lectures']:
                for removed_day in removed_days:
                    if removed_day in lecture:
                        # Store lecture content for potential redistribution
                        lectures_to_redistribute.append({
                            'week': lecture['week'],
                            'content': lecture[removed_day]
                        })
                        del lecture[removed_day]
                        lectures_updated += 1
            
            # Remove empty lecture weeks
            schedule_data['lectures'] = [
                lecture for lecture in schedule_data['lectures'] 
                if len(lecture) > 1  # More than just the 'week' key
            ]
            
            if lectures_updated > 0:
                messages.append(f'Removed {lectures_updated} lectures for discontinued class days: {", ".join(removed_days)}')
                
                # Try to redistribute removed lectures to new days if available
                if added_days and lectures_to_redistribute:
                    redistributed = 0
                    new_days_list = list(added_days)
                    
                    for removed_lecture in lectures_to_redistribute:
                        week = removed_lecture['week']
                        content = removed_lecture['content']
                        
                        # Find the lecture week entry
                        for lecture in schedule_data['lectures']:
                            if lecture.get('week') == week:
                                # Assign to first available new day
                                target_day = new_days_list[redistributed % len(new_days_list)]
                                lecture[target_day] = content
                                redistributed += 1
                                break
                        else:
                            # Week doesn't exist, create it
                            target_day = new_days_list[redistributed % len(new_days_list)]
                            schedule_data['lectures'].append({
                                'week': week,
                                target_day: content
                            })
                            redistributed += 1
                    
                    if redistributed > 0:
                        messages.append(f'Redistributed {redistributed} lectures to new class days: {", ".join(added_days)}')
        
        # Handle newly added days - create placeholder lectures for existing weeks
        elif added_days:
            weeks_with_placeholders = 0
            existing_weeks = set()
            
            # Find all existing weeks
            for lecture in schedule_data['lectures']:
                existing_weeks.add(lecture['week'])
            
            # Add placeholder lectures for new days in existing weeks
            for week in sorted(existing_weeks):
                for lecture in schedule_data['lectures']:
                    if lecture.get('week') == week:
                        for new_day in added_days:
                            if new_day not in lecture:
                                lecture[new_day] = {
                                    'topic': 'TBD',
                                    'materials': []
                                }
                                weeks_with_placeholders += 1
                        break
            
            if weeks_with_placeholders > 0:
                messages.append(f'Added placeholder lectures for new class days in {len(existing_weeks)} existing weeks')
    
    # Update holidays
    holidays_text = request.form['holidays'].strip()
    holidays = []
    if holidays_text:
        holidays = [line.strip() for line in holidays_text.split('\n') if line.strip()]
    
    schedule_data['course_schedule']['holidays'] = holidays
    
    save_yaml_file('course_schedule.yml', schedule_data)
    
    # Display all messages
    for message in messages:
        flash(message, 'info')
    
    flash('Schedule settings updated successfully!', 'success')
    return redirect(url_for('schedule'))

@app.route('/schedule/cleanup_lectures', methods=['POST'])
@require_auth
def cleanup_lectures():
    schedule_data = load_yaml_file('course_schedule.yml')
    
    # Get current class days
    current_days = set()
    if 'course_schedule' in schedule_data and 'class_days' in schedule_data['course_schedule']:
        current_days = {day['day'] for day in schedule_data['course_schedule']['class_days']}
    
    if not current_days:
        return jsonify({'success': False, 'message': 'No class days configured'})
    
    lectures_updated = 0
    if 'lectures' in schedule_data:
        for lecture in schedule_data['lectures']:
            # Get all days in this lecture except 'week'
            lecture_days = set(lecture.keys()) - {'week'}
            # Find days that are no longer in class schedule
            days_to_remove = lecture_days - current_days
            
            for day_to_remove in days_to_remove:
                del lecture[day_to_remove]
                lectures_updated += 1
        
        # Remove empty lecture weeks
        schedule_data['lectures'] = [
            lecture for lecture in schedule_data['lectures'] 
            if len(lecture) > 1  # More than just the 'week' key
        ]
    
    save_yaml_file('course_schedule.yml', schedule_data)
    
    message = f'Cleaned up {lectures_updated} lectures for discontinued class days.'
    if lectures_updated == 0:
        message = 'No cleanup needed - all lectures match current class schedule.'
    
    return jsonify({'success': True, 'message': message})

@app.route('/schedule/bulk_operations', methods=['POST'])
@require_auth
def bulk_operations():
    operation = request.json.get('operation')
    schedule_data = load_yaml_file('course_schedule.yml')
    
    if operation == 'fill_missing_days':
        # Fill missing days for all existing weeks
        current_days = set()
        if 'course_schedule' in schedule_data and 'class_days' in schedule_data['course_schedule']:
            current_days = {day['day'] for day in schedule_data['course_schedule']['class_days']}
        
        if not current_days:
            return jsonify({'success': False, 'message': 'No class days configured'})
        
        filled_count = 0
        if 'lectures' in schedule_data:
            for lecture in schedule_data['lectures']:
                week_days = set(lecture.keys()) - {'week'}
                missing_days = current_days - week_days
                
                for missing_day in missing_days:
                    lecture[missing_day] = {
                        'topic': 'TBD',
                        'materials': []
                    }
                    filled_count += 1
        
        save_yaml_file('course_schedule.yml', schedule_data)
        return jsonify({'success': True, 'message': f'Added {filled_count} placeholder lectures for missing days'})
    
    elif operation == 'generate_weeks':
        # Generate placeholder weeks up to a specified number
        max_week = request.json.get('max_week', 16)
        current_days = []
        if 'course_schedule' in schedule_data and 'class_days' in schedule_data['course_schedule']:
            current_days = [day['day'] for day in schedule_data['course_schedule']['class_days']]
        
        if not current_days:
            return jsonify({'success': False, 'message': 'No class days configured'})
        
        # Find existing weeks
        existing_weeks = set()
        if 'lectures' in schedule_data:
            for lecture in schedule_data['lectures']:
                existing_weeks.add(lecture['week'])
        
        # Generate missing weeks
        created_count = 0
        for week in range(1, max_week + 1):
            if week not in existing_weeks:
                new_lecture = {'week': week}
                for day in current_days:
                    new_lecture[day] = {
                        'topic': 'TBD',
                        'materials': []
                    }
                
                if 'lectures' not in schedule_data:
                    schedule_data['lectures'] = []
                
                schedule_data['lectures'].append(new_lecture)
                created_count += 1
        
        # Sort lectures by week
        if 'lectures' in schedule_data:
            schedule_data['lectures'].sort(key=lambda x: x['week'])
        
        save_yaml_file('course_schedule.yml', schedule_data)
        return jsonify({'success': True, 'message': f'Generated {created_count} new weeks (up to week {max_week})'})
    
    return jsonify({'success': False, 'message': 'Unknown operation'})

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

@app.route('/upload_file', methods=['POST'])
@require_auth
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        file_path = os.path.join(UPLOAD_DIR, filename)
        file.save(file_path)
        
        # Return relative path for use in materials
        relative_path = f'/static_files/uploads/{filename}'
        
        return jsonify({
            'success': True, 
            'message': 'File uploaded successfully',
            'file_path': relative_path,
            'filename': filename
        })
    
    return jsonify({'success': False, 'message': 'Invalid file type'})

@app.route('/get_uploaded_files')
@require_auth
def get_uploaded_files():
    files = []
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            if allowed_file(filename):
                files.append({
                    'name': filename,
                    'path': f'/static_files/uploads/{filename}'
                })
    
    # Sort by newest first
    files.sort(key=lambda x: x['name'], reverse=True)
    return jsonify({'files': files[:10]})  # Return latest 10 files

@app.route('/edit_lecture', methods=['POST'])
@require_auth
def edit_lecture():
    data = request.get_json()
    week = data.get('week')
    day = data.get('day')
    topic = data.get('topic')
    materials = data.get('materials', [])
    
    schedule_data = load_yaml_file('course_schedule.yml')
    
    # Find the lecture
    for lecture in schedule_data.get('lectures', []):
        if lecture.get('week') == week:
            if day in lecture:
                lecture[day]['topic'] = topic
                lecture[day]['materials'] = materials
                break
            else:
                # Add new day to existing week
                lecture[day] = {
                    'topic': topic,
                    'materials': materials
                }
                break
    else:
        # Week doesn't exist, create it
        new_lecture = {
            'week': week,
            day: {
                'topic': topic,
                'materials': materials
            }
        }
        if 'lectures' not in schedule_data:
            schedule_data['lectures'] = []
        schedule_data['lectures'].append(new_lecture)
        schedule_data['lectures'].sort(key=lambda x: x['week'])
    
    save_yaml_file('course_schedule.yml', schedule_data)
    return jsonify({'success': True, 'message': 'Lecture updated successfully'})

@app.route('/delete_material', methods=['POST'])
@require_auth
def delete_material():
    data = request.get_json()
    week = data.get('week')
    day = data.get('day')
    index = data.get('index')
    
    schedule_data = load_yaml_file('course_schedule.yml')
    
    # Find the lecture and remove material
    for lecture in schedule_data.get('lectures', []):
        if lecture.get('week') == week and day in lecture:
            materials = lecture[day].get('materials', [])
            if 0 <= index < len(materials):
                materials.pop(index)
                break
    
    save_yaml_file('course_schedule.yml', schedule_data)
    return jsonify({'success': True, 'message': 'Material deleted successfully'})

@app.route('/delete_file', methods=['POST'])
@require_auth
def delete_file():
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'success': False, 'message': 'No filename provided'})
    
    # Security check - only allow deletion of files in uploads directory
    if not filename.startswith('/static_files/uploads/'):
        return jsonify({'success': False, 'message': 'Invalid file path'})
    
    # Extract actual filename
    actual_filename = filename.replace('/static_files/uploads/', '')
    file_path = os.path.join(UPLOAD_DIR, actual_filename)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True, 'message': 'File deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'File not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting file: {str(e)}'})

@app.route('/add_additional_event', methods=['POST'])
@require_auth
def add_additional_event():
    event_date = request.form['event_date']
    event_type = request.form['event_type']
    event_topic = request.form['event_topic']
    material_name = request.form.get('event_material_name', '').strip()
    material_url = request.form.get('event_material_url', '').strip()
    
    additional_events_data = load_yaml_file('additional_events.yml')
    
    if 'additional_events' not in additional_events_data:
        additional_events_data['additional_events'] = []
    
    new_event = {
        'date': event_date,
        'type': event_type,
        'topic': event_topic,
        'materials': []
    }
    
    # Add material if provided
    if material_name and material_url:
        new_event['materials'].append({
            'name': material_name,
            'url': material_url
        })
    
    additional_events_data['additional_events'].append(new_event)
    
    # Sort events by date
    additional_events_data['additional_events'].sort(key=lambda x: x['date'])
    
    save_yaml_file('additional_events.yml', additional_events_data)
    flash('Additional event added successfully!', 'success')
    return redirect(url_for('events'))

@app.route('/edit_additional_event', methods=['POST'])
@require_auth
def edit_additional_event():
    data = request.get_json()
    index = data.get('index')
    date = data.get('date')
    event_type = data.get('type')
    topic = data.get('topic')
    materials = data.get('materials', [])
    
    additional_events_data = load_yaml_file('additional_events.yml')
    
    if 'additional_events' in additional_events_data and 0 <= index < len(additional_events_data['additional_events']):
        additional_events_data['additional_events'][index] = {
            'date': date,
            'type': event_type,
            'topic': topic,
            'materials': materials
        }
        
        # Sort events by date
        additional_events_data['additional_events'].sort(key=lambda x: x['date'])
        
        save_yaml_file('additional_events.yml', additional_events_data)
        return jsonify({'success': True, 'message': 'Event updated successfully'})
    
    return jsonify({'success': False, 'message': 'Event not found'})

@app.route('/delete_additional_event', methods=['POST'])
@require_auth
def delete_additional_event():
    data = request.get_json()
    index = data.get('index')
    
    additional_events_data = load_yaml_file('additional_events.yml')
    
    if 'additional_events' in additional_events_data and 0 <= index < len(additional_events_data['additional_events']):
        additional_events_data['additional_events'].pop(index)
        save_yaml_file('additional_events.yml', additional_events_data)
        return jsonify({'success': True, 'message': 'Event deleted successfully'})
    
    return jsonify({'success': False, 'message': 'Event not found'})

@app.route('/events')
@require_auth
def events():
    additional_events_data = load_yaml_file('additional_events.yml')
    return render_template('events.html', events=additional_events_data)

@app.route('/add_event_material', methods=['POST'])
@require_auth
def add_event_material():
    data = request.get_json()
    event_index = data.get('event_index')
    material_name = data.get('material_name')
    material_url = data.get('material_url')
    
    additional_events_data = load_yaml_file('additional_events.yml')
    
    if 'additional_events' in additional_events_data and 0 <= event_index < len(additional_events_data['additional_events']):
        event = additional_events_data['additional_events'][event_index]
        if 'materials' not in event:
            event['materials'] = []
        
        event['materials'].append({
            'name': material_name,
            'url': material_url
        })
        
        save_yaml_file('additional_events.yml', additional_events_data)
        return jsonify({'success': True, 'message': 'Material added successfully'})
    
    return jsonify({'success': False, 'message': 'Event not found'})

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=8080)