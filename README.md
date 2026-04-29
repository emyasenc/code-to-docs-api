# 📝 Code-to-Docs API

**Generate professional README files from any GitHub repository using LLM + RAG**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-LLM-orange.svg)](https://groq.com)
[![Tests](https://img.shields.io/badge/tests-38%20passing-brightgreen.svg)](tests/)
[![Deployed on Render](https://img.shields.io/badge/deployed-Render-purple.svg)](https://render.com)

---

## 🚀 What This API Does

Feed it a GitHub repository URL. Get a professional README.

No more writing documentation by hand. No more outdated READMEs.

**What you get:**
- ✅ Project description (specific to your repo)
- ✅ Features list (based on actual code)
- ✅ Tech stack detection
- ✅ **ASCII directory tree** (shows your project structure)
- ✅ Installation & usage instructions
- ✅ Contributing guidelines
- ✅ License

**Powered by:** FastAPI + Groq Llama 3 + RAG

---

## 📊 Example Output

For `https://github.com/emyasenc/phone-validation-api`:

## Project Structure
phone-validation-api/
├── core/
│ ├── usage_tracker.py
│ └── webhooks.py
├── main.py
├── requirements.txt
└── README.md

## Tech Stack
- Python 3.11
- FastAPI
- phonenumbers library

## 🛠️ Tech Stack
Category	Technologies
API Framework	FastAPI
LLM	Groq (Llama 3.3-70B)
RAG	Custom code parser + directory tree
Deployment	Render (free tier)
Caching	File-based (24h TTL)
Rate Limiting	10-50 requests/minute
Testing	Pytest (38+ tests)

## 📦 Installation (Local Development)
Prerequisites
Python 3.10+

Groq API key (free tier)

## Setup

# Clone the repository
git clone https://github.com/emyasenc/code-to-docs-api.git
cd code-to-docs-api

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# Run the API
uvicorn src.main:app --reload
The API will be available at http://localhost:8000

## 🔗 API Endpoints
Method	Endpoint	Description
GET	/health	Health check
GET	/	API information
POST	/api/v1/generate	Generate README from GitHub URL
GET	/api/v1/frameworks	List supported frameworks
GET	/api/v1/stats	API statistics
GET	/docs	Interactive Swagger documentation

## 📝 Request Example

curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/emyasenc/phone-validation-api",
    "include_readme": true
  }'
  
Response
json
{
  "success": true,
  "readme": "# Phone Validation API\n\n## Description\n...",
  "detected_framework": "python",
  "estimated_tokens": 500,
  "credits_used": 1
}

## 💰 Pricing (via RapidAPI)
Plan	Price	Requests/Month	Rate Limit
Free	$0	50	5 req/min
Pro	$19	1,000	20 req/min
Ultra	$49	5,000	50 req/min
Free tier available — test before you buy.

## 📁 Project Structure

code-to-docs-api/
├── src/
│   ├── api/v1/endpoints/    # FastAPI endpoints
│   ├── services/            # GitHub, LLM, code parser, cache
│   ├── core/                # Exceptions, security
│   ├── utils/               # Validators, logger
│   └── main.py              # Application entry point
├── tests/                   # 38+ passing tests
├── docs/                    # API & development docs
├── requirements.txt
└── README.md

## 🧪 Running Tests

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term

# Run specific test file
pytest tests/test_api/test_generate.py -v

## 🚀 Deployment
Deploy to Render (Free Tier)
Push code to GitHub

Go to render.com

Click New Web Service → Connect your repo

## 🔒 Environment Variables
Variable	Description	Required
GROQ_API_KEY	Groq API key for LLM	✅ Yes
LOG_LEVEL	Logging level (INFO, DEBUG)	❌ No
API_KEY	Optional API key protection	❌ No

## ❓ FAQ
How accurate is the generated README?
The LLM analyzes your actual repository structure and files. It doesn't invent features that don't exist.

What languages are supported?
Python, JavaScript, TypeScript, Go, Rust, Java, and more. Generic fallback for others.

Do I need a Groq API key to use the API?
No — only to run locally. The hosted API on RapidAPI uses a shared key.

How long does it take?
2-5 seconds per repository (depends on size and LLM response).

Is there a free tier?
Yes — 50 free requests/month on RapidAPI.

## 🤝 Contributing
Contributions are welcome!

Fork the repository

Create a feature branch

Make your changes

Run tests (pytest tests/ -v)

Open a Pull Request

## 📄 License
MIT License — see LICENSE for details.

## 👩‍💻 Author
Emma Yasenchak - ML Engineer & API Developer

GitHub: @emyasenc

LinkedIn: Emma Yasenchak

RapidAPI: YASEN-ALPHA

💛 Support
📧 Email: emmayasenchak@gmail.com
