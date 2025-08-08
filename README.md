# Here are your Instructions
How to Launch the Ticketing System App from Terminal in VS Code

Launching the Frontend (React Application:
Navigate to the frontend directory:

cd frontend

Install dependencies (only needed the first time or when dependencies change):
npm install
or if using yarn (which is preferred based on yarn.lock file):

yarn install



Launch the frontend:
npm start

or with yarn:

yarn start


The frontend will be accessible at http://localhost:3000

Launching the Backend (Python/FastAPI Application)
Open a new terminal in VS Code (Terminal → New Terminal or Ctrl+Shift+`)

Navigate to the backend directory:

cd backend

Install Python dependencies (only needed the first time or when dependencies change):
pip install -r requirements.txt

Launch the backend server:
python -m uvicorn server:app --reload


The backend API will be accessible at http://localhost:8000

Important Notes
You'll need to run both terminals simultaneously (frontend and backend)
Make sure MongoDB is installed and running as mentioned in the frontend README
The frontend uses Craco (as seen in package.json scripts), so yarn start is the correct command
The backend will automatically reload when you make code changes due to the --reload flag

# drop database
see dropdatabse.py to clean the database