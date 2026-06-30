# Candidate Data Unification Pipeline

A multi-source, config-driven candidate profile transformer and identity resolution engine built for the **Eightfold engineering intern assignment**. It ingests candidate data from structured (CSV, ATS JSON) and unstructured (GitHub, LinkedIn, Resumes, Recruiter Notes) sources, merges them into canonical profiles with provenance tracking + confidence scoring, and filters views dynamically using a runtime schema projector.

---

## 🏗️ Architecture — 3 Layers

```
┌──────────────────────────────────────────────────────────────────┐
│  INGESTION LAYER  ingestion/                                     │
│  Plugin-based adapters: CSV · ATS JSON · Resume (PDF/DOCX) ·    │
│  Recruiter Notes (TXT) · GitHub API · LinkedIn scraper          │
│  Output: flat list of RawRecord(field, value, source, method)    │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  ENGINE LAYER  engine/                                           │
│  1. Normalize  — E.164 phones, YYYY-MM dates, ISO-3166 countries │
│  2. Match      — O(N) email/phone index, name-only excluded      │
│  3. Merge      — priority-list conflict resolution + provenance  │
│  4. Confidence — weighted field-level scoring                    │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  PROJECTION LAYER  projection/                                   │
│  Runtime schema config: rename keys, extract paths, normalize,   │
│  handle missing (null / omit / error), validate output types     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart

### 1. Clone & Install Dependencies

```bash
git clone <repo-url>
cd EightfoldAI_Data_Transformer
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python run.py
```

Open your browser at **`http://127.0.0.1:8080`**

### 3. Run Automated Tests

```bash
python3 -m pytest tests/ -v
```

### 4. Run the End-to-End Verification Script

```bash
python3 verify_pipeline.py
```

---

## 📁 Project Structure

```
EightfoldAI_Data_Transformer/
├── run.py                    # Flask entry point (port 8080)
├── requirements.txt          # Python dependencies
├── verify_pipeline.py        # End-to-end verification script
│
├── api/
│   └── routes.py             # REST API endpoints
│
├── app/
│   ├── app.py                # Flask app factory
│   └── templates/
│       └── index.html        # Full-stack UI dashboard
│
├── engine/
│   ├── pipeline.py           # Orchestrates all stages
│   ├── normalize.py          # Phone / date / country / skill normalization
│   ├── match.py              # O(N) identity matching
│   ├── merge.py              # Priority-driven merge + provenance
│   ├── confidence.py         # Confidence scoring
│   └── canonical.py          # CanonicalProfile dataclass
│
├── ingestion/
│   ├── registry.py           # Adapter auto-detection
│   ├── base.py               # SourceAdapter ABC + RawRecord
│   ├── csv_adapter.py        # Recruiter CSV
│   ├── ats_json_adapter.py   # ATS JSON
│   ├── resume_adapter.py     # PDF / DOCX resumes
│   ├── notes_adapter.py      # Plain-text recruiter notes
│   ├── github_adapter.py     # GitHub profile API
│   └── linkedin_adapter.py   # LinkedIn scraper
│
├── projection/
│   ├── project.py            # Runtime schema projector
│   ├── config_schema.py      # Config validation
│   └── validate.py           # Output type validation
│
├── storage/
│   └── canonical_store.py    # Thread-safe in-memory profile store
│
├── samples/
│   ├── recruiter_export.csv  # Sample CSV (4 candidates)
│   ├── ats_candidates.json   # Sample ATS JSON (2 candidates)
│   ├── recruiter_notes.txt   # Sample plain-text notes
│   └── Kanimuthu AR M_23CS076.pdf             # Sample resume PDF
│
├── tests/
│   └── ...                   # pytest unit tests
│
└── uploads/                  # Uploaded source files (auto-created)
```

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Dashboard UI |
| `POST` | `/api/ingest` | Upload a file or provide a URL to ingest |
| `POST` | `/api/run-pipeline` | Run full unification on ingested sources |
| `GET`  | `/api/candidates` | List all unified profiles |
| `GET`  | `/api/candidates/<id>` | Get a single canonical profile |
| `POST` | `/api/project` | Apply a projection config to stored profiles |

### POST `/api/ingest`

**File upload:**
```bash
curl -X POST http://127.0.0.1:8080/api/ingest \
  -F "file=@samples/recruiter_export.csv"
```

**URL ingestion:**
```bash
curl -X POST http://127.0.0.1:8080/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/username"}'
```

### POST `/api/run-pipeline`
```bash
curl -X POST http://127.0.0.1:8080/api/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": ["/absolute/path/to/uploads/recruiter_export.csv"],
    "priority_list": ["ATS JSON", "Recruiter CSV", "Resume", "Recruiter Notes"]
  }'
```

### POST `/api/project`
```bash
curl -X POST http://127.0.0.1:8080/api/project \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "fields": [
        { "path": "name", "from": "full_name", "type": "string" },
        { "path": "skills", "from": "skills[].name", "type": "string[]", "normalize": "upper" }
      ],
      "include_confidence": true,
      "on_missing": "null"
    }
  }'
```

---

## 📋 Supported Source Types

| Source | Adapter | Detected By |
|--------|---------|------------|
| Recruiter CSV | `CSVAdapter` | `.csv` extension |
| ATS JSON | `ATSJsonAdapter` | `.json` with ATS schema |
| Resume PDF | `ResumeAdapter` | `.pdf` extension |
| Resume DOCX | `ResumeAdapter` | `.docx` extension |
| Recruiter Notes | `NotesAdapter` | `.txt` extension |
| GitHub Profile | `GitHubAdapter` | `github.com/` URL |
| LinkedIn Profile | `LinkedInAdapter` | `linkedin.com/in/` URL |

---

## 🎛️ Projection Config Reference

```json
{
  "fields": [
    {
      "path": "output_field_name",
      "from": "canonical_field_path",
      "type": "string | number | boolean | string[]",
      "normalize": "upper | lower | E.164",
      "required": true
    }
  ],
  "include_confidence": true,
  "include_provenance": false,
  "on_missing": "null | omit | error"
}
```

**Path syntax:**
- `full_name` — top-level field
- `emails[0]` — first item of an array
- `skills[].name` — extract `name` from every item in `skills` array
- `links.linkedin` — nested field access

---

## 📦 Sample Walkthrough

Upload both sample files and run the pipeline to see:

- **Alice Smith** — merged by email (`alice@example.com`) from CSV + ATS JSON
- **Bob Johnson** — merged by phone fallback (`+15559876543`), no email in CSV
- **Charlie Brown** — standalone candidate (unique to CSV)

Each profile includes full **provenance** (which source each field came from) and **confidence scores** per field and overall.

---

## ⚙️ Design Decisions

| Decision | Rationale |
|----------|-----------|
| **O(N) identity matching** | Inverted email/phone index avoids O(N²) cross-product |
| **Priority-list conflict resolution** | Config-driven, no hardcoded source names in engine |
| **`null` not invented** | Missing values become `null`, never fabricated |
| **Adapter failure = empty list** | Corrupted sources don't crash the pipeline |
| **Store cleared per run** | Re-uploading a modified file always produces fresh results |
| **Projection never mutates store** | Views are computed on the fly |

---

## 🧪 Running Tests

```bash
# All tests
python3 -m pytest tests/ -v

# With coverage
python3 -m pytest tests/ -v --tb=short

# End-to-end verification
python3 verify_pipeline.py
```
