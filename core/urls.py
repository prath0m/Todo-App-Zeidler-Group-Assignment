from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('today/', views.today_tasks, name='today_tasks'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('send-reset-otp/', views.send_reset_otp, name='send_reset_otp'),
    path('verify-reset-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('resend-reset-otp/', views.resend_reset_otp, name='resend_reset_otp'),
    path('logout/', views.logout, name='logout'),

    path('completed/', views.completed_tasks, name='completed_tasks'),
    path('list/<int:list_id>/', views.task_list_view, name='task_list_view'),
    path('workspace/<int:workspace_id>/', views.workspace_view, name='workspace_view'),
    
    path('api/task-lists/', views.get_task_lists, name='get_task_lists'),
    path('api/task-lists/create/', views.create_task_list, name='create_task_list'),
    path('api/task-lists/<int:list_id>/delete/', views.delete_task_list, name='delete_task_list'),
    path('api/workspaces/', views.get_workspaces, name='get_workspaces'),
    path('api/workspaces/create/', views.create_workspace, name='create_workspace'),
    path('api/workspaces/<int:workspace_id>/delete/', views.delete_workspace, name='delete_workspace'),
    path('api/tasks/create/', views.create_task, name='create_task'),
    path('api/tasks/<int:task_id>/get/', views.get_task, name='get_task'),
    path('api/tasks/<int:task_id>/toggle/', views.toggle_task, name='toggle_task'),
    path('api/tasks/<int:task_id>/update/', views.update_task, name='update_task'),
    path('api/tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
]