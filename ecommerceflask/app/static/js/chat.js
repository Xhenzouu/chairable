let receiverId = null;
let currentUser_Id = null;

const loadingSpinner = document.getElementById('loading-spinner');

function fetchUsers() {
    fetch('/get_users')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(users => {
            console.log(users); // Debug output to see the fetched users
            const userList = document.getElementById('user-list');
            userList.innerHTML = ''; // Clear existing users

            users.forEach(user => {
                const button = document.createElement('button');
                button.classList.add('user-button');
                button.setAttribute('data-receiver-id', user.id); // Set the user ID as a data attribute
                button.textContent = user.name; // Set the button text to the user's name

                // Add click event to set receiverId
                button.addEventListener('click', function() {
                    // Remove active class from all buttons
                    const allButtons = document.querySelectorAll('.user-button');
                    allButtons.forEach(btn => btn.classList.remove('active'));

                    // Set active class to the clicked button
                    button.classList.add('active');

                    receiverId = user.id; // Set the receiver ID
                    loadMessages(receiverId); // Load messages for the selected user

                    // Show the chat popover
                    showChatPopover(); // Function to make the chat popover visible
                });

                userList.appendChild(button); // Add the button to the user list
            });
        })
        .catch(error => {
            console.error('Error fetching users:', error);
        });
}

// Call fetchUsers on page load
fetchUsers();

// Function to show the chat popover
function showChatPopover() {
    const chatPopover = document.getElementById('chat-popover');
    chatPopover.style.visibility = 'visible';
    chatPopover.style.opacity = '1';
}

// Function to load messages between the current user and the selected receiver
function loadMessages(otherUser_Id) {
    const chatMessages = document.getElementById('chat-messages');

    // Show loading spinner
    loadingSpinner.style.display = 'block';

    fetch(`/get_messages/${otherUser_Id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            chatMessages.innerHTML = ''; // Clear existing messages

            if (data.success) {
                data.messages.forEach(message => {
                    addMessage(message.message, message.is_sender, message.created_at); // Use `is_sender` field
                });
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching messages:', error);
        })
        .finally(() => {
            // Hide loading spinner
            loadingSpinner.style.display = 'none';
        });
}

// Add the Typing Indicator Functionality Here
const typingIndicator = document.getElementById('typing-indicator');
let typingTimeout;

document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("user-search-input");
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            const searchTerm = this.value.toLowerCase();
            const userList = document.getElementById("user-list");

            // Show a loading spinner (optional)
            document.getElementById("loading-spinner").style.display = "block";

            // Use AJAX to fetch filtered users
            fetch(`/search-users?query=${encodeURIComponent(searchTerm)}`)
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json(); // Try to parse the response JSON
                })
                .then((users) => {
                    userList.innerHTML = "";

                    if (users.length === 0) {
                        userList.innerHTML = "<p>No users found.</p>";
                    } else {
                        users.forEach((user) => {
                            const userButton = document.createElement("button");
                            userButton.className = "user-button";
                            userButton.textContent = user.name;
                            userList.appendChild(userButton);
                        });
                    }
                })
                .catch((error) => {
                    console.error("Error fetching users:", error);
                    userList.innerHTML = "<p>Error loading users.</p>";
                })
                .finally(() => {
                    document.getElementById("loading-spinner").style.display = "none";
                });
        });
    }
});




document.getElementById('message-input').addEventListener('input', function() {
    // Show typing indicator
    typingIndicator.style.display = 'block';

    // Send a typing event to the server
    fetch('/typing', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ receiver_id: receiverId }),
    });

    // Reset the timeout
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        // Hide typing indicator after 2 seconds of inactivity
        typingIndicator.style.display = 'none';
    }, 2000);
});

function addMessage(message, isSender, timestamp) {
    const chatMessages = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');

    // Use the isSender boolean to determine the message alignment
    if (isSender) {
        messageDiv.classList.add('sender-message');
    } else {
        messageDiv.classList.add('receiver-message');
    }

    // Create a timestamp element
    const timeDiv = document.createElement('small');
    timeDiv.classList.add('message-time');
    timeDiv.textContent = new Date(timestamp).toLocaleTimeString(); // Format the timestamp

    messageDiv.textContent = message; // Set the message text
    messageDiv.appendChild(timeDiv); // Append the timestamp
    chatMessages.appendChild(messageDiv); // Add the message to the chat

    // Scroll to the bottom of the chat messages
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
function addMessage(message, isSender, timestamp) {
    const chatMessages = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');

    // Determine the message type based on isSender
    if (isSender) {
        messageDiv.classList.add('sender-message'); // Align to the right for sender
    } else {
        messageDiv.classList.add('receiver-message'); // Align to the left for receiver
    }

    // Create a timestamp element
    const timeDiv = document.createElement('small');
    timeDiv.classList.add('message-time');
    timeDiv.textContent = new Date(timestamp).toLocaleTimeString(); // Format the timestamp

    messageDiv.textContent = message; // Set the message text
    messageDiv.appendChild(timeDiv); // Append the timestamp
    chatMessages.appendChild(messageDiv); // Add the message to the chat

    // Scroll to the bottom of the chat messages
    chatMessages.scrollTop = chatMessages.scrollHeight;
}


// Event listener for sending messages when clicking the send button
document.getElementById('send-message').addEventListener('click', function() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value;

    if (!receiverId) {
        alert('Please select a user to send a message.');
        return;
    }

    if (message.trim() === '') {
        alert('Please enter a message.');
        return;
    }

    // Show loading spinner
    loadingSpinner.style.display = 'block';

    fetch('/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'receiver_id': receiverId,
            'message': message,
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addMessage(message, true, new Date().toISOString()); // `isSender` is `true` for sent messages
            messageInput.value = ''; // Clear the input
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    })
    .finally(() => {
        // Hide loading spinner
        loadingSpinner.style.display = 'none';
    });
});

// Event listener for sending messages when pressing Enter
document.getElementById('message-input').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault(); // Prevent the default action (like a form submission)
        document.getElementById('send-message').click(); // Trigger the click event on the send button
    }
});