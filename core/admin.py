from django.contrib import admin
from .models import UserOTP, PasswordReset, TaskList, Workspace, Todo

@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'completed', 'priority', 'due_date', 'due_time', 'created_at')
    list_filter = ('status', 'completed', 'priority', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'user__username', 'user__email')
    list_editable = ('status', 'completed', 'priority')
    ordering = ('-created_at',)

@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'user__username')

@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'user__username')

@admin.register(UserOTP)
class UserOTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'otp', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('email',)

@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ('email', 'otp', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('email',)
