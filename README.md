# Mekari MLE Test

## Objective

The goal of this test is to evaluate your ability to work with AI and machine learning in a practical context. Specifically, you are expected to:

1. Create a chat interface that interacts with table data stored in a database.
2. Create a chat interface that interacts with documents using Retrieval-Augmented Generation (RAG).
3. You may use AI tools, but do **not** use any frameworks.

## Dataset

The test uses the following datasets:

1. `fraudTest.csv` — Table data for testing database chat functionality.
2. `Bgatla.pdf` — Document for testing RAG-based chat functionality.

## Project Structure

```
MEKARI/
├── instruction/
├── raw_dataset/
│   ├── Bgatla.pdf
│   └── fraudTest.csv
├── services/             # BE application related files
├── web/                  # Web application related files
├── flagged/              # Possibly flagged items or logs
├── .gitignore
├── LICENSE
├── dockerfile
├── main.py               # Main entry point
├── pyproject.toml
├── uv.lock
├── README.md
```

## How to Run

### Backend
1. **Ensure Python 3.10+ is installed.**
2. **Install dependencies**: If listed in `pyproject.toml` or `requirements.txt`, install them using your package manager:

   ```bash
   cd services
   ```

   ```bash
   uv sync
   ```
3. **Run the application**: Execute `main.py` to start the backend services:

   ```bash
   uv run cmd/run.py
   ```
4. **For Docker usage**: Build and run the container:

   ```bash
   docker build -t mekari-be .
   docker run -p 8000:8000 -d --name mekari-be mekari-be
   ```


### Web
1. **Ensure Python 3.10+ is installed.**
2. **Install dependencies**: If listed in `pyproject.toml` or `requirements.txt`, install them using your package manager:

   ```bash
   cd web
   ```

   ```bash
   uv sync
   ```
3. **Run the application**: Execute `main.py` to start the backend services:

   ```bash
   uv run main.py
   ```
4. **For Docker usage**: Build and run the container:

   ```bash
   docker build -t mekari-fe .
   docker run -p 7860:7860 -d --name mekari-be mekari-fe
   ```

**Notes:**

* AI tools can be used for assistance.
* Do not use frameworks like Flask, FastAPI, or Streamlit.

