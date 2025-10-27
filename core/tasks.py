from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Todo


@shared_task(name='send_task_reminder')
def send_task_reminder(task_id):
    print(f"\n{'='*60}")
    print(f"REMINDER EMAIL TASK EXECUTING - Task ID: {task_id}")
    print(f"{'='*60}")
    
    try:
        task = Todo.objects.get(id=task_id)
        print(f"Task found: '{task.title}'")
        print(f"User: {task.user.email}")
        
        if task.completed:
            print(f"Task {task_id} is already completed. Skipping reminder.")
            return f"Task {task_id} already completed"
        
        if not task.due_date or not task.due_time:
            print(f"Task {task_id} has no due date/time. Skipping reminder.")
            return f"Task {task_id} has no due date/time"
        
        now = timezone.now()
        current_tz = timezone.get_current_timezone()
        naive_datetime = datetime.combine(task.due_date, task.due_time)
        due_datetime = timezone.make_aware(naive_datetime, current_tz)
        
        print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Due datetime: {due_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        if due_datetime <= now:
            print(f"Task {task_id} due date/time has already passed. Skipping reminder.")
            return f"Task {task_id} due date/time has passed"
        
        today = now.date()
        if task.due_date < today:
            print(f"Task {task_id} due date ({task.due_date}) is in the past. Skipping reminder.")
            return f"Task {task_id} due date is in the past"
        
        print(f"All validation checks passed. Sending email...")
        
        # Prepare email content
        subject = f"Todo AppReminder: {task.title}"
        
        # Build task details
        task_details = f"""
            Hi {task.user.first_name or task.user.username},

            This is a friendly reminder about your upcoming task:

            Task: {task.title}
            """
        
        if task.description:
            task_details += f"Description: {task.description}\n"
        
        if task.due_date:
            task_details += f"Due Date: {task.due_date.strftime('%B %d, %Y')}\n"
        
        if task.due_time:
            task_details += f"Due Time: {task.due_time.strftime('%I:%M %p')}\n"
        
        if task.priority > 0:
            priority_map = {1: 'Medium', 2: 'High', 3: 'Urgent'}
            task_details += f"Priority: {priority_map.get(task.priority, 'Low')}\n"
        
        task_details += """
            Don't forget to complete this task on time!

            Thank you
            """
        message = task_details
        print(f"Sending email to: {task.user.email}")
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [task.user.email],
            fail_silently=False,
        )
        
        print(f"SUCCESS! Reminder email sent for task {task_id}: {task.title}")
        print(f"{'='*60}\n")
        return f"Reminder sent for task {task_id}"
        
    except Todo.DoesNotExist:
        print(f"ERROR: Task {task_id} does not exist")
        print(f"{'='*60}\n")
        return f"Task {task_id} not found"
    except Exception as e:
        print(f"ERROR sending reminder for task {task_id}: {str(e)}")
        print(f"{'='*60}\n")
        return f"Error: {str(e)}"


@shared_task(name='cancel_task_reminder')
def cancel_task_reminder(task_id):
    print(f"Cancellation requested for task {task_id}")
    return f"Cancellation processed for task {task_id}"
