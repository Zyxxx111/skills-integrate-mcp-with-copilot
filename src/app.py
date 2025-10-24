"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
import os
import json
from pathlib import Path
from typing import Optional
import secrets

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Session storage (in-memory for simplicity)
active_sessions = {}

# Load teachers from JSON file
def load_teachers():
    teachers_file = os.path.join(Path(__file__).parent, "teachers.json")
    with open(teachers_file, 'r') as f:
        data = json.load(f)
        return data['teachers']

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

# Helper function to verify auth token
def verify_teacher_token(authorization: Optional[str] = Header(None)) -> bool:
    if not authorization:
        return False
    
    token = authorization.replace("Bearer ", "")
    return token in active_sessions


# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(credentials: LoginRequest):
    """Authenticate a teacher and return a session token"""
    teachers = load_teachers()
    
    # Check credentials
    for teacher in teachers:
        if teacher['username'] == credentials.username and teacher['password'] == credentials.password:
            # Generate session token
            token = secrets.token_urlsafe(32)
            active_sessions[token] = credentials.username
            
            return {
                "token": token,
                "username": credentials.username,
                "message": "Login successful"
            }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    """Logout a teacher by invalidating their session token"""
    if authorization:
        token = authorization.replace("Bearer ", "")
        if token in active_sessions:
            del active_sessions[token]
    
    return {"message": "Logout successful"}


@app.get("/auth/verify")
def verify_auth(authorization: Optional[str] = Header(None)):
    """Verify if the current session is authenticated"""
    is_authenticated = verify_teacher_token(authorization)
    
    if is_authenticated:
        token = authorization.replace("Bearer ", "")
        username = active_sessions.get(token)
        return {"authenticated": True, "username": username}
    
    return {"authenticated": False}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, authorization: Optional[str] = Header(None)):
    """Sign up a student for an activity (requires teacher authentication)"""
    # Verify teacher is authenticated
    if not verify_teacher_token(authorization):
        raise HTTPException(status_code=403, detail="Authentication required. Only teachers can register students.")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, authorization: Optional[str] = Header(None)):
    """Unregister a student from an activity (requires teacher authentication)"""
    # Verify teacher is authenticated
    if not verify_teacher_token(authorization):
        raise HTTPException(status_code=403, detail="Authentication required. Only teachers can unregister students.")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
