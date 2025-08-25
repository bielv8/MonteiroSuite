// WhatsApp interface JavaScript functionality
let currentConversation = null;
let messageRefreshInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeWhatsApp();
    setupMessageForm();
    setupNewMessageForm();
});

function initializeWhatsApp() {
    // Setup conversation list click handlers
    setupConversationHandlers();
    
    // Auto-refresh messages every 10 seconds
    messageRefreshInterval = setInterval(refreshMessages, 10000);
    
    // Setup phone number input handling
    setupPhoneInputs();
}

function setupConversationHandlers() {
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', function() {
            const phone = this.getAttribute('data-phone');
            loadConversation(phone);
        });
    });
}

function loadConversation(phoneNumber) {
    currentConversation = phoneNumber;
    
    // Update active conversation in sidebar
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const activeItem = document.querySelector(`[data-phone="${phoneNumber}"]`);
    if (activeItem) {
        activeItem.classList.add('active');
    }
    
    // Show chat header and input
    document.getElementById('chat-header').style.display = 'block';
    document.getElementById('chat-input').style.display = 'block';
    
    // Update chat header
    const contactName = activeItem ? 
        activeItem.querySelector('.fw-bold').textContent : 
        phoneNumber;
    
    document.getElementById('chat-contact-name').textContent = contactName;
    document.getElementById('chat-contact-phone').textContent = phoneNumber;
    document.getElementById('current-phone').value = phoneNumber;
    
    // Load messages for this conversation
    loadConversationMessages(phoneNumber);
}

function loadConversationMessages(phoneNumber) {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div></div>';
    
    // In a real implementation, this would fetch messages via AJAX
    // For now, we'll simulate with the messages we have
    fetch(`/api/whatsapp/messages?phone=${encodeURIComponent(phoneNumber)}`)
    .then(response => response.json())
    .then(data => {
        displayMessages(data.messages);
    })
    .catch(error => {
        console.error('Error loading messages:', error);
        messagesContainer.innerHTML = `
            <div class="text-center text-danger">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                <p>Erro ao carregar mensagens</p>
            </div>
        `;
    });
}

function displayMessages(messages) {
    const messagesContainer = document.getElementById('chat-messages');
    
    if (!messages || messages.length === 0) {
        messagesContainer.innerHTML = `
            <div class="text-center text-muted">
                <i class="fab fa-whatsapp fa-3x mb-3"></i>
                <p>Nenhuma mensagem ainda</p>
                <p>Comece uma conversa enviando uma mensagem</p>
            </div>
        `;
        return;
    }
    
    let messagesHTML = '';
    messages.forEach(message => {
        const messageClass = message.direction === 'incoming' ? 'message-incoming' : 'message-outgoing';
        const timeString = formatMessageTime(message.timestamp);
        
        messagesHTML += `
            <div class="message-bubble ${messageClass}">
                <div>${escapeHtml(message.content)}</div>
                <div class="message-time">${timeString}</div>
            </div>
        `;
    });
    
    messagesContainer.innerHTML = messagesHTML;
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function setupMessageForm() {
    const form = document.getElementById('messageForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessage(e);
        });
    }
}

function sendMessage(event) {
    if (event) {
        event.preventDefault();
    }
    
    const form = document.getElementById('messageForm');
    const messageInput = form.querySelector('input[name="message"]');
    const submitBtn = form.querySelector('button[type="submit"]');
    const phoneNumber = document.getElementById('current-phone').value;
    const messageText = messageInput.value.trim();
    
    if (!messageText || !phoneNumber) {
        return;
    }
    
    // Show loading state
    const originalBtnHTML = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    submitBtn.disabled = true;
    messageInput.disabled = true;
    
    // Add message to UI immediately (optimistic update)
    addMessageToUI(messageText, 'outgoing');
    
    // Clear input
    messageInput.value = '';
    
    // Send message
    const formData = new FormData();
    formData.append('phone_number', phoneNumber);
    formData.append('message', messageText);
    
    fetch('/whatsapp/send', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            // Message sent successfully
            showAlert('Mensagem enviada!', 'success');
        } else {
            // Remove the optimistic message and show error
            removeLastMessage();
            showAlert('Erro ao enviar mensagem. Tente novamente.', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        removeLastMessage();
        showAlert('Erro ao enviar mensagem. Verifique sua conexão.', 'danger');
    })
    .finally(() => {
        // Reset form state
        submitBtn.innerHTML = originalBtnHTML;
        submitBtn.disabled = false;
        messageInput.disabled = false;
        messageInput.focus();
    });
}

function addMessageToUI(content, direction) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageClass = direction === 'incoming' ? 'message-incoming' : 'message-outgoing';
    const currentTime = new Date();
    const timeString = currentTime.toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    const messageHTML = `
        <div class="message-bubble ${messageClass}">
            <div>${escapeHtml(content)}</div>
            <div class="message-time">${timeString}</div>
        </div>
    `;
    
    // Check if container has empty state and clear it
    if (messagesContainer.querySelector('.text-center.text-muted')) {
        messagesContainer.innerHTML = '';
    }
    
    messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeLastMessage() {
    const messagesContainer = document.getElementById('chat-messages');
    const lastMessage = messagesContainer.querySelector('.message-outgoing:last-child');
    if (lastMessage) {
        lastMessage.remove();
    }
}

function setupNewMessageForm() {
    const form = document.querySelector('#newMessageModal form');
    const phoneSelect = document.getElementById('new_phone');
    const manualPhoneInput = document.getElementById('manual_phone');
    
    if (phoneSelect && manualPhoneInput) {
        manualPhoneInput.addEventListener('input', function() {
            if (this.value.trim()) {
                phoneSelect.value = '';
                phoneSelect.required = false;
                this.name = 'phone_number';
            } else {
                phoneSelect.required = true;
                this.name = '';
            }
        });
        
        phoneSelect.addEventListener('change', function() {
            if (this.value) {
                manualPhoneInput.value = '';
                manualPhoneInput.name = '';
                this.required = true;
            }
        });
    }
}

function setupPhoneInputs() {
    const phoneInputs = document.querySelectorAll('input[type="text"][placeholder*="99999"]');
    
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            
            if (value.length > 0) {
                if (value.length <= 11) {
                    // Brazilian mobile format
                    if (value.length <= 2) {
                        value = `+55 ${value}`;
                    } else if (value.length <= 7) {
                        value = `+55 ${value.substring(0, 2)} ${value.substring(2)}`;
                    } else {
                        value = `+55 ${value.substring(0, 2)} ${value.substring(2, 7)}-${value.substring(7)}`;
                    }
                }
            }
            
            this.value = value;
        });
    });
}

function refreshMessages() {
    if (currentConversation) {
        // Silently refresh current conversation
        fetch(`/api/whatsapp/messages?phone=${encodeURIComponent(currentConversation)}`)
        .then(response => response.json())
        .then(data => {
            const messagesContainer = document.getElementById('chat-messages');
            const currentScrollTop = messagesContainer.scrollTop;
            const currentScrollHeight = messagesContainer.scrollHeight;
            const currentClientHeight = messagesContainer.clientHeight;
            const wasAtBottom = currentScrollTop + currentClientHeight >= currentScrollHeight - 5;
            
            displayMessages(data.messages);
            
            // Maintain scroll position unless user was at bottom
            if (wasAtBottom) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            } else {
                messagesContainer.scrollTop = currentScrollTop;
            }
        })
        .catch(error => {
            // Silently fail for background refresh
            console.log('Background refresh failed:', error);
        });
    }
}

function setNewQuickMessage(message) {
    document.getElementById('new_message').value = message;
}

function formatMessageTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    
    // Check if it's today
    if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    // Check if it's yesterday
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
        return 'Ontem ' + date.toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    // Older messages
    return date.toLocaleDateString('pt-BR', { 
        day: '2-digit', 
        month: '2-digit' 
    }) + ' ' + date.toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showAlert(message, type) {
    // Create alert and add to page
    const alertContainer = document.querySelector('main');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 3000);
}

// Handle window focus to refresh messages
window.addEventListener('focus', function() {
    if (currentConversation) {
        refreshMessages();
    }
});

// Handle modal events
document.addEventListener('shown.bs.modal', function(e) {
    if (e.target.id === 'newMessageModal') {
        document.getElementById('new_message').focus();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (messageRefreshInterval) {
        clearInterval(messageRefreshInterval);
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to send message
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const messageInput = document.querySelector('#messageForm input[name="message"]');
        if (messageInput && messageInput === document.activeElement) {
            e.preventDefault();
            sendMessage();
        }
    }
    
    // Escape to close new message modal
    if (e.key === 'Escape') {
        const newMessageModal = document.getElementById('newMessageModal');
        if (newMessageModal && newMessageModal.classList.contains('show')) {
            const modalInstance = bootstrap.Modal.getInstance(newMessageModal);
            modalInstance.hide();
        }
    }
});

