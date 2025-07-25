from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json

import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

token: Final = os.getenv("BOT_TOKEN")
api_key: Final = os.getenv("API_KEY")
bot_name: Final = "@explainmelikeIm5_bot"

#commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Hello! I am {bot_name}. What do you want to know today?")

async def hi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi there! I'm online and ready to explain things! Try /explain <question>")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    # Get the text after the command
    message_text = update.message.text
    question = message_text.replace("/explain", "").strip()
    
    if not question:
        await update.message.reply_text("Please ask me something! For example: /explain Why is the sky blue?")
        return
    
    try:
        # Call OpenRouter AI to explain like you're 5
        ai_response = get_explanation(question)
        await update.message.reply_text(ai_response)
    except Exception as e:
        print(f"Error getting AI explanation: {e}")
        await update.message.reply_text("Sorry, I'm having trouble thinking right now. Please try again later!")

# handlers
def get_explanation(question: str) -> str:
    """Get AI explanation for a question using OpenRouter API"""
    print(f"🔄 API Call starting for question: '{question}'")
    
    try:
        print("📡 Making request to OpenRouter API...")
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
        
        print(f"📊 API Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response received successfully!")
            # print(data)
            ai_response = data['choices'][0]['message']['content']
            print(f"✅ AI Response: '{ai_response}'")
            return ai_response
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return "Sorry, I couldn't explain that right now. Try asking something else!"
            
    except Exception as e:
        print(f"💥 Exception in get_explanation: {e}")
        return "Oops! My brain is having trouble right now. Try again later!"

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"user ({update.message.chat.id}) in {message_type}: '{text}'")

    # Simple logic: work in private chats, ignore groups unless it's a command
    if message_type == 'private':
        response: str = handle_response(text)
        print('bot:', response)
        await update.message.reply_text(response)

async def err(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

if __name__ == "__main__":
    print("Starting bot...")
    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("hi", hi_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("explain", explain_command))

    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Error handler
    app.add_error_handler(err)

    print("Bot is ready to receive messages...")
    app.run_polling(poll_interval=3)
