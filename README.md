# FastAPI Service Template

A clean and modern template for building microservices with **FastAPI**, **PDM**, **SQLAlchemy**, and **Alembic**.

---

## 🚀 Getting Started

### 1. Install dependencies

Make sure you have [PDM](https://pdm.fming.dev/latest/) installed, then run:

```bash
pdm install
```

### 2. Run database migrations
Use Alembic to generate and apply migrations:

* Create a new migration:

```bash
alembic revision --autogenerate -m "Add something"
```

* Apply migrations:

```bash
alembic upgrade head
```

### 3. Run the FastAPI app
You can run the app directly using:

```bash
python main.py
```

Or with a server like uvicorn (if configured):

```bash
uvicorn main:app --reload
```
