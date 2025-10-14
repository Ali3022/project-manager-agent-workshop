# Migration Guide: Google ADK to Google GenAI SDK

This document outlines the migration from the deprecated Google ADK to the new Google GenAI SDK.

## Major Changes Made

### 1. Dependencies Updated (requirements.txt)

**Before:**
```
google-adk[database]==0.5.0
yfinance==0.2.56
psutil==5.9.5
litellm==1.66.3
google-generativeai==0.8.5
python-dotenv==1.1.0
```

**After:**
```
google-genai>=1.43.0
python-dotenv==1.1.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
```

### 2. Architecture Changes

#### Old Architecture (google.adk)
- Used `google.adk.agents.Agent` for agent creation
- Used `google.adk.tools.tool_context.ToolContext` for tool functions
- Used `google.adk.sessions.DatabaseSessionService` for persistence
- Used `google.adk.runners.Runner` for execution

#### New Architecture (google-genai)
- Uses `google.genai.Client` for model interactions
- Uses `google.genai.types.FunctionDeclaration` for function declarations
- Uses custom `SessionManager` class with SQLite for persistence
- Uses direct async function calling for execution

### 3. Code Changes

#### main.py
- Replaced ADK session service with custom SessionManager
- Replaced Runner with direct client usage
- Updated imports to use google.genai
- Simplified conversation loop

#### agent.py (Completely Rewritten)
- Changed from standalone tool functions to class-based architecture
- Updated function declarations to use `types.FunctionDeclaration`
- Implemented custom function execution handling
- Added async message processing with function calling support

### 4. New Features
- Uses Gemini 2.0 Flash model
- Modern async/await patterns
- Better error handling
- Simplified function calling mechanism

### 5. API Key Configuration
- Changed from `GOOGLE_API_KEY` to `GEMINI_API_KEY` (both still supported)
- Updated .env.example file

## Installation & Setup

1. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Update your .env file:**
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

## Breaking Changes

1. **Tool Function Signatures**: All tool functions now use regular Python parameters instead of `ToolContext`
2. **Session Management**: Custom session management replaces ADK's DatabaseSessionService
3. **Agent Creation**: Class-based agent instead of ADK Agent configuration
4. **Function Calling**: Uses Google GenAI SDK's native function calling instead of ADK tools

## Benefits of Migration

1. **Future-Proof**: Uses the actively maintained Google GenAI SDK
2. **Better Performance**: More efficient function calling and message processing
3. **Simpler Architecture**: Fewer dependencies and cleaner code structure
4. **Latest Models**: Access to Gemini 2.0 and newer model versions
5. **Unified SDK**: Single SDK for all Google AI services

## Backward Compatibility

The application maintains the same user interface and functionality. All existing data in the SQLite database remains compatible.
