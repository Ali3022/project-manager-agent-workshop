import asyncio
import os
import json
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from project_management_agent.agent import ProjectManagementAgent

load_dotenv()

# ===== PART 1: Initialize Database for Persistent Storage =====
# Using SQLite database for persistent storage
DB_PATH = "./project_management_data.db"


class SessionManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                app_name TEXT,
                user_id TEXT,
                state TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_or_create_session(self, app_name: str, user_id: str, initial_state: dict) -> dict:
        """Get existing session or create a new one."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Try to get existing session
        cursor.execute('''
            SELECT id, state FROM sessions 
            WHERE app_name = ? AND user_id = ? 
            ORDER BY updated_at DESC LIMIT 1
        ''', (app_name, user_id))
        
        result = cursor.fetchone()
        
        if result:
            session_id, state_json = result
            state = json.loads(state_json)
            conn.close()
            return {"id": session_id, "state": state, "is_new": False}
        else:
            # Create new session
            import uuid
            session_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO sessions (id, app_name, user_id, state)
                VALUES (?, ?, ?, ?)
            ''', (session_id, app_name, user_id, json.dumps(initial_state)))
            
            conn.commit()
            conn.close()
            return {"id": session_id, "state": initial_state, "is_new": True}
    
    def update_session_state(self, session_id: str, state: dict):
        """Update the session state."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions 
            SET state = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (json.dumps(state), session_id))
        
        conn.commit()
        conn.close()

# ===== PART 2: Define Initial State =====
# This will only be used when creating a new session
initial_state = {
    "user_name": "Project Manager",
    "projects": [],
    "team_members": []
}


async def main_async():
    # Setup constants
    APP_NAME = "Project Management Assistant"
    USER_ID = "project_manager_user"

    # ===== PART 3: Session Management - Find or Create =====
    session_manager = SessionManager(DB_PATH)
    session_info = session_manager.get_or_create_session(APP_NAME, USER_ID, initial_state)
    
    SESSION_ID = session_info["id"]
    current_state = session_info["state"]
    
    if session_info["is_new"]:
        print(f"Created new session: {SESSION_ID}")
    else:
        print(f"Continuing existing session: {SESSION_ID}")

    # ===== PART 4: Agent Setup =====
    # Initialize the GenAI client
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    
    # Create the project management agent
    agent = ProjectManagementAgent(current_state, session_manager, SESSION_ID)

    # ===== PART 5: Interactive Conversation Loop =====
    print("\nWelcome to Project Management Assistant!")
    print("Your projects, tasks, and team members will be remembered across conversations.")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        # Get user input
        user_input = input("You: ")

        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit"]:
            print("Ending conversation. Your data has been saved to the database.")
            break

        # Process the user query through the agent
        response = agent.process_message(client, user_input)
        print(f"\n🤖 Assistant: {response}\n")


if __name__ == "__main__":
    asyncio.run(main_async())
