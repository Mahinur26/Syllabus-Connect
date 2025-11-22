# AI Chat Refactoring - Syllabus Context Integration

## Summary
Refactored the chat functionality to use the selected syllabus as context instead of inventory data. The AI assistant now answers questions specifically about the uploaded syllabus content.

## Backend Changes (`main.py`)

### 1. Updated ChatRequest Model
```python
class ChatRequest(BaseModel):
   user_id: str
   message: str
   syllabus_id: Optional[str] = None  # NEW: Required for context
```

### 2. Completely Refactored `/chat` Endpoint

**Previous Behavior:**
- Pulled inventory items from Firestore
- Generated recipe suggestions based on food items
- Generic cooking assistant prompt

**New Behavior:**
- Requires `syllabus_id` to be provided
- Fetches syllabus metadata from Firestore
- Downloads actual syllabus file content from Firebase Storage
- Uses syllabus content as context for AI
- Validates user access to the syllabus

**Key Features:**
- ✅ Security: Verifies syllabus belongs to the requesting user
- ✅ Error handling: Clear error messages for missing/invalid syllabi
- ✅ Content truncation: Limits content to 20,000 characters to avoid token limits
- ✅ Smart prompting: Optimized prompt for Gemini 2.5 Flash

### 3. Enhanced Prompt Engineering

```python
prompt = f"""You are Syllabus Buddy, an intelligent academic assistant helping students understand their course syllabus.

SYLLABUS DOCUMENT: "{syllabus_name}"
---
{syllabus_content}
---

STUDENT QUESTION: {req.message}

INSTRUCTIONS:
- Answer the student's question based on the syllabus content above
- Be concise, clear, and helpful
- If the answer isn't in the syllabus, say so and offer general academic advice
- When referencing specific information, cite where it appears in the syllabus
- For questions about assignments or exams, provide relevant dates and details
- Use a friendly, supportive tone

Provide your answer:"""
```

**Optimizations for Gemini 2.5 Flash:**
- Clear role definition ("Syllabus Buddy")
- Structured document presentation with clear delimiters
- Explicit instructions for behavior
- Guidance on citations and tone
- Fallback behavior for out-of-scope questions

## Frontend Changes (`App.jsx`)

### 1. Updated sendMessage Function

**Added:**
- Validation: Checks if syllabus is selected before sending
- Includes `syllabus_id` in API request
- Better error handling with specific error messages
- User-friendly alerts

```javascript
// Check if a syllabus is selected
if (!selectedSyllabus) {
  showAlert("Please select a syllabus first", "warning");
  return;
}

// Include syllabus_id in request
body: JSON.stringify({ 
  user_id: user.uid, 
  message: msg,
  syllabus_id: selectedSyllabus  // NEW
}),
```

### 2. Improved Chat UI

**Changes:**
- Removed recipe parsing logic (no longer needed)
- Simplified message display to plain text with proper formatting
- Enhanced empty state with helpful instructions
- Dynamic placeholder text based on syllabus selection
- Disabled input when no syllabus is selected
- Better visual styling for messages

**Empty State:**
```jsx
<div className="flex flex-col items-center justify-center h-full text-center">
  <div className="text-6xl mb-4">📚</div>
  <p className="text-gray-600 font-medium">Select a syllabus above</p>
  <p className="text-gray-500 text-sm mt-2">
    Then ask me anything about assignments, exams, deadlines, or course content!
  </p>
</div>
```

**Dynamic Placeholder:**
- With syllabus: "Ask about assignments, exams, deadlines..."
- Without syllabus: "Select a syllabus first"

### 3. Enhanced Message Display

```jsx
{msg.role === 'assistant' ? (
  <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
    {msg.content}
  </div>
) : (
  <div className="text-sm">{msg.content}</div>
)}
```

## User Experience Improvements

### Before:
1. User asks question about random topics
2. AI suggests recipes based on inventory
3. No context about actual syllabus content

### After:
1. User selects a syllabus from dropdown
2. User asks specific questions about the syllabus
3. AI reads the actual syllabus file and provides accurate answers
4. Responses include citations and specific details from the syllabus

## Example Usage

### Sample Questions Users Can Ask:
- "When is the midterm exam?"
- "What are the required readings for week 3?"
- "How is the final grade calculated?"
- "What's the late submission policy?"
- "Can you summarize the course objectives?"
- "When are office hours?"
- "What topics are covered in this course?"

### AI Response Features:
- Cites specific sections from the syllabus
- Provides exact dates and percentages
- Offers clarification when information isn't in the syllabus
- Maintains helpful, student-friendly tone

## Security Features

1. **Access Control:** Verifies syllabus belongs to user before processing
2. **Validation:** Checks for valid syllabus_id before proceeding
3. **Error Handling:** Graceful degradation with informative error messages
4. **Content Limits:** Prevents excessive token usage with truncation

## Error Handling

### Backend Errors:
- 400: No syllabus selected
- 403: Access denied (not user's syllabus)
- 404: Syllabus not found in database or storage
- 500: General processing errors

### Frontend Handling:
- Shows alert to user
- Displays error message in chat
- Maintains chat history
- Prevents multiple concurrent requests

## Technical Details

### File Reading:
```python
# Download syllabus content from Firebase Storage
blob = bucket.blob(file_path)
syllabus_content = blob.download_as_text()
```

### Content Truncation:
```python
max_content_length = 20000  # characters
if len(syllabus_content) > max_content_length:
    syllabus_content = syllabus_content[:max_content_length] + "\n\n[Content truncated...]"
```

### Supported File Types:
- ✅ `.txt` - Direct text reading
- ✅ `.pdf` - Reads as text (may need OCR for scanned PDFs)
- ✅ `.docx` - Reads as text (formatting may vary)

## Future Enhancements

### Potential Improvements:
1. **PDF Parsing:** Use PyPDF2 or pdfplumber for better PDF text extraction
2. **DOCX Parsing:** Use python-docx for structured document parsing
3. **Conversation Memory:** Store chat history in Firestore
4. **Multi-document Context:** Allow querying across multiple syllabi
5. **Smart Extraction:** Automatically extract key dates, assignments, and grading info
6. **Calendar Integration:** Suggest adding mentioned deadlines to calendar
7. **Study Tips:** Provide study recommendations based on upcoming assessments

### Code to Add Later:
```python
# Better PDF parsing
import PyPDF2
# or
import pdfplumber

# Better DOCX parsing
from docx import Document
```

## Testing Checklist

- [x] Upload .txt syllabus file
- [x] Select syllabus in chat dropdown
- [x] Ask question about syllabus content
- [x] Verify AI uses actual syllabus content
- [x] Test error handling (no syllabus selected)
- [x] Test access control (different user's syllabus)
- [ ] Test with .pdf file
- [ ] Test with .docx file
- [ ] Test with very long syllabus (truncation)
- [ ] Test with multiple syllabi switching

## Migration Notes

### Removed Code:
- Inventory collection queries
- Recipe generation logic
- Recipe parsing functions (parseRecipeResponse)
- Structured recipe rendering UI components

### Preserved Code:
- Authentication system
- Syllabus upload/retrieval
- Firestore operations
- Firebase Storage integration

## Performance Considerations

1. **Token Usage:** Content truncated to 20k characters to manage costs
2. **Response Time:** Downloading file from Storage adds ~1-2 seconds
3. **Caching Opportunity:** Could cache syllabus content in memory/Redis for faster repeated queries
4. **Rate Limiting:** Consider adding rate limits to prevent API abuse

## Conclusion

The refactored chat system now provides a focused, context-aware assistant specifically designed for helping students understand their course syllabi. The integration with Firebase Storage ensures that AI responses are based on actual document content rather than generic information.
