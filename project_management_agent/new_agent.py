from datetime import datetime
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types
import json


class ProjectManagementAgent:
    """Project Management Agent using the latest Google GenAI SDK."""
    
    def __init__(self, initial_state: Dict[str, Any], session_manager, session_id: str):
        self.state = initial_state
        self.session_manager = session_manager
        self.session_id = session_id
        self.system_instruction = """
        You are Dwight K. Schrute (from The Office series), Assistant Regional Manager and SUPERIOR project management specialist that remembers projects, tasks, and team members across conversations.
        
        You can help users manage their projects with the following capabilities:
        
        1. Project Management
        - Add new projects
        - View existing projects
        - Update projects
        - Delete projects
        - Get project status
        - Search for projects by name or description
        
        2. Task Management
        - Add tasks to projects
        - Update tasks
        - Delete tasks
        - Search for tasks across all projects
        
        3. Team Management
        - Add team members
        - View team members
        - Update team members
        - Delete team members
        
        Always be friendly and address the user by name. If you don't know their name yet,
        ask them to tell you their name so you can update it.
        
        When dealing with projects and tasks:
        - When the user asks to update or delete a project/task but doesn't provide an index, first try to find the project or task by name
        - If they mention the name of the project or task, look through the list to find a match
        - If you find a match, use that index
        - If no match is found or multiple matches exist, ask the user to be more specific
        
        Always provide helpful, clear responses and explain what actions you've taken.
        Keep track of all state changes and make sure data persists across conversations.
        """

    def _update_state(self, key: str, value: Any):
        """Update a key in the state and persist to database."""
        self.state[key] = value
        self.session_manager.update_session_state(self.session_id, self.state)

    def add_project(self, name: str, description: Optional[str] = None, due_date: Optional[str] = None) -> dict:
        """Add a new project to the project list."""
        # Handle default values
        if description is None:
            description = "No description provided"
        if due_date is None:
            due_date = "2025-12-31"
        
        # Validate date format
        try:
            if due_date:
                datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return {
                "action": "add_project",
                "status": "error",
                "message": f"Invalid date format: {due_date}. Please use YYYY-MM-DD format."
            }
        
        # Get current projects
        projects = self.state.get("projects", [])
        
        # Create new project
        new_project = {
            "name": name,
            "description": description,
            "due_date": due_date,
            "tasks": [],
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Add project and update state
        projects.append(new_project)
        self._update_state("projects", projects)
        
        return {
            "action": "add_project",
            "project": name,
            "message": f"Added project: {name} with due date {due_date}"
        }

    def view_projects(self) -> dict:
        """View all current projects."""
        projects = self.state.get("projects", [])
        return {
            "action": "view_projects",
            "projects": projects,
            "count": len(projects)
        }

    def add_team_member(self, name: str, role: str, email: str) -> dict:
        """Add a new team member."""
        team_members = self.state.get("team_members", [])
        
        new_member = {
            "name": name,
            "role": role,
            "email": email,
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        
        team_members.append(new_member)
        self._update_state("team_members", team_members)
        
        return {
            "action": "add_team_member",
            "member": name,
            "message": f"Added team member: {name} with role {role}"
        }

    def view_team_members(self) -> dict:
        """View all team members."""
        team_members = self.state.get("team_members", [])
        return {
            "action": "view_team_members",
            "team_members": team_members,
            "count": len(team_members)
        }

    def add_task(self, project_index: int, name: str, assigned_to: Optional[str] = None, 
                 description: Optional[str] = None, due_date: Optional[str] = None, 
                 priority: Optional[str] = None) -> dict:
        """Add a task to a specific project."""
        projects = self.state.get("projects", [])
        
        # Convert 1-based index to 0-based
        zero_based_index = project_index - 1
        
        if zero_based_index < 0 or zero_based_index >= len(projects):
            return {
                "action": "add_task",
                "status": "error",
                "message": f"Invalid project index: {project_index}. Please choose between 1 and {len(projects)}."
            }
        
        # Handle defaults
        if assigned_to is None:
            assigned_to = "Unassigned"
        if description is None:
            description = "No description provided"
        if due_date is None:
            due_date = "2025-12-31"
        if priority is None:
            priority = "medium"
        
        # Create new task
        new_task = {
            "name": name,
            "description": description,
            "assigned_to": assigned_to,
            "due_date": due_date,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Add task to project
        projects[zero_based_index]["tasks"].append(new_task)
        self._update_state("projects", projects)
        
        return {
            "action": "add_task",
            "task": name,
            "project": projects[zero_based_index]["name"],
            "message": f"Added task '{name}' to project '{projects[zero_based_index]['name']}'"
        }

    def update_user_name(self, name: str) -> dict:
        """Update the user's name."""
        self._update_state("user_name", name)
        return {
            "action": "update_user_name",
            "message": f"Updated user name to: {name}"
        }

    def get_function_declarations(self) -> List[types.FunctionDeclaration]:
        """Get all function declarations for the agent."""
        return [
            types.FunctionDeclaration(
                name='add_project',
                description='Add a new project to the project list',
                parameters_json_schema={
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string', 'description': 'The name of the project'},
                        'description': {'type': 'string', 'description': 'A description of the project (optional)'},
                        'due_date': {'type': 'string', 'description': 'The due date for the project (YYYY-MM-DD) (optional)'}
                    },
                    'required': ['name']
                }
            ),
            types.FunctionDeclaration(
                name='view_projects',
                description='View all current projects',
                parameters_json_schema={'type': 'object', 'properties': {}}
            ),
            types.FunctionDeclaration(
                name='add_team_member',
                description='Add a new team member',
                parameters_json_schema={
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string', 'description': 'The name of the team member'},
                        'role': {'type': 'string', 'description': 'The role of the team member'},
                        'email': {'type': 'string', 'description': 'The email of the team member'}
                    },
                    'required': ['name', 'role', 'email']
                }
            ),
            types.FunctionDeclaration(
                name='view_team_members',
                description='View all team members',
                parameters_json_schema={'type': 'object', 'properties': {}}
            ),
            types.FunctionDeclaration(
                name='add_task',
                description='Add a task to a specific project',
                parameters_json_schema={
                    'type': 'object',
                    'properties': {
                        'project_index': {'type': 'integer', 'description': 'The 1-based index of the project'},
                        'name': {'type': 'string', 'description': 'The name of the task'},
                        'assigned_to': {'type': 'string', 'description': 'Who the task is assigned to (optional)'},
                        'description': {'type': 'string', 'description': 'Description of the task (optional)'},
                        'due_date': {'type': 'string', 'description': 'Due date for the task (YYYY-MM-DD) (optional)'},
                        'priority': {'type': 'string', 'description': 'Priority level: low, medium, high (optional)'}
                    },
                    'required': ['project_index', 'name']
                }
            ),
            types.FunctionDeclaration(
                name='update_user_name',
                description='Update the user\'s name',
                parameters_json_schema={
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string', 'description': 'The user\'s name'}
                    },
                    'required': ['name']
                }
            )
        ]

    def execute_function(self, function_name: str, args: dict) -> dict:
        """Execute a function based on the function call from the model."""
        if function_name == 'add_project':
            return self.add_project(**args)
        elif function_name == 'view_projects':
            return self.view_projects()
        elif function_name == 'add_team_member':
            return self.add_team_member(**args)
        elif function_name == 'view_team_members':
            return self.view_team_members()
        elif function_name == 'add_task':
            return self.add_task(**args)
        elif function_name == 'update_user_name':
            return self.update_user_name(**args)
        else:
            return {"error": f"Unknown function: {function_name}"}

    async def process_message(self, client: genai.Client, user_message: str) -> str:
        """Process a user message and return the response."""
        # Create the tool configuration
        tools = [types.Tool(function_declarations=self.get_function_declarations())]
        
        # Create the conversation content with context
        context_info = f"""
Current State:
- User: {self.state.get('user_name', 'Unknown')}
- Projects: {len(self.state.get('projects', []))} projects
- Team Members: {len(self.state.get('team_members', []))} members

Projects: {json.dumps(self.state.get('projects', []), indent=2)}
Team Members: {json.dumps(self.state.get('team_members', []), indent=2)}
"""
        
        # Prepare the conversation
        contents = [
            types.Content(
                role='user',
                parts=[types.Part.from_text(f"{context_info}\n\nUser Message: {user_message}")]
            )
        ]
        
        try:
            # Generate response with function calling
            response = await client.aio.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    tools=tools,
                    temperature=0.7,
                    max_output_tokens=2048
                )
            )
            
            # Process function calls if any
            if response.function_calls:
                function_results = []
                for function_call in response.function_calls:
                    result = self.execute_function(function_call.name, function_call.args)
                    function_results.append(result)
                
                # Create function response content
                function_response_parts = []
                for i, (function_call, result) in enumerate(zip(response.function_calls, function_results)):
                    function_response_parts.append(
                        types.Part.from_function_response(
                            name=function_call.name,
                            response=result
                        )
                    )
                
                # Add function responses to conversation
                contents.extend([
                    response.candidates[0].content,  # Model's function call
                    types.Content(role='tool', parts=function_response_parts)  # Tool responses
                ])
                
                # Generate final response
                final_response = await client.aio.models.generate_content(
                    model='gemini-2.0-flash-001',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_instruction,
                        tools=tools,
                        temperature=0.7,
                        max_output_tokens=2048
                    )
                )
                
                return final_response.text
            
            return response.text
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
