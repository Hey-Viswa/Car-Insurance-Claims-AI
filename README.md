# 🚗 Vanguard ClaimOS: Automated Car Insurance Claims & Damage Assessment Engine

> **Final Year Engineering Major Project / Production Adjudication Suite**  
> **Stack:** Next.js 14 (React) + Tailwind CSS (shadcn/ui Zinc) + FastAPI + PyTorch + Scikit-Learn + Neon Serverless PostgreSQL  
> **Repository:** https://github.com/Hey-Viswa/Car-Insurance-Claims-AI

---

## 🏗️ Multimodal Machine Learning Pipeline

Vanguard ClaimOS runs an end-to-end 4-phase multimodal AI evaluation pipeline for every uploaded vehicle incident photo:

`
                          [ Ingested Vehicle Image ]
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        ▼                            ▼                            ▼
 [ MobileNetV2 CNN ]          [ SVM + HOG ]             [ K-Means (k=3) HSV ]
 • Damage Severity Class     • Frame Deformation        • Surface Defect %
 • Minor / Moderate / Severe • Flag: 0 or 1             • Damage Overlay Mask
 • Softmax Confidence        • 8,100 Gradients          • Damage Pixels Isolated
        │                            │                            │
        └────────────────────────────┼────────────────────────────┘
                                     │
                                     ▼
                     [ Phase 4: Random Forest Fusion ]
                     • Feature Vector: [SeverityClass, DeformationFlag, DamageAreaPct]
                     • Repair Cost Tier: LOW / MEDIUM / HIGH
                     • Dynamic Estimate: USD ($) & INR (₹)
                     • Underwriting Action & STP SLA Decision
`

---

## ⚡ Quick Start Guide (For Setup & Execution)

### Prerequisites
- **Python 3.10+**
- **Node.js 18+ & npm**
- **Git**

### 1. Clone the Repository
`ash
git clone https://github.com/Hey-Viswa/Car-Insurance-Claims-AI.git
cd Car-Insurance-Claims-AI
`

### 2. Install Dependencies

**A. Backend Dependencies:**
`ash
pip install -r requirements.txt
`

**B. Frontend Dependencies:**
`ash
cd frontend
npm install
cd ..
`

---

## 🔑 Environment Variables

The project comes **pre-configured with live environment variables** in .env and rontend/.env.local.

- **Neon Serverless PostgreSQL Database:**
  DATABASE_URL=postgresql://neondb_owner:npg_enkrBljx35SA@ep-damp-tooth-aeq9sb5v-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require
- **Automatic Fallback:** If the network is offline or Neon cannot be reached, the system automatically falls back to local SQLite (ackend/claims.db).

---

## 🚀 Running the Application

### Option 1: One-Click Master Launcher (Windows)
Double-click:
`cmd
start_all.bat
`
This automatically boots:
1. FastAPI Backend Server on http://127.0.0.1:8000
2. Next.js 14 Frontend on http://localhost:3000
3. Opens the interactive web portal in your default browser.

---

### Option 2: Manual Terminal Launch

**Terminal 1 — FastAPI Backend:**
`ash
python -m uvicorn api:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
`
*Backend API Docs:* [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
*Health Check:* [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

**Terminal 2 — Next.js 14 Frontend:**
`ash
cd frontend
npm run dev
`
*Frontend Portal:* [http://localhost:3000](http://localhost:3000)

---

## 🌟 Key Features

1. **Autonomous Damage Appraisal Studio:**
   - Real-time multimodal damage inference under 150ms.
   - Live visual damage segmentation heatmaps with interactive split-view comparison slider.
   - Pre-loaded benchmark Kaggle test vehicles (Minor, Moderate, Severe) for instant demonstration.

2. **Dual-Layer Reload State Persistence:**
   - **Instant Client Hydration:** Synchronously restores active appraisal progress, uploaded photos, and form fields from localStorage.
   - **Neon Cloud Sync:** Automatically backs up and syncs session state to Neon Serverless PostgreSQL with a 600ms debounce timer.
   - Page reloads (F5) **never lose progress**.

3. **Claims & Settlement Ledger:**
   - Persistent PostgreSQL claims registry with status badges (APPROVED, FIELD_DISPATCH, PRE_AUTH).
   - Live query filter search by VIN, Claimant, Policy Number, or Claim ID.

4. **Dynamic Settlement Policy PDF Generation:**
   - Instant 1-click generation of formal insurance settlement policy certificates with cryptographic authorization tokens.

5. **Standalone Academic Defense Dossier (PDF):**
   - Publication-grade 4-page PDF dossier built with ReportLab (GET /api/defense-pdf).
   - Includes model performance benchmarks, confusion matrices, latency SLA analysis, and top 10 college viva defense questions with model answers.

---

## 📁 Repository Structure

`
Car-Insurance-Claims-AI/
├── .env                       # Pre-configured Neon PostgreSQL connection
├── .env.example               # Template environment configuration
├── requirements.txt           # Complete Python dependencies
├── start_all.bat              # 1-Click launcher for both services
├── run_backend.bat            # Standalone backend launcher
├── run_frontend.bat           # Standalone frontend launcher
├── train_pipeline.py          # 4-Phase ML pipeline training script
├── generate_notebook.py       # Google Colab notebook generator
├── artifacts/                 # Pre-trained production weights
│   ├── cnn_model.pth          # MobileNetV2 damage classifier (PyTorch)
│   ├── svm_hog_model.pkl      # Structural frame deformation SVM
│   ├── random_forest_model.pkl# Repair cost tier Random Forest
│   ├── class_indices.json     # Class mapping definitions
│   └── Vanguard_ClaimOS_Academic_Defense_Dossier.pdf # Viva defense dossier
├── backend/                   # FastAPI microservice
│   ├── api.py                 # REST endpoints & ML inference pipeline
│   ├── database.py            # Neon PostgreSQL + SQLite dual adapter
│   ├── pdf_generator.py       # Claim settlement policy PDF engine
│   └── academic_pdf_generator.py # Academic defense dossier PDF generator
├── frontend/                  # Next.js 14 + Tailwind (shadcn/ui Zinc)
│   ├── .env.local             # Pre-configured frontend environment variables
│   ├── package.json           # Frontend package manifest
│   ├── src/app/page.tsx       # Main appraisal studio & ledger dashboard
│   └── src/app/globals.css    # Global typography & shadcn styling
└── notebooks/                 # Turn-key Google Colab master notebook
    └── Car_Insurance_Claims_Master_Colab.ipynb
`

---

## 🎓 Academic Defense Viva Highlights

- **Q: Why MobileNetV2 instead of ResNet-50?**  
  *A:* MobileNetV2 uses depthwise separable convolutions and inverted residuals, achieving equivalent accuracy with 85% fewer parameters (3.4M vs 25.6M), making it ideal for edge underwriting without high GPU cloud inference overhead.
- **Q: Why combine CNN with HOG + SVM?**  
  *A:* CNNs excel at regional color/texture damage patterns, but can overlook subtle global geometry deformations. HOG captures exact gradient orientations across 8,100 directional bins to reliably detect structural chassis/frame warping.
- **Q: Why use Neon Serverless PostgreSQL?**  
  *A:* Neon provides instantaneous auto-scaling, scale-to-zero compute when idle, and high-concurrency ACID transactions for audited insurance claims records.
