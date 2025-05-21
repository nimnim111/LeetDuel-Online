import random
import string
import time
import math
from dataclasses import asdict
from typing import List, Dict, Optional

import socketio
import asyncio
import uvicorn

from ratelimit import limits, RateLimitException
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .submit import Problem
from .database import SessionLocal, UserRank
from .crud import get_problem, increment_reports, create_or_update_user_rank, get_user_rank, get_all_user_ranks
from .config import port

from src.routes.problems import router as problems_router
from src.routes.ladder import router as ladder_router
from src.dataclass import *

import sqlite3
import json
import threading
import requests
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import desc


app = FastAPI()
app.include_router(problems_router)
app.include_router(ladder_router)

# Enable CORS with more specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Database setup
def init_db():
    conn = sqlite3.connect('leetduel.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            total_score INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            games_won INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, app)

parties: dict[str, Party] = {}
language_id = 100
matchmaking_queue = {}  # Dictionary to store players in matchmaking queue
matchmaking_lock = asyncio.Lock()  # Lock for thread-safe operations on matchmaking queue
active_users = {}  # Dictionary to track active users by uid
user_lock = asyncio.Lock()  # Lock for thread-safe operations on active users


# <----------------- Helper functions ----------------->

def get_random_problem(difficulty: List[bool], problem_id: int | None = None) -> ProblemData | None:
    db = SessionLocal()

    try:
        problem = get_problem(db, difficulty, problem_id)
        if not problem:
            return None
        return problem.asdata()
    
    finally:
        db.close()


def generate_party_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def all_players_passed(party_code: str) -> bool:
    return all([player.passed for player in parties[party_code].players.values()])


def reset_players_passed(party_code: str) -> None:
    for player in parties[party_code].players.values():
        player.passed = False


def get_score(submission: SubmissionData, finish_order: int = 10) -> float:
    return 100 * submission.passed_test_cases / (math.log10(max(2, float(submission.time))) * finish_order * submission.total_test_cases)


async def game_timeout(party_code: str, time_limit: int, problem_name: str) -> None:
    await asyncio.sleep(time_limit * 60)
    if party_code not in parties:
        return
    
    party = parties[party_code]

    if party.status == "in_progress" and party.problem != None and party.problem.name == problem_name:
        party.status = "waiting"
        reset_players_passed(party_code)

        message = MessageData("Time is up!", True, "")
        await sio.emit("message_received", asdict(message), room=party_code)
        await asyncio.sleep(3)
        await finish_round(party_code)


@limits(calls=20, period=5)
def rate_limiter() -> None:
    return

async def start_new_round(party_code: str) -> None:
    if party_code not in parties:
        return
    
    party = parties[party_code]
    difficulty = party.difficulties
    time_limit = party.time_limit

    problem = get_random_problem(difficulty)
    if not problem:
        return
    
    party.problem = problem
    party.status = "in_progress"
    party.finish_count = 0

    end_time = time.time() + (time_limit * 60)
    party.end_time = end_time

    for player in party.players.values():
        player.passed = False
        player.finish_order = None
        player.current_score = 0
        player.code = f"{problem.function_signature}:\n    # your code here\n    return"
        player.console_output = "Test case output"
    
    game_data = GameData(problem, party_code, time_limit, party.current_round, party.total_rounds)
    await sio.emit("game_started", asdict(game_data), room=party_code)
    time_data = TimeData(time_limit * 60)
    await sio.emit("update_time", asdict(time_data), to=party.host)
    asyncio.create_task(game_timeout(party_code, time_limit, problem.name))


async def finish_round(party_code: str) -> None:
    if party_code not in parties:
        return
    
    party = parties[party_code]
    party.status = "waiting"
    # Find if any player has passed (solved the problem)
    solver_sid = None
    for sid, player in party.players.items():
        if player.passed:
            solver_sid = sid
            break
    
    if solver_sid:
        # Only the solver gets their score, others get 0
        for sid, player in party.players.items():
            if sid == solver_sid:
                player.total_score += player.current_score
            else:
                player.current_score = 0
                player.total_score = 0
        leaderboard_players = sorted(list(party.players.values()), key=lambda p: p.total_score, reverse=True)
        leaderboard = [Score(p.username, p.total_score) for p in leaderboard_players]
        leaderboard_data = LeaderboardData(leaderboard)
        await sio.emit("final_leaderboard", asdict(leaderboard_data), room=party_code)
        # Update leaderboard in DB and clean up
        db = SessionLocal()
        try:
            for player_sid, player in party.players.items():
                for uid, user_data in active_users.items():
                    if user_data["sid"] == player_sid:
                        create_or_update_user_rank(
                            db=db,
                            uid=uid,
                            username=user_data["username"],
                            email=user_data["email"],
                            score_delta=player.total_score,
                            won=player.passed
                        )
                        break
        finally:
            db.close()
        # Clean up users after game ends
        async with user_lock:
            for player_sid in party.players:
                for uid, user_data in list(active_users.items()):
                    if user_data["sid"] == player_sid:
                        remove_active_user(uid)
                        break
        # Remove the party after a short delay
        await asyncio.sleep(5)
        if party_code in parties:
            del parties[party_code]
    else:
        # If no one solved, just show leaderboard as before
        for player in party.players.values():
            player.total_score += player.current_score
        leaderboard_players = sorted(list(party.players.values()), key=lambda p: p.total_score, reverse=True)
        leaderboard = [Score(p.username, p.total_score) for p in leaderboard_players]
        leaderboard_data = LeaderboardData(leaderboard)
        await sio.emit("final_leaderboard", asdict(leaderboard_data), room=party_code)
        # Clean up users after game ends
        async with user_lock:
            for player_sid in party.players:
                for uid, user_data in list(active_users.items()):
                    if user_data["sid"] == player_sid:
                        remove_active_user(uid)
                        break
        await asyncio.sleep(5)
        if party_code in parties:
            del parties[party_code]


# <----------------- Socket events ----------------->

@sio.event
async def create_party(sid: str, data: dict) -> None:
    print(f"create_party event received from {sid}: {data}")
    party_code = generate_party_code()
    player = Player(data["username"], False, "", "", 0, 0, None)
    party = Party(sid, {sid: player}, None, "waiting", 0, 0, 0, [True, True, True], 0, 0)
    parties[party_code] = party

    player_data = PlayerData(data["username"], party_code)
    await sio.emit("party_created", asdict(player_data), to=sid)
    await sio.enter_room(sid, party_code)


@sio.event
async def start_next_round(sid: str, data: dict) -> None:
    print(f"start_next_round event received from {sid}")
    party_code = data["party_code"]
    if party_code not in parties or sid != parties[party_code].host:
        return
    await start_new_round(party_code)


@sio.event
async def join_party(sid: str, data: dict) -> None:
    print(f"join_party event received from {sid}: {data}")
    party_code = data["party_code"]
    username = data["username"]

    if party_code == "":
        if not parties:
            e = TextData("No parties to join")
            await sio.emit("error", asdict(e), to=sid)
            return

        party_code = random.choice(list(parties.keys()))
        await sio.emit("set_party_code", {"party_code": party_code}, to=sid)

    if party_code not in parties:
        e = TextData("Party not found")
        await sio.emit("error", asdict(e), to=sid)
        return
    
    party = parties[party_code]

    if len(party.players) >= 10:
        e = TextData("Party is full!")
        await sio.emit("error", asdict(e), to=sid)
        return
    
    if username in [d.username for d in party.players.values()]:
        e = TextData("Username taken!")
        await sio.emit("error", asdict(e), to=sid)
        return
    
    player = Player(username, False, "", "", 0, 0, None)
    party.players[sid] = player
    player_usernames = [d.username for d in party.players.values()]

    await sio.enter_room(sid, party_code)
    player_data = PlayerData(username, party_code, player_usernames)

    await sio.emit("player_joined", asdict(player_data), room=party_code)

    if party.status == "in_progress":
        problem = party.problem
        if not problem:
            return
        
        player.code = f"{problem.function_signature}:\n    # your code here\n    return"
        player.console_output = "Test case output"
        game_data = GameData(problem, party_code, party.time_limit, party.current_round, party.total_rounds)

        await sio.emit("game_started", asdict(game_data), to=sid)
        
        message = MessageData(f"{username} has joined the game!", True, "")
        await sio.emit("message_received", asdict(message), room=party_code)


@sio.event
async def start_game(sid: str, data: dict, difficulties: List[bool] = []) -> None:
    print(f"start_game event received from {sid}: {data}")
    party_code = data["party_code"]
    difficulty = difficulties or [data["easy"], data["medium"], data["hard"]]
    time_limit = int(data["time_limit"] or "15")
    rounds = 1  # Force 1 round

    if party_code not in parties:
        e = TextData("Party not found")
        await sio.emit("error", asdict(e), to=sid)
        return
    
    party = parties[party_code]

    if party.host != sid:
        e = TextData("You are not the host")
        await sio.emit("error", asdict(e), to=sid)
        return

    try:
        party.total_rounds = 1  # Force 1 round
        party.current_round = 1
        party.finish_count = 0

        end_time = time.time() + (time_limit * 60)
        problem = get_random_problem(difficulty)

        if not problem:
            return
        
        party.problem = problem
        party.status = "in_progress"
        party.difficulties = difficulty
        party.time_limit = time_limit
        party.end_time = end_time

        for player in party.players.values():
            player.passed = False
            player.code = f"{problem.function_signature}:\n    # your code here\n    return"
            player.console_output = "Test case output"
            player.current_score = 0
            player.total_score = 0
            player.finish_order = None

        game_data = GameData(problem, party_code, time_limit, 1, 1)  # Force 1 round
        await sio.emit("game_started", asdict(game_data), room=party_code)

        time_data = TimeData(time_limit * 60)
        await sio.emit("update_time", asdict(time_data), to=sid)

        round_info = RoundInfo(1, 1)  # Force 1 round
        await sio.emit("update_round_info", asdict(round_info), to=sid)
        asyncio.create_task(game_timeout(party_code, time_limit, problem.name))

    except Exception as e:
        print(f"Error in start_game:\n{e}")
        error = TextData("An internal error occurred while retrieving problems.")
        await sio.emit("error", asdict(error), to=sid)


@sio.event
async def submit_code(sid: str, data: dict) -> None:
    print(f"submit_code event received from {sid}")
    party_code = data["party_code"]

    if party_code not in parties:
        await sio.emit("leave_party", to=sid)
        return
    
    party = parties[party_code]
    if sid not in party.players.keys() or not party.problem:
        return
    
    player = party.players[sid]

    code = data["code"]
    problem_obj = party.problem
    problem = Problem(language_id, problem_obj)
    color = "#EF5350"

    submission = problem.submit_code(code)
    status = "Accepted" if submission.accepted else "Failed"

    if submission.message:
        message_to_client = f"{status}, {submission.message}"
        message_to_room = f"{data['username']} encountered an error."

    else:
        message_to_client = f"{status}, {str(submission.passed_test_cases)}/{str(submission.total_test_cases)} test cases in {submission.time}ms."
        message_to_room = f"{data['username']} passed {submission.passed_test_cases}/{str(submission.total_test_cases)} test cases in {submission.time}ms."
        if submission.failed_test != "":
            message_to_client += "\n" + submission.failed_test + (f" \nstdout: {submission.stdout}")
            score = get_score(submission)
            player.current_score = max(player.current_score, score)

    if submission.accepted:
        color = "#66BB6A"
        player.passed = True
        if player.finish_order is None:
            party.finish_count += 1
            player.finish_order = party.finish_count
        
        score = get_score(submission, player.finish_order)
        new_score = max(player.current_score, score)
        if new_score > player.current_score:
            player.current_score = new_score
        await sio.emit("passed_all", to=sid)
        # End the game immediately when someone solves the problem
        await finish_round(party_code)

    client_message = TextData(message_to_client)
    await sio.emit("code_submitted", asdict(client_message), to=sid)

    if submission.message == None or submission.message != "Rate limited! Please wait 5 seconds and try again.":
        room_message = MessageData(message_to_room, True, color)
        await sio.emit("message_received", asdict(room_message), room=party_code)

    if all_players_passed(party_code):
        await finish_round(party_code)


@sio.event
async def player_opened(sid: str, data: dict) -> None:
    print(f"player_opened event received from {sid}: {data}")
    party_code = data["party_code"]
    if party_code not in parties:
        return
    
    party = parties[party_code]
    if sid == party.host:
        await sio.emit("activate_settings", to=sid)

    player_usernames = [d.username for d in party.players.values()]
    player_data = PlayerData("", party_code, player_usernames)

    await sio.emit("players_update", asdict(player_data), room=party_code)


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

    message_data = MessageData(f"{username}: {message}", False, "")

    await sio.emit("message_received", asdict(message_data), room=party_code)


async def end_game(party_code: str, message: str = "Game ended due to player leaving.", remaining_sid: str = None) -> None:
    """End the game and clean up the party"""
    if party_code not in parties:
        return
        
    party = parties[party_code]
    
    # Send final scores if game was in progress
    if party.status == "in_progress":
        # If there's a remaining player (someone left), give them 20 points
        if remaining_sid and remaining_sid in party.players:
            party.players[remaining_sid].total_score = 20
            for sid, player in party.players.items():
                if sid != remaining_sid:
                    player.total_score = 0

        # Update ladder rankings for all players
        db = SessionLocal()
        try:
            for player_sid, player in party.players.items():
                for uid, user_data in active_users.items():
                    if user_data["sid"] == player_sid:
                        create_or_update_user_rank(
                            db=db,
                            uid=uid,
                            username=user_data["username"],
                            email=user_data["email"],
                            score_delta=player.total_score,
                            won=(player_sid == remaining_sid) if remaining_sid else player.passed
                        )
                        break
        finally:
            db.close()
        
        leaderboard_players = sorted(list(party.players.values()), key=lambda p: p.total_score, reverse=True)
        leaderboard = [Score(p.username, p.total_score) for p in leaderboard_players]
        leaderboard_data = LeaderboardData(leaderboard)
        await sio.emit("final_leaderboard", asdict(leaderboard_data), room=party_code)
    
    # Notify all players
    await sio.emit("message_received", asdict(MessageData(message, True, "")), room=party_code)
    
    # Clean up users
    async with user_lock:
        for player_sid in party.players:
            for uid, user_data in list(active_users.items()):
                if user_data["sid"] == player_sid:
                    remove_active_user(uid)
                    break
    
    # Remove party after a short delay
    await asyncio.sleep(3)
    if party_code in parties:
        del parties[party_code]

@sio.event
async def leave_party(sid: str, data: dict) -> None:
    print(f"leave_party event received from {sid}: {data}")
    party_code = data["party_code"]
    username = data["username"]
    
    # Remove user from active users
    async with user_lock:
        # Find and remove the user by their sid
        for uid, user_data in list(active_users.items()):
            if user_data["sid"] == sid:
                remove_active_user(uid)
                break
    
    await sio.emit("leave_party", to=sid)

    if party_code not in parties:
        return
    
    party = parties[party_code]
    
    # If game is in progress, end it
    if party.status == "in_progress":
        # Find the remaining player's sid
        remaining_sid = next((player_sid for player_sid in party.players if player_sid != sid), None)
        await end_game(party_code, f"{username} left the game. Game ended.", remaining_sid)
        return

    if party.host == sid:
        # If host leaves, end the game
        remaining_sid = next((player_sid for player_sid in party.players if player_sid != sid), None)
        await end_game(party_code, "Host left the party. Game ended.", remaining_sid)
    else:
        del party.players[sid]
        message = MessageData(f"{username} has left the party.", True, "")
        await sio.emit("message_received", asdict(message), room=party_code)
        await sio.leave_room(sid, party_code)
        # Check if party is now empty
        await cleanup_empty_party(party_code)


# @sio.event
# async def restart_game(sid: str, data: dict) -> None:
#     party_code = data["party_code"]
#     if party_code not in parties:
#         e = TextData("Party not found")
#         await sio.emit("error", asdict(e), to=sid)
#         return

#     party = parties[party_code]
#     if party.host != sid:
#         e = TextData("Only the host can restart the game.")
#         await sio.emit("error", asdict(e), to=sid)
#         return

#     party.current_round = 1
#     party.finish_count = 0
#     for player in party.players.values():
#         player.total_score = 0
#         player.current_score = 0
#         player.finish_order = None
#         player.passed = False

#     config = {
#         "party_code": party_code,
#         "time_limit": party.get("time_limit", 15),
#         "rounds": party.get("total_rounds", 1),
#         "easy": party.get("difficulties", [True, True, True])[0],
#         "medium": party.get("difficulties", [True, True, True])[1],
#         "hard": party.get("difficulties", [True, True, True])[2],
#     }
#     await start_game(sid, config, party.get("difficulties", [True, True, True]))


@sio.event
async def disconnect(sid: str) -> None:
    print(f"disconnect event received from {sid}")
    # Remove from matchmaking queue if present
    async with matchmaking_lock:
        if sid in matchmaking_queue:
            uid = matchmaking_queue[sid]["uid"]
            del matchmaking_queue[sid]
            async with user_lock:
                remove_active_user(uid)
    
    # Handle existing party disconnection logic
    for party_code, party in list(parties.items()):
        if sid not in party.players:
            continue

        player = party.players[sid]
        async with user_lock:
            # Find and remove the user by their sid
            for uid, user_data in list(active_users.items()):
                if user_data["sid"] == sid:
                    remove_active_user(uid)
                    break
            
        # If game is in progress, end it
        if party.status == "in_progress":
            # Find the remaining player's sid
            remaining_sid = next((player_sid for player_sid in party.players if player_sid != sid), None)
            await end_game(party_code, f"{player.username} disconnected. Game ended.", remaining_sid)
            continue

        message = MessageData(f"{player.username} has disconnected.", True, "")
        await sio.emit("message_received", asdict(message), room=party_code)
        await sio.emit("player_left", {"username": player.username}, room=party_code)

        del party.players[sid]
        await sio.leave_room(sid, party_code)
        # Check if party is now empty
        await cleanup_empty_party(party_code)


@sio.event
async def retrieve_players(sid: str, data: dict) -> None:
    party_code = data["party_code"]
    if party_code not in parties:
        return
    
    players = parties[party_code].players.values()
    player_usernames = [d.username for d in players]

    print(f"retrieve_players event received from {sid}, players: {player_usernames}")
    player_data = PlayerData("", party_code, player_usernames)
    await sio.emit("send_players", asdict(player_data), to=sid)


@sio.event
async def retrieve_code(sid: str, data: dict) -> None:
    print(f"retrieve_code event received from {sid}")
    party_code = data["party_code"]
    username = data["username"]
    spectate_sid = ""
    new_text = ""
    new_code = ""

    if party_code not in parties:
        return
    
    party = parties[party_code]
    for player_sid, player in party.players.items():
        if player.username == username:
            spectate_sid = player_sid
            new_text = player.console_output
            new_code = player.code
        else:
            await sio.leave_room(sid, f"{player_sid}:spectate")

    if sid != spectate_sid:
        await sio.enter_room(sid, f"{spectate_sid}:spectate")

    text_data = TextData(new_text)
    code_data = TextData(new_code)

    await sio.emit("updated_console", asdict(text_data), room=f"{spectate_sid}:spectate")
    await sio.emit("updated_code", asdict(code_data), room=f"{spectate_sid}:spectate")


@sio.event
async def leave_spectate_rooms(sid: str, data: dict) -> None:
    party_code = data["party_code"]
    for player_sid in parties[party_code].players:
        await sio.leave_room(sid, f"{player_sid}:spectate")


@sio.event
async def report_problem(sid: str, data: dict) -> None:
    print(f"Report problem event received from {sid}")
    party_code = data["party_code"]
    if party_code not in parties:
        return
    party = parties[party_code]
    db = SessionLocal()
    try:
        if party.problem:
            increment_reports(db, party.problem.name)
    finally:
        db.close()


def is_user_active(uid: str) -> bool:
    """Check if a user is currently active"""
    return uid in active_users

def add_active_user(uid: str, sid: str, username: str, email: str) -> None:
    """Add a user to the active set"""
    print(f"Adding user to active set: {username} ({uid})")
    active_users[uid] = {
        "sid": sid,
        "username": username,
        "email": email
    }

def remove_active_user(uid: str) -> None:
    """Remove a user from the active set"""
    if uid in active_users:
        print(f"Removing user from active set: {active_users[uid]['username']} ({uid})")
        del active_users[uid]

def create_user_if_not_exists(uid: str, username: str) -> None:
    """Create a user record if it doesn't exist"""
    db = SessionLocal()
    try:
        create_or_update_user_rank(
            db=db,
            uid=uid,
            username=username,
            email="",  # Email will be updated when user starts matchmaking
            score_delta=0,
            won=False
        )
    finally:
        db.close()

@sio.event
async def start_matchmaking(sid: str, data: dict) -> None:
    print(f"start_matchmaking event received from {sid}: {data}")
    username = data["username"]
    email = data["email"]
    uid = data["uid"]
    difficulties = [True, True, True]  # Fixed difficulties - all enabled
    
    # Create user record if it doesn't exist
    create_user_if_not_exists(uid, username)
    
    # Check if user is already active
    async with user_lock:
        if is_user_active(uid):
            error = TextData("You are already in a game or searching for a match.")
            await sio.emit("error", asdict(error), to=sid)
            return
        add_active_user(uid, sid, username, email)
    
    try:
        # Create a matchmaking entry
        matchmaking_entry = {
            "username": username,
            "email": email,
            "uid": uid,
            "time_limit": 15,  # Fixed 15 minutes
            "rounds": 1,  # Fixed 1 round
            "difficulties": difficulties,
            "timestamp": time.time()
        }
        
        async with matchmaking_lock:
            # Add player to matchmaking queue
            matchmaking_queue[sid] = matchmaking_entry
            
            # Check if there are at least 2 players in queue
            if len(matchmaking_queue) >= 2:
                # Get the first two players
                players = list(matchmaking_queue.items())[:2]
                player1_sid, player1_data = players[0]
                player2_sid, player2_data = players[1]
                
                # Remove these players from queue
                del matchmaking_queue[player1_sid]
                del matchmaking_queue[player2_sid]
                
                # Create a new party
                party_code = generate_party_code()
                player1 = Player(player1_data["username"], False, "", "", 0, 0, None)
                player2 = Player(player2_data["username"], False, "", "", 0, 0, None)
                
                party = Party(
                    player1_sid,
                    {player1_sid: player1, player2_sid: player2},
                    None,
                    "waiting",
                    15,  # Fixed 15 minutes
                    1,  # Fixed 1 round
                    0,
                    difficulties,  # Fixed difficulties
                    0,
                    0
                )
                parties[party_code] = party
                
                # Add both players to the party room
                await sio.enter_room(player1_sid, party_code)
                await sio.enter_room(player2_sid, party_code)
                
                # Notify both players with correct player list
                player_usernames = [player1_data["username"], player2_data["username"]]
                player_data1 = PlayerData(player1_data["username"], party_code, player_usernames)
                player_data2 = PlayerData(player2_data["username"], party_code, player_usernames)
                
                await sio.emit("player_joined", asdict(player_data1), to=player1_sid)
                await sio.emit("player_joined", asdict(player_data2), to=player2_sid)
                
                # Start the game
                await start_game(player1_sid, {
                    "party_code": party_code,
                    "time_limit": 15,  # Fixed 15 minutes
                    "rounds": 1,  # Fixed 1 round
                    "easy": True,
                    "medium": True,
                    "hard": True
                }, difficulties)
    except Exception as e:
        # If anything goes wrong, remove the user from active set
        async with user_lock:
            remove_active_user(uid)
        raise e


@app.get("/")
async def read_root():
    return JSONResponse({"message": "Server is running"})


async def cleanup_empty_party(party_code: str) -> None:
    """Clean up a party and its users if it's empty"""
    if party_code in parties and not parties[party_code].players:
        print(f"Cleaning up empty party: {party_code}")
        del parties[party_code]


# Ladder endpoints
@app.get("/ladder")
async def get_ladder():
    try:
        db = SessionLocal()
        try:
            # Get all users ordered by total score
            users = get_all_user_ranks(db)
            
            entries = []
            for i, user in enumerate(users, 1):
                entries.append({
                    "rank": i,
                    "username": user.username,
                    "total_score": user.total_score,
                    "games_played": user.games_played,
                    "games_won": user.games_won
                })
            
            return {"entries": entries}
        finally:
            db.close()
    except Exception as e:
        print(f"Error in get_ladder: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/ladder/user/{user_id}")
async def get_user_ladder_info(user_id: str):
    try:
        db = SessionLocal()
        try:
            # Get user info
            user = get_user_rank(db, user_id)
            
            if not user:
                # If user doesn't exist, create them
                if user_id in active_users:
                    username = active_users[user_id]["username"]
                    create_user_if_not_exists(user_id, username)
                    # Fetch the newly created user
                    user = get_user_rank(db, user_id)
                else:
                    raise HTTPException(status_code=404, detail="User not found")
            
            # Get user's rank
            rank = db.query(UserRank).filter(UserRank.total_score > user.total_score).count() + 1
            
            return {
                "rank": rank,
                "username": user.username,
                "total_score": user.total_score,
                "games_played": user.games_played,
                "games_won": user.games_won
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_user_ladder_info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    uvicorn.run("src.main:socket_app", host="0.0.0.0", port=int(port))