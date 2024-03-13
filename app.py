from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
from passlib.hash import sha256_crypt
import json
import random
import atexit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# Store messages in a dictionary where the key is the username and the value is a list of messages
messages = {}

# Load user data from JSON file
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Load messages from JSON file
def load_messages():
    try:
        with open('messages.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Generate a random color for each username
def generate_random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

# Load users and messages when the application starts
users = load_users()
messages = load_messages()

# Save users and messages when the application stops
def save_data():
    save_users()
    save_messages()

atexit.register(save_data)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and sha256_crypt.verify(password, users[username]['password']):
            session['username'] = username
            session['color'] = generate_random_color()
            return redirect(url_for('chat'))
        else:
            # If the username doesn't exist, create a new user
            if username not in users:
                users[username] = {'password': sha256_crypt.hash(password)}
                save_users()
                session['username'] = username
                session['color'] = generate_random_color()
                return redirect(url_for('chat'))
            else:
                return render_template('login.html', error=True)
    return render_template('login.html', error=False)

@app.route('/check_username', methods=['POST'])
def check_username():
    username = request.json.get('username')
    available = username not in users
    return jsonify({'available': available})

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('index.html', username=session['username'], messages=messages.get(session['username'], []))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@socketio.on('message')
def handle_message(msg):
    if 'username' in session:
        if session['username'] not in messages:
            messages[session['username']] = []
        messages[session['username']].append({'username': session['username'], 'message': msg, 'color': session['color']})
        emit('message', {'username': session['username'], 'message': msg, 'color': session['color']}, broadcast=True)

def save_users():
    with open('users.json', 'w') as f:
        json.dump(users, f)

def save_messages():
    with open('messages.json', 'w') as f:
        json.dump(messages, f)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', allow_unsafe_werkzeug=True)