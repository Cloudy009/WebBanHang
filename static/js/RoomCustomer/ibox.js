const roomName = "{{ room_name }}";

const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + roomName + '/'
);

let loadingOldMessages = false;
let oldestMessageTimestamp = null; // Track the timestamp of the oldest message loaded

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    const chatLog = document.querySelector('#chat-log');

    if (data.type === 'chat_message') {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(data.user === '{{ user.username }}' ? 'sender' : 'receiver');
        messageDiv.innerHTML = `<strong>${data.user}:</strong> ${data.message}`;
        chatLog.appendChild(messageDiv);
        chatLog.scrollTop = chatLog.scrollHeight;

        // Update the timestamp of the last message received
        oldestMessageTimestamp = data.timestamp;
    } else if (data.type === 'old_messages') {
        const messages = data.messages;
        messages.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.classList.add(msg.user === '{{ user.username }}' ? 'sender' : 'receiver');
            messageDiv.innerHTML = `<strong>${msg.user}:</strong> ${msg.content}`;
            chatLog.insertBefore(messageDiv, chatLog.firstChild);
        });
        // Update the timestamp of the oldest message after loading old messages
        if (messages.length > 0) {
            oldestMessageTimestamp = messages[messages.length - 1].timestamp;
        }
        loadingOldMessages = false;
    }
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

chatSocket.onerror = function(e) {
    console.error('Chat socket encountered an error:', e);
};

function sendMessage() {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    if (message.trim()) {
        chatSocket.send(JSON.stringify({
            'message': message
        }));
        messageInputDom.value = '';
    }
}

document.querySelector('#send-button').onclick = function() {
    sendMessage();
};

document.querySelector('#chat-message-input').onkeyup = function(e) {
    if (e.keyCode === 13) {
        sendMessage();
    }
};

// Send a request to load old messages when the page loads
chatSocket.onopen = function() {
    chatSocket.send(JSON.stringify({
        'action': 'load_old_messages',
        'oldest_message_timestamp': oldestMessageTimestamp
    }));
};

document.querySelector('#chat-log').onscroll = function() {
    if (this.scrollTop === 0 && !loadingOldMessages) {
        loadingOldMessages = true;
        chatSocket.send(JSON.stringify({
            'action': 'load_old_messages',
            'oldest_message_timestamp': oldestMessageTimestamp
        }));
    }
};