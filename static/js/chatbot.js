// CalmSphere AI Chatbot Frontend Script

const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

// Helper to convert simple markdown (bold and links) to HTML safely
function formatMessageText(text) {
    if (!text) return "";

    // Escape HTML first to prevent XSS, while keeping formatting safe
    let escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Convert markdown bold: **text** -> <strong>text</strong>
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Convert markdown links: [text](url) -> <a href="url">text</a>
    escaped = escaped.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>');

    // Convert literal paths to links if they aren't already linked (e.g. '/journal/' -> <a href="/journal/">/journal/</a>)
    // Avoid double linking by checking if it starts with href=" or similar
    // This is a simple regex for CalmSphere paths
    escaped = escaped.replace(/(?<!href=")(?<!['"])\/meditation\/[a-zA-Z0-9_-]+\/?/g, '<a href="$&">$&</a>');
    escaped = escaped.replace(/(?<!href=")(?<!['"])\/journal\/?/g, '<a href="$&">$&</a>');

    // Convert newlines to breaks
    escaped = escaped.replace(/\n/g, "<br>");

    return escaped;
}

// Append a message bubble to the chat pane
function appendMessage(text, isUser = false) {
    if (!text || !messagesContainer) return;

    const bubble = document.createElement('div');
    bubble.className = `msg-bubble ${isUser ? 'user' : 'bot'}`;
    
    if (isUser) {
        bubble.textContent = text;
    } else {
        bubble.innerHTML = formatMessageText(text);
    }

    messagesContainer.appendChild(bubble);
    // Smooth scroll to bottom
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
}

// Send user message to Django backend via Fetch API
async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // Render user message immediately
    appendMessage(text, true);
    userInput.value = '';
    
    // Disable inputs during network request
    userInput.disabled = true;
    sendBtn.disabled = true;

    // Render temporary "thinking" indicator
    const thinkingBubble = document.createElement('div');
    thinkingBubble.className = 'msg-bubble bot';
    thinkingBubble.id = 'typingBubble';
    thinkingBubble.innerHTML = `
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    messagesContainer.appendChild(thinkingBubble);
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });

    try {
        const urlParams = new URLSearchParams(window.location.search);
        const currentChatId = urlParams.get('chat_id') || '';
        const geminiKey = localStorage.getItem('CS_GEMINI_API_KEY') || '';
        const response = await fetch(`/chatbot/?chat_id=${currentChatId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Gemini-Key': geminiKey
            },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        
        // Remove typing indicator
        const indicator = document.getElementById('typingBubble');
        if (indicator) indicator.remove();

        // Re-enable inputs
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();

        if (data && data.status === 'success' && data.response) {
            appendMessage(data.response, false);
            // Optionally reload or dynamically append to sidebar if it was a brand new chat
            // so the title updates dynamically. But let's check: if we just reload on first message,
            // the sidebar will show the title. Let's do a simple check: if sidebar list has only
            // "New Chat" or is empty, we can reload to show the first message title.
            // Even better: just let the user see the chat, and when they refresh/navigate, it updates.
            // Let's reload to update the sidebar title ONLY if the current active chat list item is "New Chat"
            const activeItemText = document.querySelector('.chat-history-item.active .chat-history-title');
            if (activeItemText && (activeItemText.textContent.trim() === 'New Chat' || activeItemText.textContent.trim() === '')) {
                window.location.reload();
            }
        } else if (data && data.message) {
            appendMessage(`Sorry, I ran into an issue: ${data.message}`, false);
        } else {
            appendMessage("I'm sorry, I'm having trouble connecting right now. Please try again.", false);
        }
    } catch (e) {
        // Remove typing indicator
        const indicator = document.getElementById('typingBubble');
        if (indicator) indicator.remove();

        // Re-enable inputs
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
        
        console.error("Chatbot connection failed:", e);
        appendMessage("I couldn't reach the CalmSphere server. Let's try again in a moment.", false);
    }
}

// Reset conversation history
async function resetConversation() {
    if (!confirm("Are you sure you want to clear the conversation and start a new session?")) {
        return;
    }

    try {
        const urlParams = new URLSearchParams(window.location.search);
        const currentChatId = urlParams.get('chat_id') || '';
        const response = await fetch(`/chatbot/clear/?chat_id=${currentChatId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });

        const data = await response.json();
        if (data && data.status === 'success') {
            // Reload the page to load a fresh greeting from the backend
            window.location.reload();
        } else {
            alert("Could not reset conversation. Please try again.");
        }
    } catch (e) {
        console.error("Failed to clear chat history:", e);
        alert("Server connection failed. Could not clear conversation.");
    }
}

// Real-time frontend sidebar filtering
function filterChats() {
    const query = document.getElementById('chatSearch').value.toLowerCase().trim();
    const items = document.querySelectorAll('.chat-history-item');
    
    items.forEach(item => {
        const title = item.getAttribute('data-title') || '';
        if (title.includes(query)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

// Delete chat session handler
async function deleteChat(chatId, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    if (!confirm("Are you sure you want to delete this conversation?")) {
        return;
    }
    
    try {
        const response = await fetch('/chatbot/delete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ chat_id: chatId })
        });
        
        const data = await response.json();
        if (data && data.status === 'success') {
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('chat_id') === chatId) {
                // Redirect to base chatbot URL if the active chat was deleted
                window.location.href = '/chatbot/';
            } else {
                // Otherwise dynamically remove from sidebar list
                const item = document.querySelector(`.chat-history-item[data-session-key="${chatId}"]`);
                if (item) {
                    item.remove();
                }
                
                // Show empty history state if no chats are left
                const list = document.getElementById('chatHistoryList');
                if (list && list.querySelectorAll('.chat-history-item').length === 0) {
                    list.innerHTML = '<div class="empty-history">No conversations yet</div>';
                }
            }
        } else {
            alert("Could not delete conversation. Please try again.");
        }
    } catch (e) {
        console.error("Failed to delete chat:", e);
        alert("Server connection failed. Could not delete conversation.");
    }
}

// Event listener for Enter key in input field
if (userInput) {
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });
}

// On page load, scroll messages to bottom and format existing ones
document.addEventListener('DOMContentLoaded', () => {
    // Scroll to bottom
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Format any pre-rendered backend bot messages
        const botBubbles = messagesContainer.querySelectorAll('.msg-bubble.bot');
        botBubbles.forEach(bubble => {
            // If it contains raw newlines or markdown from DB, format it
            const rawText = bubble.innerHTML.replace(/<br\s*\/?>/gi, '\n');
            bubble.innerHTML = formatMessageText(rawText);
        });
    }
});

function toggleSettings() {
    const panel = document.getElementById('apiSettingsPanel');
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        document.getElementById('geminiKeyInput').value = localStorage.getItem('CS_GEMINI_API_KEY') || '';
    } else {
        panel.style.display = 'none';
    }
}

function saveApiKey() {
    const key = document.getElementById('geminiKeyInput').value.trim();
    if (key) {
        localStorage.setItem('CS_GEMINI_API_KEY', key);
        alert("Gemini API Key saved successfully! The chatbot is now ready to respond to any message using Gemini.");
    } else {
        localStorage.removeItem('CS_GEMINI_API_KEY');
        alert("API Key cleared. The chatbot will now run in offline/demo mode.");
    }
    document.getElementById('apiSettingsPanel').style.display = 'none';
}
