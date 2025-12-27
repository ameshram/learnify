# Learnify

AI-Powered Teaching Assistant built with Flask and Claude API.

## Features

- **Interactive Teaching**: Real-time AI explanations with streaming
- **Adaptive Quizzes**: Auto-generated questions with detailed feedback
- **Progress Tracking**: Session history and performance analytics
- **Modern UI**: Dark mode, responsive design

## Quick Start

```bash
# Clone and setup
cd learnify
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run
python app.py
```

Open http://localhost:5001

## Project Structure

```
learnify/
├── app.py              # Flask application
├── claude_client.py    # Claude API client
├── teaching_agent.py   # Teaching orchestration
├── quiz_manager.py     # Quiz generation/scoring
├── session_manager.py  # Database management
├── templates/          # HTML templates
├── static/             # CSS and JavaScript
└── requirements.txt    # Dependencies
```

## Deployment

### Docker

```bash
docker build -t learnify .
docker run -p 5000:5000 -e ANTHROPIC_API_KEY=your_key learnify
```

### AWS Lightsail

1. Create Lightsail instance (Ubuntu 22.04)
2. SSH and run:

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv git
git clone <your-repo> learnify
cd learnify
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your_key" > .env
gunicorn --bind 0.0.0.0:5000 app:app
```

## Tech Stack

- **Backend**: Flask, SQLAlchemy
- **AI**: Claude API (claude-sonnet-4-20250514)
- **Frontend**: Vanilla JS, CSS Variables
- **Database**: SQLite

## License

MIT
