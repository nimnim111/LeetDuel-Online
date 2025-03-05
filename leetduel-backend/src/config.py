import os
from dotenv import load_dotenv

# Load .env.local from the repository root (/Users/jeffreykim/leetduel/leetduel-backend)
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(dotenv_path=os.path.join(basedir, ".env.local"))

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set")