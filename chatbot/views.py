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

# Create your views here.

def update_file_status(status):
    user = User.objects.get(id=1)

    # If the user was created, set a default password and other necessary fields
    if user:
        # Update or create the attachment status associated with the user
        AttachmentStatus.objects.update_or_create(user=user, defaults={'status': status})

    

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

async def post_question(message, chat_id):
    url = f'https://kong.zenith-dev-gateway.com/core-be/api/rag/chats/{chat_id}/questions'
    payload = {
        'question': message
    }
    async with httpx.AsyncClient() as client:
        response = requests.post(url, json=payload)
        print("api-response",response)
        if response.status_code == 201:
            return response.json()
        else:
            return response.status_code

async def api_chat(request):
    user_input = request.GET.get('message')
    if user_input:
        session_id = await sync_to_async(request.session.__getitem__)("id")
        answer = await post_question(user_input, session_id)
        print("API ANSWER :::::::: ", answer)
    bot_response = answer["answer"]
    return JsonResponse({'message': str(bot_response)})

# @login_required(login_url='signin/')
def chat(request):
    if request.session["attachment_status"] == 'processed':
        return render(request, 'chatbot/chat.html')
    else:
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
    user, created = User.objects.get_or_create(id=user_id, defaults={
        'username': f'user_{user_id}',
        'email': f'user_{user_id}@example.com'
    })

    # If the user was created, set a default password and other necessary fields
    if created:
        user.set_password("defaultpassword")  # Set a default or generated password
        user.save()
        login(request, user)

    # Update or create the attachment status associated with the user
    AttachmentStatus.objects.update_or_create(user=user, defaults={'status': 'processed' if file_status == 'processed' else 'processing'})

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
    

def file_upload(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        attachments = []

        # Process files and build payload
        for f in files:
            try:
                # Read file content asynchronously
                file_content = f.read()
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

        # Construct the request body
        payload = attachments
        print("payload", payload)

        # API endpoint URL
        url = f'https://kong.zenith-dev-gateway.com/core-be/api/rag/chats/{request.session.get("id")}/attachments'
        
        if request.session.get("attachment_status") != "processing":
            try:
                    response = requests.post(url, json=payload)
                    if response.status_code == 201:
                        update_file_status('processing')
                        return render(request, 'chatbot/processing.html')
                    else:
                        print(f"Failed to upload files. Status: {response.status_code}, Response: {response.text}")
                        return JsonResponse({'status': 'error', 'message': f'Failed to upload files. Server responded with status {response.status_code}.'})
            except:
                print(f"HTTP request failed")
                return JsonResponse({'status': 'error', 'message': 'HTTP request failed.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

