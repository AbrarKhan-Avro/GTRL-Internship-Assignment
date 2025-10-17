# GTRL Internship Assignment — Python Intern

This repository contains both tasks for the **Genuine Technology & Research Ltd. (GTRL)** Python Internship Assignment.

Each task is designed to evaluate practical programming, analytical, and applied AI skills using real-world scenarios.

---

## 📊 Task 1 – Algorithmic Trading Adventure (Golden Cross)

A Python-based algorithmic trading simulator that uses historical stock data to implement a **Golden Cross strategy**.
It demonstrates data handling, analysis, and backtesting of a trading algorithm.

**Key Features:**

* Fetches historical market data using `yfinance`
* Calculates 50-day and 200-day moving averages
* Detects Golden Cross (buy) and Death Cross (sell) signals
* Simulates trades and evaluates profit/loss performance
* Optionally visualizes trading decisions and performance charts

---

## 🤖 Task 2 – Samsung Phone Advisor (RAG + LLM)

An AI-powered **Samsung smartphone question-answering system** capable of understanding natural language queries
and providing fluent, context-aware responses.

**Key Features:**

* Scrapes Samsung phone data from GSMArena
* Processes and stores structured specs in PostgreSQL
* Natural Language Understanding (NLU) using spaCy + RapidFuzz
* Data retrieval layer for querying structured information
* Answer generation using Groq GPT-OSS LLMs
* Exposed via a FastAPI interface for interactive use

---

## 🧠 Technologies Used

| Category                   | Tools & Libraries                           |
| -------------------------- | ------------------------------------------- |
| **Language**               | Python 3.13                                 |
| **Data Handling**          | Pandas, yfinance, JSON, PostgreSQL          |
| **Web Scraping**           | Requests, BeautifulSoup4, lxml              |
| **AI / NLP**               | spaCy, RapidFuzz, Groq API (GPT-OSS models) |
| **Backend**                | FastAPI, Uvicorn                            |
| **Visualization**          | Matplotlib (Task 1)                         |
| **Environment Management** | python-dotenv, virtualenv                   |

---

## 📂 Repository Structure

```
GTRL-Internship-Assignment/
│
├── Task1_AlgorithmicTrading/        # Golden Cross Trading System
│   ├── main.py
│   ├── requirements.txt
│   ├── README.md
│   └── outputs/
│
├── Task2_SamsungPhoneAdvisor/       # RAG + LLM Samsung Advisor
│   ├── app/
│   ├── nlu/
│   ├── retriever/
│   ├── generator/
│   ├── api/
│   ├── data/
│   ├── requirements.txt
│   ├── README.md
│   └── .env (local)
│
└── README.md                        # Main description (this file)
```

---

## 🏁 Summary

Both projects showcase applied Python development, automation, and integration with modern AI and data tools.
Together, they reflect practical, production-style coding for technical evaluation.

**Author:** Abrar
**Position:** Intern Candidate — Python
**Organization:** Genuine Technology & Research Ltd. (GTRL)
