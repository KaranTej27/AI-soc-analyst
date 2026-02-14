🛡️ AI SOC Analyst
Behavioral Log Anomaly Detection Platform

AI SOC Analyst is a behavioral anomaly detection platform that analyzes system log data using unsupervised machine learning.

Instead of relying on static rule-based detection, the system learns normal behavioral patterns and identifies statistical deviations in real time.

🚀 Overview

Traditional SIEM systems depend on predefined rules:

IF condition → trigger alert


AI SOC Analyst uses:

Behavioral feature engineering

Isolation Forest anomaly detection

Risk scoring normalization (0–100 scale)

Categorical risk classification (LOW / MEDIUM / HIGH)

Interactive FastAPI dashboard

The system automatically detects unusual activity patterns without manual rule configuration.

🧠 Core Capabilities
🔍 Behavioral Feature Engineering

5-minute time window aggregation per IP

Failed request analysis (HTTP ≥ 400)

Success ratio computation

Unique endpoint diversity tracking

Request rate per minute

Average inter-request time gap

🤖 Machine Learning Detection

Isolation Forest (unsupervised)

Feature scaling (StandardScaler)

Anomaly scoring

Risk normalization to 0–100 scale

Risk level classification

📊 Web Dashboard

CSV log upload

Summary metrics:

Total IPs analyzed

Total anomalies detected

High-risk sessions

Average risk score

Risk-sorted results table

Clean SaaS-style UI

🏗️ Architecture
User Upload CSV
        ↓
Schema Normalization
        ↓
Feature Engineering
        ↓
Isolation Forest Model
        ↓
Risk Score Normalization
        ↓
Risk Level Assignment
        ↓
Dashboard Rendering

📂 Project Structure
app/
│
├── routes/
│   ├── upload.py
│   ├── detect.py
│
├── services/
│   ├── preprocessing.py
│   ├── model.py
│   ├── risk.py
│
├── templates/
│   ├── about.html
│   ├── login.html
│   ├── signup.html
│   ├── onboard.html
│   ├── logs.html
│
├── static/
│
├── main.py
│
data/
│
requirements.txt

⚙️ Installation

Clone the repository:

git clone https://github.com/KaranTej27/AI-soc-analyst.git
cd AI-soc-analyst


Install dependencies:

pip install -r requirements.txt


Run the application:

python -m uvicorn app.main:app --reload


Open in browser:

http://127.0.0.1:8000

📄 Supported Log Format

The system automatically normalizes common column variants.

Minimum required fields (case-insensitive):

ip
timestamp
endpoint
status


Accepted variations:

IP / ip_address

Time / datetime

URL / path

Status / staus (typo tolerant)

📊 Risk Classification
Risk Score	Level
≥ 75	HIGH
40 – 74	MEDIUM
< 40	LOW

Risk score is derived from normalized Isolation Forest anomaly output.

🧪 Example Use Cases

Detect brute force attempts

Identify abnormal access patterns

Flag unusual off-hours activity

Detect slow-and-low data staging

Highlight behavioral deviations without predefined rules

🔐 Future Enhancements

Persistent database storage

Multi-tenant account isolation

Real-time streaming ingestion

LLM-based anomaly explanations

Automated remediation workflows

📌 Tech Stack

Backend: FastAPI

ML: Scikit-learn

Data Processing: Pandas, NumPy

Frontend: HTML, CSS, Jinja2

Server: Uvicorn

📄 License

This project is developed for educational and research purposes.

Now hit Commit changes and it’ll look clean and professional on GitHub.

If you want, I can also give you:

A version with GitHub badges

A more “startup pitch” style README

Or a recruiter-optimized version

Your move
