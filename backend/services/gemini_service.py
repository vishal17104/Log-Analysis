import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
from typing import Dict, Any, List

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

genai.configure(api_key=API_KEY)

MODEL_NAME = 'gemini-2.5-flash'

def analyze_incident(logs: List[Dict[str, Any]], service: str = None) -> Dict[str, Any]:
    """Analyze incident logs using Gemini"""

    try:
        model = genai.GenerativeModel(MODEL_NAME)

        #preparing log samples
        log_samples = logs[:20]
        log_text = "\n".join([
            f"[{log['timestamp']}] {log['service']} : {log}['message']"
            for log in log_samples
        ])

        prompt = f"""
You are an SRE (Site Reliability Engineer) analyzing a production incident.

CONTEXT:
- Service affected: {service or 'Multiple services'}
- Time window: Last few minutes
- Error logs:
{log_text}

TASK:
Analyze these logs and provide a structured incident report.

OUTPUT FORMAT (STRICT JSON):
{{
    "summary": "One-line summary of what happened",
    "root_cause_hypothesis": "Most likely root cause based on logs",
    "severity_score": <number 0-100>,
    "severity_level": "CRITICAL|HIGH|MEDIUM|LOW",
    "affected_services": ["list", "of", "services"],
    "key_errors": ["most", "important", "error", "patterns"],
    "recommended_actions": ["immediate", "steps", "to", "take"]
}}

RULES:
- severity_score: 0-100 (0=minor, 100=critical outage)
- severity_level: Map score to level (0-20=LOW, 21-50=MEDIUM, 51-80=HIGH, 81-100=CRITICAL)
- Be concise but specific
- Base everything ONLY on the provided logs
"""
        

        response = model.generate_content(prompt)

        #Extract JSON from response
        response_text = response.text

        #clean response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]

        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()


        analysis = json.loads(response_text)
        return analysis  

    except json.JSONDecodeError as e:  
        print(f"Failed to parse Gemini response to JSON: {e}")
        print(f"Raw respone : {response_text}")
        return {
            "summary": "AI analysis failed - invalid response format",
            "root_cause_hypothesis": "Could not parse AI response",
            "severity_score": 50,
            "severity_level": "MEDIUM",
            "affected_services": [service] if service else ["unknown"],
            "key_errors": ["parsing error"],
            "recommended_actions": ["Check Gemini API response", "Manual investigation required"]
        }
    except Exception as e:
        print(f"❌ Gemini analysis failed: {e}")
        return {
            "summary": "AI analysis failed",
            "root_cause_hypothesis": str(e),
            "severity_score": 50,
            "severity_level": "MEDIUM",
            "affected_services": [service] if service else ["unknown"],
            "key_errors": ["API error"],
            "recommended_actions": ["Check Gemini API key", "Manual investigation required"]
        }
    
def extract_keywords(logs: List[Dict[str, Any]]) -> List[str]:
        """Extract keywords from logs for runbook matching"""
        try:
            model = genai.GenerativeModel(MODEL_NAME)

            log_text = "\n".join([
                f"{log['service']} : {log['message']}"
                for log in logs[:15]
            ])

            prompt = f"""
Extract the top 5 technical keywords from these error logs.
Keywords should be single words or short phrases useful for searching documentation.

Logs:
{log_text}

Return ONLY a JSON array of strings, like: ["postgres", "timeout", "connection", "pool", "deadlock"]
"""
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            #clean response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]

            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            keywords = json.loads(response_text)
 
            return keywords if isinstance(keywords, list) else []
        except Exception as e:
            print(f"Failed to extract keywords: {e}")
            return []

    

# Test function
if __name__ == "__main__":
    # Test with sample logs
    test_logs = [
        {"timestamp": "2024-01-01T10:00:00Z", "service": "payment", "level": "ERROR", 
         "message": "Database connection timeout after 30s"},
        {"timestamp": "2024-01-01T10:00:01Z", "service": "payment", "level": "ERROR",
         "message": "Failed to execute query: connection refused"},
        {"timestamp": "2024-01-01T10:00:02Z", "service": "payment", "level": "ERROR",
         "message": "Transaction rollback due to connection loss"},
    ]
    
    print("🧪 Testing incident analysis...")
    analysis = analyze_incident(test_logs, service="payment")
    print(json.dumps(analysis, indent=2))
    
    print("\n🧪 Testing keyword extraction...")
    keywords = extract_keywords(test_logs)
    print(f"Keywords: {keywords}")