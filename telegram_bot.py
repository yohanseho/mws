import os
import secrets
import logging
from datetime import datetime, timedelta
# Temporarily disabled due to package conflict
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Placeholder classes to prevent import errors
class Update:
    pass

class InlineKeyboardButton:
    pass

class InlineKeyboardMarkup:
    pass

class Application:
    @staticmethod
    def builder():
        return Application()
    
    def token(self, token):
        return self
    
    def build(self):
        return self

class ContextTypes:
    DEFAULT_TYPE = None
from models import db, AccessToken
from app import app

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class TokenBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup bot command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("token", self.request_token))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_text = f"""
🔐 *Selamat datang di EVM Multi Sender Token Bot!*

Halo {user.first_name}! 👋

Bot ini akan memberikan Anda token akses untuk menggunakan aplikasi EVM Multi Sender.

🎫 *Cara mendapatkan token:*
• Ketik /token untuk mendapatkan token akses baru
• Token berlaku selama 10 jam
• Satu user hanya bisa memiliki 1 token aktif

⚡ *Fitur aplikasi:*
• Import multiple private keys
• Check balances di berbagai network EVM
• Send transactions secara batch
• Support Ethereum, Sepolia, Holesky, Monad

Ketik /help untuk bantuan lebih lanjut.
        """
        
        keyboard = [
            [InlineKeyboardButton("🎫 Minta Token", callback_data="request_token")],
            [InlineKeyboardButton("📱 Buka Aplikasi", url="https://your-app-url.replit.app")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def request_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle token request"""
        user = update.effective_user
        user_id = str(user.id)
        
        try:
            with app.app_context():
                # Check if user already has an active token
                existing_token = AccessToken.query.filter_by(
                    name=f"TG_{user_id}",
                    is_active=True
                ).first()
                
                if existing_token:
                    # Check if token is still valid (not expired)
                    if existing_token.created_at + timedelta(hours=10) > datetime.utcnow():
                        remaining_time = (existing_token.created_at + timedelta(hours=10)) - datetime.utcnow()
                        hours = int(remaining_time.total_seconds() // 3600)
                        minutes = int((remaining_time.total_seconds() % 3600) // 60)
                        
                        await update.message.reply_text(
                            f"⚠️ *Token Masih Aktif!*\n\n"
                            f"🎫 Token Anda: `{existing_token.token}`\n"
                            f"⏰ Sisa waktu: {hours} jam {minutes} menit\n\n"
                            f"_Silakan gunakan token yang sudah ada._",
                            parse_mode='Markdown'
                        )
                        return
                    else:
                        # Token expired, deactivate it
                        existing_token.is_active = False
                        db.session.commit()
                
                # Generate new token
                new_token = secrets.token_urlsafe(16)
                
                # Create token record
                token_record = AccessToken()
                token_record.token = new_token
                token_record.name = f"TG_{user_id}"
                token_record.is_active = True
                token_record.created_at = datetime.utcnow()
                
                db.session.add(token_record)
                db.session.commit()
                
                # Send token to user
                success_text = f"""
✅ *Token Berhasil Dibuat!*

🎫 *Token Akses Anda:*
`{new_token}`

⏰ *Berlaku selama:* 10 jam
👤 *Untuk:* {user.first_name} ({user.username or 'No username'})

📱 *Cara menggunakan:*
1. Buka aplikasi EVM Multi Sender
2. Masukkan token di halaman login
3. Nikmati fitur aplikasi!

⚠️ *Penting:*
• Simpan token ini dengan aman
• Jangan bagikan ke orang lain
• Token akan expire otomatis setelah 10 jam

Selamat menggunakan! 🚀
                """
                
                keyboard = [
                    [InlineKeyboardButton("📱 Buka Aplikasi", url="https://your-app-url.replit.app")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    success_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
                logging.info(f"Token created for user {user_id}: {new_token[:8]}...")
                
        except Exception as e:
            logging.error(f"Error creating token for user {user_id}: {e}")
            await update.message.reply_text(
                "❌ *Terjadi kesalahan!*\n\n"
                "Gagal membuat token. Silakan coba lagi dalam beberapa saat.",
                parse_mode='Markdown'
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 *Bantuan EVM Multi Sender Bot*

📋 *Perintah yang tersedia:*
• `/start` - Memulai bot dan info welcome
• `/token` - Minta token akses baru
• `/help` - Menampilkan bantuan ini

🎫 *Tentang Token:*
• Token berlaku selama 10 jam
• Satu user = satu token aktif
• Token otomatis expire setelah 10 jam
• Token baru akan menggantikan yang lama

⚡ *Fitur Aplikasi:*
• Import multiple wallet private keys
• Check balance di berbagai network EVM
• Send transactions secara batch
• Support: Ethereum, Sepolia, Holesky, Monad

🔒 *Keamanan:*
• Token unik untuk setiap user
• Enkripsi data di database
• Session management otomatis

❓ *Butuh bantuan lebih?*
Hubungi developer: @your_telegram_username
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "request_token":
            # Redirect to token request
            await self.request_token(update, context)
    
    async def run(self):
        """Start the bot"""
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        # Keep running until stopped
        try:
            await self.application.updater.idle()
        finally:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

async def start_bot():
    """Initialize and start the bot"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logging.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    # Temporarily disabled due to package conflict
    logging.warning("Telegram bot functionality is temporarily disabled due to package conflicts")
    logging.info("To fix: Remove conflicting 'telegram' package and ensure only 'python-telegram-bot' is installed")
    print("\n" + "="*50)
    print("⚠️  TELEGRAM BOT TEMPORARILY DISABLED")
    print("="*50)
    print("Issue: Package conflict between 'telegram' and 'python-telegram-bot'")
    print("\nTo fix properly:")
    print("1. Completely remove both packages")
    print("2. Install only 'python-telegram-bot[all]'")
    print("3. Ensure no conflicting 'telegram' package is installed")
    print("="*50 + "\n")
    return
    
    # bot = TokenBot(bot_token)
    # logging.info("Starting Telegram bot...")
    # await bot.run()

if __name__ == "__main__":
    start_bot()