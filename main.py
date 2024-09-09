import json, threading, time, os
from flask import Flask, render_template, request, redirect
import pymongo 

app = Flask(__name__)
app.secret_key = 'askd9001e'

myclient = pymongo.MongoClient("mongodb+srv://abid:1nQefcNAEIRYJ5gF@cluster0.jrkne.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
user_db = myclient["authentication"]
user_table = user_db["user_info"]


current_user = None
user_list = []
group_list = []
cid = None

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/register_check', methods=['GET', 'POST'])
def register_check():
    global current_user
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
            current_user = req["userid"]
            return redirect('dashboard')
        else:
            return render_template("invalid.html", message="User already exists")

        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')


@app.route('/login_check', methods=['GET', 'POST'])
def login_check():
    global current_user
    if(request.method == 'POST'):
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
                current_user = req["userid"]
                return redirect('dashboard')
            else:
                return render_template("invalid.html", message="Incorrect password")
        return render_template("invalid.html", message="User is not refistered")
    
        
    return render_template("login.html")    
      
    
@app.route("/fetch_user", methods=["GET", "POST"])
def fetch_user():
    global user_list
    with open("users.txt", "r") as file:
        data = file.readlines()
    user_list = [line.strip() for line in data]
    return redirect("dashboard")


@app.route("/fetch_group", methods=["GET", "POST"])
def fetch_group():
    global group_list
    with open("groups.txt", "r") as file:
        data = file.readlines()
    group_list = [line.strip() for line in data]
    return redirect("dashboard")

      
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    global current_user, user_list, group_list, cid
    return render_template(
            'dashboard.html', 
            userid=current_user, 
            user_list=user_list,
            group_list=group_list, 
            cid=cid
        )

@app.route("/update_cid/<string:chat_id>", methods=["GET", "POST"])
def update_cid(chat_id):
    global cid 
    cid = chat_id
    return redirect("/dashboard")

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
