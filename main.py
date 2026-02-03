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
        # Regex patterns for common indicators
        self.url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*'
        # Bitcoin, Ethereum, Tron, etc. (Generic crypto address matcher)
        self.crypto_pattern = r'\b(?:0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|T[A-Za-z0-9]{33})\b'
        self.phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        
        # Keywords for classification
        self.phishing_keywords = ['verify', 'account', 'suspended', 'login', 'bank', 'alert']
        self.crypto_keywords = ['btc', 'eth', 'profit', 'investment', 'wallet', 'mining']
        self.urgent_keywords = ['urgent', 'immediately', 'soon', 'expire', 'action required']

    def analyze(self, text: str) -> ExtractedIntelligence:
        # 1. Entity Extraction
        urls = list(set(re.findall(self.url_pattern, text)))
        wallets = list(set(re.findall(self.crypto_pattern, text)))
        phones = list(set(re.findall(self.phone_pattern, text)))
        
        # 2. Heuristic Classification
        text_lower = text.lower()
        
        # Detect Threat Level
        urgency_score = sum(1 for word in self.urgent_keywords if word in text_lower)
        threat_level = "High" if urgency_score > 0 or urls or wallets else "Medium"
        if not urls and not wallets and urgency_score == 0:
            threat_level = "Low"

        # Detect Scam Type
        scam_type = "Unknown/Spam"
        if any(w in text_lower for w in self.crypto_keywords) or wallets:
            scam_type = "Crypto/Investment Fraud"
        elif any(w in text_lower for w in self.phishing_keywords) or urls:
            scam_type = "Phishing/Credential Theft"
            
        # 3. Sentiment/Tone Analysis (Simple Heuristic for robustness)
        sentiment = "Urgent/Pressuring" if urgency_score > 0 else "Neutral/Informational"

        return ExtractedIntelligence(
            urls=urls,
            crypto_addresses=wallets,
            phones=phones,
            threat_level=threat_level,
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
