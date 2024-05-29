from django.urls import path
from . import views  # Import views from the current app

urlpatterns = [
    path('', views.chat, name='chat'),
    path('bot/', views.api_chat, name='api_chat'),
    path('signin/', views.signin, name='signin'),
    path('submit/', views.submit, name='submit'),
    path('attachments/', views.attachments, name='attachments'),
    path('upload/', views.file_upload, name='file_upload'),
    path('attachment_webhook/', views.attachment_webhook, name='attachment_webhook')
]