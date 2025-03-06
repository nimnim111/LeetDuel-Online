import random
import string

import socketio
import asyncio
import uvicorn

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .submit import Problem
from .database import SessionLocal
from .crud import get_problem

from src.routes.problems import router as problems_router



app = FastAPI()
app.include_router(problems_router)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, app)

parties = {}
language_id = 100


# <----------------- Helper functions ----------------->

def get_random_problem(difficulty: list[bool], problem_id: int = None) -> dict:
    db = SessionLocal()

    try:
        problem = get_problem(db, difficulty, problem_id)
        return {"name": problem.problem_name, "description": problem.problem_description, "difficulty": problem.problem_difficulty, "test_cases": problem.test_cases, "function_signature": problem.function_signature}
    
    finally:
        db.close()


def generate_party_code() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def all_players_passed(party_code: str) -> bool:
    for player in parties[party_code]["players"]:
        if not player["passed"]:
            return False
    return True


def reset_players_passed(party_code: str) -> None:
    for player in parties[party_code]["players"]:
        player["passed"] = False


async def game_timeout(party_code: str, time_limit: str) -> None:
    await asyncio.sleep(int(time_limit) * 60)
    if parties[party_code]["status"] == "in_progress":
        parties[party_code]["status"] = "finished"
        reset_players_passed(party_code)
        await sio.emit("game_over_message", {"message": "Time is up!"}, room=party_code)
        await asyncio.sleep(3)
        await sio.emit("game_over", room=party_code)



# <----------------- Socket events ----------------->

@sio.event
async def create_party(sid: str, data: dict) -> None:
    print(f"create_party event received from {sid}: {data}")
    party_code = generate_party_code()
    parties[party_code] = {
        "host": sid,
        "players": [{"sid": sid, "username": data["username"], "passed": False}],
        "problem": None,
        "status": "waiting",
    }
    await sio.emit("party_created", {"username": data["username"], "party_code": party_code}, to=sid)
    await sio.enter_room(sid, party_code)


@sio.event
async def join_party(sid: str, data: dict) -> None:
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
async def start_game(sid: str, data: dict) -> None:
    print(f"start_game event received from {sid}: {data}")
    party_code = data["party_code"]
    difficulty = [data["easy"], data["medium"], data["hard"]]
    time_limit = data["time_limit"]

    if time_limit == "":
        time_limit = "15"

    if party_code in parties and parties[party_code]["host"] == sid:
        problem = get_random_problem(difficulty)
        parties[party_code]["problem"] = problem
        parties[party_code]["status"] = "in_progress"

        await sio.emit("game_started", {"problem": problem, "party_code": party_code, "time_limit": time_limit}, room=party_code)
        asyncio.create_task(game_timeout(party_code, time_limit))
    else:
        await sio.emit("error", {"message": "You are not the host"}, to=sid)


@sio.event
async def submit_code(sid: str, data: dict) -> None:
    print(f"submit_code event received from {sid}: {data}")
    party_code = data["party_code"]
    code = data["code"]
    problem_obj = parties[party_code]["problem"]
    problem = Problem(language_id, problem_obj)

    r = problem.submit_code(code)

    if "message" in r:
        message_to_client = r["status"] + ", " + r["message"]
        message_to_room = data["username"] + " encountered an error."

    else:
        message_to_client = r["status"] + ", " + str(r["passed test cases"]) + "/" + str(r["total test cases"]) + " test cases in " + str(r["time"]) + " seconds."
        message_to_room = data["username"] + " passed " + str(r["passed test cases"]) + "/" + str(r["total test cases"]) + " test cases in " + str(r["time"]) + " seconds."
        if r["failed_test"] is not None:
            message_to_client += "\n" + r["failed_test"]

    if r["status"] == "Accepted":
        for player in parties[party_code]["players"]:
            if player["sid"] == sid:
                player["passed"] = True

    await sio.emit("code_submitted", {"message": message_to_client}, to=sid)
    await sio.emit("player_submit", {"message": message_to_room}, room=party_code)

    if all_players_passed(party_code):
        parties[party_code]["status"] = "finished"
        reset_players_passed(party_code)
        await sio.emit("game_over_message", {"message": "All players passed! Game over."}, room=party_code)
        await asyncio.sleep(3)
        await sio.emit("game_over", room=party_code)


@sio.event
async def chat_message(sid: str, data: dict) -> None:
    print(f"chat_message event received from {sid}: {data}")
    party_code = data["party_code"]
    message = data["message"]
    username = data["username"]

    await sio.emit("message_received", {"username": username, "message": message}, room=party_code)


@sio.event
async def leave_party(sid: str, data: dict) -> None:
    print(f"leave_party event received from {sid}: {data}")
    party_code = data["party_code"]
    username = data["username"]

    if party_code in parties:
        if parties[party_code]["host"] == sid:
            await sio.emit("game_over_message", {"message": "Host left the party."}, room=party_code)
            await asyncio.sleep(3)
            await sio.emit("game_over", room=party_code)
        else:
            for player in parties[party_code]["players"]:
                if player["sid"] == sid:
                    parties[party_code]["players"].remove(player)
                    await sio.emit("player_submit", {"message": username + " has left the party."}, room=party_code)
                    await sio.leave_room(sid, party_code)
                    break


@app.get("/")
async def read_root():
    return JSONResponse({"message": "Server is running"})


@app.get("/parties")
async def read_root():
    return JSONResponse({"parties": parties})


if __name__ == "__main__":
    uvicorn.run("src.main:socket_app", host="0.0.0.0", port=8000)