# ⚡ HealthEngine

> A personalized health progression and gym overload tracker answering one daily question:  
> **"Am I becoming healthier today than yesterday?"**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57)
![Chart.js](https://img.shields.io/badge/Visuals-Chart.js-FF6384)
![TailwindCSS](https://img.shields.io/badge/Styling-Tailwind-38B2AC)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌟 Overview

Unlike standard calorie counters, **HealthEngine** unifies:
1. **🏋️ 5-Split Gym Tracker**: Push, Pull, Legs, Core, and Cardio with automated PR detection, volume tonnage, and Epley 1RM calculations.
2. **🥗 Smart Nutrition & Protein Engine**: Descriptive natural-language meal logging with automated macro estimation.
3. **🌙 Sleep & Vitality Sentinel**: Sleep duration, stress buffer, meditation check-in, and joint readiness check.
4. **📈 Strength Curves (Chart.js)**: Multi-week strength progression curves comparing day-over-day progression against baseline.
5. **⚡ Tomorrow Recovery Recommender**: Predicts neuromuscular fatigue and recommends prime training vs. active deloading.
6. **💾 Data Portability**: Complete JSON backup export and restore.

---

## 🚀 Quickstart Options

### Option A: Run Locally with Python

```bash
# 1. Clone repository
git clone https://github.com/your-username/health-engine.git
cd health-engine

# 2. Virtual environment setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start server
python run.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.  
API documentation: **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

### Option B: Run with Docker & Docker Compose (Zero Setup)

Run the entire application in an isolated container with persistent volume storage:

```bash
# 1-command startup with Docker Compose
docker compose up --build -d
```

To stop:
```bash
docker compose down
```

Using pure Docker:
```bash
docker build -t health-engine .
docker run -d -p 8000:8000 --name health-engine-app health-engine
```

---

## 🌐 100% Free Cloud Deployment Guide

### Deploying to Render.com (Free Tier — Zero Credit Card Required)

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/<your-username>/health-engine.git
   git push -u origin main
   ```
2. **Sign up at [render.com](https://render.com)** (sign in with your GitHub account).
3. Click **"New +"** → **"Web Service"**.
4. Select your `health-engine` repository.
5. Configure these fields (Render will auto-detect most via `render.yaml`):
   * **Name**: `health-engine` (or any unique name)
   * **Language**: `Python 3`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `python run.py`
   * **Instance Type**: `Free`
6. Click **"Create Web Service"**.  
   Within 2 minutes, Render will build your app and give you a live HTTPS public link (e.g., `https://health-engine-xxxx.onrender.com`) that you and your friends can open on any mobile phone or computer!

---

## 🗄️ Free Cloud Database Setup

HealthEngine uses **SQLite** by default, which works out-of-the-box with zero configuration. When scaling to a multi-user hosted database:

### Free PostgreSQL via Supabase
1. Go to **[supabase.com](https://supabase.com)** and create a free project (includes 500MB free PostgreSQL + Auth).
2. Go to **Project Settings** → **Database** → copy the **Connection string (URI)**.
3. In your Render or local `.env`, set:
   ```env
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres
   ```

### Free Serverless PostgreSQL via Neon
1. Go to **[neon.tech](https://neon.tech)** and create a free serverless PostgreSQL branch in 10 seconds.
2. Copy the connection string to `DATABASE_URL`.

---

## 📱 Mobile App Roadmap (Upcoming Phase)

HealthEngine is built using standard responsive APIs, making the upcoming mobile transition seamless:
* **Frontend Mobile Stack**: React Native + Expo.
* **Architecture**: The existing FastAPI endpoints (`/api/workout`, `/api/food`, `/api/day`, `/api/ai`) serve as the mobile backend without modifications.
* **Native Capabilities**: Background Apple HealthKit / Google Health Connect syncing for sleep and steps.

---

## 🧪 Testing

```bash
python -m unittest discover tests
```

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for details.
