from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app, origins=['*'], allow_headers=['Content-Type'], methods=['GET', 'POST', 'OPTIONS'])

# Import email configuration
try:
    from email_config import EMAIL_ADDRESS, EMAIL_PASSWORD
except ImportError:
    EMAIL_ADDRESS = "ocooper830@gmail.com"
    EMAIL_PASSWORD = "qbixjsqrwrfhukoe"
    print("⚠️  Please update email_config.py with your Gmail credentials")

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

def send_ticket_email(ticket_data):
    """Simple email sender with fallback to file"""
    try:
        print(f"🔄 Sending email to {ticket_data['email']}...")
        
        # Create email content
        email_content = f"""
Hello {ticket_data['full_name']}!

🎟️ Your access Ticket is Ready!

Ticket Details:
- Ticket Number: {ticket_data['ticket_number']}
- Name: {ticket_data['full_name']}
- Username: @{ticket_data['github_username']}
- Date: {ticket_data['date']}
- Location: {ticket_data['location']}

Please keep this email as confirmation.

we will be expecting you! 🚀

Millitary agent
"""
        
        # Try Gmail first
        try:
            msg = MIMEText(email_content)
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = ticket_data['email']
            msg['Subject'] = f"Ticket {ticket_data['ticket_number']} Ready!"
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, ticket_data['email'], msg.as_string())
            server.quit()
            
            print(f"✅ Email sent via Gmail to {ticket_data['email']}")
            return True
            
        except Exception as e:
            print(f"❌ Gmail failed: {str(e)}")
        
        # Fallback: Save to file
        with open('ticket_emails.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"TO: {ticket_data['email']}\n")
            f.write(f"SUBJECT: Ticket {ticket_data['ticket_number']} Ready!\n")
            f.write(f"DATE: {datetime.now()}\n")
            f.write(f"{'='*50}\n")
            f.write(email_content)
            f.write(f"\n{'='*50}\n")
        
        print(f"📁 Email saved to ticket_emails.txt for {ticket_data['email']}")
        return True
        
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
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