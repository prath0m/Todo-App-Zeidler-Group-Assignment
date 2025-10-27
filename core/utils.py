import random
import string
from django.core.mail import send_mail
from django.conf import settings
from .models import UserOTP
from datetime import datetime, timedelta

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    subject = 'Todo App Verification Code'
    message = f"""
    Hello,

    Your OTP for registering with Todo App is: {otp}

    Thank You
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def create_and_send_otp(email):
    otp = generate_otp()
    UserOTP.objects.filter(email=email).delete()
    
    user_otp = UserOTP.objects.create(email=email, otp=otp)
    
    if send_otp_email(email, otp):
        return True
    else:
        user_otp.delete()
        return False

def verify_user_otp(email, otp):
    try:
        user_otp = UserOTP.objects.get(email=email, otp=otp)
        
        from django.utils import timezone
        expiry_time = user_otp.created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        now = timezone.now()
        
        if now > expiry_time:
            user_otp.delete()
            return False, "OTP has expired"
        
        user_otp.is_verified = True
        user_otp.save()
        return True, "OTP verified successfully"
    except UserOTP.DoesNotExist:
        return False, "Invalid OTP"

def delete_otp(email):
    UserOTP.objects.filter(email=email).delete()
