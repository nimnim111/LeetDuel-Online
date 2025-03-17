import random
import string

import socketio
import asyncio
import uvicorn

from ratelimit import limits, RateLimitException
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .submit import Problem
from .database import SessionLocal
from .crud import get_problem
from .config import port

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


async def game_timeout(party_code: str, time_limit: str, problem_name: str) -> None:
    await asyncio.sleep(int(time_limit) * 60)
    if party_code in parties and parties[party_code]["status"] == "in_progress" and problem_name == parties[party_code]["problem"]["name"]:
        parties[party_code]["status"] = "waiting"
        reset_players_passed(party_code)
        await sio.emit("announcement", {"message": "Time is up!"}, room=party_code)
        await asyncio.sleep(3)
        await sio.emit("game_over", room=party_code)


@limits(calls=20, period=5)
def rate_limiter() -> None:
    return



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

    if party_code not in parties or parties[party_code]["status"] != "waiting":
        await sio.emit("error", {"message": "Party not found"}, to=sid)
        return

    if len(parties[party_code]["players"]) >= 10:
        await sio.emit("error", {"message": "Party is full!"}, to=sid)
        return

    parties[party_code]["players"].append({"sid": sid, "username": username})
    player_usernames = [d["username"] for d in parties[party_code]["players"]]
    await sio.enter_room(sid, party_code)
    await sio.emit(
        "player_joined",
        {
            "username": username,
            "players": player_usernames,
        }, 
        room=party_code,
    )
    print(f"players being added:\n{parties[party_code]['players']}")


@sio.event
async def start_game(sid: str, data: dict, difficulties: list[bool] = []) -> None:
    print(f"start_game event received from {sid}: {data}")
    party_code = data["party_code"]
    difficulty = difficulties or [data["easy"], data["medium"], data["hard"]]
    time_limit = data["time_limit"] or "15"

    if party_code in parties and parties[party_code]["host"] == sid:
        try:
            problem = get_random_problem(difficulty)
            parties[party_code]["problem"] = problem
            parties[party_code]["status"] = "in_progress"
            parties[party_code]["difficulties"] = difficulty
            parties[party_code]["time_limit"] = time_limit

            await sio.emit("game_started", {"problem": problem, "party_code": party_code, "time_limit": time_limit}, room=party_code)
            asyncio.create_task(game_timeout(party_code, time_limit, problem["name"]))

        except Exception as e:
            print(f"Error in start_game:\n{e}")
            await sio.emit("error", {"message": "An internal error occurred while retrieving problems."}, to=sid)

    else:
        await sio.emit("error", {"message": "You are not the host"}, to=sid)


@sio.event
async def submit_code(sid: str, data: dict) -> None:
    print(f"submit_code event received from {sid}: {data}")
    party_code = data["party_code"]
    code = data["code"]
    problem_obj = parties[party_code]["problem"]
    problem = Problem(language_id, problem_obj)
    color = "Red"

    r = problem.submit_code(code)

    if "message" in r:
        message_to_client = r["status"] + ", " + r["message"]
        message_to_room = data["username"] + " encountered an error."

    else:
        message_to_client = r["status"] + ", " + str(r["passed test cases"]) + "/" + str(r["total test cases"]) + " test cases in " + str(r["time"]) + "ms."
        message_to_room = data["username"] + " passed " + str(r["passed test cases"]) + "/" + str(r["total test cases"]) + " test cases in " + str(r["time"]) + "ms."
        if "failed_test" in r and r["failed_test"] is not None:
            message_to_client += "\n" + r["failed_test"]

    if r["status"] == "Accepted":
        color = "green"
        for player in parties[party_code]["players"]:
            if player["sid"] == sid:
                player["passed"] = True

    await sio.emit("code_submitted", {"message": message_to_client}, to=sid)

    if "message" not in r or r["message"] != "Rate limited! Please wait 5 seconds and try again.":
        await sio.emit("player_submit", {"message": message_to_room, "bold": True, "color": color}, room=party_code)

    if all_players_passed(party_code):
        parties[party_code]["status"] = "waiting"
        reset_players_passed(party_code)
        await sio.emit("announcement", {"message": "All players passed! Game over."}, room=party_code)
        await asyncio.sleep(3)
        await sio.emit("game_over", room=party_code)


@sio.event
async def chat_message(sid: str, data: dict) -> None:
    try:
        rate_limiter()
    except RateLimitException:
        return
    
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
    await sio.emit("leave_party", to=sid)

    if party_code not in parties:
        return
    
    if parties[party_code]["status"] == "waiting":
        if parties[party_code]["host"] == sid:
            await sio.leave_room(sid, party_code)
            del parties[party_code]
        else:
            for player in parties[party_code]["players"]:
                if player["sid"] == sid:
                    parties[party_code]["players"].remove(player)
                    await sio.emit("player_left", {"username": username}, room=party_code)
                    await sio.leave_room(sid, party_code)
                    break
        
        return

    if parties[party_code]["host"] == sid:
        await sio.emit("announcement", {"message": "Host left the party."}, room=party_code)
        await asyncio.sleep(3)
        await sio.emit("leave_party", room=party_code)
        for player in parties[party_code]["players"]:
            await sio.leave_room(sid, party_code)

        del parties[party_code]

    else:
        for player in parties[party_code]["players"]:
            if player["sid"] == sid:
                parties[party_code]["players"].remove(player)
                await sio.emit("announcement", {"message": f"{username} has left the party."}, room=party_code)
                await sio.leave_room(sid, party_code)
                break


@sio.event
async def disconnect(sid: str) -> None:
    # Handle player disconnection by removing from parties
    print(f"disconnect event received from {sid}")
    for party_code, party in list(parties.items()):
        if party["host"] == sid or not party["players"]:
            await sio.leave_room(sid, party_code)
            del parties[party_code]
            await sio.emit("announcement", {"message": "Party deleted due to disconnect."}, room=party_code)

        for player in party["players"]:
            if player["sid"] == sid:
                await sio.emit("announcement", {"message": f"{player['username']} has left the party."}, room=party_code)
                party["players"].remove(player)
                await sio.leave_room(sid, party_code)
                break


@sio.event
async def skip_problem(sid: str, data: dict) -> None:
    party_code = data["party_code"]
    print(f"skip problem event received from {sid}, party code: {party_code}")
    if party_code not in parties:
        return
    
    party = parties[party_code]

    if party["host"] != sid:
        return
    
    await sio.emit("announcement", {"message": "Problem is being skipped..."}, room=party_code)
    await asyncio.sleep(2)

    for player in party["players"]:
        player["passed"] = False

    await start_game(sid, {"party_code": party_code, "time_limit": party["time_limit"]}, party["difficulties"])


@app.get("/")
async def read_root():
    return JSONResponse({"message": "Server is running"})


@app.get("/parties")
async def read_root():
    return JSONResponse({"parties": parties})


if __name__ == "__main__":
    uvicorn.run("src.main:socket_app", host="0.0.0.0", port=port or 8000)