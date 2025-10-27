from datetime import datetime, timedelta
from django.utils import timezone
from celery import current_app


def schedule_task_reminder(task):

    if not task.due_date or not task.due_time or task.completed:
        print(f"Task {task.id}: Cannot schedule - due_date={task.due_date}, due_time={task.due_time}, completed={task.completed}")
        return None
    
    try:
        current_tz = timezone.get_current_timezone()
        naive_datetime = datetime.combine(task.due_date, task.due_time)
        due_datetime = timezone.make_aware(naive_datetime, current_tz)
        
        reminder_time = due_datetime - timedelta(minutes=30)

        now = timezone.now()
        
        print(f"Task {task.id} '{task.title}':")
        print(f"  Current time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"  Due datetime: {due_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"  Reminder time: {reminder_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        if reminder_time <= now:
            time_diff = now - reminder_time
            minutes_ago = int(time_diff.total_seconds() / 60)
            print(f"Reminder time was {minutes_ago} minutes ago. Not scheduling.")
            return None
        
        from .tasks import send_task_reminder        
        result = send_task_reminder.apply_async(
            args=[task.id],
            eta=reminder_time
        )
        
        time_diff = reminder_time - now
        minutes_until = int(time_diff.total_seconds() / 60)
        print(f"Scheduled! Reminder will be sent in {minutes_until} minutes")
        print(f"Celery Task ID: {result.id}")
        return result.id
        
    except Exception as e:
        print(f"Error scheduling reminder for task {task.id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def cancel_task_reminder(task):
    if not task.reminder_task_id:
        return False
    
    try:
        current_app.control.revoke(task.reminder_task_id, terminate=True)
        print(f"Cancelled reminder for task {task.id}")
        return True
    except Exception as e:
        print(f"Error cancelling reminder for task {task.id}: {str(e)}")
        return False


def reschedule_task_reminder(task):
    if task.reminder_task_id:
        cancel_task_reminder(task)
        task.reminder_task_id = None

    new_task_id = schedule_task_reminder(task)
    if new_task_id:
        task.reminder_task_id = new_task_id
        task.save(update_fields=['reminder_task_id'])
        return True
    
    return False
