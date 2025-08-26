import os
import logging
import asyncio
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.middleware.proxy_fix import ProxyFix
from blockchain import BlockchainService
from models import db, AccessToken, UserSession
from datetime import timedelta
from email_service import send_token_notification, get_user_device_info

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Initialize blockchain service
blockchain_service = BlockchainService()

# Create tables and default tokens
with app.app_context():
    db.create_all()
    
    # Create default tokens if they don't exist
    if not AccessToken.query.first():
        default_tokens = [
            {'token': 'admin123', 'name': 'Admin Token'},
            {'token': 'user456', 'name': 'User Token'},
            {'token': secrets.token_urlsafe(32), 'name': 'Secure Token'}
        ]
        
        for token_data in default_tokens:
            token = AccessToken()
            token.token = token_data['token']
            token.name = token_data['name']
            db.session.add(token)
        
        db.session.commit()
        logging.info("Default access tokens created")

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def is_authenticated():
    """Check if user is authenticated"""
    session_id = session.get('session_id')
    if not session_id:
        return False
    
    user_session = UserSession.query.filter_by(session_id=session_id).first()
    if not user_session or user_session.is_expired():
        session.clear()
        return False
    
    # Also check if the underlying token is still valid
    if user_session.token.is_expired():
        session.clear()
        return False
    
    return True

@app.route('/')
def index():
    """Landing page or main app"""
    if is_authenticated():
        return render_template('index.html')
    else:
        # Show landing page for unauthenticated users
        return render_template('landing.html', bot_username='your_bot_username')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Token-based login page"""
    if request.method == 'POST':
        token = request.form.get('token')
        if not token:
            flash('Token diperlukan', 'error')
            return render_template('login.html')
        
        # Verify token
        access_token = AccessToken.query.filter_by(token=token, is_active=True).first()
        if not access_token or access_token.is_expired():
            flash('Token tidak valid atau sudah expired', 'error')
            return render_template('login.html')
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=5)
        
        user_session = UserSession()
        user_session.session_id = session_id
        user_session.token_id = access_token.id
        user_session.expires_at = expires_at
        
        # Update token last used
        access_token.last_used = datetime.utcnow()
        
        db.session.add(user_session)
        db.session.commit()
        
        # Set session
        session['session_id'] = session_id
        
        flash('Login berhasil!', 'success')
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session_id = session.get('session_id')
    if session_id:
        UserSession.query.filter_by(session_id=session_id).delete()
        db.session.commit()
    
    session.clear()
    flash('Logout berhasil', 'info')
    return redirect(url_for('login'))

@app.route('/import_keys', methods=['POST'])
@require_auth
def import_keys():
    """Import private keys from uploaded file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Tidak ada file yang diupload'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Tidak ada file yang dipilih'}), 400
        
        # Read file content
        content = file.read().decode('utf-8')
        private_keys = []
        
        # Parse private keys line by line
        for line in content.strip().split('\n'):
            line = line.strip()
            if line:
                # Remove 0x prefix if present
                if line.startswith('0x'):
                    line = line[2:]
                
                # Validate hex format (64 characters)
                if len(line) == 64 and all(c in '0123456789abcdefABCDEF' for c in line):
                    private_keys.append('0x' + line)
                else:
                    logging.warning(f"Invalid private key format: {line[:10]}...")
        
        if not private_keys:
            return jsonify({'error': 'Tidak ditemukan private key yang valid dalam file'}), 400
        
        # Generate wallet addresses
        wallets = []
        for pk in private_keys:
            try:
                address = blockchain_service.get_address_from_private_key(pk)
                wallets.append({
                    'private_key': pk,
                    'address': address
                })
            except Exception as e:
                logging.error(f"Error generating address for private key: {e}")
                continue
        
        # Store in session (temporary, not persistent)
        session['wallets'] = wallets
        
        return jsonify({
            'success': True,
            'wallets': [{'address': w['address']} for w in wallets],
            'count': len(wallets)
        })
        
    except Exception as e:
        logging.error(f"Error importing keys: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_balances', methods=['POST'])
@require_auth
def get_balances():
    """Get balances for all wallets on selected network"""
    try:
        data = request.get_json()
        network_config = data.get('network')
        
        if not network_config:
            return jsonify({'error': 'Konfigurasi jaringan diperlukan'}), 400
        
        wallets = session.get('wallets', [])
        if not wallets:
            return jsonify({'error': 'Tidak ada wallet yang diimpor'}), 400
        
        # Get balances for all wallets
        balances = asyncio.run(blockchain_service.get_balances_async(
            [w['address'] for w in wallets], 
            network_config
        ))
        
        return jsonify({
            'success': True,
            'balances': balances
        })
        
    except Exception as e:
        logging.error(f"Error getting balances: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/send_transactions', methods=['POST'])
@require_auth
def send_transactions():
    """Send transactions from all wallets"""
    try:
        data = request.get_json()
        network_config = data.get('network')
        percentage = data.get('percentage')
        recipient_address = data.get('recipient_address')
        
        if not all([network_config, percentage, recipient_address]):
            return jsonify({'error': 'Parameter yang diperlukan tidak lengkap'}), 400
        
        wallets = session.get('wallets', [])
        if not wallets:
            return jsonify({'error': 'Tidak ada wallet yang diimpor'}), 400
        
        # Send transactions
        results = asyncio.run(blockchain_service.send_transactions_async(
            wallets, network_config, percentage, recipient_address
        ))
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logging.error(f"Error sending transactions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear_session', methods=['POST'])
@require_auth
def clear_session():
    """Clear session data (wallets)"""
    session.clear()
    return jsonify({'success': True})

@app.route('/request_token', methods=['GET', 'POST'])
def request_token():
    """Request new access token page"""
    if request.method == 'POST':
        user_identifier = request.form.get('user_identifier', '').strip()
        
        if not user_identifier:
            flash('Identitas pengguna diperlukan (email, username, atau nama)', 'error')
            return render_template('request_token.html')
        
        if len(user_identifier) < 3:
            flash('Identitas pengguna minimal 3 karakter', 'error')
            return render_template('request_token.html')
        
        try:
            # Deactivate old tokens for this user
            old_tokens = AccessToken.query.filter(
                AccessToken.name.like(f'USER_{user_identifier}_%'),
                AccessToken.is_active == True
            ).all()
            
            for old_token in old_tokens:
                old_token.is_active = False
            
            # Generate new token
            new_token = secrets.token_urlsafe(24)
            
            # Create token record with 5 hour expiration
            token_record = AccessToken()
            token_record.token = new_token
            token_record.name = f'USER_{user_identifier}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}'
            token_record.is_active = True
            token_record.created_at = datetime.utcnow()
            token_record.expires_at = datetime.utcnow() + timedelta(hours=5)
            
            db.session.add(token_record)
            db.session.commit()
            
            # Send notification email with device info
            try:
                device_info = get_user_device_info(request)
                # Gunakan email yang sudah diverifikasi di SendGrid
                admin_email = os.environ.get("ADMIN_EMAIL") or os.environ.get("SENDGRID_FROM_EMAIL", "your-email@example.com")
                
                send_token_notification(user_identifier, new_token, device_info, admin_email)
                logging.info(f"Token notification sent for user: {user_identifier}")
            except Exception as e:
                logging.error(f"Failed to send token notification: {e}")
            
            flash('Token berhasil dibuat! Salin token di bawah dan simpan dengan aman.', 'success')
            return render_template('request_token.html', 
                                 new_token=new_token, 
                                 user_identifier=user_identifier,
                                 expires_at=(datetime.utcnow() + timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S UTC'))
        
        except Exception as e:
            logging.error(f"Error creating token: {e}")
            flash('Terjadi kesalahan saat membuat token. Coba lagi.', 'error')
            return render_template('request_token.html')
    
    return render_template('request_token.html')

@app.route('/admin/config', methods=['GET', 'POST'])
@require_auth
def admin_config():
    """Admin configuration page"""
    if request.method == 'POST':
        admin_email = request.form.get('admin_email', '').strip()
        if admin_email:
            # For demo, we'll just show success. In production, you'd store this in database
            flash(f'Email admin diupdate ke: {admin_email}', 'success')
            # You can save to database or environment here
        else:
            flash('Email admin tidak boleh kosong', 'error')
    
    current_email = os.environ.get("ADMIN_EMAIL", "diltaaja41@gmail.com")
    return render_template('admin_config.html', admin_email=current_email)

@app.route('/admin/tokens')
@require_auth
def view_tokens():
    """View active tokens (admin only)"""
    tokens = AccessToken.query.filter_by(is_active=True).order_by(AccessToken.created_at.desc()).all()
    return jsonify({
        'tokens': [{
            'id': token.id,
            'name': token.name,
            'token': token.token[:8] + '...' if len(token.token) > 8 else token.token,
            'last_used': token.last_used.isoformat() if token.last_used else None,
            'created_at': token.created_at.isoformat(),
            'expires_at': token.expires_at.isoformat() if token.expires_at else None,
            'is_expired': token.is_expired()
        } for token in tokens]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
