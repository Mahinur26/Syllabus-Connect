# Google Calendar Integration Setup Guide

## Overview
The Google Calendar feature has been implemented! This guide will help you enable the Google Calendar API for your service account.

## What's Been Implemented

### ✅ Backend Features
1. **AI Syllabus Parsing**: Gemini automatically extracts assignments, exams, projects, etc. with dates in YYYY-MM-DD format
2. **Auto-parsing on Upload**: When a syllabus is uploaded, it's automatically parsed and items are stored in Firestore
3. **Syllabus Items Endpoint**: `/syllabi/{syllabus_id}/items` now returns parsed items from Firestore
4. **Google Calendar Endpoint**: `/calendar/add` creates calendar events for selected items

### ✅ Frontend Features
- Already implemented and working!
- Displays parsed items grouped by category
- Checkboxes for item selection
- "Add to Google Calendar" button

## Setup Instructions

### Step 1: Enable Google Calendar API

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Select your project: `syllabus-connect`

2. **Enable the Calendar API**
   - Navigate to: **APIs & Services** > **Library**
   - Search for "Google Calendar API"
   - Click on it and press **"ENABLE"**

### Step 2: Update Service Account Permissions

Your existing service account already has the necessary setup, but we need to verify the Calendar API scope:

1. **Go to IAM & Admin** > **Service Accounts**
2. Find your service account: `firebase-adminsdk-fbsvc@syllabus-connect.iam.gserviceaccount.com`
3. The service account will automatically have access to the Calendar API once it's enabled

### Step 3: Configure Calendar Access

**IMPORTANT**: Since you're using a service account, it will create events in its own calendar. To make events visible to your users, you have two options:

#### Option A: Share Service Account Calendar (Recommended for Testing)
1. Log into Google Calendar with the service account email
2. Share the calendar with your test user accounts
3. Events will appear in the shared calendar

#### Option B: Use Domain-Wide Delegation (For Production)
1. Enable Domain-Wide Delegation for your service account
2. Grant calendar scopes: `https://www.googleapis.com/auth/calendar`
3. The service account can then create events on behalf of users

### Step 4: Install Dependencies

Run this command to install the new Google Calendar API packages:

```bash
cd backend
pip install -r requirements.txt
```

New packages added:
- `google-auth==2.23.0`
- `google-auth-oauthlib==1.1.0`
- `google-auth-httplib2==0.1.1`
- `google-api-python-client==2.100.0`

### Step 5: Test the Implementation

1. **Start the backend**:
   ```bash
   cd backend
   python main.py
   ```

2. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test the workflow**:
   - Upload a syllabus (PDF, DOCX, or TXT)
   - Wait for auto-parsing (check backend console logs)
   - Select the syllabus from dropdown
   - View parsed items grouped by category
   - Select items with checkboxes
   - Click "Add to Google Calendar"
   - Check Google Calendar for events

## How It Works

### Syllabus Upload & Parsing Flow
```
1. User uploads syllabus file
   ↓
2. File saved to Firebase Storage
   ↓
3. Metadata saved to Firestore 'syllabi' collection
   ↓
4. Auto-parsing triggered
   ↓
5. Gemini extracts items with AI (categories + dates)
   ↓
6. Items saved to Firestore 'syllabus_items' collection
   ↓
7. User selects syllabus → items displayed
```

### Calendar Integration Flow
```
1. User selects items with checkboxes
   ↓
2. User clicks "Add to Google Calendar"
   ↓
3. Frontend sends selected items to /calendar/add
   ↓
4. Backend authenticates with Calendar API
   ↓
5. Backend creates all-day events for each item
   ↓
6. Events include: title, category, due date, reminders
   ↓
7. Success/failure summary returned to frontend
```

## Data Structure

### Syllabus Item in Firestore
```json
{
  "syllabus_id": "abc123",
  "category": "Assignments",
  "name": "Assignment 1: Introduction to Python",
  "due_date": "2025-01-15",
  "selected": false,
  "created_at": "2025-11-22T10:30:00Z"
}
```

### Google Calendar Event
```json
{
  "summary": "Assignments: Assignment 1: Introduction to Python",
  "description": "From syllabus: CS101_Syllabus.pdf\nCategory: Assignments",
  "start": {
    "date": "2025-01-15",
    "timeZone": "America/New_York"
  },
  "end": {
    "date": "2025-01-15",
    "timeZone": "America/New_York"
  },
  "reminders": {
    "overrides": [
      {"method": "email", "minutes": 1440},
      {"method": "popup", "minutes": 60}
    ]
  }
}
```

## Supported Categories
- Exams
- Assignments
- Homework
- Projects
- Tests
- Quizzes
- Essays
- Other

## Date Format
All dates are in **YYYY-MM-DD** format (ISO 8601) as required by Google Calendar API.

## Error Handling
- Items without dates (due_date = "TBD") are skipped
- Failed events are tracked and reported
- Response includes: `created_events`, `failed_events`, `total_created`, `total_failed`

## Testing Tips

1. **Test with a sample syllabus**: Create a text file with clear dates like:
   ```
   Assignment 1 - Due: January 15, 2025
   Midterm Exam - March 10, 2025
   Final Project - May 1, 2025
   ```

2. **Check backend logs**: Watch for parsing results:
   ```
   🔍 Parsing syllabus: test_syllabus.txt
   📤 Sending to Gemini for parsing...
   📥 Received response from Gemini
   ✅ Parsed 3 items from syllabus
   💾 Stored 3 items in Firestore
   ```

3. **Verify in Firestore**: Check the `syllabus_items` collection in Firebase Console

4. **Check Calendar**: Log into Google Calendar with the service account or shared calendar

## Troubleshooting

### "Calendar API not enabled"
- Make sure you enabled the Calendar API in Google Cloud Console
- Wait a few minutes for changes to propagate

### "No items found"
- Check if auto-parsing succeeded (backend logs)
- Verify the syllabus has clear dates
- Check Firestore `syllabus_items` collection

### "Failed to create events"
- Verify service account has Calendar API access
- Check date format is valid YYYY-MM-DD
- Ensure items have non-TBD dates

### Parsing Issues
- Gemini might struggle with unclear date formats
- Try syllabi with explicit dates like "Due: March 15, 2025"
- Check backend logs for JSON parsing errors

## Next Steps

1. ✅ Enable Google Calendar API
2. ✅ Install dependencies
3. ✅ Test with sample syllabus
4. 🔄 Configure calendar sharing (if needed)
5. 🔄 Test end-to-end workflow

## Support

If you encounter issues:
1. Check backend console logs for detailed error messages
2. Verify all dependencies are installed
3. Ensure Firebase and Calendar APIs are enabled
4. Check Firestore data structure matches documentation
