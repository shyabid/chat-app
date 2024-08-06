import json, threading, time, os
from flask import Flask, render_template, request, redirect
import pymongo 

app = Flask(__name__)
app.secret_key = 'askd9001e'

myclient = pymongo.MongoClient("mongodb://localhost:27017")
user_db = myclient["authentication"]
user_table = user_db["user_info"]

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/register_check', methods=['GET', 'POST'])
def register_check():
    if(request.method == 'POST'):
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
        
        if(flag == 0):
            temp = user_table.insert_one(reg_dict)
        else:
            return "User already exists"

        return render_template('dashboard.html')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def ashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
    
    