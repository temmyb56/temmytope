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

# Import email configuration from environment or config file
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS', 'olivers@email.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'Mattandrew56A@')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.mail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))

print(f"📧 Email config: {EMAIL_ADDRESS} via {SMTP_SERVER}:{SMTP_PORT}")
print(f"🔧 Using Mail.com SMTP server")

# Store tickets in memory (in production, use a database)
tickets = []
ticket_counter = 100000

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/test')
def test_endpoint():
    return jsonify({'status': 'success', 'message': 'Backend is working!'})

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

def send_ticket_email_async(ticket_data):
    """Send email in background thread"""
    try:
        print(f"🔄 Sending email to {ticket_data['email']}...")
        
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
        
        # Try Gmail
        msg = MIMEText(email_content)
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ticket_data['email']
        msg['Subject'] = f"Military Access Ticket {ticket_data['ticket_number']} Ready!"
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, ticket_data['email'], msg.as_string())
        server.quit()
        
        print(f"✅ Email sent to {ticket_data['email']}")
        
    except Exception as e:
        print(f"❌ Email failed: {str(e)}")

def send_ticket_email(ticket_data):
    """Send email synchronously to catch errors"""
    try:
        print(f"🔄 Sending email to {ticket_data['email']}...")
        print(f"📧 Using Mail.com: {EMAIL_ADDRESS} via {SMTP_SERVER}:{SMTP_PORT}")
        
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
        
        # Create email message
        msg = MIMEText(email_content)
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ticket_data['email']
        msg['Subject'] = f"Military Access Ticket {ticket_data['ticket_number']} Ready!"
        
        print(f"🔗 Connecting to Mail.com SMTP...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        print("🔐 Starting TLS...")
        server.starttls()
        print("🔑 Logging in with Mail.com credentials...")
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("📤 Sending email...")
        server.sendmail(EMAIL_ADDRESS, ticket_data['email'], msg.as_string())
        server.quit()
        
        print(f"✅ Email successfully sent to {ticket_data['email']}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Mail.com Authentication failed: {str(e)}")
        print("💡 Check your Mail.com email and password")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Email failed: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        return False

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
        
        print(f"✅ Generated ticket {ticket_number} for {data['full_name']}")
        
        return jsonify({
            'status': 'success',
            'ticket': ticket_data,
            'email_sent': email_sent
        })
        
    except Exception as e:
        print(f"❌ Error generating ticket: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/tickets', methods=['GET'])
def get_all_tickets():
    return jsonify({'tickets': tickets})

@app.route('/api/ticket/<ticket_number>', methods=['GET'])
def get_ticket(ticket_number):
    ticket = next((t for t in tickets if t['ticket_number'] == ticket_number), None)
    if ticket:
        return jsonify({'status': 'success', 'ticket': ticket})
    return jsonify({'status': 'error', 'message': 'Ticket not found'}), 404

@app.route('/api/test-email', methods=['GET', 'POST'])
def test_email():
    """Test Mail.com email functionality"""
    if request.method == 'GET':
        test_email_addr = EMAIL_ADDRESS  # Send to yourself first
    else:
        data = request.get_json() or {}
        test_email_addr = data.get('email', EMAIL_ADDRESS)
    
    test_ticket = {
        'ticket_number': 'TEST-001',
        'full_name': 'Test User',
        'email': test_email_addr,
        'github_username': 'testuser',
        'date': 'Jan 31, 2025',
        'location': 'Test Location'
    }
    
    print(f"🧪 Testing Mail.com email to: {test_email_addr}")
    success = send_ticket_email(test_ticket)
    
    return jsonify({
        'status': 'success' if success else 'error', 
        'email_sent': success,
        'test_email': test_email_addr,
        'provider': 'Mail.com',
        'smtp_server': SMTP_SERVER,
        'message': 'Check Railway logs for detailed info'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Army Ticket Generator Backend Running'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("\n🎟️ CONFERENCE TICKET GENERATOR BACKEND")
    print(f"   Running on port {port}")
    print("   Backend is ready to serve tickets!\n")
    app.run(host='0.0.0.0', port=port, debug=False)