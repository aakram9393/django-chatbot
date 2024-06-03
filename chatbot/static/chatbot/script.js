// script.js
function sendMessage() {
    var userInput = document.getElementById('userInput').value;
    if (userInput.trim() === '') return;

    var chatbox = document.getElementById('chatbox');
    var userLine = `<li class="user"><img src="https://ps.w.org/user-avatar-reloaded/assets/icon-256x256.png?rev=2540745" alt="User Avatar"><span>${userInput}</span></li>`;
    chatbox.innerHTML += userLine;

    var typingIndicator = `<li class="bot typing"><img src="https://img.freepik.com/free-vector/cartoon-style-robot-vectorart_78370-4103.jpg" alt="Bot Avatar"><span>typing...</span></li>`;
    chatbox.innerHTML += typingIndicator;

    fetch(`bot/?message=${encodeURIComponent(userInput)}`, {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=UTF-8'
        }
    })
    .then(response => response.json())
    .then(data => {
        var typingElement = document.querySelector('.typing');
        if (typingElement) {
            typingElement.remove();
        }
        var botLine = `<li class="bot"><img src="https://img.freepik.com/free-vector/cartoon-style-robot-vectorart_78370-4103.jpg" alt="Bot Avatar"><span>${data.message}</span></li>`;
        chatbox.innerHTML += botLine;
        document.getElementById('userInput').value = '';
        chatbox.scrollTop = chatbox.scrollHeight;
    })
    .catch(error => {
        console.error('Failed to fetch response:', error);
        var typingElement = document.querySelector('.typing');
        if (typingElement) {
            typingElement.remove();
        }
    });
}

document.getElementById('signin-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    var username = document.getElementById('username').value;

    if (username.trim() === '') {
        alert('Please enter your username.');
        return;
    }

    // Construct URL with query parameter for username
    var url = new URL('chatbot/submit/', window.location.origin);
    url.searchParams.append('username', username);

    fetch(url)
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        // Handle response data here, e.g., redirect or display a message
    })
    .catch(error => console.error('Error:', error));
});