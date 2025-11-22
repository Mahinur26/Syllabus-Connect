# Quick Deployment Commands

## Backend (Render)

### Start Command (configured in Render):
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Local Testing:
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
PORT=8000 uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Frontend (Vercel)

### Already deployed at:
```
https://syllabus-connect.vercel.app
```

### Environment Variable to Set:
```
VITE_API_URL=https://syllabus-connect-backend.onrender.com
```
(Replace with your actual Render URL)

---

## Complete Deployment Flow:

1. **Deploy Backend to Render**
   - Use GitHub integration or manual deploy
   - Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Get your URL (e.g., `https://syllabus-connect-backend.onrender.com`)

2. **Update Environment Variables**
   - **In Render**: Set `BACKEND_URL` to your Render URL
   - **In Vercel**: Update `VITE_API_URL` to your Render URL
   - **In Google Cloud Console**: Add Render URL to OAuth redirect URIs

3. **Redeploy Frontend**
   - Vercel will auto-redeploy when you update environment variables
   - Or manually trigger redeploy

4. **Test**
   - Visit your frontend at `https://syllabus-connect.vercel.app`
   - Test all features end-to-end

---

## Environment Variables Needed

### Render (Backend):
- `FRONTEND_URL`: `https://syllabus-connect.vercel.app`
- `BACKEND_URL`: `https://your-app.onrender.com` (your Render URL)
- `GOOGLE_CLOUD_PROJECT`: `syllabus-connect`
- `VERTEX_AI_LOCATION`: `us-central1`
- `VERTEX_AI_MODEL`: `gemini-2.0-flash-exp`
- `FIREBASE_CREDENTIALS_JSON`: (paste full JSON content)
- `FIREBASE_STORAGE_BUCKET`: `syllabus-connect.appspot.com`

### Vercel (Frontend):
- `VITE_API_URL`: `https://your-app.onrender.com` (your Render URL)

---

## Files Ready for Deployment:

✅ `main.py` - Updated with dynamic REDIRECT_URI
✅ `requirements.txt` - All dependencies listed
✅ `render.yaml` - Render configuration
✅ `.env.example` - Environment variable template
✅ `RENDER_DEPLOYMENT.md` - Detailed deployment guide

---

## Next Steps:

1. Push your code to GitHub (if not already)
2. Create Render web service
3. Configure environment variables
4. Deploy!
5. Update Google Cloud Console OAuth redirect URIs
6. Update Vercel environment variables
7. Test complete flow
