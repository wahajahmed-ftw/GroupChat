from flask import Flask,request,session,render_template,redirect,url_for
from flask_socketio import join_room,leave_room,send,SocketIO
import random
from string import ascii_uppercase

app=Flask(__name__)
app.config['SECRET_KEY']="kfndjfnsdjf"
socketio=SocketIO(app)

rooms={}

def generate_code(length):
    while True:
        code =""
        for _ in range(length):
            code+= random.choice(ascii_uppercase)
        if code not in rooms:
            break
    print(f"Room code: {code}")
    return code

@app.route('/', methods=["POST","GET"])
def home():
    session.clear()
    if request.method=='POST':
        name=request.form.get('name')
        code=request.form.get('code')
        join=request.form.get('join',False)
        create=request.form.get('create',False)

        if not name:
            return render_template("home.html", error ="Please enter your name", name=name, code=code)
        if join!= False and not code:
            return render_template("home.html", error ="Please enter the code", name=name, code=code)
        room = code
        if create!=False:
            room = generate_code(4)
            rooms[room]={"members":0, "messages":[]}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist",name=name, code=code )
        session["room"] = room
        session["name"] = name

        return redirect(url_for("room"))

    return render_template("home.html")

@app.route('/room')
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        print("hello")
        return
    
    if room not in rooms:
        leave_room(room)
        print("goodbye")
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")
    print(rooms)

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    if room in rooms:
        rooms[room]["members"] -=1
        if rooms[room]["members"]<=0:
            del rooms[room]
    send({"name":name, "message":"Has left the room"}, to=room)
    print(f"{name} left room {room}")
    print(rooms)


if __name__ =='__main__':
    socketio.run(app,debug=True)