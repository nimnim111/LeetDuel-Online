import socketio
import random
import string
from fastapi import FastAPI
import uvicorn
from fastapi.responses import JSONResponse


app = FastAPI()
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, app)

# Stores active parties
parties = {}


def generate_party_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


@sio.event
async def create_party(sid, data):
    # Log successful receive
    print(f"create_party event received from {sid}: {data}")
    """ Host creates a new party """
    party_code = generate_party_code()
    parties[party_code] = {
        "host": sid,
        "players": [{"sid": sid, "username": data["username"]}],
        "problem": None,
        "status": "waiting",
    }
    print(party_code)
    await sio.emit("party_created", {"party_code": party_code}, to=sid)


@sio.event
async def join_party(sid, data):
    # Log successful receive
    print(f"join_party event received from {sid}: {data}")
    """ User joins an existing party """
    party_code = data["party_code"]
    username = data["username"]

    if party_code in parties and parties[party_code]["status"] == "waiting":
        parties[party_code]["players"].append({"sid": sid, "username": username})
        await sio.emit("player_joined", {"username": username}, room=party_code)
        await sio.enter_room(sid, party_code)
        
    else:
        await sio.emit("error", {"message": "Party not found"}, to=sid)


@sio.event
async def start_game(sid, data):
    # Log successful receive
    print(f"start_game event received from {sid}: {data}")
    """ Host starts the game, assigns a problem, and notifies all players """
    party_code = data["party_code"]

    if party_code in parties and parties[party_code]["host"] == sid:
        problem = {"title": "Two Sum", "description": "Find two numbers that add up to a target."}
        parties[party_code]["problem"] = problem
        parties[party_code]["status"] = "in_progress"

        await sio.emit("game_started", {"problem": problem}, room=party_code)
    else:
        await sio.emit("error", {"message": "You are not the host"}, to=sid)


@app.get("/")
async def read_root():
    return JSONResponse({"message": "Server is running"})

@app.get("/parties")
async def read_root():
    return JSONResponse({"parties": parties})


if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)