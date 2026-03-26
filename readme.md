# 📡 NewsFlow - AI-Powered News Aggregator

NewsFlow is an intelligent news aggregation platform that curates personalized news digests from 100+ RSS sources across multiple categories and delivers them directly to your inbox. Built with modern AI technologies, it filters, summarizes, and ranks news articles based on your interests.

## ✨ Features

- **Personalized News Curation**: Choose from 5 main categories and 20+ subcategories
- **AI-Powered Summarization**: Intelligent article summaries using LangChain and Groq
- **Smart Ranking System**: Breaking news detection and relevance scoring
- **Beautiful Email Newsletters**: HTML email templates with organized content
- **Multi-Source Aggregation**: Pulls from 100+ trusted RSS feeds
- **Automated Scheduling**: Daily/periodic newsletter delivery via APScheduler
- **Modern Web Interface**: Streamlit-based UI with elegant design
- **RESTful API**: FastAPI backend for user and preference management

## 📋 Categories & Subcategories

### 🏃 Sports
- ⚽ Football
- 🏏 Cricket  
- 🏀 Basketball
- 🏒 Hockey

### 💻 Tech
- 🤖 AI
- 🚀 Startups & Business
- 📱 Mobile & Apps
- 🔒 Cybersecurity

### 📈 Finance
- 📊 Stocks & Investing
- 🪙 Crypto & Blockchain
- 🇮🇳 India-Focused
- 💰 General Finance & Markets
- 🏦 Central Banks & Policy

### 🔬 Science
- 🧬 Biology & Medicine
- 🚀 Space & Astronomy
- ⚗️ Physics & Chemistry
- 🔭 General Science News

### 🏛️ Policy
- 🇮🇳 Indian Government
- 🇺🇸 USA
- 🌍 International Policy Bodies

## 🏗️ Architecture

### Containerized Architecture (Docker Compose)

All services run in isolated Docker containers and can be deployed together on a single server or EC2 instance:

```
┌─────────────────┐
│   Streamlit UI  │  (Port 8501)
│   (Frontend)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │  (Port 8000)
│   (Backend API) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│   PostgreSQL    │◄─────┤  Scheduler   │
│   (Supabase)    │      │  (APScheduler)│
└─────────────────┘      └──────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  LangChain   │
                         │  Workflow    │
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  SendGrid    │
                         │  Email       │
                         └──────────────┘
```

**Deployment**: All three containers (Frontend, API, Scheduler) run on a single AWS EC2 instance using Docker Compose, making it cost-effective and easy to manage. 

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- PostgreSQL (Supabase account recommended)
- SendGrid API key (for email delivery)
- Groq API key (for AI summarization)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Soumya-RanjanBhoi/ai_news_aggregator.git
   cd ai_news_aggregator
   ```

2. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@host:port/database
   supabase_pass=your_supabase_password
   
   # AI/LLM
   GROQ_API_KEY=your_groq_api_key
   
   # Email
   SENDGRID_API_KEY=your_sendgrid_api_key
   SENDGRID_FROM_EMAIL=your_verified_sender_email
   
   # Optional
   MISTRAL_API_KEY=your_mistral_api_key  # if using Mistral
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

   This will start three services:
   - **Frontend**: http://localhost:8501
   - **API**: http://localhost:8000
   - **Scheduler**: Background news processing

4. **Access the application**
   - Open your browser and navigate to `http://localhost:8501`
   - Follow the onboarding flow to set up your preferences
   - Wait for the next scheduled run to receive your first newsletter!

### Manual Setup (Without Docker)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the API server**
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Start the Streamlit frontend** (in a new terminal)
   ```bash
   streamlit run main.py --server.port 8501
   ```

4. **Start the scheduler** (in a new terminal)
   ```bash
   python -m scheduler.sch
   ```

## ☁️ AWS EC2 Deployment

This project is designed to run on a single AWS EC2 instance using Docker Compose, making deployment simple and cost-effective. All three services (API, Frontend, and Scheduler) run together in isolated containers.

### EC2 Instance Requirements

**Recommended Instance Type**: `t3.medium` or higher
- **vCPUs**: 2
- **Memory**: 2 GB
- **OS**: Ubuntu 22.04 LTS



### Architecture on EC2

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS EC2 Instance                         │
│                  (Ubuntu 22.04 LTS)                         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          Docker Compose Network                       │  │
│  │                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │  │
│  │  │   Frontend   │  │     API      │  │Scheduler     │ │  │
│  │  │  (Streamlit) │  │  (FastAPI)   │  │(APScheduler) │ │  │
│  │  │   Port 8501  │  │   Port 8000  │  │ Background   │ │  │
│  │  └──────┬───────┘  └───────┬──────┘  └──────┬───────┘ │  │
│  │         │                  │                │         │  │
│  │         └──────────────────┴────────────────┘         │  │
│  │                    app_network                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Internet Gateway
                           ▼
        ┌──────────────────────────────────────┐
        │     External Services                 │
        │  • Supabase (PostgreSQL)             │
        │  • SendGrid (Email)                  │
        │  • Groq API (LLM)                    │
        │  • Mistral API (LLM)                 │
        │  • Firecrawl (Web Scraping)          │
        └──────────────────────────────────────┘
```

All three Docker containers run on the same EC2 instance, communicating through Docker's internal network. This single-instance architecture is:
- ✅ Cost-effective
- ✅ Easy to manage
- ✅ Simple to deploy
- ✅ Suitable for small to medium user bases (up to 1000+ users)

## 📁 Project Structure

```
ai_news_aggregator/
├── app.py                      # FastAPI backend application
├── main.py                     # Streamlit frontend application
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Backend Docker configuration
├── Dockerfile.frontend         # Frontend Docker configuration
├── scheduler/
│   ├── __init__.py
│   └── sch.py                 # APScheduler for automated news delivery
├── src/
│   ├── __init__.py
│   ├── datasource.py          # RSS feed sources configuration
│   ├── app/
│   │   └── all_function_2.py  # LangChain workflow implementation
│   ├── Gmail/
│   │   ├── send_mail.py       # Email sending functionality
│   │   └── newsletter_template.html  # Email template
│   ├── database/
│   │   ├── database.py        # Database connection setup
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schema.py          # Pydantic schemas
│   │   └── crud.py            # Database operations
│   └── Structures/            # Data structures
└── research/                  # Jupyter notebooks for experimentation
    ├── database.ipynb
    ├── final_check.ipynb
    ├── sports.ipynb
    ├── trail1.ipynb
    └── trail2.ipynb
```

## 🔧 API Endpoints

### User Management

- **GET** `/` - Health check
- **GET** `/health` - Service status
- **POST** `/create_user` - Create a new user with preferences
- **GET** `/get_user?email={email}` - Retrieve user details
- **PUT** `/user/{email}` - Update user preferences

### Example API Usage

```python
import requests

# Create a new user
response = requests.post("http://localhost:8000/create_user", json={
    "name": "John Doe",
    "email": "john@example.com",
    "preferences": [
        {
            "category": "Tech",
            "subcategories": ["AI", "Cybersecurity"]
        },
        {
            "category": "Finance",
            "subcategories": ["Crypto & Blockchain"]
        }
    ]
})

# Get user details
user = requests.get("http://localhost:8000/get_user?email=john@example.com")
```

## 🤖 How It Works

### High-Level Flow

1. **User Onboarding**: Users sign up and select their news preferences through the Streamlit interface

2. **Data Collection**: The scheduler periodically fetches articles from configured RSS feeds based on user preferences

3. **AI Processing**: 
   - Articles are processed through a dual-workflow LangGraph pipeline
   - LangChain agents analyze and summarize content
   - Breaking news detection and relevance scoring
   - Duplicate detection and filtering

4. **Newsletter Generation**: 
   - HTML emails are generated using the newsletter template
   - Articles are organized by category and subcategory
   - Top stories are highlighted

5. **Email Delivery**: 
   - Personalized newsletters are sent via SendGrid
   - Each user receives only content matching their preferences

### 🔄 Detailed Workflow Architecture

The system uses a sophisticated two-stage LangGraph workflow for processing news:

#### **Workflow 1: Single Category Processing Pipeline**

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WORKFLOW 1                                   │
│              (Processes one category/subcategory pair)              │
└─────────────────────────────────────────────────────────────────────┘

    START
      │
      ▼
┌──────────────┐
│ Extract URLs │ ──► Get RSS feed URLs from datasource.py
└──────┬───────┘     based on category and subcategory
       │
       ▼
┌──────────────────┐
│ Extract Content  │ ──► Parse RSS feeds in parallel
└──────┬───────────┘     Get top 4 articles from each source
       │
       ▼
┌──────────────────┐
│  Route by        │ ──► Conditional routing based on category
│  Category        │     (Sports, Tech, Finance, Science, Policy)
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│         Category-Specific Filtering (AI-Powered)                 │
│                                                                  │
│  Uses ChatGroq (GPT-OSS-120B) to intelligently select            │
│  TOP 4 most attention-grabbing articles based on:                │
│                                                                  │
│  • Sports: Controversy, star players, big clubs, urgency         │
│  • Tech: Innovation, major companies, breakthroughs              │
│  • Finance: Market impact, major institutions, policy changes    │
│  • Science: Discoveries, prestigious institutions, public impact │
│  • Policy: Geopolitical significance, public impact, urgency     │
│                                                                  │
│  Ensures: No duplicates, mix of topics, India-focused inclusion  │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│              Generate Summaries (AI-Powered)                      │
│                                                                   │
│  For each filtered article (async with concurrency limit):       │
│  1. Scrape full article content using Firecrawl                  │
│  2. Pass to ChatMistralAI (Devstral-2512)                        │
│  3. Generate 2-3 sentence summary                                │
│  4. Detect if breaking news (boolean)                            │
│  5. Assign relevance score (0-10)                                │
│                                                                   │
│  Retry logic: If scraping fails, return "Summary unavailable"    │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────┐
│ Format Output Structure │ ──► Create FinalResult object with:
└─────────────────────────┘     • Title, URL, Source
                                • Category, Subcategory
      │                         • Summary text
      │                         • is_breaking flag
      ▼                         • Relevance score
     END

```

#### **Workflow 2: Multi-User Parallel Processing**

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WORKFLOW 2                                   │
│             (Orchestrates Workflow 1 for all users)                 │
└─────────────────────────────────────────────────────────────────────┘

    START (User preferences list)
      │
      ▼
┌───────────────────────────────────────────────────────────────────┐
│              Run Parallel Workflows                               │
│                                                                   │
│  For each user preference (category + subcategory):               │
│                                                                   │
│  Tech_AI          ──► │                                           │
│  Finance_Crypto   ──► ├─► Execute Workflow 1 in parallel          │
│  Sports_Cricket   ──► │    (RunnableParallel)                     │
│  Science_Space    ──► │                                           │
│                                                                   │
│  Result: Dictionary with all processed articles                   │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│              Build Retry Map                                      │
│                                                                   │
│  Scan all results for "Summary unavailable"(have arised due to    │ 
│    429 error)                                                     │ 
│  For each failed summary:                                         │
│    1. Re-scrape URL using Firecrawl                               │
│    2. Use ChatMistralAI (Ministral-8B) for re-summarization       │
│    3. Create retry task in parallel map                           │
│                                                                   │
│  Output: retry_map with all failed articles                       │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│              Execute Retry                                        │
│                                                                   │
│  Run all retry tasks in parallel (RunnableParallel)               │
│  Update original results with new summaries                       │
│  Replace "Summary unavailable" with actual content                │
│                                                                   │
│  Output: Complete, gap-free results for all preferences           │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
                           END
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│              Email Generation & Delivery                          │
│                                                                   │
│  1. Group articles by category and subcategory                    │
│  2. Render HTML using newsletter_template.html                    │
│  3. Inject user name and personalized content                     │
│  4. Send via SendGrid API                                         │
└───────────────────────────────────────────────────────────────────┘
```
```
Since the workflow for each user preference is executed in parallel, it typically completes in around 30 seconds under optimal conditions.
However, if a 429 error occurs, the retry map node is triggered, which can add additional time—approximately 30 seconds depending on the number of retries.
In the worst-case scenario, the workflow may take between 1 to 1.5 minutes to complete
```

### 🧠 AI Models Used

| Model | Purpose | Provider |
|-------|---------|----------|
| **ChatGroq (GPT-OSS-120B)** | Article filtering & selection | Groq |
| **ChatMistralAI (Devstral-2512)** | Primary summarization | Mistral AI |
| **ChatMistralAI (Ministral-8B-2512)** | Retry summarization | Mistral AI |

### ⚙️ Key Technical Features

1. **Parallel Processing**: Uses `RunnableParallel` from LangChain to process multiple categories simultaneously
2. **Async Operations**: Concurrent article scraping with semaphore-based rate limiting
3. **Retry Mechanism**: Automatic retry with exponential backoff for failed API calls
4. **Smart Filtering**: AI-powered selection ensures only high-quality, relevant articles
5. **Breaking News Detection**: AI evaluates urgency and assigns scores
6. **Duplicate Prevention**: Cross-source deduplication in filtering stage

## 🛠️ Tech Stack

### Frontend
- **Streamlit**: Interactive web interface
- **Custom CSS**: Modern, responsive design

### Backend
- **FastAPI**: High-performance REST API
- **PostgreSQL**: User and preference storage
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation

### AI/ML
- **LangChain**: LLM orchestration framework
- **LangGraph**: Workflow orchestration
- **Groq**: Fast LLM inference
- **Mistral AI**: Alternative LLM provider

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **APScheduler**: Job scheduling
- **SendGrid**: Email delivery service
- **Feedparser**: RSS feed parsing

## 📧 Email Configuration

The newsletter uses a responsive HTML template that includes:
- Personalized greeting
- Category-based article organization
- Article summaries with read more links
- Source attribution
- Breaking news badges
- Clean, modern design


## 📊 Monitoring

View logs for each service:
```bash
# API logs
docker logs -f ai_news_api

# Frontend logs
docker logs -f ai_news_frontend

# Scheduler logs
docker logs -f ai_news_scheduler
```


**Made with  using AI and Python**
