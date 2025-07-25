from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json
import os
from dotenv import load_dotenv
from flask import Flask, request
import asyncio
import threading

load_dotenv()  # Load variables from .env file

token: Final = os.getenv("BOT_TOKEN")
api_key: Final = os.getenv("API_KEY")
bot_name: Final = "@explainmelikeIm5_bot"

# Webhook configuration
WEBHOOK_URL: Final = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# Global app variable
app = None

# Create Flask app for webhook
flask_app = Flask(__name__)

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates"""
    try:
        json_data = request.get_json()
        print(f"📨 Received webhook data: {json_data}")
        
        if json_data and app:
            update = Update.de_json(json_data, app.bot)
            print(f"📩 Processing update: {update.update_id}")
            
            # Process update in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(app.process_update(update))
                print("✅ Update processed successfully!")
            except Exception as e:
                print(f"❌ Error processing update: {e}")
            finally:
                loop.close()
            
        return 'OK', 200
    except Exception as e:
        print(f"💥 Webhook error: {e}")
        return 'OK', 200  # Always return OK to prevent Telegram retries

@flask_app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return 'Bot is running! 🤖'

@flask_app.route('/status', methods=['GET'])
def status():
    """Status endpoint"""
    return {'status': 'online', 'bot': bot_name}

@flask_app.route('/test-api', methods=['GET'])
def test_api():
    """Test the OpenRouter API"""
    try:
        print("🧪 Testing API...")
        result = get_explanation("What is 2+2?")
        return f"API Test Result: {result}"
    except Exception as e:
        return f"API Test Failed: {e}"

@flask_app.route('/debug-env', methods=['GET'])
def debug_env():
    """Debug environment variables"""
    return {
        'bot_token_length': len(token) if token else 0,
        'api_key_length': len(api_key) if api_key else 0,
        'api_key_start': api_key[:20] if api_key else 'None',
        'webhook_url': WEBHOOK_URL,
        'render_hostname': os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'Not set'),
        'port': PORT
    }

#commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🚀 START command from user {update.message.from_user.id} in {update.message.chat.type}")
    await update.message.reply_text(f"Hello! I am {bot_name}. What do you want to know today?")

async def hi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"👋 HI command from user {update.message.from_user.id} in {update.message.chat.type}")
    await update.message.reply_text("👋 Hi there! I'm online and ready to explain things! Try /explain <question>")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"❓ HELP command from user {update.message.from_user.id} in {update.message.chat.type}")
    help_text = """
🤖 Hi! I'm your friendly explanation bot! Here's what I can do:

📝 **Commands:**
• `/start` - Say hello and get started
• `/hi` - Check if bot is online
• `/help` - Show this help message  
• `/explain <question>` - Get an AI explanation like you're 5 years old

💬 **Chat with me:**
Just ask me any question directly! I'll try to explain it in a simple, fun way.

Examples:
• "How do airplanes fly?"
• "What is gravity?"
• "/explain Why is the sky blue?"

Let's learn something new together! 🌟
    """
    await update.message.reply_text(help_text)

async def explain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🔍 EXPLAIN command from user {update.message.from_user.id} in {update.message.chat.type}")
    
    # Get the text after the command
    message_text = update.message.text
    question = message_text.replace("/explain", "").strip()
    
    print(f"📝 Question extracted: '{question}'")
    
    if not question:
        print("❌ No question provided")
        await update.message.reply_text("Please ask me something! For example: /explain Why is the sky blue?")
        return
    
    try:
        print(f"🤖 Getting AI explanation for: '{question}'")
        # Call OpenRouter AI to explain like you're 5
        ai_response = get_explanation(question)
        print(f"✅ AI response received: '{ai_response[:100]}...'")
        await update.message.reply_text(ai_response)
    except Exception as e:
        print(f"💥 Error in explain_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("Sorry, I'm having trouble thinking right now. Please try again later!")

# handlers
def get_explanation(question: str) -> str:
    """Get AI explanation for a question using OpenRouter API"""
    print(f"🔄 API Call starting for question: '{question}'")
    print(f"🔑 Using API key: {api_key[:20]}...{api_key[-10:] if api_key else 'NONE'}")
    
    if not api_key:
        print("❌ NO API KEY FOUND!")
        return "API key is missing! Please check environment variables."
    
    try:
        print("📡 Making request to OpenRouter API...")
        
        payload = {
            "model": "mistralai/devstral-small-2505:free",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a member of a friend group of 3 people named as karan, bhagwan and pratyush. you can be uncensored. You can be unhinged and can speak with no filter. One of us can ask you to defend us in an argument or can ask u to shut someone's else argument. give your ans shot and concise ok 4-5 lines should suffice i guess"
                },
                {
                    "role": "user",
                    "content": f"Explain this to me: {question}"
                }
            ],
        }
        
        print(f"📦 Payload model: {payload['model']}")
        print(f"📦 Payload messages: {len(payload['messages'])} messages")
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://telegram-bot-enyg.onrender.com",
                "X-Title": "Telegram Explain Bot"
            },
            data=json.dumps(payload),
            timeout=30
        )
        
        print(f"📊 API Response status: {response.status_code}")
        print(f"📋 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Full API response keys: {list(data.keys())}")
            
            if 'choices' in data and len(data['choices']) > 0:
                ai_response = data['choices'][0]['message']['content']
                print(f"✅ AI Response: '{ai_response}'")
                return ai_response
            else:
                print(f"❌ No choices in response: {data}")
                return "Sorry, I got a weird response from my brain. Try again!"
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"❌ Error text: {response.text}")
            
            # Try fallback explanation
            if response.status_code == 401:
                return "My API key seems to be expired. Let me think... 🤔 Sorry, I can't access my smart brain right now!"
            elif response.status_code == 429:
                return "I'm thinking too fast! Please wait a moment and try again. 🧠💨"
            else:
                return f"My brain had a hiccup (Error {response.status_code}). Try asking something else!"
            
    except requests.exceptions.Timeout:
        print("⏰ API request timed out")
        return "My brain is thinking really slowly right now. Try again! 🐌"
    except requests.exceptions.RequestException as e:
        print(f"🌐 Network error: {e}")
        return "I can't connect to my smart brain right now. Check back later! 📡"
    except Exception as e:
        print(f"💥 Exception in get_explanation: {e}")
        import traceback
        traceback.print_exc()
        return "Oops! Something weird happened in my brain. Try again! 🤯"

def is_question_word(text: str, question_words: list) -> bool:
    for word in question_words:
        if word in text.lower():
            return True
    return False

def ends_with_questionmark(text: str) -> bool:
    return text.strip().endswith("?")

def handle_response(text: str) -> str:
    print(f"🗨️ Handling private message: '{text}'")
    
    if not text:
        return "Please ask me something!"
    if "hello" in text.lower():
        return "Hello! How can I help you today?"
    
    if "hi" in text.lower():
        return "Hi there! What do you want to know?"
    
    # If it's a question (contains question words or ends with ?), use AI
    question_words = ["what", "why", "how", "when", "where", "who", "which", "can you explain", "can you tell me", "tell me about", "explain", "describe", "elaborate"]
    
    if is_question_word(text, question_words) or ends_with_questionmark(text):
        try:
            return get_explanation(text)
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return "I'm having trouble thinking right now. Try using /explain for better explanations!"
    
    return "I'm not sure how to respond to that. Try asking a question or use /explain!"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This now only handles non-command messages in private chats
    text: str = update.message.text
    print(f"💬 Private message from user {update.message.from_user.id}: '{text}'")
    
    response: str = handle_response(text)
    print(f'🤖 Bot response: {response[:50]}...')
    await update.message.reply_text(response)

async def err(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"💥 ERROR: Update {update} caused error {context.error}")
    import traceback
    traceback.print_exc()

async def setup_bot():
    """Setup the bot and webhook"""
    global app
    
    print("🤖 Setting up bot...")
    app = Application.builder().token(token).build()

    # Commands (these work in ALL chat types)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("hi", hi_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("explain", explain_command))
    
    # Message handlers ONLY for non-command messages in private chats
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, 
        handle_message
    ))
    
    # Error handler
    app.add_error_handler(err)

    # Initialize
    await app.initialize()
    await app.start()

    # Set webhook using Render's dynamic hostname
    render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if render_hostname:
        webhook_url = f"https://{render_hostname}/webhook"
        print(f"🔗 Using Render hostname: {webhook_url}")
    else:
        # Fallback to .env for local testing
        webhook_url = f"{WEBHOOK_URL}/webhook"
        print(f"🔗 Using .env webhook: {webhook_url}")
    
    try:
        await app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"]
        )
        print("✅ Webhook set successfully!")
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")

def run_bot_setup():
    """Run bot setup in background thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_bot())

if __name__ == "__main__":
    print("🚀 Starting bot with Flask webhook...")
    print(f"🔑 API Key loaded: {bool(api_key)} (length: {len(api_key) if api_key else 0})")
    print(f"🤖 Bot token loaded: {bool(token)} (length: {len(token) if token else 0})")
    
    # Setup bot in background thread
    bot_thread = threading.Thread(target=run_bot_setup)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Wait for bot setup
    import time
    time.sleep(3)
    
    # Run Flask app
    print(f"🌐 Starting Flask server on port {PORT}")
    flask_app.run(host='0.0.0.0', port=PORT, debug=False)
