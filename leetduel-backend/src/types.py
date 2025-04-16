import json
from dataclasses import dataclass, asdict
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

    def __init__(self, name: str, description: str, function_signature: str, difficulty: str, test_cases: List[TestCase], any_order: bool, reports: int):
        self.name = name
        self.description = description
        self.function_signature = function_signature
        self.difficulty = difficulty
        self.test_cases = test_cases
        self.any_order = any_order
        self.reports = reports


    def toJSON(self):
        return json.dumps(asdict(self))


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
class GameData:
    problem: ProblemData
    party_code: str
    time_limit: str

    def __init__(self, problem: ProblemData, party_code: str, time_limit: str):
        self.problem = problem
        self.party_code = party_code
        self.time_limit = time_limit


@dataclass
class ErrorData:
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