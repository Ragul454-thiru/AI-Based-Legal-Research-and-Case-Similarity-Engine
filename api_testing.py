"""
API Testing and Example Usage
AI-Based Legal Research Platform

This file contains examples of how to use the API endpoints.
"""

import requests
import json
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

class LegalResearchAPIClient:
    """Client for interacting with the Legal Research API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    # ========================================================================
    # Document Management
    # ========================================================================
    
    def upload_document(self, pdf_path: str) -> dict:
        """Upload a PDF document"""
        print(f"\n📤 Uploading: {pdf_path}")
        
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/upload",
                files=files,
                timeout=TIMEOUT
            )
        
        return response.json()
    
    def list_cases(self) -> dict:
        """List all uploaded cases"""
        print("\n📚 Fetching all cases...")
        response = requests.get(f"{self.base_url}/cases", timeout=TIMEOUT)
        return response.json()
    
    def get_case_details(self, case_id: str) -> dict:
        """Get details of a specific case"""
        print(f"\n🔍 Fetching details for: {case_id}")
        response = requests.get(
            f"{self.base_url}/cases/{case_id}",
            timeout=TIMEOUT
        )
        return response.json()
    
    # ========================================================================
    # Search and Discovery
    # ========================================================================
    
    def semantic_search(self, query: str, top_k: int = 5) -> dict:
        """Perform semantic search"""
        print(f"\n🔎 Searching for: '{query}'")
        
        payload = {
            "query": query,
            "top_k": top_k,
            "similarity_threshold": 0.3
        }
        
        response = requests.post(
            f"{self.base_url}/search",
            json=payload,
            timeout=TIMEOUT
        )
        return response.json()
    
    def find_similar_cases(self, case_id: str, top_k: int = 5) -> dict:
        """Find similar cases"""
        print(f"\n🔗 Finding similar cases to: {case_id}")
        
        response = requests.get(
            f"{self.base_url}/similar/{case_id}?top_k={top_k}",
            timeout=TIMEOUT
        )
        return response.json()
    
    # ========================================================================
    # Question & Answer
    # ========================================================================
    
    def ask_question(self, case_id: str, question: str) -> dict:
        """Ask a question about a case"""
        print(f"\n❓ Question: {question}")
        
        payload = {
            "case_id": case_id,
            "question": question
        }
        
        response = requests.post(
            f"{self.base_url}/chat",
            json=payload,
            timeout=TIMEOUT
        )
        return response.json()
    
    # ========================================================================
    # Analytics
    # ========================================================================
    
    def get_statistics(self) -> dict:
        """Get platform statistics"""
        print("\n📊 Fetching platform statistics...")
        response = requests.get(f"{self.base_url}/stats", timeout=TIMEOUT)
        return response.json()
    
    def health_check(self) -> dict:
        """Check if API is running"""
        print("\n✓ Checking API health...")
        response = requests.get(f"{self.base_url}/", timeout=TIMEOUT)
        return response.json()

# ============================================================================
# Example Usage
# ============================================================================

def print_result(title: str, data: dict):
    """Pretty print API results"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=2, default=str))

def example_workflow():
    """Example workflow demonstrating key features"""
    
    client = LegalResearchAPIClient()
    
    # 1. Health Check
    try:
        health = client.health_check()
        print_result("API Health", health)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the backend is running: python legal_backend.py")
        return
    
    # 2. Get Statistics
    try:
        stats = client.get_statistics()
        print_result("Platform Statistics", stats)
    except Exception as e:
        print(f"Error getting statistics: {e}")
    
    # 3. List Cases
    try:
        cases = client.list_cases()
        print_result("All Cases", cases)
        
        if cases.get('cases'):
            first_case_id = cases['cases'][0]['case_id']
            
            # 4. Get Case Details
            case_details = client.get_case_details(first_case_id)
            print_result(f"Case Details: {first_case_id}", {
                "case_id": case_details['case'].get('case_id'),
                "title": case_details['case'].get('title'),
                "court": case_details['case'].get('court'),
                "legal_area": case_details['case'].get('legal_area'),
                "judges": case_details['case'].get('judges'),
                "parties": case_details['case'].get('parties'),
                "content_length": case_details.get('content_length'),
                "preview": case_details.get('content_preview', '')[:200]
            })
            
            # 5. Find Similar Cases
            try:
                similar = client.find_similar_cases(first_case_id, top_k=3)
                print_result(f"Similar Cases to {first_case_id}", similar)
            except Exception as e:
                print(f"Error finding similar cases: {e}")
            
            # 6. Ask Question
            try:
                answer = client.ask_question(
                    first_case_id,
                    "What was the final judgment?"
                )
                print_result("Q&A Result", answer)
            except Exception as e:
                print(f"Error asking question: {e}")
    
    except Exception as e:
        print(f"Error listing cases: {e}")
    
    # 7. Semantic Search
    search_queries = [
        "property rights violation",
        "contract dispute settlement",
        "criminal law precedent"
    ]
    
    for query in search_queries[:1]:  # Use one example
        try:
            results = client.semantic_search(query, top_k=3)
            print_result(f"Search Results: '{query}'", {
                "query": results.get('query'),
                "results_count": results.get('results_count'),
                "results": results.get('results', [])[:2]
            })
        except Exception as e:
            print(f"Error searching: {e}")

# ============================================================================
# Sample Test Cases (for documentation)
# ============================================================================

SAMPLE_TEST_CASES = {
    "case_1": {
        "title": "State vs. Criminal X",
        "court": "Supreme Court",
        "year": 2023,
        "judges": ["Justice Smith", "Justice Johnson"],
        "parties": ["State", "Criminal X"],
        "legal_area": "Criminal Law",
        "judgment_date": "2023-06-15",
        "keywords": ["murder", "evidence", "appeal"]
    },
    "case_2": {
        "title": "Company A vs. Company B",
        "court": "High Court",
        "year": 2023,
        "judges": ["Justice Brown"],
        "parties": ["Company A", "Company B"],
        "legal_area": "Commercial Law",
        "judgment_date": "2023-07-20",
        "keywords": ["contract", "breach", "damages"]
    },
    "case_3": {
        "title": "Intellectual Property Case",
        "court": "District Court",
        "year": 2023,
        "judges": ["Justice Davis"],
        "parties": ["Patent Holder A", "Competitor B"],
        "legal_area": "Intellectual Property",
        "judgment_date": "2023-08-10",
        "keywords": ["patent", "infringement", "royalties"]
    }
}

# ============================================================================
# CURL Command Examples
# ============================================================================

CURL_EXAMPLES = """
# 1. Health Check
curl http://localhost:8000/

# 2. Upload Document
curl -X POST "http://localhost:8000/upload" \\
  -F "file=@judgment.pdf"

# 3. List All Cases
curl http://localhost:8000/cases

# 4. Get Case Details
curl http://localhost:8000/cases/CASE-A1B2C3D4

# 5. Semantic Search
curl -X POST "http://localhost:8000/search" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "trademark infringement",
    "top_k": 5,
    "similarity_threshold": 0.3
  }'

# 6. Find Similar Cases
curl "http://localhost:8000/similar/CASE-A1B2C3D4?top_k=5"

# 7. Ask Question
curl -X POST "http://localhost:8000/chat" \\
  -H "Content-Type: application/json" \\
  -d '{
    "case_id": "CASE-A1B2C3D4",
    "question": "What was the judgment?"
  }'

# 8. Get Statistics
curl http://localhost:8000/stats

# 9. Using jq for prettier output
curl http://localhost:8000/cases | jq '.'

# 10. Save response to file
curl -X POST "http://localhost:8000/search" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "criminal law"}' \\
  -o search_results.json
"""

if __name__ == "__main__":
    import sys
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   AI Legal Research - API Testing                        ║
    ║   Version 1.0.0                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Run example workflow
    example_workflow()
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)
    
    print("\nFor CURL examples, see CURL_EXAMPLES variable in this file.")
    print(f"\nSample test cases: {len(SAMPLE_TEST_CASES)} cases available")
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Interactive Swagger UI: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
