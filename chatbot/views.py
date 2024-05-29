from django.shortcuts import redirect, render
from django.http import JsonResponse
import requests
import base64
import httpx
from asgiref.sync import sync_to_async
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login

# Create your views here.

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
    return render(request, 'chatbot/chat.html')
    

def home(request):
    return render(request, 'chatbot/base.html')

def attachment_webhook(request):
    request.session["attachment_status"] = "processed"
    return render(request, 'chatbot/processed.html')

def attachments(request):
    if request.session["attachment_status"] != "processing" and request.session["attachment_status"] != "processed":
        return render(request, 'chatbot/attachment.html') 
    elif  request.session["attachment_status"] == "processing":
        return render(request, 'chatbot/processing.html')
    elif  request.session["attachment_status"] == "processed":
        return render(request, 'chatbot/processed.html')

def signin(request):
    return render(request, 'chatbot/signin.html')

def submit(request):
    username = request.GET.get('username')
    password = request.GET.get('password', '') 
    request.session['username'] = username
    request.session["id"] = retrieve_user_id(request.session['username'])
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
        base64_files = []
        
        # Convert each file to a base64-encoded string
        for f in files:
            try:
                # Read the file's content
                file_content = f.read()
                # Encode file content to base64
                b64_content = base64.b64encode(file_content)
                # Convert bytes to string (necessary for JSON serialization)
                b64_string = b64_content.decode('utf-8')
                # Append the base64 string to the list
                base64_files.append(b64_string)
            except Exception as e:
                print(f"Error processing file {f.name}: {str(e)}")
                return JsonResponse({'status': 'error', 'message': f'Failed to process file {f.name}.'})
        
        # Prepare the payload
        payload = {
            "attachment": base64_files[0]
        }
        
        # URL to which the request is sent
        url = f'https://kong.zenith-dev-gateway.com/core-be/api/rag/chats/{request.session.get("id")}/questions'
        print(payload)
        
        try:
            # Post the data as JSON
            if request.session["attachment_status"] != "processing":
                response = requests.post(url, json=payload)
            # Check the response status
            if response.ok:
                print(JsonResponse({'status': 'success', 'message': 'Files uploaded successfully!'}))
                request.session["attachment_status"] = "processing"
                return render(request, 'chatbot/processing.html')
            else:
                print(f"Failed to upload files. Status: {response.status_code}, Response: {response.text}")
                return JsonResponse({'status': 'error', 'message': f'Failed to upload files. Server responded with status {response.status_code}.'})
        except requests.exceptions.RequestException as e:
            print(f"HTTP request failed: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'HTTP request failed.'})

