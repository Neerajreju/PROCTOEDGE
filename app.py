from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import uuid
import threading
import time
import subprocess

app = Flask(__name__)
app.secret_key = 'secret'

# In-memory storage for exams and alerts
exam_sessions = {}  # token: {duration, sdr, name, email, alerts}

# Function to run proctoring tools
def run_proctoring(token, duration, sdr_enabled):
    end_time = time.time() + duration * 60

    def face_mobile_detection():
        subprocess.run(['python', 'the_fin.py', token])  
        send_alert(token, "Face or Mobile detection triggered!")

    def run_sdr():
        subprocess.run(['python', 'sdr_script.py'])  # SDR script filename
        send_alert(token, "SDR detected anomalies!")

    threads = []

    # Start face + mobile detection
    t1 = threading.Thread(target=face_mobile_detection)
    t1.start()
    threads.append(t1)

    # Start SDR if enabled
    if sdr_enabled:
        t2 = threading.Thread(target=run_sdr)
        t2.start()
        threads.append(t2)

    # Wait for exam to finish
    while time.time() < end_time:
        time.sleep(1)

    # Optional: Terminate threads or processes if needed
    for t in threads:
        t.join()

# Function to send alerts to the admin
def send_alert(token, alert):
    if token in exam_sessions:
        exam_sessions[token]['alerts'].append(alert)

@app.route('/')
def home():
    return redirect(url_for('admin_dashboard'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        # Get exam settings from the form
        duration = int(request.form['duration'])
        sdr_enabled = 'sdr' in request.form
        token = str(uuid.uuid4())
        
        # Store exam session data
        exam_sessions[token] = {
            'duration': duration,
            'sdr': sdr_enabled,
            'alerts': [],
            'students': []
        }

        # Generate the full exam URL for sharing
        exam_url = request.host_url + 'exam/' + token  # This creates the full URL (with protocol)

        return render_template('admin_dashboard.html', token=token, sessions=exam_sessions, exam_url=exam_url)
    
    return render_template('admin_dashboard.html', token=None, sessions=exam_sessions)

@app.route('/exam/<token>', methods=['GET', 'POST'])
def exam_page(token):
    if token not in exam_sessions:
        return "Invalid exam link."
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        exam_sessions[token]['students'].append({'name': name, 'email': email})
        session['token'] = token
        session['name'] = name
        session['email'] = email

        # Start proctoring tools in background
        threading.Thread(target=run_proctoring, args=(token, exam_sessions[token]['duration'], exam_sessions[token]['sdr'])).start()

        return render_template('student_exam.html', duration=exam_sessions[token]['duration'], token=token)
    
    return render_template('student_login.html', token=token)

@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    data = request.json
    token = data.get('token')
    student_name = data.get('student_name')
    student_email = data.get('student_email')

    if token in exam_sessions:
        # Optionally store the student info and alerts here
        exam_sessions[token]['students'][-1]['status'] = "Submitted"
        exam_sessions[token]['alerts'].append(f"Exam submitted by {student_name} ({student_email})")

        # Optionally stop any proctoring services here

        return jsonify(message="Exam submitted successfully")
    
    return jsonify(message="Invalid token or session")

@app.route('/send_alert', methods=['POST'])
def send_alert_route():
    data = request.json
    token = data.get('token')
    alert = data.get('alert')

    if token in exam_sessions:
        exam_sessions[token]['alerts'].append(alert)
    
    return '', 204

@app.route('/alerts/<token>')
def view_alerts(token):
    if token in exam_sessions:
        return jsonify(alerts=exam_sessions[token]['alerts'])
    return jsonify(alerts=[])


if __name__ == '__main__':
    app.run(debug=True)
