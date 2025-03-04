from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="./.env.local")
judge0_api_key = os.getenv("JUDGE0_API_KEY")
database_url = os.getenv("DATABASE_URL")