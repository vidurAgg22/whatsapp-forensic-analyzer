# 🔍 WhatsApp Forensic Analyzer

A full-stack web application for forensic analysis of WhatsApp group chats using Exploratory Data Analysis (EDA), Natural Language Processing (NLP), and forensic algorithms. Built with Django, Plotly, and D3.js.

> 📄 This project is an extended implementation of the research paper:
> **"WhatsApp Forensic Analysis for Group Chats Using Exploratory Data Analysis and Natural Language Processing"**
> Published in *Lecture Notes in Networks and Systems, Vol. 1265*, Springer Nature Singapore, 2025.
> 🔗 [View Paper on Springer](https://link.springer.com/chapter/10.1007/978-981-96-2299-3_3)

---

## 🌐 Live Demo

> [**https://whatsapp-forensic-analyzer-production.up.railway.app/**](https://whatsapp-forensic-analyzer-production.up.railway.app/)
> *(Try the built-in sample chats — no upload required)*

---

## 📸 Screenshots

| Landing Page | EDA Dashboard | Forensics Report |
|:---:|:---:|:---:|
| ![Home](screenshots/home.png) | ![Dashboard](screenshots/dashboard.png) | ![Forensics](screenshots/forensics.png) |

---

## ✨ Features

### 📊 Exploratory Data Analysis

- **Message frequency over time** — Line chart showing daily message volume across the entire chat history
- **Activity heatmap** — Month × Day-of-week heatmap to pinpoint the most communicative periods
- **Top active members** — Horizontal bar chart of the most frequent senders
- **Average message length** — Communication style analysis per member
- **Hourly, daily, and monthly activity** — Three charts showing when the group is most active
- **Top 10 most active dates** — Table with message counts for peak days
- **Top media senders** — Bar chart of members who share the most media
- **Word cloud** — Visual frequency map of the most common vocabulary
- **Most used words** — Horizontal bar chart of top 20 words (stopwords filtered in English and Hindi)
- **Emoji leaderboard** — Visual grid of top 10 emojis with counts

### 😊 Sentiment Analysis

- **VADER NLP** — Every message classified as positive, negative, or neutral
- **Overall sentiment pie chart** — Group-wide emotional distribution
- **Per-member stacked bar chart** — Each member's emotional profile side by side
- **Sentiment table** — Detailed breakdown with tone badge (Positive / Negative / Neutral) per member

### 🔍 Forensic Analysis

- **Criminal keyword detection** — 50+ keywords scanned using whole-word regex matching
- **Message context** — 2 messages before and after each flagged message shown automatically
- **Multi-language translation** — Each flagged message can be translated to 15+ languages (English, Hindi, French, Arabic, Chinese, Japanese, etc.) using free Google Translate API
- **Link attribution** — Every URL extracted and attributed to its sender with timestamp
- **Most shared links** — Top 10 links with full list of who shared them and when
- **Knowledge graph** — Interactive D3.js force-directed graph showing communication flows between top 10 members. Draggable nodes, edge weight labels, directional arrows
- **Message search** — Search by keyword, sender (dropdown), or date (only valid chat dates shown). Results highlighted in yellow

### 🧪 Built-in Sample Chats

Four ready-to-use sample chats — no upload needed:

- 🎓 College Study Group (Android, Hindi+English)
- 💼 Business Team (iPhone, professional)
- 🚨 Suspicious Group (forensics demo with criminal keywords)
- 💻 Real Coders Dataset (11,000+ messages, 237 members, used in the published paper)

### 🔧 Infrastructure

- Supports both **Android** and **iPhone** WhatsApp export formats
- Handles **multi-line messages**, **invisible unicode characters**, **emoji mentions**
- Robust datetime parser handles all regional WhatsApp timestamp formats
- **Loading animation** during file processing
- **Session management** — view, revisit, and delete any previous analysis
- Clean dark-theme UI built with Tailwind CSS

---

## 🛠️ Tech Stack

| Layer | Technology |
|:---|:---|
| Backend | Django 4.x (Python) |
| Database | SQLite (local) / PostgreSQL (production) |
| NLP | NLTK VADER |
| Translation | deep-translator (Google Translate, free) |
| Charts | Plotly.js |
| Knowledge Graph | D3.js v7 |
| Word Cloud | Python wordcloud + matplotlib |
| Frontend | Tailwind CSS (CDN) |
| Deployment | Railway.app |

---

## 🚀 Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/whatsapp-forensic-analyzer.git
cd whatsapp-forensic-analyzer
```

### 2. Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root directory:

```
SECRET_KEY=your-django-secret-key-here
DEBUG=True
```

Generate a secret key:

```bash
python -c "from django.utils.crypto import get_random_string; print(get_random_string(50))"
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Start the server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000`

---

## 📦 Requirements

Create a `requirements.txt` file with:

```
django>=4.0
python-dotenv
pillow
nltk
vaderSentiment
wordcloud
matplotlib
deep-translator
gunicorn
whitenoise
psycopg2-binary
```

After creating it, install with:

```bash
pip install -r requirements.txt
```

Also download the NLTK vader lexicon:

```bash
python -c "import nltk; nltk.download('vader_lexicon')"
```

---

## 📱 How to Export a WhatsApp Chat

**Android:**

1. Open the group chat
2. Tap ⋮ → More → Export chat
3. Choose **Without Media**
4. Save the `.txt` file

**iPhone:**

1. Open the group chat
2. Tap the group name at the top
3. Scroll down → Export Chat
4. Choose **Without Media**

---

## 🗂️ Project Structure

```
whatsapp_forensic_analyzer/
├── analyzer/
│   ├── models.py                  # ChatSession and Message models
│   ├── views.py                   # All Django views + AJAX endpoints
│   ├── urls.py                    # URL routing
│   ├── services/
│   │   ├── parser.py              # Android + iPhone chat parser
│   │   ├── analysis.py            # EDA, word cloud, sentiment engine
│   │   ├── forensics.py           # Keyword detection, link extraction, graph
│   │   └── save.py                # Save parsed chat to database
│   ├── sample_chats/              # Built-in sample .txt files
│   └── templates/analyzer/
│       ├── base.html              # Base layout with loading animation
│       ├── home.html              # Landing + upload page
│       ├── dashboard.html         # EDA dashboard with Plotly charts
│       ├── forensics.html         # Forensics report with D3 graph
│       └── sessions.html          # Session management
├── core/
│   ├── settings.py
│   └── urls.py
├── .env
├── requirements.txt
└── manage.py
```

---

## 🔬 Research Background

This project implements and extends the methodology described in the published paper:

**Vij, S., Agarwal, V., Aggarwal, V., & Goyal, V. (2025)**
*WhatsApp Forensic Analysis for Group Chats Using Exploratory Data Analysis and Natural Language Processing.*
In: Nanda, S.J., et al. (eds.) Data Science and Applications. Lecture Notes in Networks and Systems, vol 1265. Springer Nature Singapore.
🔗 https://link.springer.com/chapter/10.1007/978-981-96-2299-3_3

### Key extensions beyond the paper

- Web application interface (paper used Jupyter notebooks / Streamlit)
- Multi-language translation with language selection (paper used English only)
- Message search with keyword highlighting, sender filter, and date filter
- Message context display around flagged keywords
- Full link attribution showing every sender per link with timestamp
- Interactive draggable knowledge graph with edge weights and directional arrows
- Per-member sentiment stacked bar chart and table
- Activity heatmap (month × day of week)
- Built-in sample datasets including the paper's original dataset

---

## 📊 Dataset

The **Coders Group** sample included in this project is a modified version of the dataset used in the original paper:

- Source: [GitHub — tusharnankani/whatsapp-chat-data-analysis](https://github.com/tusharnankani/whatsapp-chat-data-analysis)
- Modified: Member names anonymized, date range trimmed for the paper
- Contains: 11,010 messages from 237 members (Jan–Aug 2020)

---

## 🚢 Deployment (Railway.app — Free Tier)

### 1. Create a `Procfile` in the root

```
web: gunicorn core.wsgi --log-file -
```

### 2. Update `settings.py` for production

```python
import os
from dotenv import load_dotenv
load_dotenv()

DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... rest of middleware
]

# Database (Railway provides DATABASE_URL automatically)
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR}/db.sqlite3'
    )
}
```

### 3. Add to `requirements.txt`

```
dj-database-url
```

### 4. Deploy

- Push to GitHub
- Connect repo to Railway.app
- Add environment variables: `SECRET_KEY`, `DEBUG=False`
- Railway auto-detects Django and deploys

---

## 👨‍💻 Authors

- **Vidur Agarwal** — Implementation & Web Application
  🔗 [GitHub](https://github.com/vidurAgg22) · [LinkedIn](https://linkedin.com/in/viduragarwal1)
- **Sonakshi Vij, Vinay Aggarwal, Vaibhav Goyal** — Original research paper

---

## 📄 License

This project is for educational and research purposes. The implementation is original work by the authors. The research methodology is based on the published paper referenced above.

---

⭐ If you found this useful, please star the repository!
