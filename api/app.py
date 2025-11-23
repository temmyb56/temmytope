from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading

app = Flask(__name__)
CORS(app, origins=['*'], allow_headers=['Content-Type'], methods=['GET', 'POST', 'OPTIONS'])

# Gmail configuration
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS', 'Matttingle18@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'ertbsrcfqfftceml')
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# Store tickets in memory (in production, use a database)
tickets = []
ticket_counter = 100000

@app.route('/')
def serve_index():
    return jsonify({'status': 'success', 'message': 'Military Ticket Generator API'})

@app.route('/test')
def test_endpoint():
    return jsonify({'status': 'success', 'message': 'Backend is working!'})

def send_ticket_email_async(ticket_data):
    """Send email in background thread"""
    try:
        # Create email content
        email_content = f"""
Hello {ticket_data['full_name']}!

🎟️ Your Military Access Ticket is Ready!

Ticket Details:
- Ticket Number: {ticket_data['ticket_number']}
- Name: {ticket_data['full_name']}
- Username: @{ticket_data['github_username']}
- Date: {ticket_data['date']}
- Location: {ticket_data['location']}

Please keep this email as confirmation.

We will be expecting you! 🚀

Military Security Team
"""
        
        msg = MIMEText(email_content)
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ticket_data['email']
        msg['Subject'] = f"Military Access Ticket {ticket_data['ticket_number']} Ready!"
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, ticket_data['email'], msg.as_string())
        server.quit()
        
    except Exception as e:
        print(f"❌ Email failed: {str(e)}")

def send_ticket_email(ticket_data):
    """Start email sending in background thread"""
    email_thread = threading.Thread(target=send_ticket_email_async, args=(ticket_data,))
    email_thread.daemon = True
    email_thread.start()
    return True

@app.route('/api/generate-ticket', methods=['POST', 'OPTIONS'])
def generate_ticket():
    if request.method == 'OPTIONS':
        return '', 200
    global ticket_counter
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['full_name', 'email', 'github_username', 'avatar_base64']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'status': 'error', 'message': f'Missing {field}'}), 400
        
        # Generate unique ticket number
        ticket_number = f"TKT-{str(ticket_counter).zfill(6)}"
        ticket_counter += 1
        
        # Get user's timezone info
        timezone = data.get('timezone', 'UTC')
        location_map = {
            'America/New_York': 'New York, NY',
            'America/Los_Angeles': 'Los Angeles, CA',
            'America/Chicago': 'Chicago, IL',
            'Europe/London': 'London, UK',
            'Europe/Paris': 'Paris, France',
            'Asia/Tokyo': 'Tokyo, Japan',
            'Australia/Sydney': 'Sydney, Australia'
        }
        location = location_map.get(timezone, 'Military Base')
        
        # Create ticket data
        ticket_data = {
            'ticket_number': ticket_number,
            'full_name': data['full_name'],
            'email': data['email'],
            'github_username': data['github_username'].replace('@', ''),
            'avatar_base64': data['avatar_base64'],
            'location': location,
            'date': 'Jan 31, 2025',
            'created_at': datetime.now().isoformat()
        }
        
        # Store ticket
        tickets.append(ticket_data)
        
        # Send email to user
        email_sent = send_ticket_email(ticket_data)
        
        return jsonify({
            'status': 'success',
            'ticket': ticket_data,
            'email_sent': email_sent
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/test-email', methods=['POST'])
def test_email():
    """Test email functionality"""
    data = request.get_json()
    test_email = data.get('email', 'test@example.com')
    
    test_ticket = {
        'ticket_number': 'TEST-001',
        'full_name': 'Test User',
        'email': test_email,
        'github_username': 'testuser',
        'date': 'Jan 31, 2025',
        'location': 'Test Location'
    }
    
    success = send_ticket_email(test_ticket)
    return jsonify({'status': 'success' if success else 'error', 'email_sent': success})

if __name__ == '__main__':
    app.run(debug=True)