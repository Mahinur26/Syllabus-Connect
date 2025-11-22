# Syllabus Connect - Quick Deploy Guide

## 🚀 Deploy Frontend to Vercel in 3 Steps

### Option 1: One-Click Deploy (Easiest)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Mahinur26/Syllabus-Connect&project-name=syllabus-connect&root-directory=frontend&env=VITE_API_URL&envDescription=Backend%20API%20URL&envLink=https://github.com/Mahinur26/Syllabus-Connect)

1. Click the button above
2. Sign in with GitHub
3. Set `VITE_API_URL` to your backend URL
4. Click Deploy!

### Option 2: Manual Deploy

1. **Push code to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Deploy frontend"
   git push origin main
   ```

2. **Go to [vercel.com](https://vercel.com)**
   - Sign in with GitHub
   - Click "Add New Project"
   - Import `Syllabus-Connect` repository

3. **Configure Project**
   - **Root Directory**: `frontend` ⚠️ IMPORTANT!
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

4. **Add Environment Variable**
   - Name: `VITE_API_URL`
   - Value: `http://localhost:8000` (update after backend deployment)

5. **Deploy!**

### Option 3: Using CLI

```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```

---

## 🔧 After Deployment

### 1. Update Backend CORS
Edit `backend/.env`:
```
FRONTEND_URL=https://your-vercel-url.vercel.app
```

### 2. Update OAuth Settings
Go to [Google Cloud Console](https://console.cloud.google.com/):
- Add Vercel URL to "Authorized JavaScript origins"
- Add backend callback URL to "Authorized redirect URIs"

### 3. Update Frontend API URL
In Vercel dashboard:
- Go to Settings > Environment Variables
- Update `VITE_API_URL` to your backend URL
- Redeploy

---

## ✅ Testing Checklist

After deployment, test:
- [ ] Frontend loads
- [ ] Login works
- [ ] Upload syllabus works
- [ ] Google Calendar connection works
- [ ] Events appear in Google Calendar

---

## 🌐 Your URLs

- **Frontend**: `https://syllabus-connect-xyz.vercel.app`
- **Backend**: `https://your-backend.com`

---

## 📚 Full Documentation

See [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md) for detailed instructions.

---

## 🆘 Need Help?

Common issues:
- **CORS Error**: Check `FRONTEND_URL` in backend `.env`
- **API Not Found**: Check `VITE_API_URL` in Vercel settings
- **OAuth Error**: Check Google Cloud Console redirect URIs

---

**Ready to deploy? Start with Option 1 or 2 above!** 🚀
