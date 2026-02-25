# Files AI — Agnilonda Pakou

A Streamlit web application that uses **Google Gemini 1.5 Pro** to summarize web articles and PDF documents. The assistant has the personality and name of **Agnilonda Pakou** — warm, knowledgeable, and concise.

---

## Features

- **URL summarization** — paste any public web article link and get a structured summary
- **PDF summarization** — upload a text-based PDF and get a document summary
- **Personality** — every summary is delivered by Agnilonda Pakou, a consistent AI persona that always ends with a "Key Takeaway:" line
- **Structured JSON logging** — all events (requests, completions, errors) are written to `assistant_log.json`
- **Graceful error handling** — user-friendly messages for network errors, bad PDFs, API failures, and invalid input

---

## Prerequisites

- Python 3.10 or higher
- A Google Gemini API key
  Get one at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- Internet access (for URL summarization and Gemini API calls)

---

## Installation

### 1. Clone or navigate to the project directory

```bash
cd /path/to/files-ai
```

### 2. Create and activate a virtual environment

```bash
# Create
python -m venv venv

# Activate (Linux / macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

```bash
cp .env.example .env
```

Open `.env` in a text editor and replace the placeholder with your real key:

```
GOOGLE_API_KEY=AIza...your_actual_key...
```

---

## Running the App

```bash
streamlit run app.py
```

Streamlit will print a local URL (default: `http://localhost:8501`). Open it in your browser.

To stop the app press `Ctrl+C` in the terminal.

---

## How to Use

### Summarize a Web Article (URL)

1. Click the **"Summarize a URL"** tab.
2. Paste a full URL (e.g. `https://bbc.com/news/science...`) into the text field.
3. Click **"Summarize URL"**.
4. The summary appears below the button, ending with a **Key Takeaway** line.

### Summarize a PDF

1. Click the **"Summarize a PDF"** tab.
2. Click **"Browse files"** and select a text-based PDF from your computer.
3. Click **"Summarize PDF"**.
4. The summary appears below the button, ending with a **Key Takeaway** line.

> **Note:** Only text-based PDFs are supported. Scanned documents or image-only PDFs (those without an embedded text layer) cannot be processed.

---

## Project Structure

```
files-ai/
├── app.py              # Streamlit UI — page layout, tabs, session state,
│                       #   error display; delegates all logic to other modules
├── gemini_client.py    # GeminiClient class — API key loading, model init,
│                       #   and generate() method
├── summarizer.py       # summarize_url() and summarize_pdf() functions;
│                       #   content extraction, truncation, prompt construction
├── logger.py           # setup_logger(), log_event(), _flush_to_file();
│                       #   structured JSON event logging
├── requirements.txt    # Python package dependencies
├── .env                # Your API key (not committed to version control)
├── .env.example        # API key template — safe to commit
├── .gitignore          # Excludes .env, venv/, __pycache__/, log file
├── assistant_log.json  # Auto-created at runtime; all events logged here
└── README.md           # This file
```

---

## Logging

Every significant event is appended to `assistant_log.json` in the project root. The file is created automatically on first run.

### Log Entry Schema

| Field | Type | Description |
|---|---|---|
| `timestamp` | ISO 8601 string | When the event occurred |
| `level` | `"INFO"` / `"WARNING"` / `"ERROR"` | Severity |
| `event_type` | string | One of the event types below |
| `session_id` | UUID4 string | Identifies a browser session |
| `source_type` | `"URL"` / `"PDF"` / `null` | Input type; null for `app_started` |
| `source_identifier` | string / `null` | The URL or PDF filename |
| `model` | string | Gemini model name |
| `error_message` | string / `null` | Populated only on error events |
| `summary_length` | integer / `null` | Character count; set on `summary_completed` |

### Event Types

| Event | When it fires |
|---|---|
| `app_started` | Once when the Streamlit session initialises |
| `summary_requested` | When the user clicks a Summarize button |
| `summary_completed` | After a successful Gemini response |
| `fetch_error` | Network or HTTP error fetching a URL |
| `pdf_error` | Error reading or extracting PDF text |
| `gemini_error` | Gemini API error or unexpected exception |
| `validation_error` | Invalid input (bad URL format, empty content) |

### Example Log Entry

```json
{
  "timestamp": "2026-02-24T15:42:04.123456",
  "level": "INFO",
  "event_type": "summary_completed",
  "session_id": "3f8a2b1c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "source_type": "URL",
  "source_identifier": "https://bbc.com/news/article",
  "model": "gemini-2.0-flash",
  "error_message": null,
  "summary_length": 512
}
```

---

## Limitations

| Limitation | Details |
|---|---|
| Scanned PDFs | Only PDFs with an embedded text layer are supported. Image-only PDFs require OCR (not included). |
| Bot-blocked sites | Some news and paywalled sites block automated requests. Try another URL if you see a fetch error. |
| Content cap | Article/PDF text is truncated at **100,000 characters** (~25,000 words) before sending to Gemini. This covers virtually all articles and most full-length books. |
| Gemini rate limits | Paid API keys have per-minute and per-day limits. If you see a quota error, wait a moment and retry. |

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `GOOGLE_API_KEY not found` | `.env` file missing or key not set | Run `cp .env.example .env` and add your key |
| `No text could be extracted` | Scanned / image-only PDF | Use a text-based PDF |
| `Could not reach that URL` | Network issue or bot-blocked site | Check internet connection; try a different URL |
| `HTTP error … 403` | Site denies automated access | Try a different article or source |
| `Could not read the PDF` | Corrupt or password-protected file | Try a different PDF |

---

## Security Notes

- **Never commit `.env`** to version control. The `.gitignore` in this project excludes it automatically.
- `assistant_log.json` records URL paths and PDF filenames. Review it before sharing or committing.
- This application makes outbound HTTP requests to external URLs. Do not run it with untrusted user input in uncontrolled environments.

---

## License

This project is for educational purposes as part of the MEST programme.
