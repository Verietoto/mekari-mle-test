# ⚡ FastAPI Services for Mekari Testing

A modular and scalable **FastAPI** backend service following clean architecture principles.  
This repository includes layers for business logic, handlers, middleware, and configuration management.

---

## 📂 Project Structure

```
services/
├── agentic/                # Agents or intelligent automation logic
├── business/               # Core business logic / domain layer
├── chroma_data/            # Data storage (vector DB, embeddings, etc.)
├── cmd/                    # Command-line entry points or scripts
├── contracts/              # Data contracts, schemas, and interfaces
├── extra/                  # Helper utilities or integrations
├── handler/                # FastAPI routers and request handlers
├── middleware/             # Custom middlewares (logging, auth, etc.)
├── transformed_data/       # Processed or cached data outputs
├── .env                    # Local environment variables
├── .env.example            # Example environment file
├── config.py               # App configuration and settings
├── main.py                 # FastAPI app entry point
├── test.py                 # Unit / integration tests
├── pyproject.toml          # Poetry or build configuration
├── uv.lock                 # Dependency lock file
└── README.md
```

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/services.git
cd services
```

### 2️⃣ Create a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3️⃣ Install Dependencies
If using `uv`:
```bash
uv sync
```

Or with `pip`:
```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

### Development Mode
```bash
uvicorn main:app --reload
```
Then open your browser at:  
👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## ⚙️ Environment Variables

Copy the `.env.example` to `.env` and set your variables:

```bash
cp .env.example .env
```

Example:
```
APP_NAME=FastAPI Services
DEBUG=True
DATABASE_URL=sqlite:///./data.db
API_KEY=your-api-key
```

---


## 🧠 Design Overview

| Layer | Description |
|-------|--------------|
| **handler/** | Defines API endpoints and request handling |
| **business/** | Core logic independent of frameworks |
| **contracts/** | Data schemas and validation models |
| **middleware/** | Cross-cutting concerns (auth, logging, tracing) |
| **config.py** | Centralized settings using Pydantic or dotenv |

This structure ensures separation of concerns and simplifies maintenance, testing, and scaling.

---

## 📜 License

Licensed under the **MIT License**.  
See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to open a PR or submit an issue on GitHub.

---

## 💡 Author

Maintained by **Your Name** — built with ❤️ using FastAPI.
