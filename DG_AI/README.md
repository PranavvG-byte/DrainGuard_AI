# 🧠 DrainGuard AI – Intelligent Urban Drainage Monitoring & Flood Risk Prediction System

> **Smart Infrastructure for Smarter Cities** – Predicting drainage blockages and urban floods before they happen.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Our Solution](#our-solution)
- [Core Features](#core-features)
- [Dataset](#dataset)
- [System Workflow](#system-workflow)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Example AI Output](#example-ai-output)
- [Hackathon Value Proposition](#hackathon-value-proposition)
- [Future Enhancements](#future-enhancements)
- [Team](#team)

---

## Overview

**DrainGuard AI** is a smart, AI-powered urban drainage monitoring system designed to predict blockages, overflow risks, and urban flooding events **before they occur**.

The system combines:
- 🌐 **IoT sensor data** for real-time monitoring
- 🤖 **Machine Learning models** for predictive analytics
- ✨ **Generative AI explanations** for actionable insights

### Why DrainGuard AI?

Instead of only monitoring water levels, DrainGuard AI:

| Capability | Traditional Systems | DrainGuard AI |
|-----------|-------------------|--------------|
| Detect abnormal patterns | ❌ No | ✅ Yes |
| Predict overflow risks | ❌ No | ✅ Yes |
| Explain root causes | ❌ No | ✅ Yes |
| Recommend actions | ❌ No | ✅ Yes |

---

## Problem Statement

### Current Challenges

Urban flooding and drainage overflow occur due to:

- 🚫 **Undetected blockages** – Silent failures in drainage systems
- 🌧️ **Sudden rainfall surges** – Unpredictable weather events
- 📅 **Poor maintenance scheduling** – Reactive, not proactive
- ⏱️ **Delayed response** – Authorities respond after issues occur

### The Gap

Traditional monitoring systems:
- Provide raw sensor data only
- Alert **only after** threshold breach
- Lack predictive intelligence
- Do not offer actionable recommendations

**Key Question:** Authorities know **when** flooding starts, but not:
- ❓ **Why** did it happen?
- ❓ **Which drain** is at risk next?
- ❓ **What maintenance action** should be taken?

---

## Our Solution

DrainGuard AI transforms raw sensor data into **intelligent, actionable insights** through a three-layer architecture:

### 🌧️ Layer 1: Predictive Analytics
Uses time-series forecasting to predict:
- Water level rise trends
- Flow rate surges
- Rainfall impact on drainage

### 🚨 Layer 2: Risk Detection Engine
Automatically identifies:
- Blockage probability scores
- Imminent overflow risk windows
- High-risk drainage zones
- Sensor anomaly signals

### ✨ Layer 3: Generative AI Reasoning
Transforms numerical predictions into:
- Clear, understandable risk explanations
- Root-cause identification
- Priority-based maintenance recommendations
- Municipal action plans

### 📊 Data Flow

```
Sensor Data → Prediction → Risk Detection → AI Explanation → Action
```

---

## 🚀 Core Features

| Feature | Description |
|---------|-------------|
| 📊 **Real-time Monitoring** | Water level & flow rate tracking |
| 🌧️ **Rainfall Analysis** | Impact assessment on drainage systems |
| 🚨 **Smart Alerts** | Automatic overflow & blockage detection |
| 🧠 **AI Explanations** | Why risks occur and what to do |
| 🗺️ **Risk Visualization** | Location-wise risk mapping |
| 💬 **Ask-the-AI Interface** | Query system for municipal teams |
| 🖥️ **Interactive Dashboard** | Streamlit-based web interface |

---

## 📊 Dataset

### Source
- Simulated IoT sensor dataset
- Historical weather/rainfall data

### Data Type
Multivariate time-series data with enhanced realism:

| Enhancement | Purpose |
|------------|---------|
| Synthetic blockage signals | Simulate real blockage patterns |
| Rain intensity spikes | Model extreme weather events |
| Cleaning cycle delays | Reflect operational realities |
| Random sensor noise | Account for sensor imprecision |

### Dataset Schema

```
timestamp, drain_id, water_level, flow_rate, rainfall_intensity, blockage_indicator
```

---

## 🧠 System Workflow

**Steps:**
1. Collect sensor data & rainfall information
2. Preprocess and clean data
3. Forecast water level & flow trends
4. Detect blockage/overflow risks
5. Generate AI-powered explanations
6. Display actionable insights on dashboard

```
Sensor Data Collection
         ↓
Data Preprocessing
         ↓
Water Level & Flow Forecasting
         ↓
Blockage/Overflow Detection
         ↓
AI Explanation Generation
         ↓
Dashboard & Alerts
```

---

## 🛠️ Technology Stack

### Programming Language
- **Python** 3.8+

### Data & Machine Learning
| Library | Purpose |
|---------|---------|
| **Pandas** | Data manipulation & analysis |
| **NumPy** | Numerical computing |
| **Scikit-learn** | Machine learning models |
| **Statsmodels** | ARIMA forecasting |
| **TensorFlow/LSTM** | Deep learning (optional) |

### Generative AI
- **Large Language Model (LLM)** – For intelligent explanations
- **Prompt Engineering** – Customized municipal guidance

### Frontend
- **Streamlit** – Interactive web dashboard

---

## 📂 Project Structure

```
drainguard_ai/
│
├── data/              # Raw & processed datasets
│   ├── raw/           # Original sensor data
│   └── processed/     # Cleaned datasets
│
├── notebooks/         # Data analysis & experiments
│   ├── eda.ipynb
│   └── model_experiments.ipynb
│
├── src/               # Core ML & AI modules
│   ├── models/        # ML model implementations
│   ├── preprocessing/ # Data cleaning pipeline
│   ├── reasoning/     # AI explanation engine
│   └── utils/         # Helper functions
│
├── dashboard/         # Streamlit application
│   └── streamlit_app.py
│
├── outputs/           # Generated predictions & reports
│
├── config/            # Configuration files
│
├── demo/              # Hackathon presentation materials
│
├── requirements.txt   # Python dependencies
│
├── README.md          # Project documentation
│
└── .gitignore         # Git ignore rules
```

---

## ⚙️ Installation & Setup

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd drainguard_ai
```

### Step 2: Create Virtual Environment

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables (Optional)

```bash
cp .env.example .env
# Edit .env with your LLM API keys if using external services
```

---

## ▶️ Running the Application

### Launch Streamlit Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

### Access in Browser

Open your web browser and navigate to:

```
http://localhost:8501
```

### Interactive Features

- 📈 View real-time drainage metrics
- 🎯 Set custom alert thresholds
- 📊 Analyze historical trends
- 🤖 Ask DrainGuard AI for insights
- 📥 Download prediction reports

---

## 💡 Example AI Output

### ⚠️ Overflow Risk Detected – Drain ID: D-204

**Risk Level:** 🔴 **CRITICAL** (87% probability)

**AI Analysis:**

Water level has risen by **28% in the last 6 hours** due to increased rainfall intensity. Flow rate shows **irregular fluctuation** indicating potential debris blockage.

If rainfall continues at current rate, **overflow is likely within 3–4 hours**.

**Recommended Actions:**
1. ✅ Dispatch maintenance team to drain D-204
2. ✅ Clear debris and perform unclogging
3. ✅ Monitor adjacent drains (D-203, D-205) for cascading risks
4. ✅ Notify residents in flood-prone zones

**Confidence:** 87% | **Last Updated:** 2 minutes ago

---

## 🧑‍⚖️ Hackathon Value Proposition

✔️ **Innovative Integration** – Combines IoT + ML + Generative AI  
✔️ **Real-World Impact** – Transforms reactive to predictive city management  
✔️ **Practical Use-Case** – Addresses critical urban infrastructure challenges  
✔️ **Highly Demonstrable** – Interactive dashboard with instant results  
✔️ **Scalable** – Ready for smart city adoption  
✔️ **Socially Responsible** – Saves lives and protects critical infrastructure  

---

## 🔮 Future Enhancements

| Phase | Features |
|-------|----------|
| **Phase 2** | 📡 Live IoT hardware integration |
| **Phase 3** | 🗺️ GIS-based drain network visualization |
| **Phase 4** | 📱 SMS/Email alert system for teams |
| **Phase 5** | 🤖 Autonomous maintenance scheduling |
| **Phase 6** | 🔗 Smart City ERP integration |
| **Phase 7** | 🌍 Multi-city deployment framework |

---

## 👥 Team

**DrainGuard AI** – Built with passion for smarter cities.

---

**Last Updated:** February 2026
