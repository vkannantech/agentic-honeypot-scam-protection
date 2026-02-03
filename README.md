# KannanTech Agentic Honey-Pot
### AI Scam Intelligence System

**Problem Statement:** Problem 2: Agentic Honey-Pot  
**Participant:** KannanTech  

## 🚀 Overview
This API acts as an intelligent "Honey-Pot" that accepts scam messages (SMS, Email, Social Media) and uses an agentic workflow to extract actionable intelligence:
- **Malicious URLs** (Phishing links)
- **Crypto Wallets** (Bitcoin, Ethereum, etc.)
- **Contact Info** (Phone numbers)
- **Scam Type Classification** (Phishing, Crypto Fraud, etc.)

## 🛠️ Tech Stack
- **Framework:** FastAPI (Python 3.10+)
- **Security:** API Key Authentication via `x-api-key` header
- **Deployment:** Ready for Render / Koyeb
- **Formatting:** Returns STRICT JSON format for evaluation

## 🏃‍♂️ Local Setup
1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure API Key**
   - Open `.env` and set `PARTICIPANT_API_KEY` to your secret key.
3. **Run Server**
   ```bash
   python main.py
   ```
   The server will start at `http://localhost:8000`.

## 🧪 Testing
Use `curl` or Postman to test the endpoint:

```bash
curl -X POST http://localhost:8000/evaluate \
     -H "x-api-key: YOUR_KEY_HERE" \
     -H "Content-Type: application/json" \
     -d '{"content": "Urgent! Send 1 BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa to verify your account."}'
```
