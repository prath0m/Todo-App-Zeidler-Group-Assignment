# Celery Task Reminder Setup

## Overview
This Todo app now includes automated email reminders sent 30 minutes before task due times using Celery and Redis.

## Components

### 1. **Celery Configuration** (`todo/celery.py`)
- Celery app configured to use Redis as message broker
- Auto-discovers tasks from all Django apps
- Integrated with Django settings

### 2. **Task Reminders** (`core/tasks.py`)
- `send_task_reminder(task_id)`: Sends email 30 minutes before due time
- Checks if task is completed before sending
- Formats email with task details (title, description, due date/time, priority)

### 3. **Reminder Utilities** (`core/reminder_utils.py`)
- `schedule_task_reminder(task)`: Schedules a reminder email for a task
- `cancel_task_reminder(task)`: Cancels a scheduled reminder
- `reschedule_task_reminder(task)`: Cancels old reminder and schedules new one

### 4. **Model Updates** (`core/models.py`)
- Added `reminder_task_id` field to Todo model to store Celery task IDs
- Enables tracking and cancellation of scheduled reminders

### 5. **View Integration** (`core/views.py`)
- **create_task**: Schedules reminder when task with due_date and due_time is created
- **toggle_task**: Cancels reminder when task is completed, reschedules when uncompleted
- **update_task**: Reschedules reminder when due_date or due_time changes
- **delete_task**: Cancels reminder before deleting task

## Installation Steps

### 1. Install Required Packages
```bash
cd /Users/prathameshkale/Documents/Todo\ App
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Install and Start Redis Server
**Using Homebrew (macOS):**
```bash
brew install redis
brew services start redis
```

**Or using Docker:**
```bash
docker run -d -p 6379:6379 redis:latest
```

**To verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### 4. Start Celery Worker
In a separate terminal window:
```bash
cd /Users/prathameshkale/Documents/Todo\ App
source .venv/bin/activate
celery -A todo worker --loglevel=info
```

### 5. Start Celery Beat (Optional - for periodic tasks)
If you need periodic task scheduling in the future:
```bash
celery -A todo beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## How It Works

1. **Task Creation**: When you create a task with a due date and time:
   - System calculates reminder time (due_time - 30 minutes)
   - Schedules Celery task with `apply_async(eta=reminder_time)`
   - Stores task ID in database

2. **Task Completion**: When you mark a task as complete:
   - System cancels the scheduled reminder
   - No email will be sent

3. **Task Update**: When you change due date or time:
   - System cancels old reminder
   - Schedules new reminder with updated time

4. **Task Deletion**: When you delete a task:
   - System cancels the scheduled reminder before deletion

5. **Email Delivery**: At reminder time (30 min before due time):
   - Celery worker picks up the scheduled task
   - Checks if task is still pending (not completed)
   - Sends formatted email with task details
   - Email sent from: prathamkale88401@gmail.com

## Testing

### Test Reminder Scheduling
1. Create a task with due_date and due_time set to 35 minutes from now
2. Check Celery worker logs - should show scheduled task
3. Wait 5 minutes
4. Check email - should receive reminder with task details

### Monitor Celery Tasks
```bash
# In Python shell
python manage.py shell
```

```python
from celery import current_app
from core.models import Todo

# Check scheduled tasks
i = current_app.control.inspect()
scheduled = i.scheduled()
print(scheduled)

# Check active tasks
active = i.active()
print(active)
```

## Troubleshooting

### Redis Connection Issues
- Verify Redis is running: `redis-cli ping`
- Check connection: `redis-cli -h localhost -p 6379`
- Restart Redis: `brew services restart redis`

### Celery Worker Issues
- Check worker is running and connected to Redis
- Look for errors in worker terminal
- Restart worker: Ctrl+C then restart command

### Email Not Sending
- Verify SMTP settings in `todo/settings.py`
- Check spam/junk folder
- Verify task wasn't completed before reminder time
- Check Celery worker logs for errors

### Task Not Scheduled
- Verify due_date AND due_time are both set
- Check that reminder_task_id is saved in database
- Ensure Celery worker is running when task is created

## Development Notes

- Reminders are only scheduled for tasks with BOTH due_date and due_time
- Reminder time is fixed at 30 minutes before due time
- If due time is less than 30 minutes away, reminder will be scheduled immediately or might be in the past (won't send)
- Completed tasks will not receive reminders even if scheduled
- All times use Django's TIME_ZONE setting (UTC)

## Future Enhancements

- [ ] Configurable reminder time (5, 15, 30, 60 minutes)
- [ ] Multiple reminders per task
- [ ] Push notifications in addition to email
- [ ] Recurring task support
- [ ] SMS reminders via Twilio
