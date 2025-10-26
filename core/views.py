from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import UserOTP, PasswordReset, Todo, TaskList, Workspace
from .utils import create_and_send_otp, verify_user_otp, delete_otp
import json
from datetime import datetime

@login_required(login_url='login')
def home(request):
    # Get today's date
    from datetime import date
    today = date.today()
    
    # Get all tasks for the user (excluding completed)
    all_tasks = Todo.objects.filter(user=request.user, completed=False)
    
    # Get today's tasks count
    today_tasks_count = Todo.objects.filter(user=request.user, due_date=today, completed=False).count()
    
    # Get completed tasks
    completed_tasks = Todo.objects.filter(user=request.user, completed=True)
    
    # Get task lists
    task_lists = TaskList.objects.filter(user=request.user)
    
    # Get workspaces
    workspaces = Workspace.objects.filter(user=request.user)
    
    context = {
        'all_tasks': all_tasks,
        'completed_tasks': completed_tasks,
        'task_lists': task_lists,
        'workspaces': workspaces,
        'today_tasks_count': today_tasks_count,
        'completed_tasks_count': completed_tasks.count(),
        'all_tasks_count': all_tasks.count(),
    }
    
    return render(request, 'core/home.html', context)


@login_required(login_url='login')
def today_tasks(request):
    # Get today's date
    from datetime import date
    today = date.today()
    
    # Get all tasks for the user
    all_tasks = Todo.objects.filter(user=request.user)
    
    # Get today's tasks (tasks with due_date = today, both completed and incomplete)
    today_tasks = all_tasks.filter(due_date=today).order_by('completed', '-priority', 'created_at')
    
    # Get completed tasks count
    completed_tasks = all_tasks.filter(completed=True)
    
    # Get task lists
    task_lists = TaskList.objects.filter(user=request.user)
    
    # Get workspaces
    workspaces = Workspace.objects.filter(user=request.user)
    
    # Count only incomplete today tasks for the sidebar
    today_tasks_incomplete_count = all_tasks.filter(due_date=today, completed=False).count()
    
    context = {
        'today_tasks': today_tasks,
        'completed_tasks': completed_tasks,
        'all_tasks': all_tasks,
        'task_lists': task_lists,
        'workspaces': workspaces,
        'today_tasks_count': today_tasks_incomplete_count,
        'completed_tasks_count': completed_tasks.count(),
        'all_tasks_count': all_tasks.filter(completed=False).count(),
        'today_date': today,
    }
    
    return render(request, 'core/today.html', context)

def login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Try to get user by email
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'core/login.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Validation
        if not full_name or not email or not password or not password_confirm:
            messages.error(request, 'All fields are required')
            return render(request, 'core/register.html')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'core/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'core/register.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')
            return render(request, 'core/register.html')
        
        # Store registration data in session
        request.session['temp_full_name'] = full_name
        request.session['temp_email'] = email
        request.session['temp_password'] = password
        
        # Send OTP to email
        if create_and_send_otp(email):
            messages.success(request, 'OTP sent to your email')
            return redirect('verify_otp')
        else:
            messages.error(request, 'Failed to send OTP. Please try again.')
            return render(request, 'core/register.html')
    
    return render(request, 'core/register.html')

def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    email = request.session.get('temp_email')
    if not email:
        messages.error(request, 'Please complete registration first')
        return redirect('register')
    
    if request.method == 'POST':
        otp = request.POST.get('otp')
        
        if not otp:
            messages.error(request, 'Please enter OTP')
            return render(request, 'core/verify_otp.html', {'email': email})
        
        # Verify OTP
        is_valid, message_text = verify_user_otp(email, otp)
        
        if is_valid:
            # Create user account
            full_name = request.session.get('temp_full_name')
            password = request.session.get('temp_password')
            
            # Generate username from email
            username = email.split('@')[0]
            original_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            # Split full name
            first_name = full_name.split()[0] if full_name else ''
            last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Delete OTP
            delete_otp(email)
            
            # Clear session
            del request.session['temp_full_name']
            del request.session['temp_email']
            del request.session['temp_password']
            
            # Login user
            auth_login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
        else:
            messages.error(request, f'Invalid OTP: {message_text}')
            return render(request, 'core/verify_otp.html', {'email': email})
    
    return render(request, 'core/verify_otp.html', {'email': email})

def resend_otp(request):
    """AJAX endpoint to resend OTP"""
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'})
        
        if create_and_send_otp(email):
            return JsonResponse({'success': True, 'message': 'OTP sent successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Failed to send OTP'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def logout(request):
    auth_logout(request)
    return redirect('login')

def forgot_password(request):
    """Display forgot password form"""
    if request.user.is_authenticated:
        return redirect('home')
    
    return render(request, 'core/forgot_password.html')

def send_reset_otp(request):
    """Send OTP for password reset"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            
            if not email:
                return JsonResponse({'success': False, 'message': 'Email is required'})
            
            # Check if email exists
            if not User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email not found'})
            
            # Delete old password reset records
            PasswordReset.objects.filter(email=email).delete()
            
            # Send OTP to email (this creates UserOTP and sends email)
            if create_and_send_otp(email):
                # Get the OTP that was just created in UserOTP
                user_otp = UserOTP.objects.get(email=email)
                # Create password reset record with the same OTP
                PasswordReset.objects.create(email=email, otp=user_otp.otp)
                
                return JsonResponse({'success': True, 'message': 'OTP sent to your email'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to send OTP'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

def verify_reset_otp(request):
    """Verify OTP for password reset"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            otp = data.get('otp', '').strip()
            
            if not email or not otp:
                return JsonResponse({'success': False, 'message': 'Email and OTP are required'})
            
            # Check if OTP matches
            reset_record = PasswordReset.objects.filter(email=email, otp=otp).first()
            
            if reset_record:
                reset_record.is_verified = True
                reset_record.save()
                return JsonResponse({'success': True, 'message': 'OTP verified successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid OTP'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

def reset_password(request):
    """Reset password"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            new_password = data.get('new_password', '').strip()
            
            if not email or not new_password:
                return JsonResponse({'success': False, 'message': 'Email and password are required'})
            
            # Check if OTP is verified
            reset_record = PasswordReset.objects.filter(email=email, is_verified=True).first()
            
            if not reset_record:
                return JsonResponse({'success': False, 'message': 'Please verify OTP first'})
            
            # Validate password
            if len(new_password) < 6:
                return JsonResponse({'success': False, 'message': 'Password must be at least 6 characters long'})
            
            if not any(c.isupper() for c in new_password):
                return JsonResponse({'success': False, 'message': 'Password must contain at least one uppercase letter'})
            
            if not any(c.isdigit() for c in new_password):
                return JsonResponse({'success': False, 'message': 'Password must contain at least one number'})
            
            # Update user password
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            # Delete password reset record
            reset_record.delete()
            
            return JsonResponse({'success': True, 'message': 'Password updated successfully'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

def resend_reset_otp(request):
    """Resend OTP for password reset"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            
            if not email:
                return JsonResponse({'success': False, 'message': 'Email is required'})
            
            # Delete old password reset OTPs
            PasswordReset.objects.filter(email=email).delete()
            
            # Send OTP to email
            if create_and_send_otp(email):
                # Create password reset record
                import random
                otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                PasswordReset.objects.create(email=email, otp=otp)
                
                return JsonResponse({'success': True, 'message': 'OTP sent successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to send OTP'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


# API Views for Tasks
@login_required
@require_http_methods(["GET"])
def get_task_lists(request):
    """Get all task lists for the current user"""
    task_lists = TaskList.objects.filter(user=request.user)
    data = [{
        'id': tl.id,
        'name': tl.name,
        'list_type': tl.list_type,
        'icon': tl.icon,
        'color': tl.color
    } for tl in task_lists]
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["GET"])
def get_workspaces(request):
    """Get all workspaces for the current user"""
    workspaces = Workspace.objects.filter(user=request.user)
    data = [{
        'id': ws.id,
        'name': ws.name,
        'color': ws.color
    } for ws in workspaces]
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["POST"])
def create_task_list(request):
    """Create a new task list"""
    try:
        name = request.POST.get('name', '').strip()
        icon = request.POST.get('icon', '📋').strip()
        color = request.POST.get('color', '#667eea').strip()
        
        if not name:
            return JsonResponse({'success': False, 'message': 'List name is required'})
        
        task_list = TaskList.objects.create(
            user=request.user,
            name=name,
            icon=icon,
            color=color,
            list_type='custom'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Task list created successfully',
            'task_list': {
                'id': task_list.id,
                'name': task_list.name,
                'icon': task_list.icon,
                'color': task_list.color
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def create_workspace(request):
    """Create a new workspace"""
    try:
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '#667eea').strip()
        
        if not name:
            return JsonResponse({'success': False, 'message': 'Workspace name is required'})
        
        workspace = Workspace.objects.create(
            user=request.user,
            name=name,
            color=color
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Workspace created successfully',
            'workspace': {
                'id': workspace.id,
                'name': workspace.name,
                'color': workspace.color
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def delete_task_list(request, list_id):
    """Delete a task list"""
    try:
        task_list = TaskList.objects.get(id=list_id, user=request.user)
        task_list.delete()
        return JsonResponse({'success': True, 'message': 'Task list deleted successfully'})
    except TaskList.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Task list not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def delete_workspace(request, workspace_id):
    """Delete a workspace"""
    try:
        workspace = Workspace.objects.get(id=workspace_id, user=request.user)
        workspace.delete()
        return JsonResponse({'success': True, 'message': 'Workspace deleted successfully'})
    except Workspace.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Workspace not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def create_task(request):
    """Create a new task"""
    try:
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        due_date = request.POST.get('due_date', '').strip()
        due_time = request.POST.get('due_time', '').strip()
        priority = request.POST.get('priority', '0')
        status = request.POST.get('status', 'pending').strip()
        task_list_id = request.POST.get('task_list', '').strip()
        workspace_id = request.POST.get('workspace', '').strip()
        color = request.POST.get('color', '#667eea')
        
        # Validate required fields
        if not title:
            return JsonResponse({'success': False, 'message': 'Title is required'})
        
        # Create task
        task_data = {
            'user': request.user,
            'title': title,
            'description': description if description else None,
            'color': color,
            'priority': int(priority) if priority else 0,
            'status': status if status in ['pending', 'completed'] else 'pending',
        }
        
        # Add due date if provided
        if due_date:
            try:
                task_data['due_date'] = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Add due time if provided
        if due_time:
            try:
                task_data['due_time'] = datetime.strptime(due_time, '%H:%M').time()
            except ValueError:
                pass
        
        # Add task list if provided
        if task_list_id:
            try:
                task_list = TaskList.objects.get(id=int(task_list_id), user=request.user)
                task_data['task_list'] = task_list
            except (TaskList.DoesNotExist, ValueError):
                pass
        
        # Add workspace if provided
        if workspace_id:
            try:
                workspace = Workspace.objects.get(id=int(workspace_id), user=request.user)
                task_data['workspace'] = workspace
            except (Workspace.DoesNotExist, ValueError):
                pass
        
        # Create the task
        task = Todo.objects.create(**task_data)
        
        return JsonResponse({
            'success': True,
            'message': 'Task created successfully',
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'completed': task.completed,
                'color': task.color,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'due_time': task.due_time.isoformat() if task.due_time else None,
                'priority': task.priority
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def toggle_task(request, task_id):
    """Toggle task completion status"""
    try:
        task = Todo.objects.get(id=task_id, user=request.user)
        task.completed = not task.completed
        # Update status based on completed field
        task.status = 'completed' if task.completed else 'pending'
        task.save()
        
        return JsonResponse({
            'success': True,
            'completed': task.completed,
            'status': task.status,
            'message': 'Task updated successfully'
        })
    except Todo.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def update_task(request, task_id):
    """Update an existing task"""
    try:
        task = Todo.objects.get(id=task_id, user=request.user)
        
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        due_date = request.POST.get('due_date', '').strip()
        due_time = request.POST.get('due_time', '').strip()
        priority = request.POST.get('priority', '0')
        status = request.POST.get('status', '').strip()
        task_list_id = request.POST.get('task_list', '').strip()
        workspace_id = request.POST.get('workspace', '').strip()
        color = request.POST.get('color', '#667eea')
        
        # Update fields
        if title:
            task.title = title
        
        task.description = description if description else None
        task.color = color
        task.priority = int(priority) if priority else 0
        
        # Update status
        if status and status in ['pending', 'completed']:
            task.status = status
            # Sync completed field with status
            task.completed = (status == 'completed')
        
        # Update due date
        if due_date:
            try:
                task.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                task.due_date = None
        else:
            task.due_date = None
        
        # Update due time
        if due_time:
            try:
                task.due_time = datetime.strptime(due_time, '%H:%M').time()
            except ValueError:
                task.due_time = None
        else:
            task.due_time = None
        
        # Update task list
        if task_list_id:
            try:
                task_list = TaskList.objects.get(id=int(task_list_id), user=request.user)
                task.task_list = task_list
            except (TaskList.DoesNotExist, ValueError):
                task.task_list = None
        else:
            task.task_list = None
        
        # Update workspace
        if workspace_id:
            try:
                workspace = Workspace.objects.get(id=int(workspace_id), user=request.user)
                task.workspace = workspace
            except (Workspace.DoesNotExist, ValueError):
                task.workspace = None
        else:
            task.workspace = None
        
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Task updated successfully',
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'completed': task.completed,
                'color': task.color,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'due_time': task.due_time.isoformat() if task.due_time else None,
                'priority': task.priority
            }
        })
        
    except Todo.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
def get_task(request, task_id):
    """Get task details for editing"""
    try:
        task = Todo.objects.get(id=task_id, user=request.user)
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description or '',
                'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
                'due_time': task.due_time.strftime('%H:%M') if task.due_time else '',
                'priority': task.priority,
                'color': task.color or '#667eea',
                'status': task.status,
                'completed': task.completed,
                'task_list': task.task_list.id if task.task_list else '',
                'workspace': task.workspace.id if task.workspace else '',
            }
        })
    except Todo.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def delete_task(request, task_id):
    """Delete a task"""
    try:
        task = Todo.objects.get(id=task_id, user=request.user)
        task.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Task deleted successfully'
        })
    except Todo.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
def completed_tasks(request):
    """View for completed tasks page"""
    from datetime import date
    today = date.today()
    
    # Get all tasks for the user
    all_tasks = Todo.objects.filter(user=request.user)
    
    # Get completed tasks
    completed = all_tasks.filter(completed=True)
    
    # Get today's tasks count
    today_tasks = all_tasks.filter(due_date=today)
    
    # Get task lists
    task_lists = TaskList.objects.filter(user=request.user)
    
    # Get workspaces
    workspaces = Workspace.objects.filter(user=request.user)
    
    context = {
        'completed_tasks': completed,
        'today_tasks_count': today_tasks.count(),
        'completed_tasks_count': completed.count(),
        'all_tasks_count': all_tasks.count(),
        'task_lists': task_lists,
        'workspaces': workspaces,
    }
    
    return render(request, 'core/completed.html', context)


@login_required
def task_list_view(request, list_id):
    """View for a specific task list"""
    from datetime import date
    today = date.today()
    
    try:
        task_list = TaskList.objects.get(id=list_id, user=request.user)
    except TaskList.DoesNotExist:
        messages.error(request, 'Task list not found')
        return redirect('home')
    
    # Get all tasks in this list
    list_tasks = Todo.objects.filter(user=request.user, task_list=task_list)
    
    # Get task lists
    task_lists = TaskList.objects.filter(user=request.user)
    
    # Get workspaces
    workspaces = Workspace.objects.filter(user=request.user)
    
    # Get today's tasks count
    today_tasks_count = Todo.objects.filter(user=request.user, due_date=today, completed=False).count()
    
    # Get completed tasks count
    completed_tasks_count = Todo.objects.filter(user=request.user, completed=True).count()
    
    # Get all tasks count
    all_tasks_count = Todo.objects.filter(user=request.user, completed=False).count()
    
    context = {
        'task_list': task_list,
        'list_tasks': list_tasks,
        'task_lists': task_lists,
        'workspaces': workspaces,
        'today_tasks_count': today_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'all_tasks_count': all_tasks_count,
    }
    
    return render(request, 'core/task_list.html', context)


@login_required
def workspace_view(request, workspace_id):
    """View for a specific workspace"""
    from datetime import date
    today = date.today()
    
    try:
        workspace = Workspace.objects.get(id=workspace_id, user=request.user)
    except Workspace.DoesNotExist:
        messages.error(request, 'Workspace not found')
        return redirect('home')
    
    # Get all tasks in this workspace
    workspace_tasks = Todo.objects.filter(user=request.user, workspace=workspace)
    
    # Get task lists
    task_lists = TaskList.objects.filter(user=request.user)
    
    # Get workspaces
    workspaces = Workspace.objects.filter(user=request.user)
    
    # Get today's tasks count
    today_tasks_count = Todo.objects.filter(user=request.user, due_date=today, completed=False).count()
    
    # Get completed tasks count
    completed_tasks_count = Todo.objects.filter(user=request.user, completed=True).count()
    
    # Get all tasks count
    all_tasks_count = Todo.objects.filter(user=request.user, completed=False).count()
    
    context = {
        'workspace': workspace,
        'workspace_tasks': workspace_tasks,
        'task_lists': task_lists,
        'workspaces': workspaces,
        'today_tasks_count': today_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'all_tasks_count': all_tasks_count,
    }
    
    return render(request, 'core/workspace.html', context)
