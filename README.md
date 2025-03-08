**LeetDuel**

To run the backend server locally, cd into leetduel-backend and create a venv. In the venv, run:
```
pip install -r requirements.txt
```
To start the server, run:
```
uvicorn "src.main:socket_app" --host 0.0.0.0 --port 8000 --reload
```

To run the frontend server, cd into leetduel-frontend and run:
```
npm install
npm run dev
```
