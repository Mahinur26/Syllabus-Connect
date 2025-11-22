# 🔧 Fixing "No items found" Issue

## The Problem
Your syllabus (`syllabus-COP2510-F25-Yi.pdf`) was uploaded **before** the parsing feature was implemented, so it has no extracted items in the database.

## ✅ Solution 1: Re-Upload the Syllabus (Easiest)

1. In the frontend, simply **upload the same PDF again**
2. The new upload will automatically trigger parsing
3. Select it from the dropdown
4. Items will appear!

## ✅ Solution 2: Trigger Re-Parsing for Existing Syllabus

### Step 1: Find Your User ID
Open browser console (F12) and check `localStorage`:
```javascript
JSON.parse(localStorage.getItem('bullavor_user')).uid
```

### Step 2: Get Syllabus ID
In backend directory, run:
```bash
cd "/Users/toxal/Projects/Syllabus Connect/backend"
python3 reparse_syllabus.py YOUR_USER_ID
```

This will list all your syllabi with their IDs.

### Step 3: Re-Parse
Copy the syllabus ID and run:
```bash
python3 reparse_syllabus.py SYLLABUS_ID parse
```

## ✅ Solution 3: Use the API Directly

You can also trigger re-parsing via the browser:

1. Open browser console
2. Get your syllabus ID from the dropdown or from localStorage
3. Run:
```javascript
const syllabusId = "YOUR_SYLLABUS_ID"; // Get from dropdown
fetch(`http://localhost:8000/syllabi/${syllabusId}/reparse`, {
  method: 'POST'
})
.then(r => r.json())
.then(data => console.log('✅ Parsed!', data))
.catch(err => console.error('❌ Error:', err));
```

## Verify Backend Is Running

Make sure you see this in the terminal:
```
🔧 CORS Configuration:
   FRONTEND_URL: http://localhost:5173
   Allowed Origins: ['http://localhost:5173', 'http://localhost:5173/']
   Allow Credentials: True
📦 Storage bucket initialized: syllabus-connect.firebasestorage.app
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## What Will Happen

When parsing succeeds, you'll see in the backend logs:
```
🔍 Parsing syllabus: syllabus-COP2510-F25-Yi.pdf
📤 Sending to Gemini for parsing...
📥 Received response from Gemini
✅ Parsed X items from syllabus
💾 Stored X items in Firestore
```

Then refresh the frontend and select the syllabus - items should appear!

## Common Issues

### Backend not running
```bash
cd "/Users/toxal/Projects/Syllabus Connect/backend"
python3 main.py
```

### Frontend not finding items
- Check backend logs for parsing errors
- Verify syllabus was selected in dropdown
- Try re-uploading the PDF

### Parsing failed
- Check if PDF is readable (not scanned image)
- Verify dates are in clear format (e.g., "Due: January 15, 2025")
- Check backend console for error messages

## Quick Test

The fastest way: Just **re-upload your PDF** in the frontend! 🚀
