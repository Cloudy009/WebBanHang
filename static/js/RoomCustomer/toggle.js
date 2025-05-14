const chatIcon = document.getElementById('chat-icon');
const chatboxContainer = document.getElementById('chatbox-container');
const closeChatbox = document.getElementById('close-chatbox');

// Open chatbox when chat icon is clicked
chatIcon.addEventListener('click', () => {
    chatboxContainer.style.display = 'block';
    chatIcon.style.display = 'none';
});

// Close chatbox and show chat icon
closeChatbox.addEventListener('click', () => {
    chatboxContainer.style.display = 'none';
    chatIcon.style.display = 'block';
});