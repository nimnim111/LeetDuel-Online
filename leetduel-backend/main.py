import socketio
import random
import string
from fastapi import FastAPI
import uvicorn
from fastapi.responses import JSONResponse
import json
import os
from dotenv import load_dotenv
from submit import Problem
import asyncio

load_dotenv(dotenv_path="../.env.local")
judge0_api_key = os.getenv("JUDGE0_API_KEY")
language_id = 100

app = FastAPI()
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, app)

parties = {}

with open("problems.json", "r") as f:
    problems = json.load(f)

def generate_party_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def all_players_passed(party_code):
    for player in parties[party_code]["players"]:
        if not player["passed"]:
            return False
    return True

def reset_players_passed(party_code):
    for player in parties[party_code]["players"]:
        player["passed"] = False

async def game_timeout(party_code):
    await asyncio.sleep(900)
    if parties[party_code]["status"] == "in_progress":
        parties[party_code]["status"] = "finished"
        reset_players_passed(party_code)
        await sio.emit("game_over", {"message": "Time is up!"}, room=party_code)

@sio.event
async def create_party(sid, data):
    print(f"create_party event received from {sid}: {data}")
    party_code = generate_party_code()
    parties[party_code] = {
        "host": sid,
        "players": [{"sid": sid, "username": data["username"], "passed": False}],
        "problem": None,
        "status": "waiting",
    }
    print(party_code)
    await sio.emit("party_created", {"username": data["username"], "party_code": party_code}, to=sid)
    await sio.enter_room(sid, party_code)


@sio.event
async def join_party(sid, data):
    print(f"join_party event received from {sid}: {data}")
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
    print(f"start_game event received from {sid}: {data}")
    party_code = data["party_code"]

    if party_code in parties and parties[party_code]["host"] == sid:
        problem = problems[random.choice(list(problems.keys()))]
        parties[party_code]["problem"] = problem
        parties[party_code]["status"] = "in_progress"

        await sio.emit("game_started", {"problem": problem, "party_code": party_code}, room=party_code)
        # Start the game timeout task
        asyncio.create_task(game_timeout(party_code))
    else:
        await sio.emit("error", {"message": "You are not the host"}, to=sid)

@sio.event
async def submit_code(sid, data):
    print(f"submit_code event received from {sid}: {data}")
    party_code = data["party_code"]
    code = data["code"]
    problem_obj = parties[party_code]["problem"]
    problem = Problem(language_id, problem_obj, judge0_api_key)

    r = problem.submit_code(code)
    message_to_client = r["status"] + ", " + str(r["passed test cases"]) + "/" + str(r["total test cases"]) + " test cases passed."
    message_to_room = data["username"] + " passed " + str(r["passed test cases"]) + "/" + str(r["total test cases"]) + " test cases."

    print("message " + message_to_client)

    if r["status"] == "Accepted":
        for player in parties[party_code]["players"]:
            if player["sid"] == sid:
                player["passed"] = True

    await sio.emit("code_submitted", {"message": message_to_client}, to=sid)
    await sio.emit("player_submit", {"message": message_to_room}, room=party_code)

    if all_players_passed(party_code):
        print("All players passed!")
        parties[party_code]["status"] = "finished"
        reset_players_passed(party_code)
        await sio.emit("game_over", {"message": "All players passed! Game over."}, room=party_code)

@sio.event
async def chat_message(sid, data):
    print(f"chat_message event received from {sid}: {data}")
    party_code = data["party_code"]
    message = data["message"]
    username = data["username"]

    await sio.emit("message_received", {"username": username, "message": message}, room=party_code)


@app.get("/")
async def read_root():
    return JSONResponse({"message": "Server is running"})

@app.get("/parties")
async def read_root():
    return JSONResponse({"parties": parties})


if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)