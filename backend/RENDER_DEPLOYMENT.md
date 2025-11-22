# Render Deployment Guide for Syllabus Connect Backend

## Prerequisites
1. ✅ Backend code ready with FastAPI
2. ✅ `requirements.txt` with all dependencies
3. ✅ Firebase service account JSON file
4. ✅ Google OAuth client secrets JSON file
5. GitHub repository (recommended for auto-deployment)

---

## Step 1: Prepare Backend for Deployment

### Your backend is already configured! ✅
- `uvicorn main:app --host 0.0.0.0 --port $PORT` command ready
- PORT environment variable properly configured
- Dynamic REDIRECT_URI based on BACKEND_URL

---

## Step 2: Create Render Account & New Web Service

1. **Go to [Render.com](https://render.com)**
2. **Sign up/Login** (can use GitHub account)
3. **Click "New +"** → **"Web Service"**
4. **Connect your GitHub repository** or choose "Deploy from a Git repository"
5. **Configure the service:**
   - **Name**: `syllabus-connect-backend`
   - **Region**: Choose closest to your users (e.g., Oregon, Ohio)
   - **Branch**: `main` or `Mahi` (your current branch)
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or paid for better performance)

---

## Step 3: Configure Environment Variables in Render

Go to **Environment** tab and add these variables:

### Required Variables:

1. **FRONTEND_URL**
   ```
   https://syllabus-connect.vercel.app
   ```

2. **GOOGLE_CLOUD_PROJECT**
   ```
   syllabus-connect
   ```

3. **VERTEX_AI_LOCATION**
   ```
   us-central1
   ```

4. **VERTEX_AI_MODEL**
   ```
   gemini-2.0-flash-exp
   ```

5. **FIREBASE_STORAGE_BUCKET**
   ```
   syllabus-connect.appspot.com
   ```

6. **BACKEND_URL** (will be your Render URL)
   ```
   https://syllabus-connect-backend.onrender.com
   ```
   ⚠️ Replace with your actual Render URL after deployment

7. **FIREBASE_CREDENTIALS_JSON** (IMPORTANT!)
   - Open your Firebase service account JSON file
   - Copy the ENTIRE JSON content
   - Paste it as the value (keep it as a single line or use the "File" option)
   - Example format:
   ```json
   {"type":"service_account","project_id":"syllabus-connect","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
   ```

### Note about Google OAuth Client Secrets:
The file `client_secret_469326734352-6hhcchpik5b0ov5v6a3gl2h45tfho7q0.apps.googleusercontent.com.json` needs to be in your repository. Make sure it's committed (it's already in your backend folder).

---

## Step 4: Deploy!

1. Click **"Create Web Service"** or **"Deploy"**
2. Wait for build to complete (5-10 minutes for first deployment)
3. Once deployed, you'll get a URL like: `https://syllabus-connect-backend.onrender.com`

---

## Step 5: Update Google Cloud Console OAuth Settings

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project: **syllabus-connect**
3. Go to **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Under **Authorized redirect URIs**, add:
   ```
   https://syllabus-connect-backend.onrender.com/auth/google/callback
   ```
6. Click **Save**

---

## Step 6: Update Frontend Environment Variable

1. Go to your **Vercel Dashboard**
2. Select your **syllabus-connect** project
3. Go to **Settings** → **Environment Variables**
4. Update `VITE_API_URL`:
   ```
   https://syllabus-connect-backend.onrender.com
   ```
5. **Redeploy** your frontend for changes to take effect

---

## Step 7: Test Your Deployment

1. Visit your frontend: `https://syllabus-connect.vercel.app`
2. Sign up/Login
3. Upload a syllabus (test parsing)
4. Connect Google Calendar (test OAuth flow)
5. Add items to calendar (test end-to-end)

---

## Common Issues & Troubleshooting

### ❌ Build fails with "Module not found"
- Check `requirements.txt` has all dependencies
- Make sure you selected the correct root directory (`backend`)

### ❌ "Firebase credentials not found"
- Verify `FIREBASE_CREDENTIALS_JSON` environment variable is set
- Make sure the JSON is valid (no extra line breaks or formatting issues)

### ❌ OAuth redirect fails
- Make sure `BACKEND_URL` environment variable matches your Render URL
- Verify Google Cloud Console has the correct redirect URI
- Check that OAuth client secrets file is in your repository

### ❌ CORS errors
- Make sure `FRONTEND_URL` is set to your Vercel URL (no trailing slash)
- Check that your frontend is using the correct API URL

### ❌ Free tier limitations
- Render free tier sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- Consider upgrading to paid tier for production use

---

## Environment Variables Summary

| Variable | Example Value | Required |
|----------|---------------|----------|
| `FRONTEND_URL` | `https://syllabus-connect.vercel.app` | ✅ |
| `BACKEND_URL` | `https://syllabus-connect-backend.onrender.com` | ✅ |
| `GOOGLE_CLOUD_PROJECT` | `syllabus-connect` | ✅ |
| `VERTEX_AI_LOCATION` | `us-central1` | ✅ |
| `VERTEX_AI_MODEL` | `gemini-2.0-flash-exp` | ✅ |
| `FIREBASE_CREDENTIALS_JSON` | `{...full JSON...}` | ✅ |
| `FIREBASE_STORAGE_BUCKET` | `syllabus-connect.appspot.com` | ✅ |
| `PORT` | Auto-provided by Render | ✅ |

---

## Quick Deployment Checklist

- [ ] Created Render web service
- [ ] Set build command: `pip install -r requirements.txt`
- [ ] Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Added all environment variables in Render
- [ ] Deployed and got Render URL
- [ ] Updated `BACKEND_URL` in Render to match actual URL
- [ ] Added redirect URI to Google Cloud Console
- [ ] Updated `VITE_API_URL` in Vercel
- [ ] Redeployed frontend
- [ ] Tested complete flow

---

## After Deployment

Your backend will be live at: `https://syllabus-connect-backend.onrender.com`

You can monitor:
- **Logs**: Real-time logs in Render dashboard
- **Metrics**: CPU, memory usage
- **Events**: Deployment history

Good luck with your deployment! 🚀
