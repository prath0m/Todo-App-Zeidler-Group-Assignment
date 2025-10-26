import random
import string
from django.core.mail import send_mail
from django.conf import settings
from .models import UserOTP
from datetime import datetime, timedelta

def generate_otp():
    """Generate a random 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP to user's email via SMTP"""
    subject = 'Your Todo App Verification Code'
    message = f"""
    Hello,

    Your OTP for registering with Todo App is: {otp}

    This OTP will expire in 10 minutes.

    If you didn't request this, please ignore this email.

    Best regards,
    Todo App Team
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
    """Create OTP and send to email"""
    otp = generate_otp()
    
    # Delete any existing OTP for this email
    UserOTP.objects.filter(email=email).delete()
    
    # Create new OTP
    user_otp = UserOTP.objects.create(email=email, otp=otp)
    
    # Send OTP via email
    if send_otp_email(email, otp):
        return True
    else:
        user_otp.delete()
        return False

def verify_user_otp(email, otp):
    """Verify OTP for given email"""
    try:
        user_otp = UserOTP.objects.get(email=email, otp=otp)
        
        # Check if OTP has expired (10 minutes)
        expiry_time = user_otp.created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        if datetime.now() > expiry_time.replace(tzinfo=None):
            user_otp.delete()
            return False, "OTP has expired"
        
        user_otp.is_verified = True
        user_otp.save()
        return True, "OTP verified successfully"
    except UserOTP.DoesNotExist:
        return False, "Invalid OTP"

def delete_otp(email):
    """Delete OTP for given email after successful verification"""
    UserOTP.objects.filter(email=email).delete()
