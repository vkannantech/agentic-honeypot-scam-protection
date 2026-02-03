import asyncio
from main import IntelligenceEngine, ExtractedIntelligence

def print_result(name, text, result: ExtractedIntelligence):
    print(f"\n--- {name} ---")
    print(f"Input: {text[:60]}...")
    print(f"Threat Level: {result.threat_level}")
    print(f"Scam Type: {result.scam_type}")
    print(f"Score Components: {result.sentiment}")
    print(f"Entities: URLs={len(result.urls)}, Crypto={len(result.crypto_addresses)}")

def main():
    engine = IntelligenceEngine()
    
    test_cases = [
        (
            "Clear Crypto Scam", 
            "URGENT: Your BTC wallet bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh is compromised. Move funds to security wallet 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa immediately to avoid loss!",
            "Critical", "Crypto Scam"
        ),
        (
            "Phishing", 
            "Dear Customer, your bank account is suspended due to unusual activity. Click http://secure-bank-verify.com/login to restore access.",
            "Critical", "Phishing"
        ),
        (
            "Lottery Spam",
            "CONGRATULATIONS!! You have won the $1,000,000 prize in our international lottery. CLAIM NOW by sending your details.",
            "High", "Lottery"
        ),
        (
            "Safe Message",
            "Hey, are we still on for lunch tomorrow? Let me know.",
            "Low", "Likely Safe"
        ),
        (
            "Subtle Phishing",
            "Kindly verify your login details due to security alert. unusual activity detected.",
            "High", "Phishing"
        )
    ]
    
    passes = 0
    for name, text, expected_level, expected_type in test_cases:
        result = engine.analyze(text)
        print_result(name, text, result)
        
        # Soft assertion
        if expected_level in result.threat_level:
            print("✅ Threat Level Match")
            passes += 1
        else:
            print(f"❌ Threat Level Mismatch (Expected {expected_level})")
            
        if expected_type in result.scam_type or (expected_type == "Advance Fee" and "Lottery" in result.scam_type):
             print("✅ Scam Type Match")
        else:
             print(f"❌ Scam Type Mismatch (Expected {expected_type})")

    print(f"\nTotal Passed: {passes}/{len(test_cases)}")

if __name__ == "__main__":
    main()
