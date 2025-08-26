#!/usr/bin/env python3
"""
Script to run the Telegram bot
"""
import os
import sys
import asyncio
from telegram_bot import start_bot

async def main():
    """Main function to start the bot"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN not found in environment variables")
        print("Please add your bot token to Replit Secrets")
        return
    
    print("Starting Telegram bot...")
    print("Bot will run continuously")
    print("Use Ctrl+C to stop")
    
    try:
        await start_bot()
    except KeyboardInterrupt:
        print("\nStopping bot...")
    except Exception as e:
        print(f"Bot error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error running bot: {e}")