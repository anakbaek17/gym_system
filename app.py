from flask import Flask, request, redirect, url_for, session, render_template_string, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'gym_secret_key_2026'
DB_PATH = 'database.db'

# =========================================================
# ⚠️ ISIKAN NOMOR GOPAY & NAMA ASLI KAMU DI SINI:
GOPAY_NUMBER = "083857533722"  # Ganti dengan Nomor HP GoPay Kamu
GOPAY_NAME = "NAUFAL HANIF JABRAN SUKMA"     # Nama Akun GoPay Kamu
# =========================================================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS membership_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_name TEXT NOT NULL,
            duration_months INTEGER NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'Aktif'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS member_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            package_id INTEGER,
            remaining_days INTEGER DEFAULT 30,
            status_paket TEXT DEFAULT 'Paket Premium',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            checkin_time TEXT NOT NULL,
            status TEXT DEFAULT 'Berhasil',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_id INTEGER,
            member_id INTEGER,
            exercise_name TEXT NOT NULL,
            sets INTEGER,
            reps INTEGER,
            weight_kg REAL,
            schedule_date TEXT,
            schedule_time TEXT,
            status TEXT DEFAULT 'Belum',
            FOREIGN KEY(member_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS member_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER,
            target_weight REAL,
            target_body_fat REAL,
            notes TEXT,
            FOREIGN KEY(member_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS member_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER,
            weight REAL,
            body_fat REAL,
            stomach_circumference REAL,
            recorded_date TEXT DEFAULT CURRENT_DATE,
            FOREIGN KEY(member_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_name TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'Tersedia'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER,
            package_id INTEGER,
            amount REAL,
            payment_date TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY(member_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO users (unique_code, name, email, password, role, phone) VALUES (?, ?, ?, ?, ?, ?)", [
            ('OWN001', 'Budi Santoso', 'budi@gym.com', 'password123', 'owner', '081234567800'),
            ('ADM001', 'Siti Aminah', 'siti@gym.com', 'password123', 'admin', '081234567801'),
            ('TRN001', 'Rian Fitness', 'rian@gym.com', 'password123', 'trainer', '081234567802'),
            ('MEM001', 'Andi Pratama', 'andi@gym.com', 'password123', 'member', '081234567803')
        ])
        cursor.executemany("INSERT INTO membership_packages (package_name, duration_months, price, status) VALUES (?, ?, ?, ?)", [
            ('Paket Biru', 1, 250000, 'Aktif'),
            ('Standard', 3, 400000, 'Aktif'),
            ('Premium', 6, 600000, 'Aktif')
        ])
        cursor.execute("INSERT INTO member_profiles (user_id, package_id, remaining_days, status_paket) VALUES (4, 3, 45, 'Paket Premium')")
        cursor.execute("INSERT INTO member_progress (member_id, weight, body_fat, stomach_circumference, recorded_date) VALUES (4, 70.5, 18.2, 82.0, '2026-10-10')")
        cursor.execute("INSERT INTO workouts (trainer_id, member_id, exercise_name, sets, reps, weight_kg, schedule_date, schedule_time, status) VALUES (3, 4, 'Bench Press', 4, 10, 60.0, '2026-10-21', '16:00', 'Belum')")
        cursor.execute("INSERT INTO equipment (equipment_name, category, status) VALUES ('Treadmill Pro X', 'Cardio', 'Tersedia'), ('Olympic Barbell', 'Beban', 'Tersedia')")
        cursor.execute("INSERT INTO payments (member_id, package_id, amount, payment_date, status) VALUES (4, 3, 600000, '2026-10-20 20:00:00', 'Lunas')")
        conn.commit()
    conn.close()

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>FIT HUB GYM ACCESS - {{ role.upper() }} Dashboard</title>
    <style>
        :root {
            --bg-main: #0b0f19;
            --bg-card: rgba(19, 27, 46, 0.82);
            --bg-sidebar: rgba(15, 23, 42, 0.95);
            --border-color: rgba(255, 255, 255, 0.1);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --accent-primary: #f5b000;
            
            {% if role == 'member' %}
                --role-badge-bg: rgba(245, 176, 0, 0.15);
            {% elif role == 'trainer' %}
                --role-badge-bg: rgba(0, 230, 118, 0.15);
            {% elif role == 'admin' %}
                --role-badge-bg: rgba(41, 121, 255, 0.15);
            {% elif role == 'owner' %}
                --role-badge-bg: rgba(213, 0, 249, 0.15);
            {% else %}
                --role-badge-bg: rgba(245, 176, 0, 0.15);
            {% endif %}
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', 'Segoe UI', Tahoma, sans-serif; }
        body { background-color: var(--bg-main); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 270px; background-color: var(--bg-sidebar); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; z-index: 10; backdrop-filter: blur(10px); }
        .sidebar-brand { padding: 24px; font-size: 17px; font-weight: 800; color: #f5b000; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; letter-spacing: 0.5px; }
        .role-pill { font-size: 10px; padding: 4px 8px; border-radius: 20px; background: var(--role-badge-bg); color: var(--accent-primary); font-weight: 600; text-transform: uppercase; }
        
        .sidebar-menu { list-style: none; padding: 20px 0; overflow-y: auto; flex-grow: 1; }
        .sidebar-menu li a { display: block; padding: 14px 24px; color: var(--text-muted); text-decoration: none; font-size: 14px; font-weight: 500; transition: all 0.3s ease; border-left: 3px solid transparent; }
        .sidebar-menu li a:hover, .sidebar-menu li a.active { background: rgba(255, 255, 255, 0.05); color: var(--text-main); border-left-color: #f5b000; }
        .sidebar-menu li a.active { color: #f5b000; font-weight: 600; }
        
        .sidebar-footer { padding: 20px 24px; border-top: 1px solid var(--border-color); }
        .btn-logout { display: block; padding: 12px; text-align: center; background: rgba(239, 68, 68, 0.1); color: var(--danger); text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px; border: 1px solid rgba(239, 68, 68, 0.2); transition: 0.2s; }
        .btn-logout:hover { background: var(--danger); color: #fff; }

        .main-container { flex-grow: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; }
        .header { height: 75px; background: rgba(19, 27, 46, 0.85); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; padding: 0 35px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); z-index: 5; }
        .header-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
        .user-info { font-size: 14px; color: var(--text-muted); display: flex; align-items: center; gap: 10px; } 
        .user-info span { color: #f5b000; font-weight: 700; background: var(--role-badge-bg); padding: 5px 12px; border-radius: 6px; }
        
        .content { 
            padding: 35px; 
            overflow-y: auto; 
            flex-grow: 1; 
            position: relative;
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            transition: background-image 0.4s ease-in-out;
        }

        {% if bg_url %}
        .content::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(180deg, rgba(11, 15, 25, 0.88) 0%, rgba(11, 15, 25, 0.95) 100%);
            z-index: 1;
        }
        {% endif %}

        .content-inner {
            position: relative;
            z-index: 2;
        }

        .card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 22px; border-radius: 14px; border: 1px solid var(--border-color); box-shadow: 0 8px 24px rgba(0,0,0,0.4); position: relative; overflow: hidden; transition: transform 0.2s; }
        .card:hover { transform: translateY(-3px); border-color: rgba(245, 176, 0, 0.3); }
        .card::before { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #f5b000; }
        .card h3 { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }
        .card .value { font-size: 26px; font-weight: 800; color: var(--text-main); }

        table { width: 100%; border-collapse: separate; border-spacing: 0; background: var(--bg-card); backdrop-filter: blur(12px); border-radius: 12px; overflow: hidden; border: 1px solid var(--border-color); margin-top: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
        th, td { padding: 15px 18px; text-align: left; border-bottom: 1px solid var(--border-color); font-size: 14px; }
        th { background: rgba(0,0,0,0.4); color: #f5b000; font-weight: 700; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; } 
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: rgba(255,255,255,0.02); }
        
        .badge { padding: 5px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; letter-spacing: 0.3px; }
        .badge-success { background: rgba(16, 185, 129, 0.15); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-warning { background: rgba(245, 158, 11, 0.15); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-danger { background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.3); }
        
        form label { display: block; margin-bottom: 8px; font-size: 13px; color: var(--text-muted); font-weight: 600; }
        form input, form select, form textarea { width: 100%; padding: 12px 16px; background: rgba(11, 15, 25, 0.8); border: 1px solid var(--border-color); border-radius: 8px; color: #fff; margin-bottom: 20px; font-size: 14px; transition: border-color 0.2s; }
        form input:focus, form select:focus, form textarea:focus { border-color: #f5b000; outline: none; box-shadow: 0 0 0 3px rgba(245, 176, 0, 0.15); }
        
        .btn-primary { background: #f5b000; color: #121212; padding: 12px 24px; border: none; border-radius: 8px; font-weight: 800; cursor: pointer; transition: background 0.2s, transform 0.1s; font-size: 14px; box-shadow: 0 4px 15px rgba(245, 176, 0, 0.2); text-decoration: none; display: inline-block; }
        .btn-primary:hover { background: #d99b00; transform: translateY(-1px); }
        .btn-danger { background: rgba(239, 68, 68, 0.2); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.3); padding: 6px 14px; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 12px; transition: 0.2s; }
        .btn-danger:hover { background: var(--danger); color: #fff; }
        
        .panel-box { background: var(--bg-card); backdrop-filter: blur(12px); padding: 28px; border-radius: 16px; border: 1px solid var(--border-color); margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); }
        .search-box { padding: 12px 18px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; color: #fff; width: 100%; max-width: 320px; margin-bottom: 20px; font-size: 14px; }
        
        h2 { font-size: 22px; font-weight: 800; color: var(--text-main); margin-bottom: 8px; }
        p { color: var(--text-muted); font-size: 14px; line-height: 1.5; }
        
        .motto-tag { font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: #f5b000; font-weight: 800; margin-bottom: 4px; display: block; }
        
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); display: none; justify-content: center; align-items: center; z-index: 1000; }
        .modal-box { background: #131b2e; border: 1px solid var(--border-color); border-top: 4px solid #f5b000; padding: 35px; border-radius: 20px; width: 90%; max-width: 520px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); position: relative; }
        .payment-method-card { background: #0b0f19; border: 1px solid var(--border-color); border-radius: 10px; padding: 15px; margin-bottom: 12px; cursor: pointer; transition: 0.2s; display: flex; align-items: center; justify-content: space-between; }
        .payment-method-card:hover, .payment-method-card.selected { border-color: #f5b000; background: rgba(245, 176, 0, 0.05); }

        @media (max-width: 1024px) {
            .owner-grid-split { grid-template-columns: 1fr !important; }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-brand">
            ⚡ FIT HUB GYM
            <span class="role-pill">{{ role }}</span>
        </div>
        <ul class="sidebar-menu">
            {% if role == 'member' %}
                <li><a href="/?menu=dashboard" class="{{ 'active' if menu=='dashboard' }}">📊 Dashboard Utama</a></li>
                <li><a href="/?menu=packages" class="{{ 'active' if menu=='packages' }}">📦 Paket Membership</a></li>
                <li><a href="/?menu=checkin" class="{{ 'active' if menu=='checkin' }}">📷 Check-in QR Code</a></li>
                <li><a href="/?menu=workouts" class="{{ 'active' if menu=='workouts' }}">🏋️ Program Latihan</a></li>
                <li><a href="/?menu=progress" class="{{ 'active' if menu=='progress' }}">📈 Progres & Perkembangan</a></li>
                <li><a href="/?menu=profile" class="{{ 'active' if menu=='profile' }}">💳 Pembayaran & Profil</a></li>
            {% elif role == 'trainer' %}
                <li><a href="/?menu=dashboard" class="{{ 'active' if menu=='dashboard' }}">📊 Dashboard Trainer</a></li>
                <li><a href="/?menu=assign_workout" class="{{ 'active' if menu=='assign_workout' }}">📋 Program Latihan Member</a></li>
                <li><a href="/?menu=set_target" class="{{ 'active' if menu=='set_target' }}">🎯 Target Latihan Member</a></li>
                <li><a href="/?menu=monitor_progress" class="{{ 'active' if menu=='monitor_progress' }}">📅 Progres & Jadwal Member</a></li>
            {% elif role == 'admin' %}
                <li><a href="/?menu=dashboard" class="{{ 'active' if menu=='dashboard' }}">📊 Dashboard Admin</a></li>
                <li><a href="/?menu=manage_members" class="{{ 'active' if menu=='manage_members' }}">👥 Kelola Member</a></li>
                <li><a href="/?menu=manage_packages" class="{{ 'active' if menu=='manage_packages' }}">📦 Kelola Paket Membership</a></li>
                <li><a href="/?menu=manage_equipment" class="{{ 'active' if menu=='manage_equipment' }}">⚙️ Data Alat Gym</a></li>
                <li><a href="/?menu=manage_payments" class="{{ 'active' if menu=='manage_payments' }}">💰 Kelola Pembayaran</a></li>
                <li><a href="/?menu=manage_trainers" class="{{ 'active' if menu=='manage_trainers' }}">🏋️ Kelola Trainer</a></li>
            {% elif role == 'owner' %}
                <li><a href="/?menu=dashboard" class="{{ 'active' if menu=='dashboard' }}">📊 Dashboard Eksekutif</a></li>
            {% endif %}
        </ul>
        <div class="sidebar-footer">
            <a href="/logout" class="btn-logout">Keluar Sistem</a>
        </div>
    </div>
    
    <div class="main-container">
        <div class="header">
            <div class="header-title">FIT HUB GYM ACCESS</div>
            <div class="user-info">Akun: <span>{{ session.name }} ({{ session.unique_code }})</span></div>
        </div>
        <div class="content" {% if bg_url %}style="background-image: url('{{ bg_url }}');"{% endif %}>
            <div class="content-inner">
                {% block content %}{% endblock %}
            </div>
        </div>
    </div>
</body>
</html>
'''

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8"><title>Login - FIT HUB GYM ACCESS</title></head>
<body style="background: linear-gradient(rgba(11, 15, 25, 0.75), rgba(11, 15, 25, 0.85)), url('https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1920&q=80'); background-size: cover; background-position: center; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: 'Inter', sans-serif;">
    <div style="background: rgba(19, 27, 46, 0.85); backdrop-filter: blur(12px); padding: 45px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); width: 100%; max-width: 420px; border: 1px solid rgba(255, 255, 255, 0.1); border-top: 4px solid #f5b000;">
        <h2 style="text-align: center; margin-bottom: 25px; color: #f8fafc; font-weight: 800; font-size: 24px; letter-spacing: 0.5px;">FIT HUB GYM <span style="color: #f5b000;">ACCESS</span></h2>
        {% if error %}<div style="background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.4); color: #ef4444; padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 20px; text-align: center;">{{ error }}</div>{% endif %}
        <form method="POST">
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; font-size: 13px; color: #94a3b8; font-weight: 600;">Kode Unik / Nama / Email</label>
                <input type="text" name="login_input" required placeholder="Contoh: MEM001 / Andi Pratama" style="width: 100%; padding: 12px 16px; background: rgba(11, 15, 25, 0.9); border: 1px solid #1e293b; border-radius: 8px; color: #fff; font-size: 15px; box-sizing: border-box;">
            </div>
            <div style="margin-bottom: 25px;">
                <label style="display: block; margin-bottom: 8px; font-size: 13px; color: #94a3b8; font-weight: 600;">Password</label>
                <input type="password" name="password" required placeholder="••••••••" style="width: 100%; padding: 12px 16px; background: rgba(11, 15, 25, 0.9); border: 1px solid #1e293b; border-radius: 8px; color: #fff; font-size: 15px; box-sizing: border-box;">
            </div>
            <button type="submit" style="width: 100%; padding: 14px; background: #f5b000; border: none; border-radius: 8px; color: #0b0f19; font-size: 15px; font-weight: 800; cursor: pointer; box-shadow: 0 4px 15px rgba(245,176,0,0.3);">MASUK SISTEM</button>
        </form>
        <div style="font-size: 12px; color: #94a3b8; text-align: center; margin-top: 25px; line-height: 1.6;">
            <b>Akun Demo Default:</b><br>
            Member: <b>Andi Pratama</b> (MEM001)<br>
            Trainer: <b>Rian Fitness</b> (TRN001)<br>
            Admin: <b>Siti Aminah</b> (ADM001) | Owner: <b>Budi Santoso</b> (OWN001)<br>
            Password semua: <code>password123</code>
        </div>
    </div>
</body>
</html>
'''

SCAN_RESULT_HTML = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Check-in Gym Success</title>
</head>
<body style="background:#0b0f19; color:#f8fafc; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; font-family:'Inter', sans-serif;">
    <div style="background:#131b2e; padding:35px; border-radius:18px; border:1px solid #1e293b; border-top:4px solid #10b981; max-width:380px; width:90%; text-align:center; box-shadow:0 15px 35px rgba(0,0,0,0.5);">
        <div style="font-size:50px; margin-bottom:10px;">✅</div>
        <h2 style="color:#10b981; margin-bottom:10px;">CHECK-IN BERHASIL</h2>
        <p style="color:#94a3b8; font-size:14px; margin-bottom:20px;">Akses gerbang pintu gym telah diverifikasi secara otomatis.</p>
        
        <div style="background:#0b0f19; padding:15px; border-radius:10px; text-align:left; font-size:14px; line-height:1.8; margin-bottom:20px; border:1px solid #1e293b;">
            <b>Nama Member:</b> {{ user['name'] }}<br>
            <b>Kode Unik:</b> {{ user['unique_code'] }}<br>
            <b>Waktu Masuk:</b> {{ time_now }}<br>
            <b>Status Pintu:</b> <span style="color:#10b981; font-weight:bold;">TERBUKA</span>
        </div>
        
        <a href="/" style="display:inline-block; padding:12px 20px; background:#f5b000; color:#121212; text-decoration:none; font-weight:bold; border-radius:8px; font-size:14px;">Kembali ke Dashboard</a>
    </div>
</body>
</html>
'''

@app.route('/qris_image')
def serve_qris():
    for filename in ['qris_gopay.png', 'qris_gopay.jpg', 'qris_gopay.jpeg', 'qris.png', 'qris.jpg']:
        if os.path.exists(filename):
            return send_from_directory('.', filename)
    qr_url = f"https://quickchart.io/qr?text=GOPAY_TRANSFER_{GOPAY_NUMBER}&size=220&margin=1"
    return redirect(qr_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip().lower()
        password = request.form.get('password', '').strip()
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE (LOWER(unique_code) = ? OR LOWER(name) = ? OR LOWER(email) = ?) AND password = ?", 
                       (login_input, login_input, login_input, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']
            session['unique_code'] = user['unique_code']
            return redirect(url_for('dashboard'))
        error = 'Kode/Nama/Email atau password salah.'
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/qr_checkin/<unique_code>')
def qr_checkin(unique_code):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE unique_code = ?", (unique_code,))
    user = cursor.fetchone()
    
    if user:
        current_wib_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO checkins (user_id, checkin_time, status) VALUES (?, ?, 'Berhasil')", 
                       (user['id'], current_wib_time))
        conn.commit()
        conn.close()
        return render_template_string(SCAN_RESULT_HTML, user=user, time_now=current_wib_time)
    
    conn.close()
    return "<h1>QR Code Tidak Valid</h1>", 400

@app.route('/')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    menu = request.args.get('menu', 'dashboard')
    search_query = request.args.get('q', '').strip().lower()
    role = session['role']
    user_id = session['user_id']
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    data = {}
    bg_url = None

    if role == 'member':
        MEMBER_BACKGROUNDS = {
            'dashboard': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1920&q=80',
            'packages': 'https://images.unsplash.com/photo-1540497077202-7c8a3999166f?auto=format&fit=crop&w=1920&q=80',
            'checkin': 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?auto=format&fit=crop&w=1920&q=80',
            'workouts': 'https://images.unsplash.com/photo-1517963879433-6ad2b056d712?auto=format&fit=crop&w=1920&q=80',
            'progress': 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=1920&q=80',
            'profile': 'https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&w=1920&q=80'
        }
        bg_url = MEMBER_BACKGROUNDS.get(menu, MEMBER_BACKGROUNDS['dashboard'])

        cursor.execute("SELECT * FROM member_profiles WHERE user_id = ?", (user_id,))
        data['profile'] = cursor.fetchone()
        cursor.execute("SELECT * FROM checkins WHERE user_id = ? ORDER BY id DESC", (user_id,))
        data['checkins'] = cursor.fetchall()
        cursor.execute("SELECT * FROM workouts WHERE member_id = ?", (user_id,))
        data['workouts'] = cursor.fetchall()
        cursor.execute("SELECT * FROM member_progress WHERE member_id = ? ORDER BY recorded_date DESC", (user_id,))
        data['progress'] = cursor.fetchall()
        cursor.execute("SELECT payments.*, membership_packages.package_name FROM payments JOIN membership_packages ON payments.package_id = membership_packages.id WHERE member_id = ? ORDER BY payments.id DESC", (user_id,))
        data['payments'] = cursor.fetchall()
        cursor.execute("SELECT * FROM membership_packages")
        data['packages'] = cursor.fetchall()

    elif role == 'trainer':
        cursor.execute("SELECT * FROM users WHERE role = 'member'")
        data['members'] = cursor.fetchall()
        cursor.execute("SELECT workouts.*, users.name as member_name FROM workouts JOIN users ON workouts.member_id = users.id ORDER BY schedule_date DESC")
        data['workouts'] = cursor.fetchall()
        cursor.execute("SELECT member_targets.*, users.name as member_name FROM member_targets JOIN users ON member_targets.member_id = users.id ORDER BY member_targets.id DESC")
        data['targets'] = cursor.fetchall()

    elif role == 'admin':
        if search_query:
            cursor.execute("SELECT * FROM users WHERE role = 'member' AND (name LIKE ? OR unique_code LIKE ? OR email LIKE ?)", 
                           (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        else:
            cursor.execute("SELECT * FROM users WHERE role = 'member'")
        data['members'] = cursor.fetchall()
        cursor.execute("SELECT * FROM users WHERE role = 'trainer'")
        data['trainers'] = cursor.fetchall()
        cursor.execute("SELECT * FROM membership_packages")
        data['packages'] = cursor.fetchall()
        cursor.execute("SELECT * FROM equipment")
        data['equipment'] = cursor.fetchall()
        cursor.execute("SELECT payments.*, users.name FROM payments JOIN users ON payments.member_id = users.id ORDER BY payments.id DESC")
        data['payments'] = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='member'")
        data['total_members'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM checkins")
        data['total_checkins'] = cursor.fetchone()[0]

    elif role == 'owner':
        # 1. Total Revenue
        cursor.execute("SELECT SUM(amount) FROM payments WHERE status='Lunas'")
        total_rev = cursor.fetchone()[0]
        data['total_revenue'] = total_rev if total_rev is not None else 0

        # 2. Total Active Members (remaining_days > 0)
        cursor.execute("SELECT COUNT(*) FROM member_profiles WHERE remaining_days > 0")
        data['total_active_members'] = cursor.fetchone()[0]

        # 3. Check-ins Today
        today_str = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM checkins WHERE checkin_time LIKE ?", (f"{today_str}%",))
        data['checkins_today'] = cursor.fetchone()[0]

        # 4. Total Members registered
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='member'")
        data['total_members'] = cursor.fetchone()[0]

        # 5. Memberships Expiring Soon (remaining_days <= 7 and > 0)
        cursor.execute("SELECT COUNT(*) FROM member_profiles WHERE remaining_days <= 7 AND remaining_days > 0")
        data['expiring_soon'] = cursor.fetchone()[0]

        # 6. Total Successful Transactions
        cursor.execute("SELECT COUNT(*) FROM payments WHERE status='Lunas'")
        data['successful_transactions'] = cursor.fetchone()[0]

        # 7. Total Checkins
        cursor.execute("SELECT COUNT(*) FROM checkins")
        data['total_checkins'] = cursor.fetchone()[0]

        # 8. Recent Transactions (Limit 5)
        cursor.execute('''
            SELECT payments.*, users.name as member_name, membership_packages.package_name 
            FROM payments 
            JOIN users ON payments.member_id = users.id 
            LEFT JOIN membership_packages ON payments.package_id = membership_packages.id 
            WHERE payments.status='Lunas' 
            ORDER BY payments.id DESC LIMIT 5
        ''')
        data['recent_payments'] = cursor.fetchall()

        # 9. Recent Check-ins (Limit 5)
        cursor.execute('''
            SELECT checkins.*, users.name as member_name, users.unique_code 
            FROM checkins 
            JOIN users ON checkins.user_id = users.id 
            ORDER BY checkins.id DESC LIMIT 5
        ''')
        data['recent_checkins'] = cursor.fetchall()

        # 10. Monthly revenue aggregation for chart
        cursor.execute("SELECT payment_date, amount FROM payments WHERE status='Lunas'")
        all_payments = cursor.fetchall()
        monthly_rev = {}
        for p in all_payments:
            p_date = p['payment_date']
            if p_date and len(p_date) >= 7:
                month_key = p_date[:7]
                monthly_rev[month_key] = monthly_rev.get(month_key, 0) + p['amount']
        data['monthly_revenue'] = monthly_rev

    conn.close()

    body_content = ""
    
    if role == 'member':
        if menu == 'dashboard':
            p = data['profile'] or {'remaining_days': 30, 'status_paket': 'Paket Premium'}
            body_content = f'''
                <span class="motto-tag">BETTER THAN YESTERDAY</span>
                <h2>Dashboard Utama Member</h2>
                <p style="margin-bottom:25px;">Selamat datang kembali, <b>{session['name']}</b>!</p>
                <div class="card-grid">
                    <div class="card"><h3>Sisa Hari Membership</h3><div class="value">{p["remaining_days"]} Hari</div></div>
                    <div class="card"><h3>Status Paket Aktif</h3><div class="value" style="font-size:18px; color:var(--success);">{p["status_paket"]}</div></div>
                    <div class="card"><h3>Jadwal Latihan Hari Ini</h3><div class="value" style="font-size:16px;">Push & Core Workout</div></div>
                </div>
            '''
        elif menu == 'packages':
            rows = "".join([f"<tr><td><b>{pkg['package_name']}</b></td><td>{pkg['duration_months']} Bulan ({pkg['duration_months']*30} Hari)</td><td>Rp {pkg['price']:,.0f}</td><td><button class='btn-primary' style='padding:8px 16px; font-size:13px;' onclick='openPaymentModal({pkg["id"]}, \"{pkg["package_name"]}\", {pkg["price"]}, {pkg["duration_months"]})'>Pilih Paket</button></td></tr>" for pkg in data['packages']])
            body_content = f'''
                <span class="motto-tag">MEMBERSHIP ACCESS</span>
                <h2>Paket Membership</h2>
                <p style="margin-bottom:20px;">Pilihan paket fleksibel untuk kebutuhan kebugaran Anda.</p>
                <table><tr><th>Nama Paket</th><th>Durasi</th><th>Harga</th><th>Aksi</th></tr>{rows}</table>

                <!-- MODAL CHECKOUT PEMBAYARAN GOPAY & QRIS -->
                <div id="paymentModal" class="modal-overlay">
                    <div class="modal-box">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                            <h3 style="font-size:18px; color:#f8fafc;">Checkout Pembayaran Gym</h3>
                            <button onclick="closePaymentModal()" style="background:none; border:none; color:#94a3b8; font-size:20px; cursor:pointer;">✕</button>
                        </div>
                        
                        <div style="background:#0b0f19; padding:15px; border-radius:10px; margin-bottom:20px; border:1px solid rgba(255,255,255,0.1);">
                            <div style="font-size:13px; color:#94a3b8;">Paket Yang Dipilih:</div>
                            <div id="modalPackageName" style="font-size:18px; font-weight:bold; color:#f5b000;">-</div>
                            <div id="modalPackagePrice" style="font-size:20px; font-weight:800; color:#fff; margin-top:5px;">Rp 0</div>
                        </div>

                        <form action="/action" method="POST">
                            <input type="hidden" name="action_type" value="process_payment">
                            <input type="hidden" name="package_id" id="inputPackageId">
                            <input type="hidden" name="duration_months" id="inputDurationMonths">
                            <input type="hidden" name="amount" id="inputAmount">
                            
                            <label style="margin-bottom:12px; display:block;">Pilih Metode Pembayaran:</label>
                            
                            <div class="payment-method-card" onclick="selectPaymentMethod('qris')">
                                <div><b>📱 Scan QRIS GoPay / DANA Resmi</b><br><small style="color:#94a3b8;">Bisa discan pakai GoPay, DANA, OVO, ShopeePay & m-Banking</small></div>
                                <input type="radio" name="payment_method" id="radioQris" value="qris" required>
                            </div>

                            <div class="payment-method-card" onclick="selectPaymentMethod('gopay_direct')">
                                <div><b>💙 Direct GoPay / Transfer Nomor HP</b><br><small style="color:#94a3b8;">Transfer langsung ke Nomor GoPay Pengelola</small></div>
                                <input type="radio" name="payment_method" id="radioGopay" value="gopay_direct">
                            </div>

                            <!-- DETAIL QRIS -->
                            <div id="qrisDetail" style="display:none; text-align:center; padding:15px; background:#0b0f19; border-radius:10px; margin:15px 0; border:1px solid rgba(245, 176, 0, 0.3);">
                                <p style="font-size:13px; color:#f8fafc; font-weight:bold; margin-bottom:10px;">Scan QRIS GoPay / DANA Di Bawah Ini:</p>
                                <img src="/qris_image" style="width:200px; height:200px; border-radius:10px; background:#fff; padding:8px; display:inline-block;" alt="QRIS GoPay">
                                <p style="font-size:12px; color:#94a3b8; margin-top:10px;">A/N: <b style="color:#f5b000;">{GOPAY_NAME}</b> ({GOPAY_NUMBER})</p>
                            </div>

                            <!-- DETAIL GOPAY DIRECT -->
                            <div id="gopayDetail" style="display:none; padding:15px; background:#0b0f19; border-radius:10px; margin:15px 0; font-size:13px; border:1px solid rgba(245, 176, 0, 0.3);">
                                <b>Nomor HP GoPay / DANA:</b><br>
                                <code style="color:#f5b000; font-size:18px; font-weight:bold;">{GOPAY_NUMBER}</code><br>
                                <b>Atas Nama:</b> {GOPAY_NAME}<br>
                                <small style="color:#94a3b8; display:block; margin-top:6px;">Lakukan transfer GoPay/DANA sesuai nominal harga paket di atas.</small>
                            </div>

                            <button type="submit" class="btn-primary" style="width:100%; margin-top:15px; padding:14px;">SAYA SUDAH BAYAR / KONFIRMASI</button>
                        </form>
                    </div>
                </div>

                <script>
                    function openPaymentModal(id, name, price, duration) {{
                        document.getElementById('paymentModal').style.display = 'flex';
                        document.getElementById('modalPackageName').innerText = name;
                        document.getElementById('modalPackagePrice').innerText = 'Rp ' + price.toLocaleString('id-ID');
                        document.getElementById('inputPackageId').value = id;
                        document.getElementById('inputDurationMonths').value = duration;
                        document.getElementById('inputAmount').value = price;
                    }}
                    function closePaymentModal() {{
                        document.getElementById('paymentModal').style.display = 'none';
                    }}
                    function selectPaymentMethod(type) {{
                        document.getElementById('qrisDetail').style.display = (type === 'qris') ? 'block' : 'none';
                        document.getElementById('gopayDetail').style.display = (type === 'gopay_direct') ? 'block' : 'none';
                        if(type === 'qris') document.getElementById('radioQris').checked = true;
                        if(type === 'gopay_direct') document.getElementById('radioGopay').checked = true;
                    }}
                </script>
            '''
        elif menu == 'checkin':
            rows = "".join([f"<tr><td>{c['checkin_time']}</td><td><span class='badge badge-success'>{c['status']}</span></td></tr>" for c in data['checkins']])
            qr_valid_url = f"{request.host_url}qr_checkin/{session['unique_code']}"
            
            body_content = f'''
                <span class="motto-tag">NO EXCUSES</span>
                <h2>Check-in QR Code</h2>
                <p style="margin-bottom:20px;">Arahkan Kamera HP / Google Lens ke QR Code ini untuk check-in otomatis.</p>
                <div class="panel-box" style="text-align:center;">
                    <div style="background:#fff; padding:15px; display:inline-block; border-radius:12px; margin-bottom:15px;">
                        <img src="https://quickchart.io/qr?text={qr_valid_url}&size=200" alt="QR Valid">
                    </div>
                    <br>
                    <a href="/qr_checkin/{session['unique_code']}" target="_blank" class="btn-primary">Simulasikan Scan Masuk</a>
                </div>
                <h3>Riwayat Check-in</h3><table><tr><th>Waktu (WIB)</th><th>Status</th></tr>{rows}</table>
            '''
        elif menu == 'workouts':
            rows = "".join([f"<tr><td>{w['exercise_name']}</td><td>{w['sets']} Set</td><td>{w['reps']} Rep</td><td>{w['weight_kg']} kg</td><td>{w['schedule_date']} {w['schedule_time']}</td><td><span class='badge badge-warning'>{w['status']}</span></td></tr>" for w in data['workouts']])
            body_content = f'''
                <span class="motto-tag">DISCIPLINE BUILDS RESULTS</span>
                <h2>Program Latihan</h2>
                <p style="margin-bottom:20px;">Daftar latihan langsung dari trainer pribadi Anda.</p>
                <table><tr><th>Latihan</th><th>Set</th><th>Repetisi</th><th>Beban</th><th>Jadwal</th><th>Status</th></tr>{rows}</table>
            '''
        elif menu == 'progress':
            rows = "".join([f"<tr><td>{pr['recorded_date']}</td><td>{pr['weight']} kg</td><td>{pr['body_fat']}%</td><td>{pr['stomach_circumference']} cm</td></tr>" for pr in data['progress']])
            body_content = f'''
                <span class="motto-tag">SMALL STEPS BIG CHANGES</span>
                <h2>Progres & Perkembangan Fisik</h2>
                <p style="margin-bottom:20px;">Rekam jejak perubahan tubuh Anda.</p>
                <table><tr><th>Tanggal</th><th>Berat Badan</th><th>Body Fat</th><th>Lingkar Perut</th></tr>{rows}</table>
            '''
        elif menu == 'profile':
            rows = "".join([f"<tr><td>#TRX-{p['id']}</td><td>{p['package_name']}</td><td>Rp {p['amount']:,.0f}</td><td>{p['payment_date']}</td><td><span class='badge badge-success'>{p['status']}</span></td></tr>" for p in data['payments']])
            body_content = f'''
                <span class="motto-tag">HEALTH IS WEALTH</span>
                <h2>Pembayaran & Profil</h2>
                <p style="margin-bottom:20px;">Riwayat transaksi dan pengaturan akun.</p>
                <table style="margin-bottom:25px;"><tr><th>ID Transaksi</th><th>Paket</th><th>Jumlah</th><th>Tanggal</th><th>Status</th></tr>{rows}</table>
                <div class="panel-box">
                    <h3>Pengaturan Profil Pribadi</h3>
                    <form onsubmit="event.preventDefault(); alert('Profil berhasil diperbarui!');" style="margin-top:15px;">
                        <label>Nama Lengkap</label><input type="text" value="{session['name']}">
                        <label>Password Baru</label><input type="password" placeholder="Kosongkan jika tidak diubah">
                        <button type="submit" class="btn-primary">Simpan Perubahan</button>
                    </form>
                </div>
            '''

    elif role == 'trainer':
        if menu == 'dashboard':
            body_content = f'''
                <h2>Dashboard Trainer</h2>
                <p style="margin-bottom:25px;">Selamat bertugas, <b>{session['name']}</b>!</p>
                <div class="card-grid">
                    <div class="card"><h3>Member Binaan Aktif</h3><div class="value">{len(data['members'])} Orang</div></div>
                    <div class="card"><h3>Program Latihan Aktif</h3><div class="value">{len(data['workouts'])} Program</div></div>
                    <div class="card"><h3>Member Terbaru</h3><div class="value" style="font-size:16px;">{data['members'][0]['name'] if data['members'] else '-'}</div></div>
                </div>
            '''
        elif menu == 'assign_workout':
            options = "".join([f"<option value='{m['id']}'>{m['name']} ({m['unique_code']})</option>" for m in data['members']])
            body_content = f'''
                <h2>Program Latihan Member</h2>
                <div class="panel-box">
                    <form action="/action" method="POST">
                        <input type="hidden" name="action_type" value="add_workout">
                        <label>Pilih Member Binaan</label><select name="member_id" required>{options}</select>
                        <label>Nama Latihan (Bench Press, Squat, Plank)</label><input type="text" name="exercise_name" required>
                        <div style="display:flex; gap:15px;">
                            <div style="flex:1;"><label>Set</label><input type="number" name="sets" required></div>
                            <div style="flex:1;"><label>Repetisi</label><input type="number" name="reps" required></div>
                            <div style="flex:1;"><label>Beban (kg)</label><input type="number" step="0.5" name="weight_kg" required></div>
                        </div>
                        <div style="display:flex; gap:15px;">
                            <div style="flex:1;"><label>Tanggal Latihan</label><input type="date" name="schedule_date" required></div>
                            <div style="flex:1;"><label>Jam Latihan</label><input type="time" name="schedule_time" required></div>
                        </div>
                        <button type="submit" class="btn-primary">Kirim Program Latihan</button>
                    </form>
                </div>
            '''
        elif menu == 'set_target':
            options = "".join([f"<option value='{m['id']}'>{m['name']}</option>" for m in data['members']])
            target_rows = "".join([f"<tr><td>{t['member_name']}</td><td>{t['target_weight']} kg</td><td>{t['target_body_fat']}%</td><td>{t['notes'] or '-'}</td></tr>" for t in data['targets']]) or "<tr><td colspan='4' style='text-align:center; color:#94a3b8;'>Belum ada target.</td></tr>"
            body_content = f'''
                <h2>Target Latihan Member</h2>
                <div class="panel-box">
                    <form action="/action" method="POST">
                        <input type="hidden" name="action_type" value="set_target">
                        <label>Pilih Member Binaan</label><select name="member_id" required>{options}</select>
                        <label>Target Berat Badan (kg)</label><input type="number" step="0.1" name="target_weight" required>
                        <label>Target Body Fat (%)</label><input type="number" step="0.1" name="target_body_fat" required>
                        <label>Catatan Target</label><textarea rows="3" name="notes"></textarea>
                        <button type="submit" class="btn-primary">Tetapkan Target</button>
                    </form>
                </div>
                <h3>Target yang Sudah Ditetapkan</h3>
                <table><tr><th>Member</th><th>Target Berat</th><th>Target Body Fat</th><th>Catatan</th></tr>{target_rows}</table>
            '''
        elif menu == 'monitor_progress':
            rows = ""
            for w in data['workouts']:
                dt_obj = datetime.strptime(w['schedule_date'], '%Y-%m-%d') if w['schedule_date'] else datetime.now()
                day_name = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'][dt_obj.weekday()]
                month_name = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'][dt_obj.month - 1]
                rows += f"<tr><td>{w['member_name']}</td><td>{w['exercise_name']} ({w['sets']}x{w['reps']})</td><td>{dt_obj.day} {month_name} {dt_obj.year} ({day_name}) - {w['schedule_time']}</td><td><span class='badge {'badge-success' if w['status']=='Selesai' else 'badge-warning'}'>{w['status']}</span></td></tr>"
            body_content = f'<h2>Progres & Jadwal Member</h2><table><tr><th>Member</th><th>Latihan</th><th>Jadwal</th><th>Status</th></tr>{rows}</table>'

    elif role == 'admin':
        if menu == 'dashboard':
            body_content = f'''
                <h2>Dashboard Admin Operasional</h2>
                <div class="card-grid">
                    <div class="card"><h3>Total Member</h3><div class="value">{data['total_members']} Orang</div></div>
                    <div class="card"><h3>Check-in Hari Ini</h3><div class="value">{data['total_checkins']} Sesi</div></div>
                    <div class="card"><h3>Inventaris Layak</h3><div class="value">96%</div></div>
                </div>
            '''
        elif menu == 'manage_members':
            rows = "".join([f"<tr><td>{m['unique_code']}</td><td><b>{m['name']}</b></td><td>{m['email']}</td><td>{m['phone'] or '-'}</td><td><form action='/action' method='POST' style='display:inline;'><input type='hidden' name='action_type' value='delete_user'><input type='hidden' name='id' value='{m['id']}'><button type='submit' class='btn-danger'>Hapus</button></form></td></tr>" for m in data['members']])
            body_content = f'''
                <h2>Kelola Data Member</h2>
                <div class="panel-box">
                    <h3>➕ Tambah Member Baru</h3>
                    <form action="/action" method="POST" style="margin-top:15px;">
                        <input type="hidden" name="action_type" value="add_user">
                        <input type="hidden" name="role" value="member">
                        <label>Nama Lengkap Member</label><input type="text" name="name" required placeholder="Contoh: Rina Wijaya">
                        <label>Email</label><input type="email" name="email" required placeholder="rina@gmail.com">
                        <label>Nomor Telepon</label><input type="text" name="phone" placeholder="08123456789">
                        <label>Password Akun</label><input type="password" name="password" required value="password123">
                        <button type="submit" class="btn-primary">Daftarkan Member Baru</button>
                    </form>
                </div>
                <h3>Daftar Member Terdaftar</h3>
                <form method="GET" action="/"><input type="hidden" name="menu" value="manage_members"><input type="text" name="q" class="search-box" placeholder="Cari member..." value="{search_query}"></form>
                <table><tr><th>Kode Unik</th><th>Nama Member</th><th>Email</th><th>Telepon</th><th>Aksi</th></tr>{rows}</table>
            '''
        elif menu == 'manage_trainers':
            rows = "".join([f"<tr><td>{t['unique_code']}</td><td><b>{t['name']}</b></td><td>{t['email']}</td><td>{t['phone'] or '-'}</td><td><form action='/action' method='POST' style='display:inline;'><input type='hidden' name='action_type' value='delete_user'><input type='hidden' name='id' value='{t['id']}'><button type='submit' class='btn-danger'>Hapus</button></form></td></tr>" for t in data['trainers']])
            body_content = f'''
                <h2>Kelola Data Trainer</h2>
                <div class="panel-box">
                    <h3>➕ Tambah Trainer Baru</h3>
                    <form action="/action" method="POST" style="margin-top:15px;">
                        <input type="hidden" name="action_type" value="add_user">
                        <input type="hidden" name="role" value="trainer">
                        <label>Nama Lengkap Trainer</label><input type="text" name="name" required placeholder="Contoh: Coach Hendra">
                        <label>Email</label><input type="email" name="email" required placeholder="hendra@gym.com">
                        <label>Nomor Telepon</label><input type="text" name="phone" placeholder="0812998877">
                        <label>Password Akun</label><input type="password" name="password" required value="password123">
                        <button type="submit" class="btn-primary">Daftarkan Trainer Baru</button>
                    </form>
                </div>
                <h3>Daftar Trainer Aktif</h3>
                <table><tr><th>Kode Unik</th><th>Nama Trainer</th><th>Email</th><th>Telepon</th><th>Aksi</th></tr>{rows}</table>
            '''
        elif menu == 'manage_packages':
            rows = "".join([f"<tr><td>{p['package_name']}</td><td>{p['duration_months']} Bulan</td><td>Rp {p['price']:,.0f}</td><td><span class='badge badge-success'>{p['status']}</span></td></tr>" for p in data['packages']])
            body_content = f'<h2>Kelola Paket Membership</h2><table><tr><th>Paket</th><th>Durasi</th><th>Harga</th><th>Status</th></tr>{rows}</table>'
        elif menu == 'manage_equipment':
            rows = "".join([f"<tr><td>{eq['equipment_name']}</td><td>{eq['category']}</td><td><span class='badge {'badge-success' if eq['status']=='Tersedia' else ('badge-warning' if eq['status']=='Perbaikan' else 'badge-danger')}'>{eq['status']}</span></td></tr>" for eq in data['equipment']])
            body_content = f'''
                <h2>Data Alat Gym</h2>
                <div class="panel-box">
                    <form action="/action" method="POST">
                        <input type="hidden" name="action_type" value="add_equipment">
                        <label>Nama Alat</label><input type="text" name="equipment_name" required>
                        <label>Kategori</label><select name="category"><option value="Cardio">Cardio</option><option value="Beban">Beban</option></select>
                        <label>Status</label><select name="status"><option value="Tersedia">Tersedia</option><option value="Perbaikan">Perbaikan</option><option value="Rusak">Rusak</option></select>
                        <button type="submit" class="btn-primary">Tambah Alat</button>
                    </form>
                </div>
                <table><tr><th>Nama Alat</th><th>Kategori</th><th>Status</th></tr>{rows}</table>
            '''
        elif menu == 'manage_payments':
            rows = "".join([f"<tr><td>{p['name']}</td><td>Rp {p['amount']:,.0f}</td><td>{p['payment_date']}</td><td><span class='badge {'badge-success' if p['status']=='Lunas' else 'badge-warning'}'>{p['status']}</span></td><td><button class='btn-primary' style='padding:4px 10px; font-size:11px;'>Terverifikasi</button></td></tr>" for p in data['payments']])
            body_content = f'<h2>Kelola Pembayaran Member</h2><table><tr><th>Member</th><th>Jumlah</th><th>Tanggal Transaksi</th><th>Status</th><th>Aksi</th></tr>{rows}</table>'

    elif role == 'owner':
        formatted_revenue = f"Rp {data['total_revenue']:,.0f}"
        
        # Render SVG chart dynamically
        months_data = data['monthly_revenue']
        sorted_months = sorted(months_data.keys())[-6:]
        chart_height = 200
        bar_width = 45
        gap = 35
        start_x = 45
        
        if not sorted_months:
            chart_content = '<div style="text-align:center; padding:50px; color:#94a3b8;">Belum ada data transaksi lunas untuk ditampilkan pada grafik.</div>'
        else:
            max_val = max(months_data.values()) if months_data and max(months_data.values()) > 0 else 1000000
            svg_items = []
            for i, m in enumerate(sorted_months):
                val = months_data[m]
                bar_h = int((val / max_val) * 120) if max_val > 0 else 10
                x = start_x + (i * (bar_width + gap))
                y = chart_height - bar_h - 35
                try:
                    dt_parsed = datetime.strptime(m, '%Y-%m')
                    m_label = dt_parsed.strftime('%b %Y')
                except:
                    m_label = m
                
                svg_items.append(f'''
                    <g>
                        <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_h}" fill="#f5b000" rx="6" opacity="0.9">
                            <title>{m_label}: Rp {val:,.0f}</title>
                        </rect>
                        <text x="{x + bar_width/2}" y="{chart_height - 12}" fill="#94a3b8" font-size="11" text-anchor="middle">{m_label}</text>
                        <text x="{x + bar_width/2}" y="{y - 8}" fill="#f8fafc" font-size="10" font-weight="bold" text-anchor="middle">Rp {val/1000:,.0f}k</text>
                    </g>
                ''')
            chart_content = f'''
                <svg viewBox="0 0 550 {chart_height}" style="width:100%; height:auto; max-height:220px;">
                    <line x1="30" y1="{chart_height-30}" x2="520" y2="{chart_height-30}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
                    {"".join(svg_items)}
                </svg>
            '''

        pay_rows = ""
        if data['recent_payments']:
            for p in data['recent_payments']:
                pay_rows += f"<tr><td><b>{p['member_name']}</b></td><td>{p['package_name'] or 'Membership'}</td><td>{p['payment_date']}</td><td><b>Rp {p['amount']:,.0f}</b></td><td><span class='badge badge-success'>{p['status']}</span></td></tr>"
        else:
            pay_rows = "<tr><td colspan='5' style='text-align:center; color:#94a3b8;'>Belum ada riwayat transaksi.</td></tr>"

        checkin_rows = ""
        if data['recent_checkins']:
            for c in data['recent_checkins']:
                checkin_rows += f"<tr><td><b>{c['member_name']}</b> <small style='color:#94a3b8;'>({c['unique_code']})</small></td><td>{c['checkin_time']}</td><td><span class='badge badge-success'>{c['status']}</span></td></tr>"
        else:
            checkin_rows = "<tr><td colspan='3' style='text-align:center; color:#94a3b8;'>Belum ada check-in hari ini.</td></tr>"

        alert_box = ""
        if data['expiring_soon'] > 0:
            alert_box += f'''
                <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.35); padding: 16px 22px; border-radius: 12px; margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <span style="font-size: 22px;">⚠️</span>
                        <div>
                            <b style="color: #f59e0b; font-size: 14px;">Pemberitahuan Penting: {data['expiring_soon']} Member Masa Aktifnya Segera Berakhir (&le; 7 hari)</b>
                            <p style="color: #94a3b8; font-size: 12px; margin: 2px 0 0 0;">Harap koordinasikan dengan tim admin untuk melakukan follow-up perpanjangan paket.</p>
                        </div>
                    </div>
                    <span class="badge badge-warning">Perlu Perhatian</span>
                </div>
            '''

        body_content = f'''
            <span class="motto-tag">EXECUTIVE BUSINESS MONITORING</span>
            <h2>Dashboard Eksekutif Owner</h2>
            <p style="margin-bottom:25px;">Selamat datang kembali, <b>{session['name']}</b>. Berikut adalah laporan performa bisnis "FIT HUB GYM ACCESS".</p>
            
            {alert_box}

            <!-- 6 KARTU STATISTIK UTAMA -->
            <div class="card-grid">
                <div class="card">
                    <h3>Total Pendapatan Gym</h3>
                    <div class="value" style="color: #f5b000;">{formatted_revenue}</div>
                    <small style="color: var(--success); font-size: 11px;">Akumulasi Lunas</small>
                </div>
                <div class="card">
                    <h3>Total Member Aktif</h3>
                    <div class="value">{data['total_active_members']} <span style="font-size: 14px; color: var(--text-muted);">Org</span></div>
                    <small style="color: var(--success); font-size: 11px;">Masa Aktif &gt; 0 Hari</small>
                </div>
                <div class="card">
                    <h3>Check-in Hari Ini</h3>
                    <div class="value">{data['checkins_today']} <span style="font-size: 14px; color: var(--text-muted);">Sesi</span></div>
                    <small style="color: var(--text-muted); font-size: 11px;">Live Hari Ini</small>
                </div>
                <div class="card">
                    <h3>Total Member</h3>
                    <div class="value">{data['total_members']} <span style="font-size: 14px; color: var(--text-muted);">Org</span></div>
                    <small style="color: var(--text-muted); font-size: 11px;">Terdaftar di Sistem</small>
                </div>
                <div class="card">
                    <h3>Segera Berakhir</h3>
                    <div class="value" style="color: var(--warning);">{data['expiring_soon']} <span style="font-size: 14px; color: var(--text-muted);">Org</span></div>
                    <small style="color: var(--warning); font-size: 11px;">Masa Aktif &le; 7 Hari</small>
                </div>
                <div class="card">
                    <h3>Transaksi Berhasil</h3>
                    <div class="value">{data['successful_transactions']} <span style="font-size: 14px; color: var(--text-muted);">Trx</span></div>
                    <small style="color: var(--success); font-size: 11px;">Status Lunas</small>
                </div>
            </div>

            <!-- GRAFIK PENDAPATAN & RINGKASAN -->
            <div class="owner-grid-split" style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px; margin-bottom: 30px;">
                <div class="panel-box" style="max-width: 100%; margin-bottom: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <div>
                            <h3 style="font-size: 16px; color: #f8fafc;">Grafik Tren Pendapatan Bulanan</h3>
                            <p style="font-size: 12px; color: #94a3b8; margin: 2px 0 0 0;">Perkembangan omset pendapatan dari transaksi lunas</p>
                        </div>
                        <span class="badge badge-success">Real-Time Data</span>
                    </div>
                    {chart_content}
                </div>

                <div class="panel-box" style="max-width: 100%; margin-bottom: 0; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <h3 style="font-size: 16px; color: #f8fafc; margin-bottom: 10px;">Ringkasan Operasional</h3>
                        <p style="font-size: 12px; color: #94a3b8; margin-bottom: 20px;">Indikator kesehatan bisnis gym.</p>
                        
                        <div style="display: flex; flex-direction: column; gap: 14px;">
                            <div style="background: rgba(11, 15, 25, 0.6); padding: 12px 15px; border-radius: 10px; border: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 13px; color: #94a3b8;">Rata-rata Trx</span>
                                <b style="color: #f5b000; font-size: 13px;">Rp {int(data['total_revenue'] / data['successful_transactions']) if data['successful_transactions'] > 0 else 0:,.0f}</b>
                            </div>
                            <div style="background: rgba(11, 15, 25, 0.6); padding: 12px 15px; border-radius: 10px; border: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 13px; color: #94a3b8;">Akumulasi Check-in</span>
                                <b style="color: #10b981; font-size: 13px;">{data['total_checkins']} Sesi</b>
                            </div>
                            <div style="background: rgba(11, 15, 25, 0.6); padding: 12px 15px; border-radius: 10px; border: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 13px; color: #94a3b8;">Sistem Server</span>
                                <b style="color: #10b981; font-size: 13px;">🟢 Online (WIB)</b>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TABEL TRANSAKSI TERBARU & CHECK-IN -->
            <div class="owner-grid-split" style="display: grid; grid-template-columns: 1.4fr 1fr; gap: 24px; margin-bottom: 30px;">
                <div class="panel-box" style="max-width: 100%; margin-bottom: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h3 style="font-size: 16px; color: #f8fafc;">Transaksi Pembayaran Terbaru</h3>
                        <span style="font-size: 12px; color: #94a3b8;">5 Teratas</span>
                    </div>
                    <table style="margin-top: 5px;">
                        <tr>
                            <th>Member</th>
                            <th>Paket</th>
                            <th>Tanggal</th>
                            <th>Jumlah</th>
                            <th>Status</th>
                        </tr>
                        {pay_rows}
                    </table>
                </div>

                <div class="panel-box" style="max-width: 100%; margin-bottom: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h3 style="font-size: 16px; color: #f8fafc;">Aktivitas Check-in Terbaru</h3>
                        <span style="font-size: 12px; color: #94a3b8;">Live Log</span>
                    </div>
                    <table style="margin-top: 5px;">
                        <tr>
                            <th>Member</th>
                            <th>Waktu</th>
                            <th>Status</th>
                        </tr>
                        {checkin_rows}
                    </table>
                </div>
            </div>

            <!-- LAPORAN KEUANGAN & REKAPITULASI -->
            <div class="panel-box" style="max-width:100%;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                    <div>
                        <h3 style="font-size:18px; color: #f8fafc;">Laporan Keuangan & Rekapitulasi Bulanan</h3>
                        <p style="font-size:12px; color:#94a3b8; margin:2px 0 0 0;">Rekapitulasi performa bisnis gym secara komprehensif.</p>
                    </div>
                    <button class="btn-primary" onclick="window.print()">Export PDF / Print</button>
                </div>
                <table>
                    <tr>
                        <th>Bulan</th>
                        <th>Total Member Terdaftar</th>
                        <th>Total Pendapatan Lunas</th>
                        <th>Akumulasi Check-in</th>
                    </tr>
                    <tr>
                        <td><b>{datetime.now().strftime('%B %Y')}</b></td>
                        <td>{data['total_members']} Orang</td>
                        <td><b style="color: #f5b000;">{formatted_revenue}</b></td>
                        <td>{data['total_checkins']} Sesi</td>
                    </tr>
                </table>
            </div>
        '''

    full_html = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', body_content)
    return render_template_string(full_html, role=role, menu=menu, bg_url=bg_url)

@app.route('/action', methods=['POST'])
def action():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    action_type = request.form.get('action_type')

    ALLOWED_ROLES = {
        'process_payment': ['member'],
        'add_user': ['admin'],
        'delete_user': ['admin'],
        'add_equipment': ['admin'],
        'add_workout': ['trainer'],
        'set_target': ['trainer'],
    }
    if session.get('role') not in ALLOWED_ROLES.get(action_type, []):
        return "<h1>Akses ditolak</h1>", 403

    next_menu = 'dashboard'
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if action_type == 'process_payment':
        package_id = request.form.get('package_id')
        duration_months = int(request.form.get('duration_months', 1))
        amount = float(request.form.get('amount', 0))
        user_id = session['user_id']
        
        wib_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("INSERT INTO payments (member_id, package_id, amount, payment_date, status) VALUES (?, ?, ?, ?, 'Lunas')",
                       (user_id, package_id, amount, wib_time))
        
        cursor.execute("SELECT package_name FROM membership_packages WHERE id = ?", (package_id,))
        pkg_res = cursor.fetchone()
        package_name = pkg_res[0] if pkg_res else "Paket Premium"

        added_days = duration_months * 30
        cursor.execute("SELECT remaining_days FROM member_profiles WHERE user_id = ?", (user_id,))
        curr = cursor.fetchone()
        
        if curr:
            new_days = curr[0] + added_days
            cursor.execute("UPDATE member_profiles SET remaining_days = ?, status_paket = ? WHERE user_id = ?",
                           (new_days, f"Paket {package_name}", user_id))
        else:
            cursor.execute("INSERT INTO member_profiles (user_id, package_id, remaining_days, status_paket) VALUES (?, ?, ?, ?)",
                           (user_id, package_id, added_days, f"Paket {package_name}"))
        
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard', menu='profile'))

    elif action_type == 'add_user':
        role = request.form.get('role')
        name = request.form.get('name').strip()
        email = request.form.get('email').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password').strip()
        
        if role not in ('member', 'trainer'):
            conn.close()
            return "<h1>Role tidak valid</h1>", 400
        next_menu = 'manage_members' if role == 'member' else 'manage_trainers'
        prefix = 'MEM' if role == 'member' else 'TRN'
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (role,))
        count = cursor.fetchone()[0] + 1
        unique_code = f"{prefix}{count:03d}"

        try:
            cursor.execute("INSERT INTO users (unique_code, name, email, password, role, phone) VALUES (?, ?, ?, ?, ?, ?)",
                           (unique_code, name, email, password, role, phone))
            new_user_id = cursor.lastrowid
            
            if role == 'member':
                cursor.execute("INSERT INTO member_profiles (user_id, package_id, remaining_days, status_paket) VALUES (?, 1, 30, 'Paket Biru')", (new_user_id,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass

    elif action_type == 'delete_user':
        u_id = request.form.get('id')
        cursor.execute("SELECT role FROM users WHERE id = ? AND role IN ('member','trainer')", (u_id,))
        target = cursor.fetchone()
        if target:
            next_menu = 'manage_members' if target[0] == 'member' else 'manage_trainers'
            cursor.execute("DELETE FROM users WHERE id = ?", (u_id,))
            conn.commit()

    elif action_type == 'add_workout':
        cursor.execute("INSERT INTO workouts (trainer_id, member_id, exercise_name, sets, reps, weight_kg, schedule_date, schedule_time, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Belum')",
                       (session['user_id'], request.form['member_id'], request.form['exercise_name'], request.form['sets'], request.form['reps'], request.form['weight_kg'], request.form['schedule_date'], request.form['schedule_time']))
        conn.commit()
        next_menu = 'monitor_progress'

    elif action_type == 'set_target':
        member_id = request.form['member_id']
        cursor.execute("SELECT id FROM member_targets WHERE member_id = ?", (member_id,))
        existing = cursor.fetchone()
        vals = (request.form['target_weight'], request.form['target_body_fat'], request.form.get('notes', '').strip())
        if existing:
            cursor.execute("UPDATE member_targets SET target_weight = ?, target_body_fat = ?, notes = ? WHERE member_id = ?", vals + (member_id,))
        else:
            cursor.execute("INSERT INTO member_targets (member_id, target_weight, target_body_fat, notes) VALUES (?, ?, ?, ?)", (member_id,) + vals)
        conn.commit()
        next_menu = 'set_target'

    elif action_type == 'add_equipment':
        cursor.execute("INSERT INTO equipment (equipment_name, category, status) VALUES (?, ?, ?)",
                       (request.form['equipment_name'], request.form['category'], request.form['status']))
        conn.commit()
        next_menu = 'manage_equipment'

    conn.close()
    return redirect(url_for('dashboard', menu=next_menu))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8080)
