# 🚀 Quick Setup Guide - Project Management Assistant

## 🎯 TL;DR - Get Started in 3 Minutes

### 1. 📁 Setup Environment
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. 🔑 Get Your API Key
1. Go to [Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key)
2. Sign in and create a new API key
3. Copy your API key

### 3. 🔐 Set Your API Key
```bash
# Option A: Create .env file (recommended)
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Option B: Export environment variable
export GEMINI_API_KEY=your_api_key_here
```

### 4. 🌐 Start Web UI
```bash
# Easy way
./run_web_ui.sh

# Or manually
streamlit run streamlit_app.py
```

### 5. 🎉 Open Browser
Go to: **http://localhost:8501**

## 💡 First Steps

Once the web UI is running:

1. **👋 Introduce yourself**: "Hi, my name is [Your Name]"
2. **📋 Create a project**: "Create a new project called Website Redesign with due date 2025-12-31"
3. **👥 Add team member**: "Add John Doe as a Developer with email john@company.com"
4. **✅ Add a task**: "Add a task called 'Design homepage' to project 1 assigned to John Doe"

## 🆘 Troubleshooting

### API Key Issues
- Make sure your API key is correct (starts with "AIza")
- Check that .env file has correct format: `GEMINI_API_KEY=AIza...`
- Try exporting directly: `export GEMINI_API_KEY=AIza...`

### Port Already in Use
```bash
# Kill process on port 8501
kill -9 $(lsof -t -i:8501)

# Or use different port
streamlit run streamlit_app.py --server.port 8502
```

### Module Import Errors
```bash
# Make sure you're in project directory
cd project-manager-agent

# Reinstall dependencies
pip install -r requirements.txt
```

## 🔄 Alternative: Command Line
If you prefer command line:
```bash
python main.py
```

Happy project managing! 🎊
