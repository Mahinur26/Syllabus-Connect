from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from datetime import datetime
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from difflib import get_close_matches


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




class DeleteItemRequest(BaseModel):
   item_id: str



class UpdateCategoryRequest(BaseModel):
   category: str




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
    try:
        # Get user's inventory
        #Stores the item with all of its data as a string in the inventory list
        inventory = []
        docs = db.collection("inventory").where("user_id", "==", req.user_id).stream()
        for doc in docs:
            data = doc.to_dict()
            #Using f-strings to get the name, quantity, and expiration date of each item in the inventory in a normalized way
            inventory.append(f"{data['name']} (qty: {data['quantity']}, expires: {data.get('expiration_date', 'N/A')})")
        
        # Build prompt
        #If inventory is empty, then the ternary statement fails and it says no items, otherwise it joins the items with new lines
        #This variable is used in the f-string for the prompt to Vertex AI
        inventory_text = "\n".join(inventory) if inventory else "No items in inventory"
        #We will be prompting Vertex AI with this prompt to get recipe suggestions based on the user's inventory
        prompt = f"""You are a helpful cooking assistant.

Current inventory:
{inventory_text}

User question: {req.message}

IMPORTANT: Format your response EXACTLY like this structure:

DISH NAME: [Name of the recipe]

INGREDIENTS:
- [ingredient 1 with amount]
- [ingredient 2 with amount]
- [ingredient 3 with amount]

INSTRUCTIONS:
1. [First step]
2. [Second step]
3. [Third step]

Rules:
- Use "DISH NAME:", "INGREDIENTS:", and "INSTRUCTIONS:" as section headers
- Use simple dashes (-) for each ingredient with amounts
- Use numbers (1., 2., 3.) for each instruction step
- Put a blank line between each section
- Keep instructions clear and concise
- Prioritize items that are expiring soon
- If the user asks a general question, still try to suggest a recipe in this format"""

        # Call Vertex AI with error handling
        # The prompt is sent to Vertex AI and the response is stored in response
        print(f"Sending prompt to Vertex AI: {prompt[:100]}...")  # Debug log
        response = model.generate_content(prompt)

        # Try different ways to access the response
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            response_text = response.candidates[0].content.parts[0].text
        else:
            print(f"Response object: {response}")  # Debug log
            response_text = str(response)

        # Returns the response from Vertex AI to the frontend
        return {"response": response_text}
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")  # Debug log
        print(f"Error type: {type(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=PORT)