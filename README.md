
### 1. Create & Activate Virtual Environment

```bash
python -m venv .venv
```

- On **Windows (PowerShell)**:

```powershell
.venv\Scripts\Activate.ps1
```

- On **macOS/Linux**:

```bash
source .venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Start the Backend
```bash
uvicorn backend.token_service:app --reload --port 8000
```
```bash
uvicorn backend.main:app --reload --port 8001
```

---

### 6. Launch the Frontend

```bash
streamlit run frontend/app.py
```
---