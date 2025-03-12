**LeetDuel**

## Local Backend

To run the backend server locally, cd into leetduel-backend and create a venv. In the venv, run:

```
pip install -r requirements.txt
```

In order to run this locally, you need the `DATABASE_URL` environment variable set in a `.env.local` file set in the `leetduel-backend` directory. To do this, create a `.env.local` and paste in your database URL:

```
DATABASE_URL=<YOUR_DATABASE_URL>
```

To start the server, run:

```
uvicorn "src.main:socket_app" --host 0.0.0.0 --port 8000 --reload
```

If you see any module not found errors, your virtual env's version of uvicorn may be overriden by your global Python's version. In this case, replace `uvicorn` with `{PATH_TO_VENV}/bin/uvicorn`

## Local Frontend

The frontend uses socket events to coordinate between players in the same room. This socket server is the backend server, but is set as an env variable. To set it, create a `.env.local` file in `leetduel-frontend` with:

```
NEXT_PUBLIC_SERVER_URL=http://localhost:8000
```

To run the frontend server, cd into leetduel-frontend and run:
```
npm install
npm run dev
```
