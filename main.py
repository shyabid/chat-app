import json, threading, time, os
from flask import Flask, render_template, request, redirect, session, jsonify
import logging
import pymongo
from flask_socketio import SocketIO, emit

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = 'askd9001e'
socketio = SocketIO(app)

myclient = pymongo.MongoClient("")
user_db = myclient["authentication"]
user_table = user_db["user_info"]
message_table = user_db["messages"]

users_data = {}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/register_check', methods=['GET', 'POST'])
def register_check():
    if request.method == 'POST':
        req = request.form
        req = dict(req)
        print(req)
        query = user_table.find({'userid': req["userid"]})
        flag = 0
        for x in query:
            if x["userid"] == req["userid"]:
                flag = 1
            break
        
        reg_dict = {
            "userid": req["userid"],
            "email": req["email"],
            "password": req["password"]
        }
        if flag == 0:
            temp = user_table.insert_one(reg_dict)
            userid = req["userid"]
            users_data[userid] = {
                "cid": None,
                "user_list": [],
                "groups_list": [],
                "msg_list": {}
            }
            session['userid'] = userid
            return redirect(f'/dashboard')
        else:
            return render_template("invalid.html", message="User already exists")
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/login_check', methods=['GET', 'POST'])
def login_check():
    if request.method == 'POST':
        req = request.form
        req = dict(req)
        print(req)
        query = user_table.find({'userid': req["userid"]})
        flag = 0
        temp = None
        for x in query:
            if x["userid"] == req["userid"]:
                flag = 1
                temp = x
                break
        
        if flag == 1:
            if temp["password"] == req["password"]:
                userid = req["userid"]
                users_data[userid] = {
                    "cid": None,
                    "user_list": [],
                    "groups_list": [],
                    "msg_list": {}
                }
                session['userid'] = userid
                return redirect('/dashboard')
            else:
                return render_template("invalid.html", message="Incorrect password")
        return render_template("invalid.html", message="User is not registered")
    
    return render_template("login.html")
    
@app.route("/fetch_users", methods=["GET"])
def fetch_users():
    if 'userid' not in session:
        return redirect('/login')
    user_id = session['userid']
    all_users = list(user_table.find({}, {'userid': 1, '_id': 0}))
    users_data[user_id]["user_list"] = [user['userid'] for user in all_users if user['userid'] != user_id]
    return jsonify(users_data[user_id]["user_list"])

@app.route("/fetch_groups", methods=["GET"])
def fetch_groups():
    if 'userid' not in session:
        return redirect('/login')
    user_id = session['userid']
    # For simplicity, we'll use a static list of groups. In a real application, you'd fetch this from the database.
    groups = ["group1", "group2", "group3"]
    users_data[user_id]["groups_list"] = groups
    return jsonify(groups)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'userid' not in session:
        return redirect('/login')
    current_user = session['userid']
    user_data = users_data.get(current_user, {})
    
    return render_template(
        'dashboard.html', 
        userid=current_user, 
        user_list=user_data.get('user_list', []),
        group_list=user_data.get('groups_list', []), 
        cid=user_data.get('cid')
    )

@app.route("/update_cid/<string:chat_id>", methods=["GET", "POST"])
def update_cid(chat_id):
    if 'userid' not in session:
        return redirect('/login')
    user_id = session['userid']
    if user_id in users_data:
        users_data[user_id]['cid'] = chat_id
    return redirect('/dashboard')

@socketio.on('send_message')
def handle_message(data):
    if 'userid' not in session:
        return {'error': 'Not logged in'}, 401
    
    user_id = session['userid']
    message = data.get('message')
    recipient = data.get('recipient')
    
    if not message or not recipient:
        return {'error': 'Invalid message or recipient'}, 400
    
    msg_data = {
        'sender': user_id,
        'recipient': recipient,
        'message': message,
        'timestamp': time.time()
    }
    
    # Store message in MongoDB
    message_table.insert_one(msg_data)
    
    # Emit the message to the recipient
    emit('new_message', msg_data, room=recipient)
    
    return {'success': True}

@app.route('/get_messages', methods=['GET'])
def get_messages():
    if 'userid' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['userid']
    chat_id = request.args.get('chat_id')
    
    if not chat_id:
        return jsonify({'error': 'No chat_id provided'}), 400
    
    # Fetch messages from MongoDB
    messages = list(message_table.find({
        '$or': [
            {'sender': user_id, 'recipient': chat_id},
            {'sender': chat_id, 'recipient': user_id}
        ]
    }).sort('timestamp', 1))
    
    # Convert ObjectId to string for JSON serialization
    for msg in messages:
        msg['_id'] = str(msg['_id'])
    
    return jsonify(messages)

@app.route('/logout')
def logout():
    session.pop('userid', None)
    return redirect('/')

@socketio.on('connect')
def handle_connect():
    if 'userid' in session:
        socketio.emit('user_connected', {'user_id': session['userid']})

@socketio.on('disconnect')
def handle_disconnect():
    if 'userid' in session:
        socketio.emit('user_disconnected', {'user_id': session['userid']})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5005, debug=True)