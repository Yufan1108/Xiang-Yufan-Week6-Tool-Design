## Business Text Analysis Tool

This project implements a lightweight tool for analyzing business and news text,
and shows how to integrate it into a simple agent.

### 1. What the tool does (`tool.py`)

- **Name**: `business_text_analyzer`
- **Purpose**: analyze a short business / news / financial paragraph and return:
  - **Character count**, **word count**, **unique word count**
  - **Sentence count**, **average sentence length (words per sentence)**
  - **Top keywords** based on word frequency (with a small stopword list)
  - **Simple sentiment** using a small set of business-related positive / negative words
- **Return format**: a JSON-serializable dict (`ToolResult`):
  - Success: `{"ok": True, "data": {...}}`
  - Error: `{"ok": False, "error_type": "...", "error_message": "..."}`

### 2. How to run the demo (`demo.py`)

- **Requirements**: Python 3.8+ (standard library only)
- **Steps**:
  1. Open a terminal and go to the project folder (same level as `tool.py`):  
     `cd e:\Desktop\iimt3688\assignment\2`
  2. Run: `python demo.py`
  3. Output:
     - **SUCCESS CASE**: `SimpleAgent` detects a news-style message, calls
       `business_text_tool.execute(...)`, and prints a human-readable summary
       plus the raw JSON payload.
     - **ERROR CASE**: the script passes invalid parameters so you can see the
       structured error result produced by `Tool.execute`.

### 3. Design decisions and limitations

- **Design**:
  - A small `Tool` wrapper holds `name`, `description`, and `fn`, and exposes
    `execute(**kwargs)` with unified error handling.
  - The core function `analyze_business_text` validates inputs (non-empty
    string text, positive integer `top_n_keywords`) and raises clear errors.
  - `Tool.execute` catches any exception and converts it into a structured
    error so that agent code does not need its own `try/except`.
- **Implementation choices**:
  - Uses only the standard library (`re`, `collections.Counter`); no external
    NLP packages.
  - Tokenization is regex-based and lowercase; keywords are frequency-based;
    sentiment uses a tiny domain lexicon.
- **Limitations**:
  - Intended for simple English text and short news-style paragraphs.
  - Sentence splitting and sentiment are heuristic and approximate, meant for
    quick signals rather than deep linguistic analysis.
