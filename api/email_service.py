import os
import sys
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import logging

def get_user_device_info(request):
    """Extract comprehensive device and location information from request"""
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Get IP address (handle proxy/load balancer headers)
    ip_address = (
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or
        request.headers.get('X-Real-IP', '') or
        request.remote_addr or
        'Unknown'
    )
    
    # Extract browser and OS info from user agent
    device_info = {
        'ip_address': ip_address,
        'user_agent': user_agent,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'referer': request.headers.get('Referer', 'Direct access'),
        'accept_language': request.headers.get('Accept-Language', 'Unknown'),
        'accept_encoding': request.headers.get('Accept-Encoding', 'Unknown'),
        'connection': request.headers.get('Connection', 'Unknown'),
        'host': request.headers.get('Host', 'Unknown')
    }
    
    # Parse user agent for more detailed info
    ua_lower = user_agent.lower()
    
    # Browser detection
    if 'chrome' in ua_lower and 'edg' not in ua_lower:
        device_info['browser'] = 'Chrome'
    elif 'firefox' in ua_lower:
        device_info['browser'] = 'Firefox'
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        device_info['browser'] = 'Safari'
    elif 'edg' in ua_lower:
        device_info['browser'] = 'Microsoft Edge'
    elif 'opera' in ua_lower:
        device_info['browser'] = 'Opera'
    else:
        device_info['browser'] = 'Unknown Browser'
    
    # OS detection
    if 'windows nt 10' in ua_lower:
        device_info['os'] = 'Windows 10/11'
    elif 'windows nt' in ua_lower:
        device_info['os'] = 'Windows'
    elif 'macintosh' in ua_lower or 'mac os x' in ua_lower:
        device_info['os'] = 'macOS'
    elif 'linux' in ua_lower:
        device_info['os'] = 'Linux'
    elif 'android' in ua_lower:
        device_info['os'] = 'Android'
    elif 'iphone' in ua_lower or 'ipad' in ua_lower:
        device_info['os'] = 'iOS'
    else:
        device_info['os'] = 'Unknown OS'
    
    # Device type
    if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
        device_info['device_type'] = 'Mobile'
    elif 'tablet' in ua_lower or 'ipad' in ua_lower:
        device_info['device_type'] = 'Tablet'
    else:
        device_info['device_type'] = 'Desktop'
    
    return device_info

def send_token_notification(user_identifier, token, device_info, admin_email=None):
    """Send email notification when new token is created"""
    
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    verified_email = os.environ.get('SENDGRID_FROM_EMAIL')
    
    if not sendgrid_key:
        logging.error("SENDGRID_API_KEY not found in environment variables")
        return False
    
    if not verified_email:
        logging.error("SENDGRID_FROM_EMAIL not found in environment variables")
        return False
    
    # Use verified email as both sender and recipient if admin_email not provided
    if not admin_email:
        admin_email = verified_email
    
    try:
        sg = SendGridAPIClient(sendgrid_key)
        
        # Create email content
        subject = f"🚨 Token Baru Dibuat - EVM Multi Sender"
        
        html_content = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 20px;">
            <div style="background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #dc3545; margin-bottom: 20px;">
                    🚨 Token Akses Baru Dibuat
                </h2>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                    <h3 style="color: #856404; margin: 0 0 10px 0;">📋 Informasi User</h3>
                    <p><strong>Identitas:</strong> {user_identifier}</p>
                    <p><strong>Token:</strong> <code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">{token[:8]}...{token[-4:]}</code></p>
                    <p><strong>Waktu:</strong> {device_info['timestamp']}</p>
                </div>
                
                <div style="background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                    <h3 style="color: #0c5460; margin: 0 0 10px 0;">🌐 Informasi Jaringan</h3>
                    <p><strong>IP Address:</strong> <code>{device_info['ip_address']}</code></p>
                    <p><strong>Host:</strong> {device_info['host']}</p>
                    <p><strong>Referer:</strong> {device_info['referer']}</p>
                </div>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                    <h3 style="color: #155724; margin: 0 0 10px 0;">💻 Informasi Perangkat</h3>
                    <p><strong>Browser:</strong> {device_info['browser']}</p>
                    <p><strong>Sistem Operasi:</strong> {device_info['os']}</p>
                    <p><strong>Tipe Perangkat:</strong> {device_info['device_type']}</p>
                    <p><strong>Bahasa:</strong> {device_info['accept_language']}</p>
                </div>
                
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px;">
                    <h3 style="color: #721c24; margin: 0 0 10px 0;">🔍 Detail Teknis</h3>
                    <p><strong>User Agent:</strong></p>
                    <p style="font-family: monospace; font-size: 12px; background: #e9ecef; padding: 10px; border-radius: 3px; word-break: break-all;">
                        {device_info['user_agent']}
                    </p>
                    <p><strong>Accept Encoding:</strong> {device_info['accept_encoding']}</p>
                    <p><strong>Connection:</strong> {device_info['connection']}</p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; text-align: center; color: #6c757d;">
                    <small>
                        📧 Notifikasi otomatis dari EVM Multi Sender<br>
                        🕐 Token berlaku selama 5 jam
                    </small>
                </div>
            </div>
        </div>
        """
        
        text_content = f"""
TOKEN BARU DIBUAT - EVM Multi Sender

Informasi User:
- Identitas: {user_identifier}
- Token: {token[:8]}...{token[-4:]}
- Waktu: {device_info['timestamp']}

Informasi Jaringan:
- IP Address: {device_info['ip_address']}
- Host: {device_info['host']}
- Referer: {device_info['referer']}

Informasi Perangkat:
- Browser: {device_info['browser']}
- OS: {device_info['os']}
- Tipe: {device_info['device_type']}
- Bahasa: {device_info['accept_language']}

Detail Teknis:
- User Agent: {device_info['user_agent']}
- Accept Encoding: {device_info['accept_encoding']}
- Connection: {device_info['connection']}

---
Notifikasi otomatis dari EVM Multi Sender
Token berlaku selama 5 jam
        """
        
        message = Mail(
            from_email=Email(verified_email, "EVM Multi Sender Security"),
            to_emails=To(admin_email),
            subject=subject
        )
        
        message.content = [
            Content("text/plain", text_content),
            Content("text/html", html_content)
        ]
        
        response = sg.send(message)
        logging.info(f"Token notification email sent successfully. Status: {response.status_code}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send token notification email: {str(e)}")
        return False