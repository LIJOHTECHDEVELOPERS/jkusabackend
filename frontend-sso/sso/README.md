# 🎓 JKUSA Student Portal - Frontend

Production-ready Single Sign-On (SSO) frontend system built with React, TypeScript, Vite, and Tailwind CSS.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

### 3. Build for Production
```bash
npm run build
```

## ✨ Features

- 🔐 Secure Cookie-Based Authentication
- 📱 Responsive Design
- 🎨 Modern UI/UX
- 🔄 Multi-Step Registration
- ✅ Real-Time Validation
- 🚀 TypeScript
- ⚡ Vite
- 🎭 Tailwind CSS

## 🔧 Backend CORS Configuration

Add this to your FastAPI backend:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://yourdomain.com",
    ],
    allow_credentials=True,  # REQUIRED!
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📁 Project Structure

```
jkusa-sso-frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── .env
```

## 🔒 Security Features

- HTTP-only cookies
- CORS protection
- Input validation
- Type safety
- Secure communication

## 📞 Support

For support, email support@jkusa.org

---

**Made with ❤️ for JKUSA Students**