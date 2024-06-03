from django.shortcuts import redirect, render
from django.http import JsonResponse
import requests
import base64
import httpx
from asgiref.sync import sync_to_async
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from chatbot.models import AttachmentStatus
from django.contrib.auth import login,authenticate
from .forms import SignUpForm 
from django.contrib.auth.forms import AuthenticationForm
import json
from django.db import connection
from .models import Message
from django.db import close_old_connections
import aiohttp
import asyncio

# Create your views here.

@require_http_methods(["POST"])
@csrf_exempt
def set_language(request):
    data = json.loads(request.body)
    language = data.get('language', 'en')  # Default to English if not specified
    request.session['language'] = language
    return JsonResponse({'status': 'success', 'message': f'Language set to {language}'})

def update_file_status(status):
    try:
        user = User.objects.get(id=1)

        # If the user was created, set a default password and other necessary fields
        if user:
            # Update or create the attachment status associated with the user
            AttachmentStatus.objects.update_or_create(user=user, defaults={'status': status})
    finally:
        connection.close()        

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST) 
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('chat') 
    else:
        form = SignUpForm()
    return render(request, 'chatbot/signup.html', {'form': form})

def login_view(request):
    request.session["attachment_status"] = 'logged_in'
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()  # Retrieve the user object
            login(request, user)  # Perform the login operation
            username = user.username  # Access the username from the user objec
            request.session["username"] = username
            request.session["id"] = retrieve_user_id(username)
            print(request.session["id"])
            return redirect('chat')  # Redirect to a home page or other
    else:
        form = AuthenticationForm()
    return render(request, 'chatbot/login.html', {'form': form})      

def retrieve_user_id(username):
    url = f'https://kong.zenith-dev-gateway.com/core-be/api/rag/chats?userName={username}'

    response = requests.post(url)
    if response.status_code == 201:
        return response.json()["id"]
    else:
        return response.status_code

@require_http_methods(["POST"])
def start_new_chat(request):
    user_id = retrieve_user_id(request.session.get("username"))
    request.session["id"] = user_id
    request.session["attachment_status"] = 'logged_in'
    return JsonResponse({'status': 'success', 'message': 'Chat restarted with new user ID.'})

async def post_question(message, chat_id, language):
    url = f'https://kong.zenith-dev-gateway.com/core-be/api/rag/chats/{chat_id}/questions'
    payload = {
        'question': message,
        'language': language
    }
    print("post question payload", payload)
    print("post question url", url)
    async with httpx.AsyncClient() as client:
        response = requests.post(url, json=payload)
        print("api-response",response)
        if response.status_code == 201:
            return response.json()
        else:
            return response.status_code
        
def get_chat_history(request):
    session_id = request.session.session_key
    try:
        user_messages = Message.objects.filter(session_id=session_id).order_by('created_at')
    finally:
        connection.close()    
    history = [{'text': msg.text, 'is_bot': msg.is_bot} for msg in user_messages]
    print(history)
    return JsonResponse(history, safe=False)     

async def api_chat(request):
    user_input = request.GET.get('message')
    if user_input:
        session_id = await sync_to_async(request.session.__getitem__)("id")
        language = await sync_to_async(request.session.__getitem__)("language")
        print("async language", language)
        print(session_id)

        session__id = request.session.session_key  # Ensure the session key is available
        if not session__id:
            await sync_to_async(request.session.save)()
            session__id = request.session.session_key
       
        # Log the user's message
        try:
            await sync_to_async(Message.objects.create)(text=user_input, is_bot=False, session_id=session__id)
        finally:
            await sync_to_async(close_old_connections)()

        answer = await post_question(user_input, session_id, language)
        print("API ANSWER :::::::: ", answer)
        bot_response = answer["answer"]

        # Log the bot's response
        try:
            await sync_to_async(Message.objects.create)(text=bot_response, is_bot=True, session_id=session__id)
        finally:
            await sync_to_async(close_old_connections)()

    return JsonResponse({'message': str(bot_response)})



# @login_required(login_url='signin/')
def chat(request):
    if request.session["attachment_status"] == 'processed':
        return render(request, 'chatbot/chat.html')
    elif request.session["attachment_status"] == 'logged_in':
        return render(request, 'chatbot/nofile.html')
    elif request.session["attachment_status"] == 'processing':
        return render(request, 'chatbot/processing.html')
    

def home(request):
    render(request, 'chatbot/signin.html')
    return redirect('login_view')

@csrf_exempt
@require_http_methods(["POST"])
def attachment_webhook(request):
    file_status = request.GET.get('file', None)  # Assuming file status comes in POST data
    user_id = 1  # Hard-coded user ID

    if user_id is None:
        return HttpResponse("User ID is required", status=400)

    # Attempt to fetch the user with the given ID, or create a new one if not found
    try:
        user, created = User.objects.get_or_create(id=user_id, defaults={
            'username': f'user_{user_id}',
            'email': f'user_{user_id}@example.com'
        })
    finally:
        connection.close()
    # If the user was created, set a default password and other necessary fields
    if created:
        user.set_password("defaultpassword")  # Set a default or generated password
        user.save()
        login(request, user)

    # Update or create the attachment status associated with the user
    try:
        AttachmentStatus.objects.update_or_create(user=user, defaults={'status': 'processed' if file_status == 'processed' else 'processing'})
    finally:
        # Ensure the connection is closed after updating/creating
        connection.close()
    # Render the appropriate template based on the file status
    if file_status == 'processed':
        print(file_status)
        render(request, 'chatbot/processed.html')
        response_data = {"message": "Processing complete.", "status": "processed"}
        return JsonResponse(response_data, status=200)  # Returning JSON response with status
    else:
        print(file_status)
        return render(request, 'chatbot/processing.html')
    
def attachments(request):
    user_id = 1  # Hard-coded user ID for testing
    try:
        user = User.objects.get(id=user_id)
        attachment_status = AttachmentStatus.objects.get(user=user).status
        print("attachment_status", attachment_status)
        if request.session["attachment_status"] != 'logged_in':
            request.session["attachment_status"] = attachment_status 
        print("inside attachments", attachment_status)
    except (User.DoesNotExist, AttachmentStatus.DoesNotExist):
        return HttpResponse("User or attachment status not found.", status=404)
    
    
    if attachment_status == 'processing':
        return render(request, 'chatbot/processing.html')
    elif attachment_status == 'processed':
        return render(request, 'chatbot/attachment.html')
    else:
        return render(request, 'chatbot/attachment.html')

def attachment_list(request):
    # Example call to an external API to get files; adjust as necessary.
    response = requests.get(f'https://kong.zenith-dev-gateway.com/core-be/api/rag/chats/{request.session.get("id")}/attachments')
    print("url", f'https://kong.zenith-dev-gateway.com/core-be/api/rag/chats/{request.session.get("id")}/attachments')
    print("response", response.json())

    if response.status_code == 200:
        files = response.json()  # Assuming the API returns a JSON list of files
        # try:
        #     if files[0]['fileName']:
        #         request.session["attachment_status"] = "logged_in"
        # except:
        #     request.session["attachment_status"] = "logged_in"       
        print("called")
        return JsonResponse({'files': files})  

def signin(request):
    return render(request, 'chatbot/signin.html')

def submit(request):
    username = request.GET.get('username')
    password = request.GET.get('password', '') 
    request.session['username'] = username
    user = authenticate(request, username=username, password=password)
    if username:
        request.session["attachment_status"] = "signedin"
        request.session["loggedin"] = True
    if user is not None:
        print("test")
        login(request, user)
        next_url = request.GET.get('next', '/chatbot/')
        return redirect(next_url)
        # next_url = request.GET.get('next', '/chatbot/')
        # return redirect(next_url)
        # return JsonResponse({'status': 'success', 'username': username})
    else:
        return JsonResponse({'status': 'error', 'message': 'no username provided'})
    

async def file_upload(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        attachments = []

        # Process files and build payload
        for f in files:
            try:
                # Read file content asynchronously using sync_to_async
                file_content = await sync_to_async(f.read)()
                # Encode the content to base64
                b64_content = base64.b64encode(file_content)
                b64_string = b64_content.decode('utf-8')
                # Append a dict with fileName and attachment to the attachments list
                attachments.append({
                    'fileName': f.name,
                    'attachment': b64_string
                })
            except Exception as e:
                print(f"Error processing file {f.name}: {str(e)}")
                return JsonResponse({'status': 'error', 'message': f'Failed to process file {f.name}.'})

        # API endpoint URL
        session_id = await sync_to_async(request.session.get)("id")
        url = f'https://kong.zenith-dev-gateway.com/core-be/api/rag/chats/{session_id}/attachments'
        
        # Check attachment status asynchronously
        attachment_status = await sync_to_async(request.session.get)("attachment_status")
        if attachment_status != "processing":
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(url, json=attachments) as response:
                        if response.status == 201:
                            # Update session state asynchronously
                            await sync_to_async(request.session.__setitem__)("attachment_status", "processing")
                            # Ensure that Django session modifications are saved
                            await sync_to_async(request.session.save)()
                            await sync_to_async(update_file_status)("processing")
                            return render(request, 'chatbot/processing.html')
                        else:
                            text = await response.text()
                            print(f"Failed to upload files. Status: {response.status}, Response: {text}")
                            return JsonResponse({'status': 'error', 'message': f'Failed to upload files. Server responded with status {response.status}.'})
                except Exception as e:
                    print(f"HTTP request failed: {str(e)}")
                    return JsonResponse({'status': 'error', 'interface': 'HTTP request failed.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

