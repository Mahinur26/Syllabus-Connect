from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from difflib import get_close_matches
import mimetypes
import json
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import pickle


# Load environment variables
load_dotenv()




# Get configuration from .env
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("VERTEX_AI_LOCATION")
MODEL_NAME = os.getenv("VERTEX_AI_MODEL")
FRONTEND_URL = os.getenv("FRONTEND_URL")
# Render provides PORT automatically, fallback to BACKEND_PORT or 8000
PORT = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))

# Google OAuth2 Configuration
GOOGLE_CLIENT_SECRETS_FILE = "client_secret_469326734352-6hhcchpik5b0ov5v6a3gl2h45tfho7q0.apps.googleusercontent.com.json"
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
SCOPES = ['https://www.googleapis.com/auth/calendar']
# Dynamic redirect URI - uses BACKEND_URL if set (for production), otherwise localhost
BACKEND_URL = os.getenv("BACKEND_URL", f"http://localhost:{PORT}")
REDIRECT_URI = f"{BACKEND_URL}/auth/google/callback"




# Initialize FastAPI
app = FastAPI()


# CORS - Cross-Origin Resource Sharing
# Allows the frontend(from a different port) to access the backend (which is also in a different port)
# These requests are usually blocked by browsers for security reasons, but this overrides that
# This block is in place to prevent other malicious domains from accessing your backend and taking precious data muhhaha

# Handle CORS origins - when allow_credentials=True, cannot use wildcard "*"
# Must specify exact origins
# Strip trailing slashes to match browser origin format
if FRONTEND_URL and FRONTEND_URL.strip():
    # Production: allow specific frontend URL (remove trailing slash)
    frontend_url_clean = FRONTEND_URL.strip().rstrip('/')
    # Allow both with and without trailing slash to be safe
    allowed_origins = [frontend_url_clean, f"{frontend_url_clean}/"]
    use_credentials = True
else:
    # Development: allow all origins (but can't use credentials with wildcard)
    allowed_origins = ["*"]
    use_credentials = False

app.add_middleware(
   CORSMiddleware,
   allow_origins=allowed_origins,
   allow_credentials=use_credentials,
   allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
   allow_headers=["*"],
   expose_headers=["*"],
   max_age=3600,  # Cache preflight for 1 hour
)

# Debug: Print CORS configuration on startup
print(f"🔧 CORS Configuration:")
print(f"   FRONTEND_URL: {FRONTEND_URL}")
print(f"   Allowed Origins: {allowed_origins}")
print(f"   Allow Credentials: {use_credentials}")


# Initialize Firebase creds and gets a database client
import json

# Try to get credentials from JSON string first (for Render), then file path
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")  # e.g., "your-project.appspot.com"

if FIREBASE_CREDENTIALS_JSON:
    # Parse JSON string from environment variable
    cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
    cred = credentials.Certificate(cred_dict)
else:
    # Fall back to file path (for local development)
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)

# Initialize Firebase with storage bucket if provided, otherwise use default
if FIREBASE_STORAGE_BUCKET:
    firebase_admin.initialize_app(cred, {
        'storageBucket': FIREBASE_STORAGE_BUCKET
    })
else:
    # Initialize without bucket - will use default project bucket
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Get storage bucket - will use the default bucket if not specified
try:
    if FIREBASE_STORAGE_BUCKET:
        bucket = storage.bucket(FIREBASE_STORAGE_BUCKET)
    else:
        bucket = storage.bucket()  # Uses default bucket
    print(f"📦 Storage bucket initialized: {bucket.name}")
except Exception as e:
    print(f"⚠️  Storage bucket initialization warning: {e}")
    print(f"   Make sure Firebase Storage is enabled in Firebase Console")
    bucket = None


# Initialize Vertex AI with explicit credentials
# Reusing the Firebase service account for Vertix AI, just using one service account with both Firebase and Vertex AI enabled
if FIREBASE_CREDENTIALS_JSON:
    vertex_credentials = service_account.Credentials.from_service_account_info(
        json.loads(FIREBASE_CREDENTIALS_JSON)
    )
else:
    vertex_credentials = service_account.Credentials.from_service_account_file(
        FIREBASE_CREDENTIALS_PATH
    )
vertexai.init(
   project=PROJECT_ID,
   location=LOCATION,
   credentials=vertex_credentials
)
model = GenerativeModel(MODEL_NAME)


# Valid categories for syllabus items
VALID_CATEGORIES = ["Exams", "Assignments", "Homework", "Projects", "Tests", "Quizzes", "Essays", "Other"]

# Category mapping for auto-detection (legacy, keeping for backward compatibility)
CATEGORY_MAPPING = {
    "exams": ["exam", "midterm", "final", "test"],
    "assignments": ["assignment", "homework", "hw", "problem set"],
    "homework": ["homework", "hw"],
    "projects": ["project", "presentation"],
    "tests": ["test", "quiz"],
    "quizzes": ["quiz"],
    "essays": ["essay", "paper", "report"],
    "other": []
}


# File upload configuration
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes


def validate_syllabus_file(file: UploadFile) -> tuple[bool, str]:
    """
    Validate uploaded syllabus file.
    Returns (is_valid, error_message).
    """
    # Check if file exists
    if not file or not file.filename:
        return False, "No file provided"
    
    # Get file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    # Check file extension
    if file_extension not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed"
    
    # Check file size (read content to check size)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()  # Get position (file size)
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, ""


def detect_category(item_name: str) -> str:
    # docstring explaining the function
   """
   Detect category of an item based on its name using predefined mapping.
   Returns category name (capitalized) or "Other" if no match found.
   """
   if not item_name:
       return "Other"


   item_lower = item_name.lower().strip()
   
   #handle plural words
   if item_lower.endswith('es'):
        item_lower = item_lower[:-2]
   elif item_lower.endswith('s'):
        item_lower = item_lower[:-1]


   # Check each category's keywords
   for category, keywords in CATEGORY_MAPPING.items():
       for keyword in keywords:
           if keyword in item_lower:
               # Capitalize first letter of category
               return category.capitalize()
           # Fuzzy match (handles typos like "strawbery" -> "strawberry")
           close = get_close_matches(item_lower, keywords, n=1, cutoff=0.8)
           if close:
                return category.capitalize() 
   

   return "Other"


async def parse_syllabus_with_ai(syllabus_id: str, file_bytes: bytes, mime_type: str, syllabus_name: str) -> List[Dict]:
    """
    Parse syllabus using Gemini AI to extract structured items with dates.
    Returns list of items with category, name, and due_date.
    """
    try:
        print(f"🔍 Parsing syllabus: {syllabus_name}")
        
        # Create Part object for Gemini
        file_part = Part.from_data(
            data=file_bytes,
            mime_type=mime_type
        )
        
        # Strict prompt for structured extraction
        parsing_prompt = """You are a syllabus parser. Analyze this course syllabus document and extract ALL assignments, exams, projects, homework, tests, quizzes, essays, and other assessments.

CRITICAL INSTRUCTIONS:
1. Extract EVERY item that has a due date or deadline
2. Categorize each item into EXACTLY ONE of these categories: Exams, Assignments, Homework, Projects, Tests, Quizzes, Essays, Other
3. Convert ALL dates to YYYY-MM-DD format (e.g., 2025-03-15)
4. If a month/day is given without year, assume the current academic year (2025-2026)
5. Return ONLY valid JSON, no other text

REQUIRED JSON FORMAT:
{
  "items": [
    {
      "category": "Assignments",
      "name": "Assignment 1: Introduction",
      "due_date": "2025-01-15"
    },
    {
      "category": "Exams",
      "name": "Midterm Exam",
      "due_date": "2025-03-10"
    }
  ]
}

RULES:
- Category must be one of: Exams, Assignments, Homework, Projects, Tests, Quizzes, Essays, Other
- Name should be descriptive and include item number/title
- due_date must be YYYY-MM-DD format
- If date is unclear or missing, use "TBD" for due_date
- Include percentage/weight in name if available (e.g., "Final Exam (30%)")

Now analyze the syllabus and return the JSON:"""

        # Call Gemini with file and parsing prompt
        print(f"📤 Sending to Gemini for parsing...")
        response = model.generate_content([file_part, parsing_prompt])
        
        # Extract response text
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            response_text = response.candidates[0].content.parts[0].text
        else:
            response_text = str(response)
        
        print(f"📥 Received response from Gemini")
        print(f"   Response preview: {response_text[:200]}...")
        
        # Parse JSON from response
        # Try to extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
            else:
                json_text = response_text
        
        # Parse the JSON
        parsed_data = json.loads(json_text)
        items = parsed_data.get("items", [])
        
        print(f"✅ Parsed {len(items)} items from syllabus")
        
        # Store items in Firestore
        stored_items = []
        for item in items:
            # Validate required fields
            if not all(key in item for key in ["category", "name", "due_date"]):
                print(f"⚠️  Skipping invalid item: {item}")
                continue
            
            # Validate category
            if item["category"] not in VALID_CATEGORIES:
                print(f"⚠️  Invalid category '{item['category']}', defaulting to 'Other'")
                item["category"] = "Other"
            
            # Create item in Firestore
            doc_ref = db.collection("syllabus_items").document()
            item_data = {
                "syllabus_id": syllabus_id,
                "category": item["category"],
                "name": item["name"],
                "due_date": item["due_date"],
                "selected": False,
                "created_at": datetime.now()
            }
            doc_ref.set(item_data)
            
            # Add ID for return
            item_data["id"] = doc_ref.id
            stored_items.append(item_data)
        
        print(f"💾 Stored {len(stored_items)} items in Firestore")
        return stored_items
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {str(e)}")
        print(f"   Response text: {response_text}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response as JSON: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error parsing syllabus: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing syllabus: {str(e)}"
        )


# The 3 models use pydantic to validate data requests for each endpoint
# FastAPI is used to automatically checks data requests and matches it to the right model



# base model means json file, with the category field below
class AuthRequest(BaseModel):
   email: str
   password: str




class InventoryItem(BaseModel):
   user_id: str
   name: str
   quantity: int
   expiration_date: Optional[str] = None
   category: Optional[str] = None




class ChatRequest(BaseModel):
   user_id: str
   message: str
   syllabus_id: Optional[str] = None


class CalendarItem(BaseModel):
   id: str
   category: str
   name: str
   due_date: str


class AddToCalendarRequest(BaseModel):
   user_id: str
   syllabus_id: str
   items: List[CalendarItem]


class DeleteItemRequest(BaseModel):
   item_id: str



class UpdateCategoryRequest(BaseModel):
   category: str


# Helper functions for OAuth
def get_user_credentials(user_id: str):
    """Get stored OAuth credentials for a user from Firestore"""
    try:
        doc = db.collection("user_tokens").document(user_id).get()
        if doc.exists:
            token_data = doc.to_dict()
            return token_data.get("credentials")
        return None
    except Exception as e:
        print(f"Error getting user credentials: {e}")
        return None


def save_user_credentials(user_id: str, credentials):
    """Save OAuth credentials for a user to Firestore"""
    try:
        # Convert credentials to dict for storage
        creds_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        db.collection("user_tokens").document(user_id).set({
            "credentials": creds_dict,
            "updated_at": datetime.now()
        })
        print(f"✅ Saved credentials for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return False


def credentials_from_dict(creds_dict):
    """Recreate credentials object from dictionary"""
    from google.oauth2.credentials import Credentials
    
    return Credentials(
        token=creds_dict.get('token'),
        refresh_token=creds_dict.get('refresh_token'),
        token_uri=creds_dict.get('token_uri'),
        client_id=creds_dict.get('client_id'),
        client_secret=creds_dict.get('client_secret'),
        scopes=creds_dict.get('scopes')
    )


# Auth Endpoints - Used for signing up and logging in users
# The @app.post here responds to POST requests from "/auth/signup" in this case (getting data from the frontend)
@app.post("/auth/signup")
async def signup(req: AuthRequest):
   try:
       # Tries to create a new user for firbase auth
       user = auth.create_user(email=req.email, password=req.password)
       return {"user": {"uid": user.uid, "email": user.email}}
   except Exception as e:
       raise HTTPException(status_code=400, detail=str(e))




@app.post("/auth/login")
async def login(req: AuthRequest):
   try:
       # Checks if user exists in firebase auth for now, but doesn't verify password(Probably ADD LATER )
       user = auth.get_user_by_email(req.email)
       return {"user": {"uid": user.uid, "email": user.email}}
   except Exception as e:
       # If DNE then the exception is raised and the user is informed of invalid credentials
       raise HTTPException(status_code=400, detail="Invalid credentials")


# Google OAuth Endpoints
@app.get("/auth/google/url")
async def get_google_auth_url(user_id: str):
    """
    Generate Google OAuth URL for user to authorize calendar access.
    Frontend redirects user to this URL to start OAuth flow.
    """
    try:
        # Try to use client secrets file first (for local dev)
        client_secrets_path = os.path.join(
            os.path.dirname(__file__),
            GOOGLE_CLIENT_SECRETS_FILE
        )
        
        if os.path.exists(client_secrets_path):
            flow = Flow.from_client_secrets_file(
                client_secrets_path,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
        else:
            # Fallback to environment variables (for Render)
            client_config = {
                "web": {
                    "client_id": GOOGLE_OAUTH_CLIENT_ID,
                    "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            }
            flow = Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
        
        # Generate authorization URL with state parameter
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to get refresh token
        )
        
        # Store state in Firestore temporarily
        db.collection("oauth_states").document(state).set({
            "user_id": user_id,
            "created_at": datetime.now()
        })
        
        return {
            "authorization_url": authorization_url,
            "state": state
        }
        
    except Exception as e:
        print(f"❌ Error generating auth URL: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating authorization URL: {str(e)}"
        )


@app.get("/auth/google/callback")
async def google_auth_callback(code: str, state: str):
    """
    Handle OAuth callback from Google.
    Exchanges authorization code for tokens and stores them.
    """
    try:
        # Get user_id from state
        state_doc = db.collection("oauth_states").document(state).get()
        if not state_doc.exists:
            raise HTTPException(
                status_code=400,
                detail="Invalid state parameter"
            )
        
        user_id = state_doc.to_dict().get("user_id")
        
        # Delete the state document
        db.collection("oauth_states").document(state).delete()
        
        # Exchange code for credentials
        client_secrets_path = os.path.join(
            os.path.dirname(__file__),
            GOOGLE_CLIENT_SECRETS_FILE
        )
        
        if os.path.exists(client_secrets_path):
            flow = Flow.from_client_secrets_file(
                client_secrets_path,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI,
                state=state
            )
        else:
            # Fallback to environment variables (for Render)
            client_config = {
                "web": {
                    "client_id": GOOGLE_OAUTH_CLIENT_ID,
                    "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            }
            flow = Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI,
                state=state
            )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Save credentials to Firestore
        save_user_credentials(user_id, credentials)
        
        print(f"✅ OAuth completed for user {user_id}")
        
        # Redirect back to frontend with success message
        frontend_redirect = f"{FRONTEND_URL}?calendar_connected=true"
        
        return {
            "message": "Google Calendar connected successfully!",
            "redirect_to": frontend_redirect
        }
        
    except Exception as e:
        print(f"❌ Error in OAuth callback: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error completing authorization: {str(e)}"
        )


@app.get("/auth/google/status/{user_id}")
async def check_google_auth_status(user_id: str):
    """
    Check if user has connected their Google Calendar.
    """
    try:
        creds_dict = get_user_credentials(user_id)
        
        if creds_dict:
            return {
                "connected": True,
                "message": "Google Calendar is connected"
            }
        else:
            return {
                "connected": False,
                "message": "Google Calendar not connected"
            }
            
    except Exception as e:
        print(f"❌ Error checking auth status: {e}")
        return {
            "connected": False,
            "message": f"Error: {str(e)}"
        }


# Syllabi Endpoints - Handle syllabus file uploads and retrieval

@app.post("/syllabi/upload")
async def upload_syllabus(
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """
    Upload a syllabus file (PDF, DOCX, or TXT).
    Stores file in Firebase Storage and metadata in Firestore.
    """
    try:
        # Check if storage bucket is initialized
        if bucket is None:
            raise HTTPException(
                status_code=503,
                detail="Firebase Storage is not enabled. Please enable Storage in Firebase Console."
            )
        
        # Validate the file
        is_valid, error_message = validate_syllabus_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Get file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Create unique filename to avoid collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        storage_path = f"syllabi/{user_id}/{safe_filename}"
        
        # Upload to Firebase Storage
        blob = bucket.blob(storage_path)
        
        # Read file content
        file_content = await file.read()
        
        # Upload with proper content type
        content_type_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain'
        }
        blob.upload_from_string(
            file_content,
            content_type=content_type_map.get(file_extension, 'application/octet-stream')
        )
        
        # Make the file publicly accessible (or use signed URLs for private access)
        blob.make_public()
        file_url = blob.public_url
        
        # Store metadata in Firestore
        doc_ref = db.collection("syllabi").document()
        syllabus_data = {
            "user_id": user_id,
            "name": file.filename,
            "file_url": file_url,
            "file_type": file_extension,
            "file_path": storage_path,
            "upload_date": datetime.now(),
            "created_at": datetime.now()
        }
        doc_ref.set(syllabus_data)
        
        # Automatically parse syllabus to extract items
        print(f"🤖 Auto-parsing syllabus after upload...")
        try:
            parsed_items = await parse_syllabus_with_ai(
                syllabus_id=doc_ref.id,
                file_bytes=file_content,
                mime_type=content_type_map.get(file_extension, 'application/octet-stream'),
                syllabus_name=file.filename
            )
            print(f"✅ Auto-parsing complete: {len(parsed_items)} items extracted")
        except Exception as parse_error:
            print(f"⚠️  Auto-parsing failed (syllabus still uploaded): {str(parse_error)}")
            # Don't fail the upload if parsing fails
        
        return {
            "id": doc_ref.id,
            "message": "Syllabus uploaded successfully",
            "name": file.filename,
            "file_url": file_url,
            "file_type": file_extension
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading syllabus: {str(e)}"
        )


@app.get("/syllabi/{user_id}")
async def get_syllabi(user_id: str):
    """
    Get all syllabi for a specific user.
    Returns list of syllabus metadata.
    """
    try:
        syllabi = []
        docs = db.collection("syllabi").where("user_id", "==", user_id).stream()
        
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            # Convert datetime to string for JSON serialization
            if "upload_date" in data:
                data["upload_date"] = data["upload_date"].isoformat()
            if "created_at" in data:
                data["created_at"] = data["created_at"].isoformat()
            syllabi.append(data)
        
        return syllabi
        
    except Exception as e:
        print(f"Error fetching syllabi: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching syllabi: {str(e)}"
        )


@app.get("/syllabi/{syllabus_id}/items")
async def get_syllabus_items(syllabus_id: str):
    """
    Get items (assignments, exams, etc.) from a syllabus.
    Returns parsed items from Firestore.
    """
    try:
        items = []
        docs = db.collection("syllabus_items").where("syllabus_id", "==", syllabus_id).stream()
        
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            # Convert datetime to string for JSON serialization
            if "created_at" in data:
                data["created_at"] = data["created_at"].isoformat()
            items.append(data)
        
        print(f"📋 Fetched {len(items)} items for syllabus {syllabus_id}")
        
        # If no items found, check if syllabus exists and trigger parsing
        if len(items) == 0:
            print(f"⚠️  No items found for syllabus {syllabus_id}, checking if parsing is needed...")
            syllabus_doc = db.collection("syllabi").document(syllabus_id).get()
            if syllabus_doc.exists:
                print(f"✨ Syllabus exists but no items - may need to re-parse or wait for parsing to complete")
        
        return items
        
    except Exception as e:
        print(f"Error fetching syllabus items: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching syllabus items: {str(e)}"
        )


@app.post("/syllabi/{syllabus_id}/reparse")
async def reparse_syllabus(syllabus_id: str):
    """
    Manually trigger re-parsing of an existing syllabus.
    Useful if parsing failed during upload or if you want to extract items from old syllabi.
    """
    try:
        # Get syllabus metadata
        syllabus_doc = db.collection("syllabi").document(syllabus_id).get()
        
        if not syllabus_doc.exists:
            raise HTTPException(
                status_code=404,
                detail="Syllabus not found"
            )
        
        syllabus_data = syllabus_doc.to_dict()
        file_path = syllabus_data.get("file_path")
        syllabus_name = syllabus_data.get("name")
        file_type = syllabus_data.get("file_type", "")
        
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail="Syllabus file path not found"
            )
        
        # Get the file from Firebase Storage
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            raise HTTPException(
                status_code=404,
                detail="Syllabus file not found in storage"
            )
        
        print(f"🔄 Re-parsing syllabus: {syllabus_name}")
        
        # Download file
        file_bytes = blob.download_as_bytes()
        
        # Determine MIME type
        mime_type_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain'
        }
        mime_type = mime_type_map.get(file_type, 'application/octet-stream')
        
        # Delete existing items for this syllabus
        existing_items = db.collection("syllabus_items").where("syllabus_id", "==", syllabus_id).stream()
        for item_doc in existing_items:
            item_doc.reference.delete()
        print(f"🗑️  Deleted existing items for syllabus {syllabus_id}")
        
        # Parse the syllabus
        parsed_items = await parse_syllabus_with_ai(
            syllabus_id=syllabus_id,
            file_bytes=file_bytes,
            mime_type=mime_type,
            syllabus_name=syllabus_name
        )
        
        return {
            "message": "Syllabus re-parsed successfully",
            "items_count": len(parsed_items),
            "items": parsed_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error re-parsing syllabus: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error re-parsing syllabus: {str(e)}"
        )


# Inventory Endpoints - Loads all the inventory items tied to the user




@app.get("/inventory/{user_id}")
async def get_inventory(user_id: str):
   # The items the user has in their inventory is stored locally in a list, and populated from the firestore database so we can fetch it for use at later times
   items = []
   # Getting the data from firestore where the user_id matches the user and putting it (streaming) in the items list
   docs = db.collection("inventory").where("user_id", "==", user_id).stream()
   for doc in docs:
       data = doc.to_dict()
       data["id"] = doc.id
       items.append(data)
   return items




@app.post("/inventory")
async def add_inventory(item: InventoryItem):
   # Creates a new inventory item/collection document in firestore for the user
   # Auto-detect category if not provided
   category = item.category if item.category else detect_category(item.name)


   doc_ref = db.collection("inventory").document()
   # Each inventory item is a dictionary with these fields
   doc_ref.set({
       "user_id": item.user_id,
       "name": item.name,
       "quantity": item.quantity,
       "expiration_date": item.expiration_date,
       "category": category,
       "created_at": datetime.now()
   })
   return {"id": doc_ref.id, "message": "Item added", "category": category}



# post request means sending data from the frontend to the backend for processing, in this case for deleting an item
@app.post("/inventory/delete")
async def delete_inventory(req: DeleteItemRequest):
   try:
       # Permanently deletes the inventory item from Firestore using its document ID
       db.collection("inventory").document(req.item_id).delete()
       return {"message": "Item deleted successfully"}
   except Exception as e:
       raise HTTPException(
           status_code=400, detail=f"Error deleting item: {str(e)}")



# put request means updating data in the backend, in this case for updating the category of an item
@app.put("/inventory/{item_id}/category")
async def update_category(item_id: str, req: UpdateCategoryRequest):
   """
   Update the category of an inventory item.
   Validates that the category is one of the allowed values.
   """
   try:
       # Validate category
       if req.category not in VALID_CATEGORIES:
           raise HTTPException(
               status_code=400,
               detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
           )


       # Update the document
       doc_ref = db.collection("inventory").document(item_id)
       doc = doc_ref.get()


       if not doc.exists:
           raise HTTPException(status_code=404, detail="Item not found")


       doc_ref.update({"category": req.category})
       return {"message": "Category updated successfully", "category": req.category}
   except HTTPException:
       raise
   except Exception as e:
       raise HTTPException(
           status_code=400, detail=f"Error updating category: {str(e)}")




@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Chat with AI assistant about the selected syllabus.
    Uses Gemini's native file understanding (supports PDF, DOCX, TXT).
    """
    try:
        # Check if syllabus_id is provided
        if not req.syllabus_id:
            raise HTTPException(
                status_code=400,
                detail="Please select a syllabus to chat about"
            )
        
        # Get syllabus metadata from Firestore
        syllabus_doc = db.collection("syllabi").document(req.syllabus_id).get()
        
        if not syllabus_doc.exists:
            raise HTTPException(
                status_code=404,
                detail="Syllabus not found"
            )
        
        syllabus_data = syllabus_doc.to_dict()
        
        # Verify the syllabus belongs to the user
        if syllabus_data.get("user_id") != req.user_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this syllabus"
            )
        
        # Get file information
        file_path = syllabus_data.get("file_path")
        file_url = syllabus_data.get("file_url")
        syllabus_name = syllabus_data.get("name", "syllabus")
        file_type = syllabus_data.get("file_type", "")
        
        if not file_path or not file_url:
            raise HTTPException(
                status_code=404,
                detail="Syllabus file information not found"
            )
        
        # Get the blob
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            raise HTTPException(
                status_code=404,
                detail="Syllabus file not found in storage"
            )
        
        print(f"💬 Chat request for syllabus: {syllabus_name}")
        print(f"   File type: {file_type}")
        print(f"   Question: {req.message[:100]}...")
        
        # Download file as bytes
        file_bytes = blob.download_as_bytes()
        
        # Determine MIME type
        mime_type_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain'
        }
        mime_type = mime_type_map.get(file_type, 'application/octet-stream')
        
        # Create Part object for Gemini (native file understanding)
        file_part = Part.from_data(
            data=file_bytes,
            mime_type=mime_type
        )
        
        # Build prompt optimized for Gemini 2.5 Flash with file context
        text_prompt = f"""You are Syllabus Buddy, an intelligent academic assistant helping students understand their course syllabus.

The student has uploaded a syllabus document named "{syllabus_name}". The document is attached to this conversation.

STUDENT QUESTION: {req.message}

INSTRUCTIONS:
- Carefully read and analyze the attached syllabus document
- Answer the student's question based on the syllabus content
- Be concise, clear, and helpful
- If the answer isn't in the syllabus, say so and offer general academic advice
- When referencing specific information, mention what section or page it's from if possible
- For questions about assignments or exams, provide relevant dates, percentages, and requirements
- Use a friendly, supportive tone

FORMATTING REQUIREMENTS:
- Do NOT use markdown, asterisks, or special symbols
- Make your answers easy to read and chat-friendly
- Leave whitespace between paragraphs for readability
- Avoid using **, *, #, or other markdown formatting

Provide your answer:"""

        # Call Vertex AI with both the file and the prompt
        print(f"📤 Sending to Gemini with file attachment...")
        response = model.generate_content([file_part, text_prompt])

        # Extract response text
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            response_text = response.candidates[0].content.parts[0].text
        else:
            print(f"⚠️  Unexpected response format: {response}")
            response_text = str(response)

        print(f"✅ Response generated successfully")
        
        return {"response": response_text}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in chat endpoint: {str(e)}")
        print(f"   Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )


# Google Calendar Endpoint
@app.post("/calendar/add")
async def add_to_calendar(req: AddToCalendarRequest):
    """
    Add selected syllabus items to user's personal Google Calendar using OAuth.
    Creates calendar events for each selected item.
    """
    try:
        print(f"📅 Adding {len(req.items)} items to Google Calendar for user {req.user_id}")
        
        # Get user's OAuth credentials
        creds_dict = get_user_credentials(req.user_id)
        if not creds_dict:
            raise HTTPException(
                status_code=401,
                detail="Google Calendar not connected. Please connect your Google account first."
            )
        
        # Convert to credentials object
        credentials = credentials_from_dict(creds_dict)
        
        # Refresh token if expired
        if credentials.expired and credentials.refresh_token:
            print(f"🔄 Refreshing expired token for user {req.user_id}")
            credentials.refresh(Request())
            # Save refreshed credentials
            save_user_credentials(req.user_id, credentials)
        
        # Get syllabus information
        syllabus_doc = db.collection("syllabi").document(req.syllabus_id).get()
        if not syllabus_doc.exists:
            raise HTTPException(
                status_code=404,
                detail="Syllabus not found"
            )
        
        syllabus_data = syllabus_doc.to_dict()
        syllabus_name = syllabus_data.get("name", "Syllabus")
        
        # Verify syllabus belongs to user
        if syllabus_data.get("user_id") != req.user_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this syllabus"
            )
        
        # Build Google Calendar service with user's OAuth credentials
        calendar_service = build('calendar', 'v3', credentials=credentials)
        
        # Create events for each selected item
        created_events = []
        failed_events = []
        
        for item in req.items:
            try:
                # Parse the date
                if item.due_date == "TBD" or not item.due_date:
                    print(f"⚠️  Skipping item with no date: {item.name}")
                    failed_events.append({
                        "item": item.name,
                        "reason": "No due date specified"
                    })
                    continue
                
                # Create event
                event = {
                    'summary': f"{item.category}: {item.name}",
                    'description': f"From syllabus: {syllabus_name}\nCategory: {item.category}",
                    'start': {
                        'date': item.due_date,  # All-day event
                        'timeZone': 'America/New_York',
                    },
                    'end': {
                        'date': item.due_date,  # All-day event
                        'timeZone': 'America/New_York',
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                            {'method': 'popup', 'minutes': 60},  # 1 hour before
                        ],
                    },
                }
                
                # Insert event into primary calendar
                created_event = calendar_service.events().insert(
                    calendarId='primary',
                    body=event
                ).execute()
                
                created_events.append({
                    "item": item.name,
                    "event_id": created_event.get('id'),
                    "event_link": created_event.get('htmlLink')
                })
                print(f"✅ Created event: {item.name} on {item.due_date}")
                
            except HttpError as e:
                print(f"❌ Failed to create event for {item.name}: {str(e)}")
                failed_events.append({
                    "item": item.name,
                    "reason": str(e)
                })
            except Exception as e:
                print(f"❌ Unexpected error for {item.name}: {str(e)}")
                failed_events.append({
                    "item": item.name,
                    "reason": str(e)
                })
        
        # Return summary
        return {
            "message": f"Successfully added {len(created_events)} events to Google Calendar",
            "created_events": created_events,
            "failed_events": failed_events,
            "total_attempted": len(req.items),
            "total_created": len(created_events),
            "total_failed": len(failed_events)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error adding to calendar: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error adding to calendar: {str(e)}"
        )


if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=PORT)