# Deploying Frontend to Vercel - Complete Guide

## 🚀 Prerequisites

1. **GitHub Account** - Your code should be on GitHub
2. **Vercel Account** - Sign up at [vercel.com](https://vercel.com) (free tier is fine)
3. **Code Pushed to GitHub** - Make sure your latest changes are committed and pushed

---

## 📋 Step-by-Step Deployment

### Step 1: Prepare Your Frontend for Deployment

First, make sure your frontend has the correct configuration:

#### 1.1 Update `vite.config.js`
Your frontend should already be configured, but verify:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
  }
})
```

#### 1.2 Create Environment Variable Configuration
The frontend will need to connect to your deployed backend. We'll handle this with environment variables.

---

### Step 2: Push Your Code to GitHub

```bash
cd "/Users/toxal/Projects/Syllabus Connect"

# Check what branch you're on
git branch

# If you're on 'Mahi' branch, switch to main or create a new branch
git checkout main
# OR merge your changes
git merge Mahi

# Add all changes
git add .

# Commit
git commit -m "Prepare frontend for Vercel deployment with OAuth2 calendar integration"

# Push to GitHub
git push origin main
```

---

### Step 3: Deploy to Vercel

#### Option A: Using Vercel Dashboard (Easiest)

1. **Go to [vercel.com](https://vercel.com)** and sign in with GitHub

2. **Click "Add New Project"**

3. **Import Your Repository**
   - Select "Import Git Repository"
   - Find `Syllabus-Connect` repository
   - Click "Import"

4. **Configure Project**
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend` (IMPORTANT!)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

5. **Add Environment Variables**
   Click "Environment Variables" and add:
   
   - **Name**: `VITE_API_URL`
   - **Value**: `https://your-backend-url.com` (we'll update this later)

6. **Click "Deploy"**
   - Vercel will build and deploy your app
   - This takes 2-3 minutes

7. **Get Your Frontend URL**
   - After deployment, you'll see: `https://syllabus-connect-xyz.vercel.app`
   - Copy this URL!

#### Option B: Using Vercel CLI

```bash
# Install Vercel CLI globally
npm install -g vercel

# Navigate to frontend directory
cd "/Users/toxal/Projects/Syllabus Connect/frontend"

# Login to Vercel
vercel login

# Deploy
vercel

# Follow the prompts:
# - Set up and deploy? Y
# - Which scope? (select your account)
# - Link to existing project? N
# - Project name? syllabus-connect
# - In which directory is your code? ./
# - Override settings? N

# For production deployment:
vercel --prod
```

---

### Step 4: Configure Backend for Vercel Frontend

Now you need to update your backend's CORS to allow the Vercel URL.

Update your `.env` file:

```bash
# Backend .env
FRONTEND_URL=https://syllabus-connect-xyz.vercel.app
```

**Important**: Replace with your actual Vercel URL!

Then update the OAuth callback in Google Cloud Console:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services > Credentials**
3. Click on your OAuth 2.0 Client ID
4. Under "Authorized JavaScript origins", add:
   ```
   https://syllabus-connect-xyz.vercel.app
   ```
5. Under "Authorized redirect URIs", add:
   ```
   https://your-backend-url.com/auth/google/callback
   ```
6. Click **Save**

---

### Step 5: Update Frontend Environment Variables

After deploying your backend (next step), update the frontend environment variable:

1. Go to your Vercel project dashboard
2. Click **Settings** > **Environment Variables**
3. Update `VITE_API_URL` to your backend URL
4. Click **Save**
5. **Redeploy** (Vercel > Deployments > Latest Deployment > "..." > Redeploy)

---

## 🔧 Common Configuration Issues

### Issue: CORS Error
**Solution**: Make sure your backend `.env` has the correct Vercel URL in `FRONTEND_URL`

### Issue: API Not Found
**Solution**: Check that `VITE_API_URL` in Vercel environment variables points to your backend

### Issue: OAuth Redirect Error
**Solution**: Add Vercel URL to Google Cloud Console authorized origins and redirect URIs

---

## 📝 Vercel Configuration File (Optional)

Create `frontend/vercel.json` for advanced configuration:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

---

## 🚀 Automatic Deployments

Once connected to GitHub, Vercel automatically deploys:
- **Every push to main** = Production deployment
- **Every pull request** = Preview deployment

---

## 🎯 Next Steps

After frontend is deployed:

1. **Deploy Backend** (to Render or Google Cloud Run)
2. **Update Environment Variables**:
   - Frontend: Set `VITE_API_URL` to backend URL
   - Backend: Set `FRONTEND_URL` to Vercel URL
3. **Update OAuth Settings** in Google Cloud Console
4. **Test Everything**:
   - Upload syllabus
   - Connect Google Calendar
   - Add events
   - Verify they appear in Google Calendar

---

## 📊 Deployment Checklist

Frontend (Vercel):
- [ ] Code pushed to GitHub
- [ ] Vercel project created
- [ ] Root directory set to `frontend`
- [ ] Environment variable `VITE_API_URL` configured
- [ ] Deployment successful

Backend Configuration:
- [ ] `.env` has correct Vercel URL in `FRONTEND_URL`
- [ ] Backend restarted with new FRONTEND_URL
- [ ] Google OAuth credentials updated with Vercel URL

Testing:
- [ ] Frontend loads at Vercel URL
- [ ] Can log in/sign up
- [ ] Can upload syllabus
- [ ] Calendar connection works
- [ ] Events created successfully

---

## 💡 Tips

1. **Use Environment Variables** - Never hardcode URLs
2. **Check Build Logs** - If deployment fails, check Vercel build logs
3. **Preview Deployments** - Test changes on preview URLs before merging to main
4. **Custom Domain** - You can add a custom domain in Vercel settings (e.g., `syllabusconnect.com`)

---

## 🔗 Useful Links

- [Vercel Dashboard](https://vercel.com/dashboard)
- [Vercel Vite Deployment Guide](https://vercel.com/docs/frameworks/vite)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)

---

**Your frontend will be live at**: `https://syllabus-connect-[random].vercel.app`

Need help deploying the backend too? Let me know! 🚀
