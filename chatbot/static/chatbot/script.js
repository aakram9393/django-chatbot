// script.js
function sendMessage() {
    var userInput = document.getElementById('userInput').value;
    if (userInput.trim() === '') return; // Prevents sending empty messages

    fetch(`bot/?message=${userInput}`)
        .then(response => response.json())
        .then(data => {
            var chatbox = document.getElementById('chatbox');
            var userLine = `<li class="user"><img src="https://ps.w.org/user-avatar-reloaded/assets/icon-256x256.png?rev=2540745" alt="User Avatar"><span>${userInput}</span></li>`;
            var botLine = `<li class="bot"><img src="https://img.freepik.com/free-vector/cartoon-style-robot-vectorart_78370-4103.jpg?t=st=1716934235~exp=1716937835~hmac=e82dab0ee88c3673a7db0610806ccf972d86f82bd0faf481bf16bb5527a4ca03&w=996" alt="Bot Avatar"><span>${data.message}</span></li>`;
            chatbox.innerHTML += userLine;
            chatbox.innerHTML += botLine;
            document.getElementById('userInput').value = ''; // clear input field after sending a message.
            chatbox.scrollTop = chatbox.scrollHeight; // Scroll to the bottom of the chatbox
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