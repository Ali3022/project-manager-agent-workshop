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
        self.conversation_history = []  # Store conversation history for context
        self.system_instruction = """
        You are a professional project management assistant with the personality of Dwight K. Schrute from The Office, but keep responses helpful and business-appropriate.
        
        IMPORTANT FORMATTING RULES:
        - Always present information in a clean, readable format
        - Never show raw JSON data to users
        - When listing projects or team members, use bullet points or numbered lists
        - Be conversational but professional
        - Keep responses concise and to the point
        - Remember recent conversation context to provide coherent responses
        - If referring to something mentioned earlier, acknowledge the previous conversation
        
        CAPABILITIES:
        
        1. Project Management
        - Add new projects with names, descriptions, and due dates
        - View all projects in a formatted list
        - Update project information
        - Delete projects
        - Search for projects by name
        
        2. Task Management  
        - Add tasks to specific projects
        - Update task information
        - Delete tasks individually or by name pattern
        - Delete all tasks matching a name across all projects (e.g., "remove all Task X tasks")
        - Search for tasks across projects
        
        3. Team Management
        - Add team members with name, role, and email
        - View all team members in formatted list
        - Update team member information (name, role, email)
        - Delete team members by name or index
        - Find team members by name
        
        SMART BEHAVIOR:
        - When users want to add tasks to projects by name (like "add task to Website Project"), use add_task_by_project_name instead of asking for indices
        - When users want to modify/delete by name (like "delete Jim Halpert"), first use find_team_member_by_name to get the index, then perform the action
        - If multiple matches are found, ask user to be more specific
        - Always try to understand user intent without requiring technical details like indices
        - Always confirm actions taken
        - Present results in human-readable format, never raw JSON
        - Be proactive in helping users accomplish their goals
        
        Keep Dwight's confident personality but stay professional and helpful. Avoid overly dramatic language.
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
        
        if not projects:
            return {
                "action": "view_projects",
                "projects": [],
                "count": 0,
                "message": "No projects found. You can create a new project by saying 'Create a project called [Project Name]'."
            }
        
        # Create a formatted message
        formatted_list = []
        for i, project in enumerate(projects, 1):
            task_count = len(project.get("tasks", []))
            completed_tasks = len([t for t in project.get("tasks", []) if t.get("status") == "completed"])
            formatted_list.append(f"{i}. {project['name']} - Due: {project['due_date']} (Tasks: {completed_tasks}/{task_count} completed)")
        
        return {
            "action": "view_projects",
            "projects": projects,
            "count": len(projects),
            "formatted_list": "\n".join(formatted_list),
            "message": f"Current projects ({len(projects)}):\n" + "\n".join(formatted_list)
        }

    def add_team_member(self, name: str, role: str, email: Optional[str] = None) -> dict:
        """Add a new team member."""
        team_members = self.state.get("team_members", [])
        
        # Use a default email if not provided
        if email is None:
            email = f"{name.lower().replace(' ', '.')}@company.com"
        
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
            "message": f"Added team member: {name} with role {role} and email {email}"
        }

    def view_team_members(self) -> dict:
        """View all team members."""
        team_members = self.state.get("team_members", [])
        
        if not team_members:
            return {
                "action": "view_team_members",
                "team_members": [],
                "count": 0,
                "message": "No team members found. You can add team members by saying 'Add [Name] as a [Role]'."
            }
        
        # Create a formatted message
        formatted_list = []
        for i, member in enumerate(team_members, 1):
            formatted_list.append(f"{i}. {member['name']} - {member['role']} ({member.get('email', 'No email')})")
        
        return {
            "action": "view_team_members",
            "team_members": team_members,
            "count": len(team_members),
            "formatted_list": "\n".join(formatted_list),
            "message": f"Current team members ({len(team_members)}):\n" + "\n".join(formatted_list)
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

    def update_team_member(self, index: int, name: Optional[str] = None, 
                          role: Optional[str] = None, email: Optional[str] = None) -> dict:
        """Update an existing team member."""
        team_members = self.state.get("team_members", [])
        
        # Convert 1-based index to 0-based
        zero_based_index = index - 1
        
        if zero_based_index < 0 or zero_based_index >= len(team_members):
            return {
                "action": "update_team_member",
                "status": "error",
                "message": f"Invalid team member index: {index}. Please choose between 1 and {len(team_members)}."
            }
        
        # Update fields if provided
        if name is not None:
            team_members[zero_based_index]["name"] = name
        if role is not None:
            team_members[zero_based_index]["role"] = role
        if email is not None:
            team_members[zero_based_index]["email"] = email
        
        # Update state
        self._update_state("team_members", team_members)
        
        return {
            "action": "update_team_member",
            "member": team_members[zero_based_index]["name"],
            "message": f"Updated team member: {team_members[zero_based_index]['name']}"
        }

    def delete_team_member(self, index: int) -> dict:
        """Delete a team member."""
        team_members = self.state.get("team_members", [])
        
        # Convert 1-based index to 0-based
        zero_based_index = index - 1
        
        if zero_based_index < 0 or zero_based_index >= len(team_members):
            return {
                "action": "delete_team_member",
                "status": "error",
                "message": f"Invalid team member index: {index}. Please choose between 1 and {len(team_members)}."
            }
        
        # Remove team member
        deleted_member = team_members.pop(zero_based_index)
        self._update_state("team_members", team_members)
        
        return {
            "action": "delete_team_member",
            "member": deleted_member["name"],
            "message": f"Deleted team member: {deleted_member['name']}"
        }

    def find_team_member_by_name(self, name: str) -> dict:
        """Find a team member by name."""
        team_members = self.state.get("team_members", [])
        
        matches = []
        for i, member in enumerate(team_members):
            if name.lower() in member["name"].lower():
                matches.append({
                    "index": i + 1,  # 1-based index
                    "member": member
                })
        
        if len(matches) == 0:
            return {
                "action": "find_team_member_by_name",
                "status": "not_found",
                "message": f"No team member found with name containing '{name}'"
            }
        elif len(matches) == 1:
            return {
                "action": "find_team_member_by_name",
                "status": "found",
                "match": matches[0],
                "message": f"Found team member: {matches[0]['member']['name']} at index {matches[0]['index']}"
            }
        else:
            return {
                "action": "find_team_member_by_name",
                "status": "multiple_matches",
                "matches": matches,
                "message": f"Found {len(matches)} team members matching '{name}'"
            }

    def find_project_by_name(self, name: str) -> dict:
        """Find a project by name."""
        projects = self.state.get("projects", [])
        
        matches = []
        for i, project in enumerate(projects):
            if name.lower() in project["name"].lower():
                matches.append({
                    "index": i + 1,  # 1-based index
                    "project": project
                })
        
        if len(matches) == 0:
            return {
                "action": "find_project_by_name",
                "status": "not_found",
                "message": f"No project found with name containing '{name}'"
            }
        elif len(matches) == 1:
            return {
                "action": "find_project_by_name",
                "status": "found",
                "match": matches[0],
                "message": f"Found project: {matches[0]['project']['name']} at index {matches[0]['index']}"
            }
        else:
            return {
                "action": "find_project_by_name",
                "status": "multiple_matches",
                "matches": matches,
                "message": f"Found {len(matches)} projects matching '{name}'"
            }

    def add_task_by_project_name(self, project_name: str, task_name: str, 
                                assigned_to: Optional[str] = None, 
                                description: Optional[str] = None, 
                                due_date: Optional[str] = None, 
                                priority: Optional[str] = None) -> dict:
        """Add a task to a project by project name (smarter version)."""
        # First, try to find the project by name
        find_result = self.find_project_by_name(project_name)
        
        if find_result["status"] == "not_found":
            return {
                "action": "add_task_by_project_name",
                "status": "error",
                "message": f"Could not find project '{project_name}'. Please check the project name or create it first."
            }
        elif find_result["status"] == "multiple_matches":
            project_list = [f"{match['index']}. {match['project']['name']}" for match in find_result["matches"]]
            return {
                "action": "add_task_by_project_name", 
                "status": "error",
                "message": f"Found multiple projects matching '{project_name}':\n" + "\n".join(project_list) + "\nPlease be more specific."
            }
        else:
            # Found exactly one project, add the task
            project_index = find_result["match"]["index"]
            return self.add_task(project_index, task_name, assigned_to, description, due_date, priority)

    def add_task_smart(self, task_description: str, project_hint: Optional[str] = None) -> dict:
        """
        Smart task adding that parses natural language.
        Examples:
        - "Add task 'Design homepage' to Website project"  
        - "Create task 'Write tests' for the API project assigned to John"
        - "Add 'Fix bug in login' to project 1"
        """
        # Extract task name and project info from description
        import re
        
        # Try to extract project from the description
        project_patterns = [
            r'to (?:the )?(.+?) project',
            r'to project (.+)',
            r'for (?:the )?(.+?) project',  
            r'for project (.+)',
            r'in (?:the )?(.+?) project',
            r'in project (.+)'
        ]
        
        project_name = project_hint
        task_name = task_description
        
        # Look for project references in the task description
        if not project_name:
            for pattern in project_patterns:
                match = re.search(pattern, task_description, re.IGNORECASE)
                if match:
                    project_name = match.group(1).strip()
                    # Remove the project reference from task name
                    task_name = re.sub(pattern, '', task_description, flags=re.IGNORECASE).strip()
                    break
        
        # Clean up task name - remove quotes and extra words
        task_name = re.sub(r'^(?:add |create )?(?:task )?[\'"]?', '', task_name, flags=re.IGNORECASE)
        task_name = re.sub(r'[\'"]?$', '', task_name)
        task_name = task_name.strip()
        
        if not project_name:
            # If no project specified, list available projects
            projects = self.state.get("projects", [])
            if not projects:
                return {
                    "action": "add_task_smart",
                    "status": "error", 
                    "message": "No projects available. Please create a project first, or specify which project to add the task to."
                }
            else:
                project_list = [f"{i+1}. {p['name']}" for i, p in enumerate(projects)]
                return {
                    "action": "add_task_smart",
                    "status": "error",
                    "message": f"Which project should I add '{task_name}' to?\n" + "\n".join(project_list)
                }
        
        # Use the smart project name function
        return self.add_task_by_project_name(project_name, task_name)

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
            ),
            types.FunctionDeclaration(
                name='update_team_member',
                description='Update an existing team member',
                parameters_json_schema={
                    'type': 'object',
                    'properties': {
                        'index': {'type': 'integer', 'description': 'The 1-based index of the team member'},
                        'name': {'type': 'string', 'description': 'The name of the team member (optional)'},
                        'role': {'type': 'string', 'description': 'The role of the team member (optional)'},
                        'email': {'type': 'string', 'description': 'The email of the team member (optional)'}
                    },
                    'required': ['index']
                }
            ),
            types.FunctionDeclaration(
                name='delete_team_member',
                description='Delete a team member',
                parameters_json_schema={
                    'type': 'object',
                    'properties': {
                        'index': {'type': 'integer', 'description': 'The 1-based index of the team member'}
                    },
                    'required': ['index']
                }
            ),
            types.FunctionDeclaration(
                name='find_team_member_by_name',
                description='Find a team member by name',
                parameters_json_schema={
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string', 'description': 'The name of the team member'}
                    },
                    'required': ['name']
                }
            ),
            types.FunctionDeclaration(
                name='find_project_by_name',
                description='Find a project by name',
                parameters_json_schema={
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string', 'description': 'The name of the project'}
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
        elif function_name == 'update_team_member':
            return self.update_team_member(**args)
        elif function_name == 'delete_team_member':
            return self.delete_team_member(**args)
        elif function_name == 'find_team_member_by_name':
            return self.find_team_member_by_name(**args)
        elif function_name == 'find_project_by_name':
            return self.find_project_by_name(**args)
        else:
            return {"error": f"Unknown function: {function_name}"}

    def get_python_functions(self):
        """Get Python functions for automatic function calling."""
        return [
            self.add_project,
            self.view_projects, 
            self.delete_project,
            self.delete_project_by_name,
            self.clear_all_projects,
            self.add_team_member,
            self.view_team_members,
            self.update_team_member,
            self.delete_team_member,
            self.clear_all_team_members,
            self.add_task,
            self.add_task_by_project_name,  # Smart task adding by project name
            self.add_task_smart,  # Very smart task adding with natural language
            self.delete_tasks_by_name,  # Delete tasks by name across all projects
            self.update_task_status,  # Update task status (complete/pending)
            self.remove_completed_tasks,  # Remove all completed tasks
            self.find_project_by_name,
            self.find_team_member_by_name,
            self.clear_all_data,  # Clear everything
            self.update_user_name
        ]

    def process_message(self, client: genai.Client, user_message: str) -> str:
        """Process a user message and return the response."""
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Keep only last 10 exchanges (20 messages) to prevent context from getting too long
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        # Create context info
        context_info = f"""
Current State:
- User: {self.state.get('user_name', 'Unknown')}
- Projects: {len(self.state.get('projects', []))} projects  
- Team Members: {len(self.state.get('team_members', []))} members

Projects: {json.dumps(self.state.get('projects', []), indent=2)}
Team Members: {json.dumps(self.state.get('team_members', []), indent=2)}
"""
        
        # Add recent conversation history for context
        conversation_context = ""
        if len(self.conversation_history) > 1:  # More than just the current message
            recent_history = self.conversation_history[-6:-1]  # Last 5 messages (excluding current)
            if recent_history:
                conversation_context = "\n\nRecent Conversation:\n"
                for msg in recent_history:
                    role = "User" if msg["role"] == "user" else "Dwight"
                    conversation_context += f"{role}: {msg['content']}\n"
        
        full_message = f"{context_info}{conversation_context}\n\nCurrent User Message: {user_message}"
        
        try:
            # Use automatic function calling with Python functions (synchronous)
            response = client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=full_message,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    tools=self.get_python_functions(),  # Pass Python functions directly
                    temperature=0.7,
                    max_output_tokens=2048
                )
            )
            
            # Add assistant response to conversation history
            assistant_response = response.text
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            
            return assistant_response
            
        except Exception as e:
            error_response = f"Sorry, I encountered an error: {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_response})
            return error_response

    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        return {
            "action": "clear_conversation_history", 
            "message": "Conversation history cleared. Starting fresh!"
        }

    def delete_project(self, index: int) -> dict:
        """Delete a project by index."""
        projects = self.state.get("projects", [])
        
        # Convert 1-based index to 0-based
        zero_based_index = index - 1
        
        if zero_based_index < 0 or zero_based_index >= len(projects):
            return {
                "action": "delete_project",
                "status": "error",
                "message": f"Invalid project index: {index}. Please choose between 1 and {len(projects)}."
            }
        
        # Remove project
        deleted_project = projects.pop(zero_based_index)
        self._update_state("projects", projects)
        
        return {
            "action": "delete_project",
            "project": deleted_project["name"],
            "message": f"Deleted project: {deleted_project['name']}"
        }

    def delete_project_by_name(self, name: str) -> dict:
        """Delete a project by name."""
        find_result = self.find_project_by_name(name)
        
        if find_result["status"] == "not_found":
            return {
                "action": "delete_project_by_name",
                "status": "error",
                "message": f"Could not find project '{name}' to delete."
            }
        elif find_result["status"] == "multiple_matches":
            project_list = [f"{match['index']}. {match['project']['name']}" for match in find_result["matches"]]
            return {
                "action": "delete_project_by_name", 
                "status": "error",
                "message": f"Found multiple projects matching '{name}':\n" + "\n".join(project_list) + "\nPlease be more specific."
            }
        else:
            # Found exactly one project, delete it
            project_index = find_result["match"]["index"]
            return self.delete_project(project_index)

    def clear_all_projects(self) -> dict:
        """Clear all projects."""
        self._update_state("projects", [])
        return {
            "action": "clear_all_projects",
            "message": "All projects have been cleared."
        }

    def clear_all_team_members(self) -> dict:
        """Clear all team members."""
        self._update_state("team_members", [])
        return {
            "action": "clear_all_team_members",
            "message": "All team members have been cleared."
        }

    def clear_all_data(self) -> dict:
        """Clear all projects, tasks, and team members."""
        self._update_state("projects", [])
        self._update_state("team_members", [])
        return {
            "action": "clear_all_data",
            "message": "All projects, tasks, and team members have been cleared."
        }

    def update_task_status(self, project_name: str, task_name: str, new_status: str) -> dict:
        """Update the status of a specific task."""
        projects = self.state.get("projects", [])
        
        # Find the project
        project_found = None
        for project in projects:
            if project_name.lower() in project["name"].lower():
                project_found = project
                break
        
        if not project_found:
            return {
                "action": "update_task_status",
                "status": "error",
                "message": f"Could not find project containing '{project_name}'."
            }
        
        # Find the task
        tasks = project_found.get("tasks", [])
        task_found = None
        for task in tasks:
            if task_name.lower() in task["name"].lower():
                task_found = task
                break
        
        if not task_found:
            return {
                "action": "update_task_status",
                "status": "error", 
                "message": f"Could not find task '{task_name}' in project '{project_found['name']}'."
            }
        
        # Update task status
        old_status = task_found.get("status", "pending")
        task_found["status"] = new_status.lower()
        
        # Update the state
        self._update_state("projects", projects)
        
        return {
            "action": "update_task_status",
            "status": "success",
            "project": project_found["name"],
            "task": task_found["name"],
            "old_status": old_status,
            "new_status": new_status,
            "message": f"Updated task '{task_found['name']}' status from '{old_status}' to '{new_status}' in project '{project_found['name']}'."
        }

    def delete_tasks_by_name(self, task_name: str) -> dict:
        """Delete all tasks that match a given name across all projects."""
        projects = self.state.get("projects", [])
        deleted_count = 0
        affected_projects = []
        
        if not projects:
            return {
                "action": "delete_tasks_by_name",
                "status": "error",
                "message": "No projects found to search for tasks."
            }
        
        # Search through all projects
        for project in projects:
            tasks = project.get("tasks", [])
            original_task_count = len(tasks)
            
            # Filter out tasks that match the name (case insensitive)
            remaining_tasks = []
            for task in tasks:
                if task_name.lower() not in task["name"].lower():
                    remaining_tasks.append(task)
                else:
                    deleted_count += 1
            
            # Update the project if tasks were removed
            if len(remaining_tasks) < original_task_count:
                project["tasks"] = remaining_tasks
                affected_projects.append(project["name"])
        
        # Update the state
        self._update_state("projects", projects)
        
        if deleted_count == 0:
            return {
                "action": "delete_tasks_by_name",
                "status": "not_found",
                "task_name": task_name,
                "message": f"No tasks found with name containing '{task_name}'."
            }
        else:
            affected_list = ", ".join(affected_projects)
            return {
                "action": "delete_tasks_by_name",
                "status": "success",
                "task_name": task_name,
                "deleted_count": deleted_count,
                "affected_projects": affected_projects,
                "message": f"Deleted {deleted_count} task(s) containing '{task_name}' from project(s): {affected_list}"
            }
    
    def remove_completed_tasks(self) -> dict:
        """Remove all completed tasks from all projects."""
        projects = self.state.get("projects", [])
        removed_count = 0
        affected_projects = []
        
        if not projects:
            return {
                "action": "remove_completed_tasks",
                "status": "error",
                "message": "No projects found."
            }
        
        # Remove completed tasks from all projects
        for project in projects:
            tasks = project.get("tasks", [])
            original_count = len(tasks)
            
            # Keep only non-completed tasks
            remaining_tasks = [task for task in tasks if task.get("status", "pending") != "completed"]
            
            if len(remaining_tasks) < original_count:
                removed_count += original_count - len(remaining_tasks)
                project["tasks"] = remaining_tasks
                affected_projects.append(project["name"])
        
        # Update the state
        self._update_state("projects", projects)
        
        if removed_count == 0:
            return {
                "action": "remove_completed_tasks",
                "status": "no_tasks",
                "message": "No completed tasks found to remove."
            }
        else:
            affected_list = ", ".join(affected_projects)
            return {
                "action": "remove_completed_tasks",
                "status": "success",
                "removed_count": removed_count,
                "affected_projects": affected_projects,
                "message": f"Removed {removed_count} completed task(s) from project(s): {affected_list}"
            }
