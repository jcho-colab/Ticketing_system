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

# access the database locally
Here’s a summary of what I found:

    Database Type: The application uses a MongoDB database, which is a NoSQL database.
    Database Location: The database is running locally on your machine. The connection string is mongodb://localhost:27017.
    Database Name: The name of the database is ticketing_system.

How to View the Data

To see the data, you will need a tool to connect to the MongoDB database. You have a few options:

    MongoDB Shell (mongosh): This is a command-line interface for MongoDB. If you have MongoDB installed, you can open a terminal and run mongosh. Once connected, you can switch to the correct database and view the data. Here are some commands you can use:

    # Switch to the ticketing_system database
    use ticketing_system

    # Find all tickets in the 'tickets' collection
    db.tickets.find().pretty()

    # Find all comments in the 'comments' collection
    db.comments.find().pretty()

    MongoDB Compass: This is a graphical user interface for MongoDB. You can download it from the MongoDB website. Once installed, you can connect to mongodb://localhost:27017 and you will be able to see the ticketing_system database and browse the tickets and comments collections visually.

The main data is stored in two collections:

    tickets: This collection stores all the tickets created in the system.
    comments: This collection stores the comments associated with each ticket.

# how to merge to main
git add .
git commit
git checkout main
git pull origin main
git merge your-branch

-- push to github
git push origin main