from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json
import os
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()

# Environment variables (with fallbacks from your working code)
token: Final = os.getenv("BOT_TOKEN", "8342320373:AAF6md0l1JCHigJBgcL5w5MPrLKSN4J0eew")
bot_name: Final = "@explainmelikeIm5_bot"
api_key: Final = os.getenv("API_KEY", "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")
PORT = int(os.getenv("PORT", 8080))

# Flask app for webhook
app = Flask(__name__)
telegram_app = None

@app.route('/webhook', methods=['POST'])
def webhook():
    """Simple webhook handler"""
    try:
        json_data = request.get_json()
        if json_data and telegram_app:
            update = Update.de_json(json_data, telegram_app.bot)
            
            # Use threading to avoid event loop conflicts
            import threading
            def process_update():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(telegram_app.process_update(update))
                finally:
                    loop.close()
            
            thread = threading.Thread(target=process_update)
            thread.daemon = True
            thread.start()
            
        return 'OK'
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'OK'

@app.route('/')
def health():
    return 'Bot is running! 🤖'

# Your original working commands (unchanged!)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Hello! I am {bot_name}. What do you want to know today?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 Hi! I'm your friendly explanation bot! Here's what I can do:

📝 **Commands:**
• `/start` - Say hello and get started
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
    # Get the text after the command
    message_text = update.message.text
    question = message_text.replace("/explain", "").strip()
    
    if not question:
        await update.message.reply_text("Please ask me something! For example: /explain <question>")
        return
    
    try:
        # Call OpenRouter AI to explain like you're 5
        ai_response = get_explanation(question)
        await update.message.reply_text(ai_response)
    except Exception as e:
        print(f"Error getting AI explanation: {e}")
        await update.message.reply_text("Sorry, I'm having trouble thinking right now. Please try again later!")

# Your original working AI function (unchanged!)
def get_explanation(question: str) -> str:
    """Get AI explanation for a question using OpenRouter API"""
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
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
        })
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return "Sorry, I couldn't think any way to explain to 5 year old, come again when your are bit older. Till then try asking something else!"
            
    except Exception as e:
        print(f"Error calling AI API: {e}")
        return "Oops! My brain is leaking fluid everywhere, I'll come back to you later!"

# Your original working helper functions (unchanged!)
def is_question_word(text: str, question_words: list) -> bool:
    for word in question_words:
        if word in text.lower():
            return True
    return False

def ends_with_questionmark(text: str) -> bool:
    return text.strip().endswith("?")

def handle_response(text: str) -> str:
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

# Your original working message handler (unchanged!)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"user ({update.message.chat.id}) in {message_type}: '{text}'")

    if message_type in ['group', 'supergroup']:
        # Only respond if bot is mentioned
        if bot_name in text:
            # Remove bot name and get the actual question
            new: str = text.replace(bot_name, "").strip()
            
            # Check if it's actually a question to explain
            question_words = ["what", "why", "how", "when", "where", "who", "which", "can you explain", "can you tell me", "tell me about", "explain", "describe", "elaborate"]
            
            if is_question_word(new, question_words) or ends_with_questionmark(new):
                try:
                    response: str = get_explanation(new)
                except Exception as e:
                    print(f"Error getting AI response: {e}")
                    response = "I'm having trouble thinking right now. Try using /explain for better explanations!"
            elif "hi" in new.lower() or "hello" in new.lower():
                response = "Hi there! 👋 Ask me something fun, and I'll explain it like you're 5!"
            else:
                response = f"Hi! I can explain things for you. Just mention me with a question like: {bot_name} explain gravity"
        else:
            return 
    else:
        # In private chats, work normally
        response: str = handle_response(text)

    print('bot:', response)
    await update.message.reply_text(response)

async def err(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")
    await update.message.reply_text("This is beyond my comprehension, please try again later.")

# Simple setup function
async def setup_telegram_bot():
    global telegram_app
    telegram_app = Application.builder().token(token).build()
    
    # Add your original handlers
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("explain", explain_command))
    telegram_app.add_handler(MessageHandler(filters.TEXT, handle_message))
    telegram_app.add_error_handler(err)
    
    # Initialize
    await telegram_app.initialize()
    await telegram_app.start()
    
    # Set webhook
    render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if render_hostname:
        webhook_url = f"https://{render_hostname}/webhook"
    else:
        webhook_url = "https://bot-jxdu.onrender.com/webhook"  # Your current URL
    
    await telegram_app.bot.set_webhook(webhook_url)
    print(f"Webhook set to: {webhook_url}")

if __name__ == "__main__":
    print("Starting bot...")
    
    # Setup telegram bot
    import asyncio
    asyncio.run(setup_telegram_bot())
    
    print("Bot is ready to receive messages...")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=PORT)
