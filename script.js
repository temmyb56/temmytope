function showImagePreview(src) {
    const preview = document.getElementById('image-preview');
    const uploadIcon = document.getElementById('upload-icon');
    const dragText = document.getElementById('drag-text');
    const controls = document.getElementById('image-controls');
    const uploadArea = document.getElementById('upload-area');
    
    preview.src = src;
    preview.style.display = 'block';
    uploadIcon.style.display = 'none';
    dragText.style.display = 'none';
    controls.style.display = 'flex';
    uploadArea.onclick = null;
    
    // Removed erroneous setting of ticketPic here – that's only for the final ticket display
}

function resetUpload() {
    const preview = document.getElementById('image-preview');
    const uploadIcon = document.getElementById('upload-icon');
    const dragText = document.getElementById('drag-text');
    const controls = document.getElementById('image-controls');
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('avater');
    const ticketPic = document.getElementById('ticket-pic');
    
    preview.style.display = 'none';
    uploadIcon.style.display = 'block';
    dragText.style.display = 'block';
    controls.style.display = 'none';
    uploadArea.onclick = function() { fileInput.click(); };
    fileInput.value = '';
    
    ticketPic.innerHTML = '';
}

// Wait for DOM to load before adding event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, adding event listeners');
    
    const avaterInput = document.getElementById('avater');
    if (avaterInput) {
        avaterInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    showImagePreview(e.target.result);
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    const btnRemove = document.getElementById('btn-remove');
    if (btnRemove) {
        btnRemove.addEventListener('click', function(e) {
            e.stopPropagation();
            resetUpload();
        });
    }
    
    const btnChange = document.getElementById('btn-change');
    if (btnChange) {
        btnChange.addEventListener('click', function(e) {
            e.stopPropagation();
            document.getElementById('avater').click();
        });
    }
});

// Event listeners moved to DOMContentLoaded above

function validateForm() {
    console.log('validateForm called');
    const fullname = document.getElementById('fullname');
    const email = document.getElementById('email');
    const github = document.getElementById('github');
    const avatar = document.getElementById('avater');
    
    console.log('Form elements:', {fullname, email, github, avatar});
    
    let isValid = true;
    
    document.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
    document.querySelectorAll('.error-message').forEach(el => el.remove());
    
    // Fixed: Target the file input directly or its container – assuming '.avater' is the class on the container
    if (!avatar.files[0]) {
        showError(document.querySelector('.avater'), 'Please upload an avatar');
        isValid = false;
    }
    
    if (!fullname.value.trim()) {
        showError(fullname, 'Please enter your full name');
        isValid = false;
    }
    
    if (!email.value.trim()) {
        showError(email, 'Please enter your email');
        isValid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
        showError(email, 'Please enter a valid email');
        isValid = false;
    }
    
    if (!github.value.trim()) { 
        showError(github, 'Please enter your username');
        isValid = false;
    }
    
    if (isValid) {
        // Get avatar as base64
        const avatarFile = avatar.files[0];
        const getBase64 = (file) => {
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => resolve(reader.result);
            });
        };

        const button = document.getElementById('button');
        button.textContent = 'Generating Ticket...';
        button.disabled = true;

        getBase64(avatarFile).then(avatarBase64 => {
            // Send data to backend
            const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            
            fetch('/api/generate-ticket', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    full_name: fullname.value.trim(),
                    email: email.value.trim(),
                    github_username: github.value.trim(),
                    avatar_base64: avatarBase64,
                    timezone: timezone
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    displayTicket(data.ticket, data.email_sent);
                } else {
                    throw new Error(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error generating ticket: ' + error.message);
                button.textContent = 'Generate My Ticket';
                button.disabled = false;
            });
        });
    }
}

function displayTicket(ticket, emailSent = false) {
    document.getElementById('jonatan').textContent = ' ' + ticket.full_name + '! ';
    document.getElementById('address').textContent = ticket.email;
    document.getElementById('ticket-name').textContent = ticket.full_name;
    document.getElementById('ticket-num').textContent = ticket.ticket_number;
    document.getElementById('ticket-username').textContent = '@' + ticket.github_username;
    
    // Generate current date and time
    const now = new Date();
    const dateOptions = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric'
    };
    const timeOptions = {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    };
    
    const currentDate = now.toLocaleDateString('en-US', dateOptions);
    const currentTime = now.toLocaleTimeString('en-US', timeOptions);
    
    document.getElementById('date').textContent = `${currentDate} at ${currentTime} / ${ticket.location || 'Military Base'}`;
    
    // Set avatar in ticket
    const ticketPic = document.getElementById('ticket-pic');
    ticketPic.innerHTML = '<img src="' + ticket.avatar_base64 + '" alt="User Avatar">';

    // Update email status message
    const emailStatus = emailSent ? 
        "We've emailed your ticket to" : 
        "Your ticket is ready! (Email sending in progress, check your inbox in a few minutes)";
    
    document.querySelector('.we').innerHTML = emailStatus + '<br><span id="address" style="word-break: break-all; max-width: 400px; display: inline-block;">' + ticket.email + '</span> and will send updates in<br>the run up to the event.';

    // Hide the .content (form section) and show congrats
    document.querySelector('.content').classList.add('hide');
    document.querySelector('.congrats').classList.add('active');
    
    // Reset button
    const button = document.getElementById('button');
    button.textContent = 'Generate My Ticket';
    button.disabled = false;
    
    console.log('✅ Ticket generated:', ticket.ticket_number);
    if (emailSent) {
        console.log('📧 Email sent successfully');
    } else {
        console.log('⚠️ Email sending failed');
    }
}

function showError(element, message) {
    element.classList.add('error');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    if (element.nextSibling) {
        element.parentNode.insertBefore(errorDiv, element.nextSibling);
    } else {
        element.parentNode.appendChild(errorDiv);
    }
}
