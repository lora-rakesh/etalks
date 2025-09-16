// app/static/etalks.js

const usersList = document.getElementById("users-list");
const chatBody = document.getElementById("chat-body");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const chatUsername = document.getElementById("chat-username");
const chatAvatar = document.getElementById("chat-username-avatar");
const themeToggle = document.getElementById("theme-toggle");
const menuToggle = document.getElementById("menu-toggle");
const dropdown = document.getElementById("dropdown");
const clearChatBtn = document.getElementById("clear-chat");
const searchInput = document.getElementById("search-input");

let selectedUser = null;
let currentUserId = parseInt(document.body.dataset.userId);

// -----------------------
// WebSocket Setup
// -----------------------
const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
let chatSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/chat/`);

// -----------------------
// Reconnect logic
// -----------------------
chatSocket.onclose = function () {
  console.log("WebSocket closed, reconnecting...");
  setTimeout(() => {
    chatSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/chat/`);
    attachSocketEvents();
  }, 1000);
};

const socket = new WebSocket(
    `ws://${window.location.host}/ws/chat/`
);

// When connection opens
socket.onopen = function(e) {
    console.log("WebSocket connected!");
};

// When message is received
socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log("New message:", data);
    // TODO: update chat UI here
};

// Sending a message
function sendMessage(senderId, receiverId, message) {
    socket.send(JSON.stringify({
        sender_id: senderId,
        receiver_id: receiverId,
        message: message
    }));
}

function attachSocketEvents() {
  chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);

    if (data.action === "new_message") {
      // Show message in chat if selected
      if (selectedUser && data.sender_id === selectedUser.id) {
        appendMessage("received", data.sender_name, data.message);
      } else {
        // Show unread badge
        const badge = document.getElementById(`unread-${data.sender_id}`);
        if (badge) badge.textContent = "•";
      }

      // Move user to top in sidebar
      moveUserToTop(data.sender_id);
    }
  };
}
attachSocketEvents();

// -----------------------
// Move user to top in sidebar
// -----------------------
function moveUserToTop(userId) {
  const userDiv = document.querySelector(`.sidebar-user[data-id='${userId}']`);
  if (userDiv) {
    usersList.prepend(userDiv);
  }
}

// -----------------------
// Load users
// -----------------------
async function loadUsers() {
  try {
    const res = await fetch("/users/");
    const data = await res.json();
    renderUsers(data.results || []);
  } catch (err) {
    console.error("Error loading users:", err);
  }
}

// -----------------------
// Render users in sidebar
// -----------------------
function renderUsers(users) {
  usersList.innerHTML = "";
  if (!users.length) {
    usersList.innerHTML = "<div class='no-results'>No users found</div>";
    return;
  }

  users.forEach(user => {
    const div = document.createElement("div");
    div.className = "sidebar-user";
    div.dataset.id = user.id;
    div.innerHTML = `
      <div class="user-icon">${user.name.charAt(0).toUpperCase()}</div>
      <span>${user.name} (${user.employee_id || ""})</span>
      <span class="badge" id="unread-${user.id}"></span>
    `;
    div.onclick = () => selectUser(user, div);
    usersList.appendChild(div);
  });
}

// -----------------------
// Select user
// -----------------------
async function selectUser(user, div) {
  selectedUser = user;
  chatUsername.textContent = user.name;
  chatAvatar.textContent = user.name.charAt(0).toUpperCase();
  chatBody.innerHTML = "";

  document.querySelectorAll(".sidebar-user").forEach(el => el.classList.remove("selected"));
  div.classList.add("selected");

  // Clear unread badge
  document.getElementById(`unread-${user.id}`).textContent = "";

  try {
    const res = await fetch(`/messages/${user.id}/`);
    const data = await res.json();
    data.results.forEach(m => {
      appendMessage(
        m.sender === currentUserId ? "sent" : "received",
        m.sender === currentUserId ? "You" : user.name,
        m.message
      );
    });
  } catch (err) {
    console.error("Error loading messages:", err);
  }
}

// -----------------------
// Send message
// -----------------------
function sendMessage() {
  const message = chatInput.value.trim();
  if (!message || !selectedUser) return;

  const data = {
    action: "send_message",
    room: selectedUser.id,
    message: message
  };

  chatSocket.send(JSON.stringify(data));
  appendMessage("sent", "You", message);
  chatInput.value = "";

  // Move user to top immediately
  moveUserToTop(selectedUser.id);
}

sendBtn.onclick = sendMessage;
chatInput.addEventListener("keypress", e => {
  if (e.key === "Enter") sendMessage();
});

// -----------------------
// Append message
// -----------------------
function appendMessage(type, sender, message) {
  const div = document.createElement("div");
  div.className = `chat-bubble ${type}`;
  div.innerHTML = `<div class="sender-name">${sender}</div>${message}`;
  chatBody.appendChild(div);
  chatBody.scrollTop = chatBody.scrollHeight;
}

// -----------------------
// Load recent chats (on page load)
// -----------------------
async function loadRecentChats() {
  try {
    const res = await fetch("/recent-chats/");
    const data = await res.json();
    renderUsers(data.results || []);
  } catch (err) {
    console.error("Error loading recent chats:", err);
  }
}

// -----------------------
// Clear chat
// -----------------------
clearChatBtn.onclick = () => {
  chatBody.innerHTML = "";
};

// -----------------------
// Search users
// -----------------------
searchInput.addEventListener("input", async function () {
  const query = this.value.trim();
  if (!query) {
    loadUsers();
    return;
  }

  try {
    const res = await fetch(`/search-users/?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    renderUsers(data.results || []);
  } catch (err) {
    console.error("Error searching users:", err);
  }
});

// -----------------------
// Theme toggle
// -----------------------
themeToggle.onclick = () => {
  document.body.classList.toggle("dark-theme");
  const icon = themeToggle.querySelector("i");
  icon.className = document.body.classList.contains("dark-theme") ? "fa fa-sun" : "fa fa-moon";
};

// -----------------------
// Initialize
// -----------------------
loadRecentChats();
loadUsers();
