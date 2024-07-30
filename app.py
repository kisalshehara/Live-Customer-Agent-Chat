from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app)

# In-memory storage for simplicity
chats = {}
users = {}

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        username = request.form['username']
        chat_id = str(int(datetime.now().timestamp() * 1000))
        session['username'] = username
        session['chat_id'] = chat_id
        chats[chat_id] = []
        users[chat_id] = username
        return redirect(url_for('chat_room', chat_id=chat_id))
    return render_template('chat.html')

@app.route('/admin')
def admin():
    return render_template('admin.html', chats=chats, users=users)

@app.route('/chat/<chat_id>')
def chat_room(chat_id):
    if 'username' not in session:
        return redirect(url_for('index'))
    username = session['username']
    return render_template('chat_room.html', chat_id=chat_id, username=username, messages=chats[chat_id])

@app.route('/admin_chat/<chat_id>')
def admin_chat_room(chat_id):
    return render_template('admin_chat_room.html', chat_id=chat_id, messages=chats[chat_id])

@socketio.on('join_chat')
def handle_join_chat(data):
    join_room(data['chat_id'])
    send({'message': f"{data['username']} has joined the chat.", 'user': 'System', 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'chat_id': data['chat_id']}, to=data['chat_id'])

@socketio.on('send_message')
def handle_send_message(data):
    message = {'message': data['message'], 'user': data['user'], 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'chat_id': data['chat_id']}
    chats[data['chat_id']].append(message)
    send(message, to=data['chat_id'])

@socketio.on('end_chat')
def handle_end_chat(data):
    leave_room(data['chat_id'])
    send({'message': "Chat has been ended by the admin.", 'user': 'System', 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'chat_id': data['chat_id']}, to=data['chat_id'])
    del chats[data['chat_id']]
    del users[data['chat_id']]

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
