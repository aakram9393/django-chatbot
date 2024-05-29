from django.shortcuts import render
from django.http import JsonResponse
import requests
import base64
import logging

# Create your views here.

def retrieve_user_id(username):
    url = f'https://kong.zenith-dev-gateway.com/core-be/api/rag/chats?userName={username}'

    response = requests.post(url)
    if response.status_code == 201:
        return response.json()["id"]
    else:
        return response.status_code

def post_question(message, chat_id):
    url = f'https://kong.zenith-dev-gateway.com/core-be/api/rag/chats/{chat_id}/questions'
    payload = {
        'question': message
    }
    response = requests.post(url, json=payload)
    print("api-response",response)
    if response.status_code == 201:
        return response.json()
    else:
        return response.status_code

def api_chat(request):
    user_input = request.GET.get('message')
    if user_input:
        answer = post_question(user_input, request.session["id"])
        print("API ANSWER :::::::: ", answer)
    bot_response = answer["answer"]
    return JsonResponse({'message': str(bot_response)})

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
    request.session['username'] = username
    request.session["id"] = retrieve_user_id(request.session['username'])
    print(request.session["id"])
    if username:
        request.session["attachment_status"] = "signedin"
        return JsonResponse({'status': 'success', 'username': username})
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

