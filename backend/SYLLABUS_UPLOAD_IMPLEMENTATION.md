# Syllabus Upload Implementation Summary

## ✅ Completed Tasks

### 1. Package Installation
- Added `python-multipart==0.0.6` to requirements.txt for FastAPI file uploads
- Installed all dependencies using Python 3.12

### 2. Firebase Storage Setup
- Imported `firebase_admin.storage` module
- Initialized storage bucket client
- Added `FIREBASE_STORAGE_BUCKET` environment variable to `.env`
- Bucket name: `syllabus-connect.appspot.com`

### 3. File Validation Function
Created `validate_syllabus_file()` function with the following checks:
- **Allowed file types**: `.pdf`, `.docx`, `.txt` only
- **Maximum file size**: 10MB
- **File existence**: Checks for empty files
- Returns clear error messages for validation failures

### 4. Upload Endpoint Implementation
**Endpoint**: `POST /syllabi/upload`

**Parameters**:
- `file`: UploadFile (multipart/form-data)
- `user_id`: string (form field)

**Functionality**:
1. Validates uploaded file (type, size, existence)
2. Creates unique filename with timestamp to prevent collisions
3. Uploads to Firebase Storage at path: `syllabi/{user_id}/{filename}`
4. Sets appropriate content type based on file extension
5. Makes file publicly accessible
6. Stores metadata in Firestore `syllabi` collection with fields:
   - `user_id`: User identifier
   - `name`: Original filename
   - `file_url`: Public download URL
   - `file_type`: File extension (.pdf, .docx, or .txt)
   - `file_path`: Storage path for reference
   - `upload_date`: Timestamp of upload
   - `created_at`: Timestamp of record creation

**Response**:
```json
{
  "id": "firestore_document_id",
  "message": "Syllabus uploaded successfully",
  "name": "original_filename.pdf",
  "file_url": "https://storage.googleapis.com/...",
  "file_type": ".pdf"
}
```

### 5. Retrieval Endpoint Implementation
**Endpoint**: `GET /syllabi/{user_id}`

**Functionality**:
1. Queries Firestore for all syllabi belonging to the user
2. Converts datetime objects to ISO format strings for JSON serialization
3. Returns array of syllabus metadata

**Response**:
```json
[
  {
    "id": "doc_id",
    "user_id": "user123",
    "name": "syllabus.pdf",
    "file_url": "https://...",
    "file_type": ".pdf",
    "upload_date": "2025-11-22T12:34:56",
    "created_at": "2025-11-22T12:34:56",
    "file_path": "syllabi/user123/20251122_123456_syllabus.pdf"
  }
]
```

## 🔧 Configuration Updates

### Environment Variables (.env)
```properties
FIREBASE_STORAGE_BUCKET=syllabus-connect.appspot.com
```

### Dependencies (requirements.txt)
```
python-multipart==0.0.6
```

## ⚠️ Required: Firebase Storage Enablement

**IMPORTANT**: The Firebase Storage bucket must be enabled in the Firebase Console before the upload functionality will work.

### Steps to Enable Firebase Storage:
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project: **syllabus-connect**
3. Click on **Storage** in the left sidebar
4. Click **Get Started**
5. Accept the default security rules (can be customized later)
6. Select a Cloud Storage location (e.g., `us-central1`)
7. Click **Done**

### Current Status:
- ❌ Storage bucket does not exist yet
- Error: "The specified bucket does not exist"
- Once enabled, the bucket will be at: `syllabus-connect.appspot.com`

## 🧪 Testing

### Test File Created:
`backend/test_syllabus.txt` - A sample syllabus for testing

### Test Commands:

#### Upload a file:
```bash
curl -X POST "http://localhost:8000/syllabi/upload" \
  -F "file=@test_syllabus.txt" \
  -F "user_id=test_user_123"
```

#### Retrieve user's syllabi:
```bash
curl "http://localhost:8000/syllabi/test_user_123"
```

#### Test with different file types:
```bash
# PDF file
curl -X POST "http://localhost:8000/syllabi/upload" \
  -F "file=@syllabus.pdf" \
  -F "user_id=test_user_123"

# DOCX file
curl -X POST "http://localhost:8000/syllabi/upload" \
  -F "file=@syllabus.docx" \
  -F "user_id=test_user_123"
```

#### Test validation errors:
```bash
# Invalid file type (should fail)
curl -X POST "http://localhost:8000/syllabi/upload" \
  -F "file=@image.jpg" \
  -F "user_id=test_user_123"

# Expected error: "Invalid file type. Only .pdf, .docx, .txt files are allowed"
```

## 🔄 Integration with Frontend

The frontend already has the upload functionality implemented in `App.jsx`:

```javascript
const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', user.uid);

  const res = await fetch(`${API_URL}/syllabi/upload`, {
    method: 'POST',
    body: formData,
  });
  // ... handle response
}
```

The frontend already calls:
- ✅ `GET /syllabi/{user_id}` - Implemented
- ✅ `POST /syllabi/upload` - Implemented

## 📝 File Storage Structure

```
syllabi/
  └── {user_id}/
      ├── 20251122_123456_syllabus1.pdf
      ├── 20251122_130000_syllabus2.docx
      └── 20251122_140000_syllabus3.txt
```

## 🔒 Security Considerations

### Current Implementation:
- Files are made publicly accessible via `blob.make_public()`
- Anyone with the URL can access the files

### Future Improvements:
1. **Use Signed URLs** instead of public URLs for private access:
   ```python
   # Generate signed URL valid for 1 hour
   url = blob.generate_signed_url(
       version="v4",
       expiration=timedelta(hours=1),
       method="GET"
   )
   ```

2. **Implement Firebase Storage Security Rules**:
   ```
   rules_version = '2';
   service firebase.storage {
     match /b/{bucket}/o {
       match /syllabi/{userId}/{filename} {
         allow read, write: if request.auth != null && request.auth.uid == userId;
       }
     }
   }
   ```

3. **Add file scanning** for malicious content before storage

## 🎯 Next Steps

1. ✅ Enable Firebase Storage in Console (see instructions above)
2. Test upload with all three file types (.pdf, .docx, .txt)
3. Verify files appear in Firebase Storage Console
4. Verify metadata appears in Firestore Console
5. Test retrieval endpoint
6. Integrate with frontend and test end-to-end
7. (Future) Implement PDF/DOCX parsing to extract assignments/dates
8. (Future) Add `/syllabi/{syllabus_id}/items` endpoint for parsed content

## 📊 API Endpoints Summary

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| POST | `/syllabi/upload` | Upload syllabus file | ✅ Implemented |
| GET | `/syllabi/{user_id}` | Get user's syllabi | ✅ Implemented |
| GET | `/syllabi/{syllabus_id}/items` | Get syllabus items | ❌ Not yet implemented |
| POST | `/calendar/add` | Add to Google Calendar | ❌ Not yet implemented |

## 🐛 Known Issues

None - Implementation is complete pending Firebase Storage enablement.

## 📚 Additional Resources

- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Firebase Storage Python SDK](https://firebase.google.com/docs/storage/admin/start)
- [Google Cloud Storage Python Client](https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-python)
