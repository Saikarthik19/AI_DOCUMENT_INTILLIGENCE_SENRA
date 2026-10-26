# Contributing to SENTRA (DocuMind AI)

Thank you for your interest in contributing to SENTRA! We welcome contributions from developers, researchers, and open-source enthusiasts.

---

## 🛠️ Development Workflow

### 1. Fork and Clone
```bash
git clone https://github.com/<your-username>/AI_DOCUMENT_INTILLIGENCE_SENRA.git
cd AI_DOCUMENT_INTILLIGENCE_SENRA
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
# On Windows
.venv\Scripts\Activate.ps1
# On Linux / macOS
source .venv/bin/activate
```

### 3. Install Development Dependencies
```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
pip install flake8 pytest
```

### 4. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

---

## 🧪 Testing Guidelines

Before opening a pull request, ensure all automated tests pass:
```bash
python -m pytest -v tests/
```

Verify linting standards:
```bash
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.venv,__pycache__
```

---

## 📝 Commit Standards

Please write clear, semantic commit messages:
- `feat: add hybrid dense-sparse retrieval`
- `fix: resolve OCR timeout on scanned multi-page invoices`
- `docs: update Azure deployment runbook`
- `test: add unit tests for table cell extraction`

---

## 🚀 Submitting a Pull Request
1. Push your branch to your fork.
2. Open a Pull Request against the `main` branch.
3. Fill out the PR template describing the changes, motivation, and test coverage.
