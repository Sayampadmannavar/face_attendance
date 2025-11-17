"""
Single-file Flask web dashboard for the Face Recognition Attendance System.

- Self-contained HTML/CSS/JS embedded in this file (no external assets required)
- Connects to your existing project modules: register.py, train.py, attendance.py, db.py
- Optionally integrates with email_notifier.py if present

Save this file in the root of your project (where register.py, train.py, attendance.py, db.py live)
Run: python flask_face_attendance_app.py
Open http://127.0.0.1:5000 in your browser

NOTE: This file tries to be defensive: if a backend module or function is missing it will return helpful errors
"""

from flask import Flask, request, jsonify, render_template_string, send_file
import threading
import traceback
import io
import csv
import os

# Defensive imports for your existing project modules
try:
    from register import register_user
except Exception as e:
    register_user = None

try:
    from train import train as train_model
except Exception as e:
    train_model = None

try:
    from attendance import attend as start_attendance
except Exception as e:
    start_attendance = None

try:
    from db import fetch_attendance, init_db
except Exception as e:
    fetch_attendance = None
    init_db = None

# Optional email notifier
try:
    import email_notifier
    email_notifier_available = True
except Exception:
    email_notifier = None
    email_notifier_available = False

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Ensure DB initialization if available
if init_db:
    try:
        init_db()
    except Exception:
        # ignore init errors here, endpoints will return details
        pass

# Embedded HTML template (single-page app)
HTML = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Face Attendance Dashboard</title>
  <style>
    /* Minimal modern styling (no external CSS) */
    :root{--bg:#0f1724;--card:#0b1220;--accent:#06b6d4;--muted:#94a3b8;--glass: rgba(255,255,255,0.03)}
    html,body{height:100%;margin:0;font-family:Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;background:linear-gradient(180deg,#071126 0%, #071428 100%);color:#e6eef8}
    .container{max-width:1100px;margin:28px auto;padding:20px}
    header{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
    h1{margin:0;font-size:20px}
    .grid{display:grid;grid-template-columns: 1fr 420px;gap:18px}
    .card{background:var(--card);border-radius:12px;padding:18px;box-shadow: 0 6px 20px rgba(2,6,23,0.6);}
    label{display:block;color:var(--muted);font-size:13px;margin-bottom:6px}
    input[type=text], input[type=email], input[type=number]{width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:transparent;color:inherit}
    button{cursor:pointer;border:0;padding:10px 14px;border-radius:10px;background:linear-gradient(90deg,var(--accent),#3b82f6);color:#032; font-weight:600}
    .muted{color:var(--muted);font-size:13px}
    .row{display:flex;gap:10px}
    .small{padding:8px 10px;border-radius:8px;background:var(--glass);border:1px solid rgba(255,255,255,0.02)}
    table{width:100%;border-collapse:collapse;margin-top:10px}
    th,td{padding:8px;border-bottom:1px solid rgba(255,255,255,0.03);text-align:left;font-size:13px}
    thead th{color:var(--muted);font-size:12px}
    .center{text-align:center}
    .notice{background:rgba(255,255,255,0.03);padding:8px;border-radius:8px;margin-bottom:10px;color:var(--muted)}
    .spinner{display:inline-block;width:16px;height:16px;border:2px solid rgba(255,255,255,0.08);border-top-color:var(--accent);border-radius:50%;animation:spin 1s linear infinite}
    @keyframes spin{to{transform:rotate(360deg)}}
    footer{margin-top:12px;font-size:12px;color:var(--muted)}
    @media(max-width:900px){.grid{grid-template-columns:1fr;}.container{padding:12px}}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Face Recognition Attendance — Dashboard</h1>
      <div class="muted">Local dev server • Single-file Flask UI</div>
    </header>

    <div class="grid">
      <!-- Left column: Actions -->
      <div>
        <div class="card">
          <h3>Register a new user</h3>
          <p class="muted">Fill the details and capture face samples (back-end handles camera & samples).</p>
          <div style="margin-top:8px">
            <label for="user_id">User ID (unique)</label>
            <input id="user_id" type="text" placeholder="e.g. 1001">
            <label for="name" style="margin-top:8px">Full Name</label>
            <input id="name" type="text" placeholder="e.g. Priya Sharma">
            <label for="email" style="margin-top:8px">Email</label>
            <input id="email" type="email" placeholder="optional - used for notifications">
            <label for="samples" style="margin-top:8px">Samples to capture</label>
            <input id="samples" type="number" value="30" min="5" max="200">
            <div style="height:10px"></div>
            <div class="row">
              <button id="btnRegister" onclick="registerUser()">Register & Capture</button>
              <div id="regStatus" class="small" style="display:flex;align-items:center;gap:8px">Ready</div>
            </div>
          </div>
        </div>

        <div class="card" style="margin-top:12px">
          <h3>Train model</h3>
          <p class="muted">Train face recognition model on the registered users.</p>
          <div class="row" style="margin-top:8px">
            <button onclick="trainModel()">Train Now</button>
            <div id="trainStatus" class="small">Idle</div>
          </div>
        </div>

        <div class="card" style="margin-top:12px">
          <h3>Take attendance (recognize)</h3>
          <p class="muted">Run recognition to mark attendance. This typically opens the webcam on the server machine.</p>
          <div class="row" style="margin-top:8px">
            <button onclick="takeAttendance()">Start Attendance</button>
            <div id="attStatus" class="small">Idle</div>
          </div>
          <div style="margin-top:8px" class="notice">Note: For webcam to be used the Python server must be run on the machine with the camera.</div>
        </div>

      </div>

      <!-- Right column: Attendance view & email -->
      <div>
        <div class="card">
          <h3>View attendance</h3>
          <p class="muted">Recent attendance records.</p>
          <div id="attendanceTable" style="max-height:420px;overflow:auto">
            <div class="muted">Loading...</div>
          </div>
          <div style="display:flex;gap:8px;margin-top:10px">
            <button onclick="downloadCSV()">Download CSV</button>
            <button onclick="refreshAttendance()" class="small">Refresh</button>
          </div>
        </div>

        <div class="card" style="margin-top:12px">
          <h3>Email notifications</h3>
          <p class="muted">Send a quick test email (requires optional email_notifier.py)</p>
          <label for="toEmail">To</label>
          <input id="toEmail" type="email" placeholder="recipient@example.com">
          <label for="subject" style="margin-top:8px">Subject</label>
          <input id="subject" type="text" value="Attendance report">
          <label for="message" style="margin-top:8px">Message</label>
          <input id="message" type="text" value="Here is a quick attendance report">
          <div style="height:10px"></div>
          <div class="row">
            <button onclick="sendEmail()">Send Email</button>
            <div id="emailStatus" class="small">Status: N/A</div>
          </div>
        </div>

      </div>
    </div>

    <footer class="muted">If any backend function is missing the UI will show descriptive errors. Place this file in your project root with your modules.</footer>
  </div>

<script>
async function jsonPost(url, body){
  try{
    const res = await fetch(url, {method:'POST',headers:{'Content-Type':'application/json'},body: JSON.stringify(body)});
    return await res.json();
  }catch(e){
    return {ok:false, error: e.toString()}
  }
}

async function registerUser(){
  const user_id = document.getElementById('user_id').value.trim();
  const name = document.getElementById('name').value.trim();
  const email = document.getElementById('email').value.trim();
  const samples = Number(document.getElementById('samples').value) || 30;
  const status = document.getElementById('regStatus');
  status.innerHTML = '<span class="spinner"></span> Registering...';
  const resp = await jsonPost('/api/register', {user_id, name, email, samples});
  if(resp && resp.ok){
    status.innerHTML = '✅ ' + resp.message;
    refreshAttendance();
  } else {
    status.innerHTML = '❌ ' + (resp && resp.error ? resp.error : 'Unknown error');
  }
}

async function trainModel(){
  const status = document.getElementById('trainStatus');
  status.innerHTML = '<span class="spinner"></span> Training...';
  const resp = await jsonPost('/api/train', {});
  if(resp && resp.ok){
    status.innerHTML = '✅ ' + resp.message;
  } else {
    status.innerHTML = '❌ ' + (resp && resp.error ? resp.error : 'Training failed');
  }
}

async function takeAttendance(){
  const status = document.getElementById('attStatus');
  status.innerHTML = '<span class="spinner"></span> Running...';
  const resp = await jsonPost('/api/attend', {});
  if(resp && resp.ok){
    status.innerHTML = '✅ ' + resp.message;
    refreshAttendance();
  } else {
    status.innerHTML = '❌ ' + (resp && resp.error ? resp.error : 'Failed');
  }
}

async function refreshAttendance(){
  const container = document.getElementById('attendanceTable');
  container.innerHTML = '<div class="muted">Loading...</div>';
  try{
    const res = await fetch('/api/attendance');
    const data = await res.json();
    if(!data.ok){ container.innerHTML = '<div class="muted">Error: '+ (data.error||'unknown') +'</div>'; return; }
    const rows = data.rows || [];
    if(rows.length === 0){ container.innerHTML = '<div class="muted">No attendance yet</div>'; return; }
    let html = '<table><thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Time</th><th>Note</th></tr></thead><tbody>';
    for(const r of rows){ html += `<tr><td>${r.id||''}</td><td>${r.name||''}</td><td>${r.email||''}</td><td>${r.time||''}</td><td>${r.note||''}</td></tr>` }
    html += '</tbody></table>';
    container.innerHTML = html;
  }catch(e){ container.innerHTML = '<div class="muted">Fetch error</div>' }
}

async function downloadCSV(){
  window.location = '/api/attendance.csv';
}

async function sendEmail(){
  const to = document.getElementById('toEmail').value.trim();
  const subject = document.getElementById('subject').value.trim();
  const message = document.getElementById('message').value.trim();
  const status = document.getElementById('emailStatus');
  status.innerHTML = '<span class="spinner"></span> Sending...';
  const resp = await jsonPost('/api/send_email', {to, subject, message});
  if(resp && resp.ok){ status.innerHTML = '✅ ' + resp.message } else { status.innerHTML = '❌ ' + (resp && resp.error ? resp.error : 'Failed') }
}

// load attendance on open
refreshAttendance();
</script>
</body>
</html>
'''

# ---------------------
# Helper functions
# ---------------------

def run_and_capture(func, *a, **kw):
    """Run a backend function and capture exception to return a dict."""
    try:
        result = func(*a, **kw)
        return {'ok': True, 'result': result}
    except Exception as e:
        tb = traceback.format_exc()
        return {'ok': False, 'error': str(e), 'traceback': tb}

# ---------------------
# Routes
# ---------------------

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/register', methods=['POST'])
def api_register():
    if register_user is None:
        return jsonify(ok=False, error='register_user function not found. Ensure register.py exists and exposes register_user(user_id,name,email,samples)')
    data = request.get_json() or {}
    user_id = data.get('user_id')
    name = data.get('name')
    email = data.get('email')
    samples = data.get('samples', 30)
    if not user_id or not name:
        return jsonify(ok=False, error='user_id and name are required')
    # call register_user synchronously and return feedback
    out = run_and_capture(register_user, user_id, name, email, samples)
    if out['ok']:
        return jsonify(ok=True, message=str(out.get('result') or 'Registration complete'))
    else:
        return jsonify(ok=False, error=out['error'], details=out.get('traceback'))

@app.route('/api/train', methods=['POST'])
def api_train():
    if train_model is None:
        return jsonify(ok=False, error='train function not found. Ensure train.py exposes train()')
    out = run_and_capture(train_model)
    if out['ok']:
        return jsonify(ok=True, message=str(out.get('result') or 'Training finished'))
    else:
        return jsonify(ok=False, error=out['error'], details=out.get('traceback'))

@app.route('/api/attend', methods=['POST'])
def api_attend():
    if start_attendance is None:
        return jsonify(ok=False, error='attend function not found. Ensure attendance.py exposes attend()')
    out = run_and_capture(start_attendance)
    if out['ok']:
        return jsonify(ok=True, message=str(out.get('result') or 'Attendance run complete'))
    else:
        return jsonify(ok=False, error=out['error'], details=out.get('traceback'))

@app.route('/api/attendance', methods=['GET'])
def api_attendance():
    if fetch_attendance is None:
        return jsonify(ok=False, error='fetch_attendance not found. Ensure db.py exposes fetch_attendance()')
    try:
        rows = fetch_attendance()
        # rows should be list of dicts or tuples. Normalize to dicts
        normalized = []
        for r in rows:
            if isinstance(r, dict):
                normalized.append(r)
            else:
                # try tuple-like: (id, name, email, time, note)
                if len(r) >= 5:
                    normalized.append({'id': r[0], 'name': r[1], 'email': r[2], 'time': r[3], 'note': r[4]})
                else:
                    normalized.append({'raw': str(r)})
        return jsonify(ok=True, rows=normalized)
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify(ok=False, error=str(e), details=tb)

@app.route('/api/attendance.csv', methods=['GET'])
def api_attendance_csv():
    if fetch_attendance is None:
        return jsonify(ok=False, error='fetch_attendance not found. Ensure db.py exposes fetch_attendance()')
    try:
        rows = fetch_attendance()
        # create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        # header
        writer.writerow(['id','name','email','time','note'])
        for r in rows:
            if isinstance(r, dict):
                writer.writerow([r.get('id',''), r.get('name',''), r.get('email',''), r.get('time',''), r.get('note','')])
            else:
                # tuple handling
                rlist = list(r)
                # pad
                while len(rlist) < 5: rlist.append('')
                writer.writerow(rlist[:5])
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='attendance.csv')
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify(ok=False, error=str(e), details=tb)

@app.route('/api/send_email', methods=['POST'])
def api_send_email():
    if not email_notifier_available:
        return jsonify(ok=False, error='email_notifier module not available. Place email_notifier.py in project root and ensure it exposes send_email(to,subject,message)')
    data = request.get_json() or {}
    to = data.get('to')
    subject = data.get('subject','Test')
    message = data.get('message','')
    if not to:
        return jsonify(ok=False, error='"to" email is required')
    # call send_email
    try:
        # email_notifier.send_email could be sync; capture result
        res = email_notifier.send_email(to, subject, message)
        return jsonify(ok=True, message=str(res or 'Email sent'))
    except Exception as e:
        return jsonify(ok=False, error=str(e), details=traceback.format_exc())

# health
@app.route('/api/health')
def health():
    available = {
        'register': register_user is not None,
        'train': train_model is not None,
        'attend': start_attendance is not None,
        'fetch_attendance': fetch_attendance is not None,
        'email_notifier': email_notifier_available,
    }
    return jsonify(ok=True, available=available)

# ---------------------
# Run server
# ---------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

