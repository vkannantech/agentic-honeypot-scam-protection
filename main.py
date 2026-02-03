import os
import re
import secrets
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Header, HTTPException, Body, Depends
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="KannanTech Agentic Honey-Pot",
    description="AI-powered Scam Intelligence Extraction API for India AI Impact Buildathon",
    version="1.0.0"
)

# --- CONFIGURATION ---
# Get API Key from environment variable or generate a temporary one for local testing
API_KEY_SECRET = os.getenv("PARTICIPANT_API_KEY")
if not API_KEY_SECRET:
    print("WARNING: PARTICIPANT_API_KEY not found in .env. Using temporary key for dev.")
    # In production, this should cause an error, but for setup we allow flow.
    API_KEY_SECRET = "temp_key_dev_mode"

# --- DATA MODELS ---
class ScamInput(BaseModel):
    message_id: Optional[str] = Field(None, description="Unique ID of the message")
    content: str = Field(..., description="The scam message text to analyze")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata like sender, timestamp")

class ExtractedIntelligence(BaseModel):
    urls: List[str]
    crypto_addresses: List[str]
    phones: List[str]
    threat_level: str
    scam_type: str
    sentiment: str

class AnalysisResponse(BaseModel):
    status: str
    message_id: Optional[str]
    extracted_intelligence: ExtractedIntelligence

# --- INTELLIGENCE EXTRACTION ENGINE ---
class IntelligenceEngine:
    def __init__(self):
        # --- 1. PATTERNS ---
        self.patterns = {
            'url': r'(?:https?://|www\.|[a-zA-Z0-9-]+\.(?:com|net|org|io|biz|info|xyz|top))[^\s]*',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            'crypto_btc': r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b',
            'crypto_eth': r'\b0x[a-fA-F0-9]{40}\b',
            'crypto_tron': r'\bT[A-Za-z0-9]{33}\b',
            'crypto_sol': r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b',
        }

        # --- 2. KEYWORD WEIGHING ---
        # Format: (Keyword, Score_Weight, Category_Tag)
        self.keywords = [
            # Urgency & Pressure
            ('urgent', 15, 'urgency'), ('immediately', 15, 'urgency'), ('act now', 15, 'urgency'), 
            ('suspend', 20, 'threat'), ('restrict', 20, 'threat'), ('expire', 10, 'threat'),
            
            # Financial & Crypto
            ('bitcoin', 10, 'crypto'), ('btc', 10, 'crypto'), ('ethereum', 10, 'crypto'), ('usdt', 10, 'crypto'),
            ('wallet', 10, 'crypto'), ('mining', 15, 'crypto'), ('investment', 10, 'finance'), ('profit', 15, 'finance'),
            ('withdrawal', 10, 'finance'), ('deposit', 10, 'finance'), ('yield', 10, 'finance'),
            
            # Phishing & Security
            ('verify', 15, 'phishing'), ('login', 10, 'phishing'), ('password', 20, 'phishing'), 
            ('security alert', 20, 'phishing'), ('unusual activity', 15, 'phishing'), ('kyc', 10, 'phishing'),
            
            # Compensation / Lottery
            ('lottery', 25, 'spam'), ('prize', 25, 'spam'), ('winner', 25, 'spam'), ('compensation', 20, 'spam'),
            ('fund', 10, 'finance'), ('claim', 15, 'spam'),
            
            # Romance / Social Engineering
            ('dear friend', 5, 'spam'), ('my love', 10, 'romance'), ('kindly', 5, 'spam')
        ]

    def analyze(self, text: str) -> ExtractedIntelligence:
        text_lower = text.lower()
        risk_score = 0
        detected_categories = []
        
        # 1. Entity Extraction
        urls = list(set(re.findall(self.patterns['url'], text, re.IGNORECASE)))
        phones = list(set(re.findall(self.patterns['phone'], text)))
        
        # Crypto Extraction
        wallets = []
        crypto_types = set()
        for name, pattern in [('BTC', 'crypto_btc'), ('ETH', 'crypto_eth'), ('TRON', 'crypto_tron'), ('SOL', 'crypto_sol')]:
            found = list(set(re.findall(self.patterns[pattern], text)))
            if found:
                wallets.extend(found)
                crypto_types.add(name)
        
        # 2. Risk Scoring - Entities
        if urls: risk_score += 25
        if wallets: risk_score += 40
        if phones: risk_score += 15
        
        # 3. Risk Scoring - Keywords
        for word, score, category in self.keywords:
            if word in text_lower:
                risk_score += score
                detected_categories.append(category)
        
        # 4. Heuristics
        # Caps Ratio (Shouting)
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if caps_ratio > 0.25 and len(text) > 20: 
            risk_score += 10
            detected_categories.append("shouting")
            
        # Punctuation spam
        if "!!" in text or "??" in text:
            risk_score += 10
            
        # Normalize Score (Cap at 100)
        risk_score = min(risk_score, 100)
        
        # 5. Classification Logic
        threat_level = "Low"
        if risk_score > 75: threat_level = "Critical"
        elif risk_score > 50: threat_level = "High"
        elif risk_score > 25: threat_level = "Medium"
        
        # Determine Scam Type
        scam_type = "Potential Spam"
        unique_cats = set(detected_categories)
        if 'crypto' in unique_cats or wallets:
            scam_type = f"Crypto Scam ({', '.join(crypto_types)})" if crypto_types else "Crypto Scam"
        elif 'phishing' in unique_cats or ('threat' in unique_cats and urls):
            scam_type = "Phishing/Security Alert"
        elif 'spam' in unique_cats:
             # Check if it's specifically a lottery/prize
             if any(k in text_lower for k in ['lottery', 'prize', 'winner', 'compensation']):
                 scam_type = "Lottery/Prize Scam"
             else:
                 scam_type = "Advance Fee / Spam"
        elif 'finance' in unique_cats:
             scam_type = "Investment/Financial Fraud"
        elif 'romance' in unique_cats:
            scam_type = "Romance Scam"
        elif threat_level == "Low":
            scam_type = "Likely Safe"
            
        sentiment = "Neutral"
        if 'urgency' in detected_categories or 'threat' in detected_categories:
            sentiment = "High Pressure / Urgent"
        elif 'romance' in detected_categories:
            sentiment = "Emotional / Luring"

        return ExtractedIntelligence(
            urls=urls,
            crypto_addresses=wallets,
            phones=phones,
            threat_level=f"{threat_level} (Score: {risk_score})",
            scam_type=scam_type,
            sentiment=sentiment
        )

# Initialize Engine
engine = IntelligenceEngine()

# --- AUTHENTICATION ---
async def verify_api_key(x_api_key: str = Header(..., description="Your Secret API Key")):
    if x_api_key != API_KEY_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key")
    return x_api_key

# --- ENDPOINTS ---
@app.get("/")
def home():
    """Health check endpoint to ensure service is live."""
    return {
        "status": "online", 
        "service": "KannanTech Agentic Honey-Pot", 
        "version": "1.0.0"
    }

@app.post("/evaluate", response_model=AnalysisResponse)
async def evaluate_scam(
    input_data: ScamInput, 
    api_key: str = Depends(verify_api_key)
):
    """
    Main evaluation endpoint. 
    Accepts a scam message -> Returns extracted intelligence.
    """
    try:
        # Perform analysis
        intelligence = engine.analyze(input_data.content)
        
        return AnalysisResponse(
            status="success",
            message_id=input_data.message_id,
            extracted_intelligence=intelligence
        )
    except Exception as e:
        # Fallback for stability - never crash
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    # Run locally with: python main.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
