import os
import json
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / 'forum.db'
CONFIG_PATH = BASE_DIR / 'config.json'

# --- Load config ---
def load_config():
    default_cfg = {
        "HOST": "0.0.0.0",
        "PORT": 5000,
        "DEBUG": True,
        "LIMITS": {
            "USERNAME": 50,
            "THREAD_TITLE": 200,
            "POST_CONTENT": 1000
        }
    }
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                user_cfg = json.load(f)
            default_cfg.update(user_cfg)
        except Exception as e:
            print("Warning: could not parse config.json, using defaults.", e)
    return default_cfg

config = load_config()
HOST = config.get("HOST", "0.0.0.0")
PORT = int(config.get("PORT", 5000))
DEBUG = bool(config.get("DEBUG", True))

# --- Limits ---
limits = config.get("LIMITS", {})
MAX_USERNAME = int(limits.get("USERNAME", 50))
MAX_THREAD_TITLE = int(limits.get("THREAD_TITLE", 200))
MAX_POST_CONTENT = int(limits.get("POST_CONTENT", 1000))

app = Flask(__name__, static_folder='static', static_url_path='')
socketio = SocketIO(app, cors_allowed_origins=None, async_mode='eventlet')

# --- DB helpers ---
def get_db_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS threads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(thread_id) REFERENCES threads(id)
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Static ---
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# --- Threads API ---
@app.route('/api/threads', methods=['GET', 'POST'])
def threads():
    conn = get_db_conn()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute('SELECT * FROM threads ORDER BY id DESC')
        threads = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(threads)

    # POST: create new thread
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'title required'}), 400
    if len(title) > MAX_THREAD_TITLE:
        return jsonify({'error': f'title too long (max {MAX_THREAD_TITLE})'}), 400

    # Prevent duplicate thread names
    cur.execute('SELECT id FROM threads WHERE title = ?', (title,))
    if cur.fetchone():
        conn.close()
        return jsonify({'error': 'thread with this title already exists'}), 400

    now = datetime.utcnow().isoformat()
    cur.execute('INSERT INTO threads (title, created_at) VALUES (?, ?)', (title, now))
    thread_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': thread_id, 'title': title, 'created_at': now}), 201

# --- Posts API ---
@app.route('/api/threads/<int:thread_id>/posts', methods=['GET', 'POST'])
def posts(thread_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT id FROM threads WHERE id = ?', (thread_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({'error': 'thread not found'}), 404

    if request.method == 'GET':
        cur.execute('SELECT * FROM posts WHERE thread_id = ? ORDER BY id ASC', (thread_id,))
        posts = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(posts)

    # POST new message
    data = request.get_json() or {}
    username = (data.get('username') or 'Anonymous').strip()
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'error': 'content required'}), 400
    if len(username) > MAX_USERNAME:
        return jsonify({'error': f'username too long (max {MAX_USERNAME})'}), 400
    if len(content) > MAX_POST_CONTENT:
        return jsonify({'error': f'content too long (max {MAX_POST_CONTENT})'}), 400

    now = datetime.utcnow().isoformat()
    cur.execute('INSERT INTO posts (thread_id, username, content, created_at) VALUES (?, ?, ?, ?)',
                (thread_id, username, content, now))
    post_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = dict(cur.fetchone())
    conn.close()

    socketio.emit('new_post', post, namespace='/chat', room=f'thread_{thread_id}')
    return jsonify(post), 201

# --- Delete single thread ---
@app.route('/api/threads/<int:thread_id>', methods=['DELETE'])
def delete_thread(thread_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT id FROM threads WHERE id = ?', (thread_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({'error': 'thread not found'}), 404

    cur.execute('DELETE FROM posts WHERE thread_id = ?', (thread_id,))
    cur.execute('DELETE FROM threads WHERE id = ?', (thread_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'}), 200

# --- Wipe all threads ---
@app.route('/api/threads/wipe', methods=['DELETE'])
def wipe_threads():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS posts')
    cur.execute('DROP TABLE IF EXISTS threads')
    conn.commit()
    conn.close()
    init_db()
    return jsonify({'status': 'all threads wiped'}), 200

# --- SocketIO ---
@socketio.on('join', namespace='/chat')
def on_join(data):
    thread_id = data.get('thread_id')
    username = (data.get('username') or 'Anonymous').strip()
    if not thread_id:
        return
    room = f'thread_{thread_id}'
    join_room(room)
    emit('status', {'msg': f'{username} joined thread {thread_id}'}, room=room)

@socketio.on('leave', namespace='/chat')
def on_leave(data):
    thread_id = data.get('thread_id')
    username = (data.get('username') or 'Anonymous').strip()
    if not thread_id:
        return
    room = f'thread_{thread_id}'
    leave_room(room)
    emit('status', {'msg': f'{username} left thread {thread_id}'}, room=room)

@socketio.on('send_message', namespace='/chat')
def on_message(data):
    thread_id = data.get('thread_id')
    username = (data.get('username') or 'Anonymous').strip()
    content = (data.get('content') or '').strip()
    if not thread_id or not content:
        return
    if len(username) > MAX_USERNAME or len(content) > MAX_POST_CONTENT:
        return

    conn = get_db_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute('INSERT INTO posts (thread_id, username, content, created_at) VALUES (?, ?, ?, ?)',
                (thread_id, username, content, now))
    post_id = cur.lastrowid
    conn.commit()
    cur.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = dict(cur.fetchone())
    conn.close()

    room = f'thread_{thread_id}'
    emit('new_post', post, room=room)

# --- Run server ---
if __name__ == '__main__':
    print(f"Starting server on http://{HOST}:{PORT} (debug={DEBUG})")
    socketio.run(app, host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
