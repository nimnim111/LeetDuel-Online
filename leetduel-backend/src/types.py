from dataclasses import dataclass
from typing import List, Optional


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