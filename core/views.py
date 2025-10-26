from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import UserOTP, PasswordReset
from .utils import create_and_send_otp, verify_user_otp, delete_otp
import json

@login_required(login_url='login')
def home(request):
    return render(request, 'core/index.html')

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


