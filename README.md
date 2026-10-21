# Signal2Stress - S&P Global & Crisil Campus Hackathon

**Candidate Name:** Hardik Agarwal

**College Email ID:** a.hardik@iitg.ac.in

**College:** Indian Institute of Technology (IIT), Guwahati

**Demo Video Link:** https://www.youtube.com/watch?v=Z01owVVjXbM

**Slide Deck Link:** Included in `docs/presentation.pdf`
 
## 1. Problem Statement & Approach
Risk managers currently struggle to instantly quantify the balance-sheet impact of breaking news and macroeconomic shifts. **Signal2Stress** bridges the gap between unstructured financial text and quantitative exposure management. It is a deterministic, low-latency wholesale financial risk intelligence system. 

Instead of relying on slow, unpredictable, and expensive generative LLMs, this solution utilizes a highly optimized deterministic NLP pipeline (regex-based rule matching combined with FinBERT sentiment scoring) to classify market events. It then automatically maps these events (Direct, Sector, or Macro) to a synthetic wholesale portfolio and instantly executes exposure-aware first-order stress calculations (e.g., ECL changes for loans, duration shocks for bonds, DV01 shifts for swaps).

## 2. Architecture & Tech Stack
The architecture follows a strict, modular Separation of Concerns (SoC) design, entirely decoupled from heavy LLM dependencies to ensure speed and reliability.

*   **Frontend:** Streamlit (`app.py`) for the interactive RiskLens dashboard.
*   **Backend / API:** FastAPI (`api.py`) with Uvicorn serving a robust REST API for batch processing and integrations.
*   **NLP Engine:** Standalone Python (`src/risk_engine.py`) utilizing PyTorch and HuggingFace Transformers (FinBERT) alongside deterministic regex extraction.
*   **Risk & Stress Engine:** Pandas-driven portfolio mapping and quantitative shock modeling (`src/stress_engine.py`, `src/exposure_mapper.py`).
*   **Data Contracts:** Pydantic (`src/schemas.py`) for strict data validation across pipeline modules.
*   **Persistence:** SQLite (`src/storage.py`) for event ledgering and historical risk-feed retrieval.

*(See `docs/architecture.png` for the detailed system data flow)*

## 3. Dataset Used
*   **Portfolio Data (`data/synthetic_portfolio.csv`):** A custom-generated synthetic wholesale portfolio encompassing corporate loans, fixed-rate bonds, and IR swaps across various sectors.
*   **Validation Scenarios (`data/demo_cases.csv`):** Hand-authored synthetic mapping cases to rigorously test Direct, Sector, and Macro exposure routing.
*   **Live Stream:** Integrated ingestion from the **GDELT 2.0 Doc API** for live global event polling.

## 4. Quickstart & Installation
**Runtime:** Python 3.12 on Windows / Linux / macOS

Step-by-step commands to set up the environment and run the code locally:

```bash
# Clone the repository
git clone https://github.com/hardikagarwal23/IITG-Hardik-Agarwal-hackathon.git
cd iitg-hardik-agarwal-hackathon

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch both the FastAPI backend and Streamlit dashboard simultaneously
python scripts/run.py
```

## 5. Key Results & Domain Impact
*   **Real-time Risk Attribution:** Demonstrates the ability to parse a breaking news headline and immediately identify affected portfolio positions within milliseconds, drastically reducing manual risk-assessment latency.
*   **Exposure-Aware Modeling:** Outputs quantifiable P&L impact estimates (e.g., total loss, incremental ECL, bond/swap value changes) based on dynamic attenuation factors, moving beyond naive blanket haircuts.
*   **Explainability & Auditability:** Every generated signal includes a strict JSON payload detailing the specific evidence quote, severity rationale, and mapping logic, ensuring compliance and trust in the system's outputs.
