from django.urls import path
from . import views  # Import views from the current app
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('conversation/', views.chat, name='chat'),
    path('accounts/login', views.login_view, name='login_view'),
    path('logout/', LogoutView.as_view(next_page='login_view'), name='logout'),
    path('accounts/signup', views.signup, name='signup'),
    path('conversation/bot/', views.api_chat, name='api_chat'),
    path('signin/', views.signin, name='signin'),
    path('submit/', views.submit, name='submit'),
    path('attachments/', views.attachments, name='attachments'),
    path('upload/', views.file_upload, name='file_upload'),
    path('attachment_webhook', views.attachment_webhook, name='attachment_webhook')
]