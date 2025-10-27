# Todo App - Django Task Management System

## Technologies Used

### Backend
- Django 5.2.7, Python 3.13, SQLite
- Celery with Redis broker
- Django Celery Beat & Results

### Frontend
- Tailwind CSS, Vanilla JavaScript, HTML5

### Email
- Django SMTP Backend with Gmail


## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Redis Server
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/prath0m/Todo-App-Zeidler-Group-Assignment.git
cd Todo-App-Zeidler-Group-Assignment
```

### 2. Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)

Change a `setting.py` file in the project root if you want to use your own email credentials:

```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Note:** The project already includes SMTP credentials configured for demonstration purposes. You can use the existing setup to run the project immediately without configuring your own email.

### 5. Database Setup

Run migrations to create database tables:

```bash
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Install and Start Redis

Redis is required for Celery to work.

**macOS:**
```bash
# Install Redis using Homebrew
brew install redis

# Start Redis service
brew services start redis

# Or run Redis manually
redis-server
```

**Windows:**
```bash
# Download Redis from: https://github.com/microsoftarchive/redis/releases
# Or use WSL (Windows Subsystem for Linux)

# Using WSL:
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start

# Or download Redis for Windows:
# https://github.com/tporadowski/redis/releases
# Run redis-server.exe
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### 8. Start Celery Worker

Open a **new terminal window**, activate your virtual environment, and run:

**macOS/Linux:**
```bash
source .venv/bin/activate
celery -A todo worker --loglevel=info
```

**Windows:**
```bash
.venv\Scripts\activate
celery -A todo worker --loglevel=info --pool=solo
```

### 9. Start Celery Beat (Scheduler)

Open **another terminal window**, activate your virtual environment, and run:

**macOS/Linux:**
```bash
source .venv/bin/activate
celery -A todo beat --loglevel=info
```

**Windows:**
```bash
.venv\Scripts\activate
celery -A todo beat --loglevel=info
```

### 10. Run Django Development Server

In your **original terminal** (or a new one):

**macOS/Linux:**
```bash
source .venv/bin/activate
python manage.py runserver
```

**Windows:**
```bash
.venv\Scripts\activate
python manage.py runserver
```

### 11. Access the Application

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

## Developer

**Prathamesh Kale**
- GitHub: [@prath0m](https://github.com/prath0m)
- Email: prath0mkale@gmail.com