"""
AI-Based Legal Research and Case Similarity Engine
Backend FastAPI Application
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import numpy as np
import json
from datetime import datetime
import sqlite3
import os
from pathlib import Path
import hashlib

# AI/NLP imports
from sentence_transformers import SentenceTransformer, util
import PyPDF2
import re

# ============================================================================
# Initialize FastAPI App
# ============================================================================
app = FastAPI(
    title="Legal Research & Case Similarity Engine",
    description="AI-powered platform for legal document analysis and case similarity detection",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Configuration
# ============================================================================
DATABASE_PATH = "legal_cases.db"
EMBEDDINGS_MODEL = "all-MiniLM-L6-v2"  # Fast model for embeddings
STORAGE_DIR = Path("uploaded_documents")
STORAGE_DIR.mkdir(exist_ok=True)

# Load embedding model
try:
    embedding_model = SentenceTransformer(EMBEDDINGS_MODEL)
    print(f"✓ Loaded embedding model: {EMBEDDINGS_MODEL}")
except Exception as e:
    print(f"Error loading model: {e}")
    embedding_model = None

# ============================================================================
# Pydantic Models
# ============================================================================
class CaseMetadata(BaseModel):
    case_id: str
    title: str
    court: str
    year: int
    judges: List[str]
    parties: List[str]
    legal_area: str
    judgment_date: str

class CaseDocument(BaseModel):
    case_id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    similarity_threshold: float = 0.3

class CaseSimilarityResult(BaseModel):
    original_case_id: str
    similar_cases: List[Dict[str, Any]]
    total_found: int

class ChatMessage(BaseModel):
    case_id: str
    question: str

class LegalDocumentInfo(BaseModel):
    case_id: str
    title: str
    uploaded_date: str
    file_path: str
    content_preview: str

# ============================================================================
# Database Setup
# ============================================================================
def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Cases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            court TEXT,
            year INTEGER,
            judges TEXT,
            parties TEXT,
            legal_area TEXT,
            judgment_date TEXT,
            uploaded_date TEXT,
            file_path TEXT,
            embedding BLOB,
            UNIQUE(case_id)
        )
    ''')
    
    # Case citations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS citations (
            citation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_case_id TEXT,
            to_case_id TEXT,
            citation_text TEXT,
            context TEXT,
            FOREIGN KEY(from_case_id) REFERENCES cases(case_id),
            FOREIGN KEY(to_case_id) REFERENCES cases(case_id)
        )
    ''')
    
    # Search history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            search_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            timestamp TEXT,
            results_count INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized")

# ============================================================================
# Document Processing Functions
# ============================================================================
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""
    return text

def parse_legal_document(content: str) -> Dict[str, Any]:
    """Parse and extract structured data from legal document"""
    metadata = {
        "sections": extract_sections(content),
        "parties": extract_parties(content),
        "judges": extract_judges(content),
        "dates": extract_dates(content),
        "citations": extract_citations(content),
        "legal_areas": extract_legal_areas(content),
    }
    return metadata

def extract_sections(content: str) -> List[str]:
    """Extract major sections from document"""
    sections = []
    section_patterns = [
        r'INTRODUCTION\s*:?(.*?)(?=\n[A-Z]|\Z)',
        r'FACTS\s*:?(.*?)(?=\n[A-Z]|\Z)',
        r'JUDGMENT\s*:?(.*?)(?=\n[A-Z]|\Z)',
        r'DECISION\s*:?(.*?)(?=\n[A-Z]|\Z)',
        r'ORDER\s*:?(.*?)(?=\n[A-Z]|\Z)',
    ]
    for pattern in section_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            sections.append(match.group(0)[:200])
    return sections

def extract_parties(content: str) -> List[str]:
    """Extract involved parties"""
    parties = []
    party_patterns = [
        r'(?:petitioner|appellant|plaintiff|complainant|claimant).*?:\s*([A-Za-z\s]+)',
        r'(?:respondent|defendant|opposite party).*?:\s*([A-Za-z\s]+)',
    ]
    for pattern in party_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        parties.extend(matches)
    return list(set(parties))[:5]

def extract_judges(content: str) -> List[str]:
    """Extract judge names"""
    judges = []
    judge_patterns = [
        r'(?:Hon\.|Honourable|Justice|J\.|Chief Justice)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
    ]
    for pattern in judge_patterns:
        matches = re.findall(pattern, content)
        judges.extend(matches)
    return list(set(judges))[:5]

def extract_dates(content: str) -> List[str]:
    """Extract important dates"""
    dates = []
    date_pattern = r'\b(\d{1,2}[/-]?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)[/-]?\d{4})\b'
    dates = re.findall(date_pattern, content, re.IGNORECASE)
    return list(set(dates))[:5]

def extract_citations(content: str) -> List[str]:
    """Extract legal citations"""
    citations = []
    citation_patterns = [
        r'\b([0-9]{4})\s+([0-9])\s+SCC\s+([0-9]+)\b',  # Indian Supreme Court
        r'\b([A-Z]{2,})\s+([0-9]{4})\s+([0-9]+)\b',
    ]
    for pattern in citation_patterns:
        matches = re.findall(pattern, content)
        citations.extend([' '.join(match) for match in matches])
    return list(set(citations))[:10]

def extract_legal_areas(content: str) -> List[str]:
    """Extract legal areas/domains"""
    legal_areas = [
        "Constitutional Law", "Criminal Law", "Civil Law", "Commercial Law",
        "Labor Law", "Family Law", "Property Law", "Intellectual Property",
        "Administrative Law", "Environmental Law", "Tax Law"
    ]
    found_areas = [area for area in legal_areas if area.lower() in content.lower()]
    return found_areas

def generate_embeddings(text: str) -> np.ndarray:
    """Generate sentence embeddings"""
    if embedding_model is None:
        return np.zeros(384)
    try:
        embedding = embedding_model.encode(text, convert_to_tensor=True)
        return embedding.cpu().numpy().astype(np.float32) if hasattr(embedding, 'cpu') else embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return np.zeros(384)

def generate_case_id(title: str, date: str) -> str:
    """Generate unique case ID"""
    hash_input = f"{title}-{date}"
    hash_hex = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    return f"CASE-{hash_hex.upper()}"

# ============================================================================
# Database Operations
# ============================================================================
def save_case_to_db(case_doc: CaseDocument):
    """Save case document to database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Convert embedding to bytes for storage
        embedding_bytes = case_doc.embedding[0].tobytes() if case_doc.embedding else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO cases 
            (case_id, title, content, court, year, judges, parties, legal_area, 
             judgment_date, uploaded_date, file_path, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            case_doc.case_id,
            case_doc.title,
            case_doc.content,
            case_doc.metadata.get('court', 'Unknown'),
            case_doc.metadata.get('year', 0),
            json.dumps(case_doc.metadata.get('judges', [])),
            json.dumps(case_doc.metadata.get('parties', [])),
            case_doc.metadata.get('legal_area', 'General'),
            case_doc.metadata.get('judgment_date', ''),
            datetime.now().isoformat(),
            case_doc.metadata.get('file_path', ''),
            embedding_bytes
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def get_case_by_id(case_id: str) -> Optional[Dict]:
    """Retrieve case from database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM cases WHERE case_id = ?', (case_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'case_id': row[0],
            'title': row[1],
            'content': row[2],
            'court': row[3],
            'year': row[4],
            'judges': json.loads(row[5]) if row[5] else [],
            'parties': json.loads(row[6]) if row[6] else [],
            'legal_area': row[7],
            'judgment_date': row[8],
            'uploaded_date': row[9],
            'file_path': row[10]
        }
    return None

def get_all_cases() -> List[Dict]:
    """Retrieve all cases from database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM cases')
    rows = cursor.fetchall()
    conn.close()
    
    cases = []
    for row in rows:
        cases.append({
            'case_id': row[0],
            'title': row[1],
            'court': row[3],
            'year': row[4],
            'legal_area': row[7],
            'judges': json.loads(row[5]) if row[5] else [],
            'parties': json.loads(row[6]) if row[6] else [],
        })
    return cases

# ============================================================================
# Similarity and Search Functions
# ============================================================================
def find_similar_cases(query_embedding: np.ndarray, case_id: str, top_k: int = 5) -> List[Dict]:
    """Find similar cases using cosine similarity"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all cases except the query case
    cursor.execute('SELECT case_id, title, content, court, legal_area FROM cases WHERE case_id != ?', (case_id,))
    cases = cursor.fetchall()
    conn.close()
    
    if not cases or embedding_model is None:
        return []
    
    similar_cases = []
    for case in cases:
        case_text = f"{case[1]} {case[2]}"
        case_embedding = generate_embeddings(case_text)
        
        # Calculate cosine similarity
        similarity = util.pytorch_cos_sim(query_embedding, case_embedding).item()
        
        if similarity > 0:
            similar_cases.append({
                'case_id': case[0],
                'title': case[1],
                'court': case[3],
                'legal_area': case[4],
                'similarity_score': float(similarity)
            })
    
    # Sort by similarity and return top k
    similar_cases.sort(key=lambda x: x['similarity_score'], reverse=True)
    return similar_cases[:top_k]

def semantic_search(query: str, top_k: int = 5) -> List[Dict]:
    """Perform semantic search across all cases"""
    if embedding_model is None:
        return []
    
    query_embedding = generate_embeddings(query)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT case_id, title, content, court, legal_area, judgment_date FROM cases')
    cases = cursor.fetchall()
    conn.close()
    
    if not cases:
        return []
    
    results = []
    for case in cases:
        case_text = f"{case[1]} {case[2]}"
        case_embedding = generate_embeddings(case_text)
        similarity = util.pytorch_cos_sim(query_embedding, case_embedding).item()
        
        if similarity > 0:
            results.append({
                'case_id': case[0],
                'title': case[1],
                'court': case[3],
                'legal_area': case[4],
                'judgment_date': case[5],
                'similarity_score': float(similarity),
                'preview': case[2][:200]
            })
    
    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    return results[:top_k]

# ============================================================================
# API Endpoints
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    print("✓ Legal Research Engine started")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AI Legal Research & Case Similarity Engine",
        "version": "1.0.0",
        "status": "active",
        "endpoints": [
            "/docs - API Documentation",
            "/upload - Upload legal documents",
            "/cases - List all cases",
            "/cases/{case_id} - Get case details",
            "/search - Semantic search",
            "/similar/{case_id} - Find similar cases",
            "/chat - Ask questions about cases",
        ]
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process legal document"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save file
        file_path = STORAGE_DIR / file.filename
        content = await file.read()
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Extract text
        text = extract_text_from_pdf(str(file_path))
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Parse document
        metadata = parse_legal_document(text)
        
        # Generate case ID
        case_id = generate_case_id(file.filename, datetime.now().isoformat())
        
        # Generate embeddings
        embedding = generate_embeddings(text)
        
        # Create case document
        case_doc = CaseDocument(
            case_id=case_id,
            title=file.filename.replace('.pdf', ''),
            content=text,
            metadata={
                **metadata,
                'file_path': str(file_path),
                'court': metadata.get('court', 'Unknown Court'),
                'year': metadata.get('year', datetime.now().year),
                'judges': metadata.get('judges', []),
                'parties': metadata.get('parties', []),
                'legal_area': metadata.get('legal_areas', ['General'])[0] if metadata.get('legal_areas') else 'General',
                'judgment_date': metadata.get('dates', [''])[0] if metadata.get('dates') else '',
            },
            embedding=[embedding]
        )
        
        # Save to database
        save_case_to_db(case_doc)
        
        return {
            "status": "success",
            "case_id": case_id,
            "title": case_doc.title,
            "message": f"Case {case_id} uploaded successfully",
            "metadata": {
                "parties": metadata['parties'],
                "judges": metadata['judges'],
                "legal_areas": metadata['legal_areas'],
                "citations_found": len(metadata['citations']),
                "sections": len(metadata['sections'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.get("/cases")
async def list_cases():
    """List all uploaded cases"""
    cases = get_all_cases()
    return {
        "total_cases": len(cases),
        "cases": cases
    }

@app.get("/cases/{case_id}")
async def get_case_details(case_id: str):
    """Get detailed information about a specific case"""
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return {
        "case": case,
        "content_length": len(case['content']),
        "content_preview": case['content'][:500]
    }

@app.post("/search")
async def search_cases(query: SearchQuery):
    """Perform semantic search across cases"""
    if not query.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    results = semantic_search(query.query, top_k=query.top_k)
    
    # Save to search history
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO search_history (query, timestamp, results_count) VALUES (?, ?, ?)',
        (query.query, datetime.now().isoformat(), len(results))
    )
    conn.commit()
    conn.close()
    
    return {
        "query": query.query,
        "results_count": len(results),
        "results": results
    }

@app.get("/similar/{case_id}")
async def find_similar(case_id: str, top_k: int = 5):
    """Find similar cases"""
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Generate embedding for the case
    case_text = f"{case['title']} {case['content']}"
    query_embedding = generate_embeddings(case_text)
    
    similar_cases = find_similar_cases(query_embedding, case_id, top_k)
    
    return CaseSimilarityResult(
        original_case_id=case_id,
        similar_cases=similar_cases,
        total_found=len(similar_cases)
    )

@app.post("/chat")
async def ask_about_case(message: ChatMessage):
    """Ask questions about a specific case (basic Q&A)"""
    case = get_case_by_id(message.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Simple keyword-based answer extraction
    content = case['content'].lower()
    question = message.question.lower()
    
    # Extract relevant paragraphs
    sentences = content.split('.')
    relevant_sentences = [s for s in sentences if any(word in s for word in question.split())]
    
    answer = '. '.join(relevant_sentences[:3]) if relevant_sentences else "Information not found in the case document."
    
    return {
        "case_id": message.case_id,
        "question": message.question,
        "answer": answer,
        "case_title": case['title'],
        "relevance_score": len(relevant_sentences) / max(len(sentences), 1)
    }

@app.get("/stats")
async def get_statistics():
    """Get platform statistics"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM cases')
    total_cases = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM citations')
    total_citations = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM search_history')
    total_searches = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT legal_area) FROM cases')
    unique_legal_areas = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_cases": total_cases,
        "total_citations": total_citations,
        "total_searches": total_searches,
        "unique_legal_areas": unique_legal_areas,
        "platform_status": "active"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
