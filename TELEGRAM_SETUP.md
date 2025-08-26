# 🚀 Telegram Bot Integration Setup

## ⚡ **It's Super Easy! Here's How:**

### **1. Create Telegram Bot (2 minutes):**
1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Choose a name for your bot (e.g., "Visa Consultant Bot")
4. Choose a username (e.g., "visa_consultant_bot")
5. **Save the bot token** - You'll need this!

### **2. Add Bot Token to GitHub Secrets:**
1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Add new secret: `TELEGRAM_BOT_TOKEN`
3. Value: Your bot token from BotFather

### **3. Deploy Your Code:**
- Push the changes (already done!)
- GitHub Actions will deploy automatically
- Your bot will be available at: `https://your-backend-url.com/telegram/webhook`

### **4. Set Telegram Webhook (1 minute):**
Visit this URL in your browser:
```
https://your-backend-url.com/telegram/set-webhook?bot_token=YOUR_BOT_TOKEN&webhook_url=https://your-backend-url.com/telegram/webhook
```

### **5. Test Your Bot:**
1. Find your bot on Telegram (by username)
2. Send a message like: "Hi, my name is John and I want to study in USA. My email is john@email.com"
3. **Your bot will:**
   - ✅ Respond with visa information
   - ✅ Save the lead to Supabase
   - ✅ Send you an email notification
   - ✅ Remember the conversation

## 🎯 **What You Get:**

### **✅ Full Integration:**
- **Same AI responses** as your website
- **Same lead capture** system
- **Same email notifications**
- **Persistent sessions** (Telegram users stay logged in)
- **Custom keyboard** with country options

### **✅ Telegram Features:**
- **Inline keyboards** for easy navigation
- **HTML formatting** for better responses
- **Session persistence** across restarts
- **User-friendly interface**

## 🔧 **Technical Details:**

### **Endpoints Created:**
- `POST /telegram/webhook` - Receives messages from Telegram
- `GET /telegram/set-webhook` - Sets up webhook with Telegram
- `GET /telegram/bot-info` - Gets bot information

### **Session Management:**
- Telegram users get persistent sessions
- Website users get temporary sessions
- All leads are saved to the same Supabase table

### **Security:**
- Webhook validation
- User session isolation
- Secure token handling

## 🚀 **Ready to Go!**

**Your Telegram bot will work exactly like your website chatbot:**
- Same AI responses
- Same lead capture
- Same email notifications
- Same database storage

**Just push the code and follow the 5 steps above!** 🎉

## 📱 **Example User Flow:**

1. **User finds your bot** on Telegram
2. **User sends:** "Hi, I want to study in USA. My name is Sarah and email is sarah@email.com"
3. **Bot responds:** Helpful visa information + saves lead
4. **You get email:** New lead notification with Sarah's details
5. **User continues chatting:** Bot remembers their preferences

**It's that simple!** 🎯
