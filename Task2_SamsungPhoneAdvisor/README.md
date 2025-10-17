# Task 2 – Samsung Phone Advisor (RAG + LLM)

## Requirements

* Python 3.10 or higher
* PostgreSQL (local instance)
* Valid **Groq API key** for GPT-OSS models
* Install dependencies:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## Project Overview

An intelligent **Samsung smartphone question-answering system** that understands **natural language** and responds with accurate, fluent answers using data scraped from **GSMArena**.

**Key abilities**

* Retrieve specifications for any Samsung phone
* Compare two or more models naturally
* Recommend the best phone under a user-defined budget

---

## Project Structure

```
Task2_SamsungPhoneAdvisor/
│
├── scraper/
│   └── gsmarena_scraper.py              # GSMArena scraper (delicate; do not modify)
│   
│
├── nlu/
│   └── nlu.py                  # Natural-language understanding module
│
├── retriever/
│   └── retriever.py            # Retrieves structured data from PostgreSQL
│
├── generator/
│   ├── generator.py            # Generates LLM summaries and recommendations
│   └── openai_client.py        # Groq API wrapper for GPT-OSS models
│
├── api/
│   └── app.py                  # FastAPI interface
│
├── data/
│   ├── samsung_phones.json     # Raw scraped data (GSMArena)
│   ├── processed_phones.json   # Cleaned structured data (output of processor)
|   └── process_raw_data.py     # Cleans and groups raw scraped data
|
├── db/
│   ├── import_json.py
|   └── models.sql    
│
├── requirements.txt
├── .env                        # Environment variables (do not commit)
└── README.md
```

---

## Setup Instructions

1. **Create and activate a virtual environment (recommended):**

   ```bash
   python -m venv venv
   # Linux/Mac
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Create the PostgreSQL database:**

   ```sql
   CREATE DATABASE samsung_db;
   ```

4. **Add environment variables to `.env` (create the file in project root):**

   ```text
   # Replace placeholders with your credentials and API key
   DATABASE_URL=postgresql://<DB_USER>:<DB_PASSWORD>@localhost:5432/samsung_db
   GROQ_API_KEY=your_groq_api_key_here
   PORT=8010
   ```

   Example (Windows-safe URL encoding note): if your password contains special characters (e.g. `@`), URL-encode them. For instance, the `@` character becomes `%40`.

   **Do not** commit `.env` to the repository.

5. **Process raw data (one-time):**

   ```bash
   python app/processor.py
   ```

   This reads `data/samsung_phones.json` and writes `data/processed_phones.json`.

6. **Load processed data into the database:**

   ```bash
   python app/load_data.py
   ```

   This connects to the `DATABASE_URL` and inserts cleaned records into the `phones` table.

---

## Running the API

Start the FastAPI server:

```bash
python api/app.py
```

Expected output (port follows `PORT` env var, default set to 8010):

```
🚀 Running Samsung Phone Advisor API on http://127.0.0.1:8010
```

---

## Using the API

Open the Swagger UI:
👉 [http://127.0.0.1:8010/docs](http://127.0.0.1:8010/docs)

**Endpoint:**
`POST /ask`

**Example request:**

```json
{
  "question": "Compare Samsung Galaxy S25 Ultra and Samsung Galaxy S25 FE for photography"
}
```

**Example response:**

```json
{
  "answer": "The Samsung Galaxy S25 Ultra offers a higher-resolution 200 MP camera...",
  "parsed_query": {
    "intent": "compare",
    "focus_features": ["camera"],
    "models": ["Samsung Galaxy S25 Ultra", "Samsung Galaxy S25 FE"]
  },
  "retrieved_type": "compare"
}
```

---

## Supported Question Types

| Intent        | Example                                      |
| ------------- | -------------------------------------------- |
| **Specs**     | “Specs of Samsung Galaxy S25 Ultra”          |
| **Compare**   | “Compare S25 and S25 Ultra for camera”       |
| **Find Best** | “Best Samsung phone under $1000 for battery” |
| **General**   | “Tell me about the Galaxy S25 series”        |

---

## Technology Stack

| Layer               | Tools                            |
| ------------------- | -------------------------------- |
| **Backend API**     | FastAPI + Uvicorn                |
| **Database**        | PostgreSQL                       |
| **Scraping**        | Requests + BeautifulSoup4 + lxml |
| **NLU**             | spaCy + RapidFuzz                |
| **LLM Integration** | Groq API (GPT-OSS models)        |
| **Env Mgmt**        | python-dotenv                    |

---

## Development & Testing

Run individual modules interactively:

```bash
# Test the NLU module
python nlu/nlu.py

# Test the Retriever module
python retriever/retriever.py

# Test the Generator (requires GROQ_API_KEY)
python generator/generator.py
```

---

## Notes

* The GSMArena scraper has strict limits; do **not** run it aggressively.
* Groq API must be active for LLM-based answer generation.
* Ensure `.env` contains correct DB credentials and API key.

