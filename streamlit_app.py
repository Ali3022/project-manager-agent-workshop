import streamlit as st
import asyncio
import os
from datetime import datetime
import json
from pathlib import Path

# Import your agent components
from project_management_agent.agent import ProjectManagementAgent
from main import SessionManager, initial_state
from google import genai

# Set page configuration
st.set_page_config(
    page_title="Project Management Assistant - Dwight K. Schrute",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
k    /* Chat message styling will be handled by Streamlit's native chat components */
    .sidebar-content {
        background-color: #37474F;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .project-card {
        background: linear-gradient(135deg, #FF9800, #F57C00);
        color: white;
        padding: 1.2rem;
        border-left: 5px solid #E65100;
        margin: 0.8rem 0;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(255, 152, 0, 0.3);
        transition: transform 0.2s ease;
    }
    .project-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(255, 152, 0, 0.4);
    }
    .project-card h4 {
        color: white;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .team-card {
        background: linear-gradient(135deg, #9C27B0, #7B1FA2);
        color: white;
        padding: 1.2rem;
        border-left: 5px solid #4A148C;
        margin: 0.8rem 0;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(156, 39, 176, 0.3);
        transition: transform 0.2s ease;
    }
    .team-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(156, 39, 176, 0.4);
    }
    .team-card h4 {
        color: white;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .task-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .task-high-priority {
        border-left: 4px solid #dc3545;
    }
    .task-medium-priority {
        border-left: 4px solid #ffc107;
    }
    .task-low-priority {
        border-left: 4px solid #28a745;
    }
    .task-completed {
        opacity: 0.7;
        background-color: #d4edda;
    }
    /* Tab styling */
    .stTabs > div > div > div > div {
        padding-top: 1rem;
    }
    /* Metric styling */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.25rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'client' not in st.session_state:
    st.session_state.client = None
if 'session_manager' not in st.session_state:
    st.session_state.session_manager = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = None

def initialize_agent():
    """Initialize the agent and session management."""
    try:
        # Check for API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            st.error("⚠️ GEMINI_API_KEY not found! Please set your API key in the environment.")
            st.stop()
        
        # Initialize client
        st.session_state.client = genai.Client(api_key=api_key)
        
        # Initialize session manager
        db_path = "./project_management_data.db"
        st.session_state.session_manager = SessionManager(db_path)
        
        # Get or create session
        app_name = "Project Management Assistant"
        user_id = "streamlit_user"
        
        session_info = st.session_state.session_manager.get_or_create_session(
            app_name, user_id, initial_state
        )
        
        st.session_state.session_id = session_info["id"]
        
        # Initialize agent
        st.session_state.agent = ProjectManagementAgent(
            session_info["state"], 
            st.session_state.session_manager, 
            st.session_state.session_id
        )
        
        return True
    except Exception as e:
        st.error(f"Error initializing agent: {str(e)}")
        return False

def display_projects():
    """Display current projects in the sidebar."""
    if st.session_state.agent:
        projects = st.session_state.agent.state.get("projects", [])
        
        st.sidebar.markdown("### 📋 Current Projects")
        
        if projects:
            for i, project in enumerate(projects, 1):
                tasks_count = len(project.get("tasks", []))
                completed_tasks = len([t for t in project.get("tasks", []) if t.get("status") == "completed"])
                
                # Create an expander for each project to show tasks
                with st.sidebar.expander(f"📋 {project['name']}", expanded=False):
                    st.markdown(f"**Due:** {project['due_date']}")
                    st.markdown(f"**Progress:** {completed_tasks}/{tasks_count} tasks completed")
                    
                    # Progress bar
                    if tasks_count > 0:
                        progress = completed_tasks / tasks_count
                        st.progress(progress)
                        st.caption(f"{progress:.1%} complete")
                    
                    st.markdown(f"**Description:** {project.get('description', 'No description')}")
                    
                    # Show tasks in this project
                    tasks = project.get("tasks", [])
                    if tasks:
                        st.markdown("**Tasks:**")
                        for j, task in enumerate(tasks):
                            status_emoji = "✅" if task.get("status") == "completed" else "⏳"
                            priority = task.get("priority", "Medium")
                            priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "🟡")
                            
                            st.markdown(f"{status_emoji} {priority_emoji} {task['name']}")
                            if task.get("assigned_to") != "Unassigned":
                                st.caption(f"Assigned to: {task.get('assigned_to', 'Unassigned')}")
                    else:
                        st.info("No tasks yet")
        else:
            st.sidebar.info("No projects yet. Start by asking to create a project!")

def display_team_members():
    """Display team members in the sidebar."""
    if st.session_state.agent:
        team_members = st.session_state.agent.state.get("team_members", [])
        
        st.sidebar.markdown("### 👥 Team Members")
        
        if team_members:
            for member in team_members:
                st.sidebar.markdown(f"""
                <div class="team-card">
                    <h4>{member['name']}</h4>
                    <p><strong>Role:</strong> {member['role']}</p>
                    <p><strong>Email:</strong> {member['email']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.sidebar.info("No team members yet. Ask to add team members!")

def display_stats():
    """Display statistics in the sidebar."""
    if st.session_state.agent:
        state = st.session_state.agent.state
        projects = state.get("projects", [])
        team_members = state.get("team_members", [])
        
        # Calculate stats
        total_tasks = sum(len(p.get("tasks", [])) for p in projects)
        completed_tasks = sum(len([t for t in p.get("tasks", []) if t.get("status") == "completed"]) for p in projects)
        
        st.sidebar.markdown("### 📊 Statistics")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Projects", len(projects))
            st.metric("Team Members", len(team_members))
        
        with col2:
            st.metric("Total Tasks", total_tasks)
            st.metric("Completed", completed_tasks)

def process_message_sync(user_input: str):
    """Process user message and get agent response synchronously."""
    try:
        if st.session_state.agent and st.session_state.client:
            # Now it's a simple synchronous call
            response = st.session_state.agent.process_message(
                st.session_state.client, user_input
            )
            return response
        else:
            return "Agent not initialized properly."
    except Exception as e:
        return f"Error processing message: {str(e)}"

def display_detailed_projects():
    """Display detailed project information in the main area."""
    if not st.session_state.agent:
        st.error("Agent not initialized")
        return
    
    projects = st.session_state.agent.state.get("projects", [])
    
    if not projects:
        st.info("📋 No projects found. Use the chat to create your first project!")
        return
    
    # Project selection
    st.markdown("#### Select a Project to View Details:")
    project_names = [f"{i+1}. {proj['name']}" for i, proj in enumerate(projects)]
    selected_idx = st.selectbox("Choose project:", range(len(projects)), 
                               format_func=lambda x: project_names[x],
                               key="project_detail_selector")
    
    if selected_idx is not None:
        project = projects[selected_idx]
        
        # Project header
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"## 📋 {project['name']}")
            st.markdown(f"**Description:** {project.get('description', 'No description')}")
        
        with col2:
            st.metric("Due Date", project['due_date'])
        
        with col3:
            tasks = project.get('tasks', [])
            completed = len([t for t in tasks if t.get('status') == 'completed'])
            st.metric("Tasks", f"{completed}/{len(tasks)}")
        
        # Tasks section
        st.markdown("### 📝 Tasks in this Project")
        
        if tasks:
            # Task filters
            col1, col2, col3 = st.columns(3)
            with col1:
                status_filter = st.selectbox("Filter by Status:", 
                                           ["All", "Pending", "Completed"],
                                           key="project_detail_status_filter")
            with col2:
                priority_filter = st.selectbox("Filter by Priority:", 
                                             ["All", "High", "Medium", "Low"],
                                             key="project_detail_priority_filter")
            with col3:
                sort_by = st.selectbox("Sort by:", 
                                     ["Name", "Priority", "Due Date", "Status"],
                                     key="project_detail_sort_by")
            
            # Filter and sort tasks
            filtered_tasks = tasks.copy()
            
            if status_filter != "All":
                status_value = "completed" if status_filter == "Completed" else "pending"
                filtered_tasks = [t for t in filtered_tasks 
                                if t.get('status', 'pending') == status_value]
            
            if priority_filter != "All":
                filtered_tasks = [t for t in filtered_tasks 
                                if t.get('priority', 'Medium') == priority_filter]
            
            # Display tasks in a table format
            if filtered_tasks:
                for i, task in enumerate(filtered_tasks):
                    with st.expander(f"{task['name']}", expanded=False):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            status = task.get('status', 'pending')
                            status_emoji = "✅" if status == "completed" else "⏳"
                            st.markdown(f"**Status:** {status_emoji} {status.title()}")
                        
                        with col2:
                            priority = task.get('priority', 'Medium')
                            priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "🟡")
                            st.markdown(f"**Priority:** {priority_emoji} {priority}")
                        
                        with col3:
                            st.markdown(f"**Due:** {task.get('due_date', 'Not set')}")
                        
                        with col4:
                            st.markdown(f"**Assigned:** {task.get('assigned_to', 'Unassigned')}")
                        
                        if task.get('description'):
                            st.markdown(f"**Description:** {task['description']}")
            else:
                st.info("No tasks match the current filters.")
        else:
            st.info("No tasks in this project yet. Use the chat to add tasks!")

def display_task_management():
    """Display task management interface."""
    if not st.session_state.agent:
        st.error("Agent not initialized")
        return
    
    projects = st.session_state.agent.state.get("projects", [])
    
    if not projects:
        st.info("📊 No projects found. Create projects first to manage tasks!")
        return
    
    # Collect all tasks from all projects
    all_tasks = []
    for proj_idx, project in enumerate(projects):
        for task in project.get('tasks', []):
            task_info = task.copy()
            task_info['project_name'] = project['name']
            task_info['project_index'] = proj_idx + 1
            all_tasks.append(task_info)
    
    if not all_tasks:
        st.info("📊 No tasks found across all projects. Add some tasks to get started!")
        return
    
    # Task overview metrics
    st.markdown("#### 📊 Task Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tasks", len(all_tasks))
    
    with col2:
        completed = len([t for t in all_tasks if t.get('status') == 'completed'])
        st.metric("Completed", completed)
    
    with col3:
        pending = len(all_tasks) - completed
        st.metric("Pending", pending)
    
    with col4:
        high_priority = len([t for t in all_tasks if t.get('priority') == 'High'])
        st.metric("High Priority", high_priority)
    
    # Progress bar
    if len(all_tasks) > 0:
        progress = completed / len(all_tasks)
        st.progress(progress)
        st.caption(f"Overall completion: {progress:.1%}")
    
    # Task filters and sorting
    st.markdown("#### 🔍 Task Filters & Sorting")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        project_filter = st.selectbox("Filter by Project:", 
                                    ["All Projects"] + [p['name'] for p in projects],
                                    key="task_mgmt_project_filter")
    
    with col2:
        status_filter = st.selectbox("Filter by Status:", 
                                   ["All", "Pending", "Completed"],
                                   key="task_mgmt_status_filter")
    
    with col3:
        priority_filter = st.selectbox("Filter by Priority:", 
                                     ["All", "High", "Medium", "Low"],
                                     key="task_mgmt_priority_filter")
    
    with col4:
        sort_by = st.selectbox("Sort by:", 
                             ["Project", "Priority", "Due Date", "Status", "Name"],
                             key="task_mgmt_sort_by")
    
    # Apply filters
    filtered_tasks = all_tasks.copy()
    
    if project_filter != "All Projects":
        filtered_tasks = [t for t in filtered_tasks if t['project_name'] == project_filter]
    
    if status_filter != "All":
        status_value = "completed" if status_filter == "Completed" else "pending"
        filtered_tasks = [t for t in filtered_tasks 
                        if t.get('status', 'pending') == status_value]
    
    if priority_filter != "All":
        filtered_tasks = [t for t in filtered_tasks 
                        if t.get('priority', 'Medium') == priority_filter]
    
    # Display filtered tasks
    st.markdown("#### 📝 Tasks")
    
    if filtered_tasks:
        # Group by project for better organization
        tasks_by_project = {}
        for task in filtered_tasks:
            proj_name = task['project_name']
            if proj_name not in tasks_by_project:
                tasks_by_project[proj_name] = []
            tasks_by_project[proj_name].append(task)
        
        for project_name, project_tasks in tasks_by_project.items():
            st.markdown(f"##### 📋 {project_name}")
            
            for task in project_tasks:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    status_emoji = "✅" if task.get('status') == "completed" else "⏳"
                    st.markdown(f"{status_emoji} **{task['name']}**")
                    if task.get('description'):
                        st.caption(task['description'])
                
                with col2:
                    priority = task.get('priority', 'Medium')
                    priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "🟡")
                    st.markdown(f"{priority_emoji} {priority}")
                
                with col3:
                    st.markdown(f"📅 {task.get('due_date', 'No due date')}")
                
                with col4:
                    assigned_to = task.get('assigned_to', 'Unassigned')
                    if assigned_to != 'Unassigned':
                        st.markdown(f"👤 {assigned_to}")
                    else:
                        st.markdown("👤 Unassigned")
                
                st.divider()
    else:
        st.info("No tasks match the current filters.")
    
    # Quick actions
    st.markdown("#### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Add New Task", use_container_width=True, key="task_mgmt_add_task"):
            st.session_state.messages.append({"role": "user", "content": "I want to add a new task"})
            with st.spinner("Getting ready to add a task..."):
                response = process_message_sync("I want to add a new task")
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("📊 Show Task Summary", use_container_width=True, key="task_mgmt_show_summary"):
            st.session_state.messages.append({"role": "user", "content": "Show me a summary of all tasks"})
            with st.spinner("Generating task summary..."):
                response = process_message_sync("Show me a summary of all tasks")
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clean Up Tasks", use_container_width=True, key="task_mgmt_cleanup_tasks"):
            st.session_state.messages.append({"role": "user", "content": "Remove all completed tasks"})
            with st.spinner("Cleaning up completed tasks..."):
                response = process_message_sync("Remove all completed tasks")
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">📋 Project Management Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Powered by Dwight K. Schrute, Assistant Regional Manager</p>', unsafe_allow_html=True)
    
    # Initialize agent if not done
    if st.session_state.agent is None:
        with st.spinner("Initializing Project Management Assistant..."):
            if not initialize_agent():
                st.stop()
        st.success("✅ Agent initialized successfully!")
        st.rerun()
    
    # Sidebar content
    with st.sidebar:
        st.markdown("## 🎯 Dashboard")
        
        # User info
        if st.session_state.agent:
            user_name = st.session_state.agent.state.get("user_name", "Project Manager")
            st.markdown(f"**Welcome back, {user_name}!**")
        
        # Display stats, projects, and team members
        display_stats()
        display_projects()
        display_team_members()
        
        # Conversation controls
        st.markdown("### 🧠 Memory")
        if st.session_state.agent:
            history_count = len(st.session_state.agent.conversation_history)
            st.write(f"Conversation memory: {history_count} messages")
            
            if st.button("🗑️ Clear Memory", use_container_width=True, key="sidebar_clear_memory"):
                if st.session_state.agent:
                    st.session_state.agent.clear_conversation_history()
                    st.success("Conversation memory cleared!")
                    st.rerun()
        
        # Quick actions
        st.markdown("### 🚀 Quick Actions")
        if st.button("📋 View All Projects", use_container_width=True, key="sidebar_view_projects"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": "Show me all my projects"})
            
            # Process the message immediately
            with st.spinner("Getting your projects..."):
                response = process_message_sync("Show me all my projects")
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        if st.button("👥 View Team Members", use_container_width=True, key="sidebar_view_team"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": "Show me all team members"})
            
            # Process the message immediately
            with st.spinner("Getting team members..."):
                response = process_message_sync("Show me all team members")
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        if st.button("➕ Add New Project", use_container_width=True, key="sidebar_add_project"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": "I want to add a new project"})
            
            # Process the message immediately
            with st.spinner("How can I help you add a project?"):
                response = process_message_sync("I want to add a new project")
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        # Danger zone
        st.markdown("### ⚠️ Danger Zone")
        if st.button("🗑️ Clear All Data", use_container_width=True, type="secondary", key="sidebar_clear_all_data"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": "Clear all projects, tasks and team members"})
            
            # Process the message immediately
            with st.spinner("Clearing all data..."):
                response = process_message_sync("Clear all projects, tasks and team members")
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat with Dwight", "📋 Project Dashboard", "📊 Task Management"])
    
    with tab1:
        # Chat interface
        st.markdown("### 💬 Chat with Dwight")
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                # Clean any potential HTML artifacts from the message content
                clean_content = message["content"]
                if "</div>" in clean_content:
                    # Remove the trailing div and any whitespace
                    clean_content = clean_content.split("</div>")[0].strip()
                
                # Remove any other HTML tags that might have snuck in
                import re
                clean_content = re.sub(r'<[^>]+>', '', clean_content).strip()
                
                if message["role"] == "user":
                    # Use Streamlit's chat_message component
                    with st.chat_message("user"):
                        st.write(clean_content)
                else:
                    # Use Streamlit's chat_message component
                    with st.chat_message("assistant"):
                        st.write(clean_content)
        
        # Chat input
        user_input = st.chat_input("Ask Dwight about your projects, tasks, or team...")
        
        if user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Process message and get response
            with st.spinner("Dwight is thinking..."):
                try:
                    # Use synchronous function that handles async properly
                    response = process_message_sync(user_input)
                    
                    # Add assistant response
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            st.rerun()
    
    with tab2:
        # Project Dashboard
        st.markdown("### 📋 Project Dashboard")
        display_detailed_projects()
    
    with tab3:
        # Task Management
        st.markdown("### 📊 Task Management")
        display_task_management()
    
    # Examples section
    if len(st.session_state.messages) == 0:
        st.markdown("## 💡 Try asking Dwight:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Project Management:**
            - "Create a new project called 'Website Redesign'"
            - "Show me all my projects"
            - "Add a task to project 1"
            """)
        
        with col2:
            st.markdown("""
            **Team Management:**
            - "Add Jim Halpert as a Sales Representative"
            - "Show me all team members"
            - "Update team member information"
            """)
        
        with col3:
            st.markdown("""
            **Status & Reports:**
            - "What's the status of my projects?"
            - "Show me completed tasks"
            - "Update my name to [Your Name]"
            """)

if __name__ == "__main__":
    main()
