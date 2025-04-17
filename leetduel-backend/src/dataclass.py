from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TestCase:
    input: str
    output: str

    def __init__(self, input: str, output: str):
        self.input = input
        self.output = output


@dataclass
class ProblemData:
    name: str
    description: str
    function_signature: str
    difficulty: str
    test_cases: List[TestCase]
    any_order: bool
    reports: int

    def __init__(self, name: str, description: str, function_signature: str, difficulty: str, test_cases: List[dict[str, str]], any_order: bool, reports: int):
        self.name = name
        self.description = description
        self.function_signature = function_signature
        self.difficulty = difficulty
        self.test_cases = [TestCase(t["input"], t["output"]) for t in test_cases]
        self.any_order = any_order
        self.reports = reports


@dataclass
class PlayerData:
    username: str
    party_code: str
    players: Optional[List[str]] = None

    def __init__(self, username: str, party_code: str, players: Optional[List[str]] = None):
        self.username = username
        self.party_code = party_code
        self.players = players


@dataclass
class Player:
    username: str
    passed: bool
    code: str
    console_output: str
    current_score: float
    total_score: float
    finish_order: int | None

    def __init__(self, username: str, passed: bool, code: str, console_output: str, current_score: float, total_score: float, finish_order: int | None):
        self.username = username
        self.passed = passed
        self.code = code
        self.console_output = console_output
        self.current_score = current_score
        self.total_score = total_score
        self.finish_order = finish_order


@dataclass
class Party:
    host: str
    players: dict[str, Player]
    problem: ProblemData | None
    status: str
    total_rounds: int
    current_round: int
    finish_count: int
    difficulties: List[bool]
    time_limit: int
    end_time: float

    def __init__(self, host: str, players: dict[str, Player], problem: ProblemData | None, status: str, total_rounds: int, current_round: int, finish_count: int, difficulties: List[bool], time_limit: int, end_time: float):
        self.host = host
        self.players = players
        self.problem = problem
        self.status = status
        self.total_rounds = total_rounds
        self.current_round = current_round
        self.finish_count = finish_count
        self.difficulties = difficulties
        self.time_limit = time_limit
        self.end_time = end_time


@dataclass
class GameData:
    problem: ProblemData
    party_code: str
    time_limit: int
    round: int
    total_rounds: int

    def __init__(self, problem: ProblemData, party_code: str, time_limit: int, round: int, total_rounds: int):
        self.problem = problem
        self.party_code = party_code
        self.time_limit = time_limit
        self.round = round
        self.total_rounds = total_rounds


@dataclass
class TextData:
    message: str

    def __init__(self, message: str):
        self.message = message


@dataclass
class MessageData:
    message: str
    bold: bool
    color: str
    username: Optional[str] = None

    def __init__(self, message: str, bold: bool, color: str, username: Optional[str] = None):
        self.message = message
        self.bold = bold
        self.color = color
        self.username = username


@dataclass
class TimeData:
    time_left: float

    def __init__(self, time_left: float):
        self.time_left = time_left


@dataclass
class Score:
    username: str
    score: float

    def __init__(self, username: str, score: float):
        self.username = username
        self.score = score


@dataclass
class LeaderboardData:
    leaderboard: List[Score]
    rounds: int
    total_rounds: int

    def __init__(self, leaderboard: List[Score], rounds: int, total_rounds: int):
        self.leaderboard = leaderboard
        self.rounds = rounds
        self.total_rounds = total_rounds


@dataclass
class RoundInfo:
    current: int
    total: int

    def __init__(self, current: int, total: int):
        self.current = current
        self.total = total