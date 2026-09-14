
# 🌾 WAHA KUN AI - Vision Service

> AI-Powered Irrigation Problem Diagnosis System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139.0-green.svg)](https://fastapi.tiangolo.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.21.0-orange.svg)](https://www.tensorflow.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)

---

## 📋 **Table of Contents**

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Installation](#installation)
- [Run Commands](#run-commands)
- [API Endpoints](#api-endpoints)
- [Response Examples](#response-examples)
- [Severity Levels](#severity-levels)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [Troubleshooting](#troubleshooting)
- [Contributors](#contributors)

---

## 1. Overview

WAHA KUN AI Vision Service is a **Computer Vision system** that analyzes images of irrigation systems and provides a **complete diagnosis in Arabic**.

### What It Does

| Input | Process | Output |
|-------|---------|--------|
| 📸 Image of irrigation system | 🤖 EfficientNet AI Model | 📋 Complete diagnosis in Arabic |

### Diagnosis Includes

| Field | Description | Example |
|-------|-------------|---------|
| **Problem** | Arabic name | "تلف في أنبوب المياه" |
| **Problem Code** | English code | `Pipe_Damage` |
| **Confidence** | AI certainty | 77.39% |
| **Severity** | Urgency level | "حرجة" (Critical) |
| **Recommendation** | What to do | "يوصى بإيقاف مصدر المياه" |
| **Explanation** | Why AI decided | "اكتشف النموذج وجود تلف..." |
| **Repair Steps** | Step-by-step guide | 7 steps |

---

## 2. Features

### Core Features

| Feature | Description |
|---------|-------------|
| 🖼️ **Image Analysis** | Analyze irrigation system images |
| 🤖 **AI Model** | EfficientNet deep learning model (90%+ accuracy) |
| 📊 **Confidence Scoring** | 0-100% confidence percentage |
| ⚠️ **Severity Assessment** | 5 levels from Critical to Minor |
| 📝 **Repair Steps** | Detailed step-by-step instructions |
| 🔍 **Quality Check** | Automatic image validation |
| ✨ **Image Enhancement** | Auto-enhance poor quality images |

### Additional Features

| Feature | Description |
|---------|-------------|
| ⚡ **Async Processing** | RabbitMQ for background tasks |
| 🐳 **Docker Support** | Easy deployment with Docker |
| 🌐 **Arabic Output** | All responses in Arabic |
| 🚫 **No Problem Detection** | Refuses unclear/no-problem images |
| 📚 **RAG System** | Dynamic recommendations from knowledge docs |

---

## 3. Architecture

### System Layers
┌─────────────────────────────────────────────────────────────────┐
│ API Layer │
│ POST /predict | POST /predict-async | GET /health │
├─────────────────────────────────────────────────────────────────┤
│ Application Layer │
│ Prediction Service | Severity Service | RAG Service │
├─────────────────────────────────────────────────────────────────┤
│ Core Layer │
│ Entities | Interfaces | Enums | Value Objects │
├─────────────────────────────────────────────────────────────────┤
│ Infrastructure Layer │
│ AI Model | RabbitMQ | Repository | Storage │
├─────────────────────────────────────────────────────────────────┤
│ Shared Layer │
│ Config | Logger | Validators | Exceptions │
├─────────────────────────────────────────────────────────────────┤
│ Worker Layer │
│ Background Task Processing | RabbitMQ Consumer │
└─────────────────────────────────────────────────────────────────┘

text

### Layer Responsibilities

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| **API** | Endpoints, routing, schemas | `api/routes.py`, `api/app.py` |
| **Application** | Business logic orchestration | `application/services/` |
| **Core** | Domain entities and interfaces | `core/entities/`, `core/interfaces/` |
| **Infrastructure** | External dependencies | `infrastructure/models/`, `infrastructure/messaging/` |
| **Shared** | Cross-cutting concerns | `shared/config.py`, `shared/logger.py` |
| **Worker** | Background processing | `worker/worker.py` |

---

## 4. Project Structure
vision-service/
│
├── api/ # API Layer (FastAPI)
│ ├── init.py
│ ├── app.py # Main entry point
│ ├── routes.py # API endpoints
│ ├── schemas.py # Pydantic models
│ ├── dependencies.py # Dependency injection
│ └── middleware.py # CORS, logging
│
├── application/ # Application Layer
│ └── services/
│ ├── prediction_service.py # Main prediction logic
│ ├── severity_service.py # Severity calculation
│ └── recommendation_service.py # RAG recommendation
│
├── core/ # Core Layer
│ ├── entities/
│ │ └── problem.py # Problem entity
│ │
│ ├── interfaces/
│ │ ├── i_predictor.py # Interface for prediction
│ │ ├── i_severity_calculator.py # Interface for severity
│ │ └── i_recommendation_provider.py # Interface for RAG
│ │
│ ├── enums/
│ │ ├── problem_code.py # Problem types enum
│ │ ├── severity_level.py # Severity levels enum
│ │ └── status_code.py # Response status enum
│ │
│ └── value_objects/
│ ├── confidence.py # Confidence value object
│ └── diagnosis_result.py # Diagnosis result DTO
│
├── infrastructure/ # Infrastructure Layer
│ ├── messaging/
│ │ ├── rabbitmq_consumer.py # RabbitMQ consumer
│ │ └── rabbitmq_publisher.py # RabbitMQ publisher
│ │
│ ├── models/
│ │ └── efficientnet_model.py # AI model wrapper
│ │
│ ├── storage/
│ │ ├── file_storage.py # Upload/delete files
│ │ └── image_processor.py # Image processing
│ │
│ └── repositories/
│ └── problem_repository.py # Problem database access
│
├── shared/ # Shared Layer
│ ├── config.py # Configuration
│ ├── logger.py # Logging setup
│ ├── validators.py # File validation
│ ├── exceptions.py # Custom exceptions
│ └── constants.py # Shared constants
│
├── worker/ # Worker Layer
│ └── worker.py # Background task processor
│
├── knowledge_docs/ # RAG Knowledge Documents
│ ├── pipe_damage.txt
│ ├── overflow.txt
│ ├── blockage.txt
│ └── expert_advice.txt
│
├── docker/ # Docker files
│ ├── Dockerfile
│ └── docker-compose.yml
│
├── models/ # AI Model files
│ └── efficientnet_waha_kun.keras
│
├── tests/ # Test folder
│ ├── test_api.py
│ ├── test_model.py
│ └── test_severity.py
│
├── logs/ # Log files
├── uploads/ # Temporary uploads
├── test_images/ # Test images
│
├── .env # Environment variables
├── .env.example # Environment template
├── .gitignore # Git ignore
├── requirements.txt # Dependencies
├── main.py # Entry point (optional)
└── README.md # Documentation

text

---

## 5. Technologies

| Category | Technology | Version |
|----------|------------|---------|
| **Language** | Python | 3.10+ |
| **Web Framework** | FastAPI | 0.139.0 |
| **AI/ML** | TensorFlow | 2.21.0 |
| **AI Model** | EfficientNet | Pre-trained |
| **Image Processing** | Pillow | 12.3.0 |
| **Numerical** | NumPy | 2.4.6 |
| **Message Queue** | RabbitMQ | 3.x |
| **Async** | Pika | 1.3.2 |
| **Container** | Docker | Latest |
| **RAG** | ChromaDB | 0.5.0 |

---

## 6. Installation

### Prerequisites

- Python 3.10+
- Docker Desktop (for RabbitMQ)
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/malak-wq/vision-service.git
cd vision-service

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
cp .env.example .env

# 5. Start RabbitMQ
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
7. Run Commands
Option 1: Docker (Recommended)
bash
# Navigate to project
cd D:\Graduation_Project\VisionService

# Build and run
docker-compose -f docker/docker-compose.yml up --build

# Run in background
docker-compose -f docker/docker-compose.yml up -d --build

# Stop
docker-compose -f docker/docker-compose.yml down
Option 2: Local Development
Terminal 1 - API
bash
cd D:\Graduation_Project\VisionService
venv\Scripts\activate
$env:PYTHONPATH = "D:\Graduation_Project\VisionService"
uvicorn api.app:app --host 127.0.0.1 --port 8001
Terminal 2 - Worker
bash
cd D:\Graduation_Project\VisionService
venv\Scripts\activate
$env:PYTHONPATH = "D:\Graduation_Project\VisionService"
python -m worker.worker
8. API Endpoints
Method	Endpoint	Description
GET	/health	Service health check
GET	/	Service information
POST	/api/v1/predict	Synchronous prediction (1-3s)
POST	/api/v1/predict-async	Asynchronous prediction (RabbitMQ)
GET	/docs	Swagger API documentation
9. Response Examples
✅ Success Response
json
{
  "status": "success",
  "problem": "تلف في أنبوب المياه",
  "problem_code": "Pipe_Damage",
  "confidence": "77.39%",
  "severity": "حرجة",
  "recommendation": "يوصى بإيقاف مصدر المياه فوراً...",
  "explanation": "اكتشف نموذج الذكاء الاصطناعي وجود تلف...",
  "repair_steps": [
    "إيقاف مصدر المياه.",
    "تحديد مكان التلف.",
    "فحص الأنبوب بالكامل.",
    "استبدال أو إصلاح الجزء التالف.",
    "إعادة تشغيل المياه.",
    "اختبار شبكة الري.",
    "التأكد من عدم وجود أي تسرب."
  ],
  "timestamp": "2026-07-24T10:00:00"
}
❌ Refused Response (No Problem)
json
{
  "status": "refused",
  "message": "لم يتم الكشف عن مشكلة واضحة في الصورة.",
  "confidence": "45.23%",
  "suggestion": "يرجى رفع صورة توضح مكان المشكلة بشكل أفضل.",
  "timestamp": "2026-07-24T10:00:00"
}
⚠️ Uncertain Response
json
{
  "status": "uncertain",
  "message": "الصورة غير واضحة أو لا تظهر مشكلة محددة بوضوح.",
  "confidence": "58.00%",
  "suggestion": "يرجى رفع صورة أوضح أو التأكد من وجود مشكلة.",
  "timestamp": "2026-07-24T10:00:00"
}
10. Severity Levels
Level (Arabic)	Level (English)	Urgency
حرجة جداً	Very Critical	Within 1 hour
حرجة	Critical	Within 4 hours
عالية جداً	Very High	Within 12 hours
عالية	High	Within 24 hours
متوسطة	Medium	Within 48 hours
منخفضة	Low	Within 1 week
بسيطة	Minor	Next maintenance
بسيطة جداً	Very Minor	Schedule later
غير مؤثرة	Negligible	No action needed
11. Testing
bash
# Health check
curl http://localhost:8001/health

# Synchronous prediction
curl -X POST -F "file=@test_images/pipe_damage.jpg" \
  http://localhost:8001/api/v1/predict

# Asynchronous prediction
curl -X POST -F "file=@test_images/pipe_damage.jpg" \
  http://localhost:8001/api/v1/predict-async

# Swagger UI
# Open in browser: http://localhost:8001/docs

# RabbitMQ UI
# Open in browser: http://localhost:15672
# Login: guest / guest
12. Docker Deployment
bash
# Build and run
docker-compose -f docker/docker-compose.yml up --build

# Run in background
docker-compose -f docker/docker-compose.yml up -d --build

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop containers
docker-compose -f docker/docker-compose.yml down

# Stop and remove volumes
docker-compose -f docker/docker-compose.yml down -v
13. Troubleshooting
ModuleNotFoundError
bash
$env:PYTHONPATH = "D:\Graduation_Project\VisionService"
Port 8001 in Use
bash
netstat -ano | findstr :8001
taskkill /PID [PID] /F
RabbitMQ Connection Refused
bash
docker start rabbitmq
Model File Not Found
bash
# Place your model in the models folder
ls models/efficientnet_waha_kun.keras
Reinstall Dependencies
bash
pip install --no-cache-dir -r requirements.txt
14. Contributors
Name	Role	GitHub
Malak Ragab	Developer	@malak-wq
📄 License
MIT License

⭐ Star the Project
If you found this project useful, please give it a ⭐ on GitHub!

Made with ❤️ by Malak Ragab

text

---

## 🚀 **How to Add README to GitHub**

```bash
# 1. Create README.md with the content above
# 2. Add and commit
git add README.md
git commit -m "Add clean hierarchical README for vision service"
git push origin main
