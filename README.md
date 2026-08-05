# Credit Risk Models — CreditMetrics, KMV, and BIS/Basel IRB

Three independent portfolio credit risk models, each estimating **Credit Value-at-Risk (Credit VaR)**
via a different methodology, packaged as standalone Python modules plus a comparison Jupyter notebook.

| Model | Approach | Folder |
|---|---|---|
| **CreditMetrics** | Monte Carlo — rating migration (single-factor Gaussian copula) | [`creditmetrics-var/`](./creditmetrics-var) |
| **KMV / Merton** | Monte Carlo — structural default (asset value vs. debt) | [`kmv-model/`](./kmv-model) |
| **BIS / Basel IRB** | Closed-form regulatory capital formula | [`bis-irb-model/`](./bis-irb-model) |

A side-by-side comparison notebook lives in [`notebooks/Credit_VaR_Models_Comparison.ipynb`](./notebooks/Credit_VaR_Models_Comparison.ipynb).

---

## 🇹🇭 ภาพรวมโปรเจกต์ (Thai)

โปรเจกต์นี้รวบรวมโมเดลประเมินความเสี่ยงด้านเครดิต (Credit Risk) 3 แบบที่แยกกันทำงานอิสระ โดยแต่ละโมเดลใช้วิธีการคำนวณ Credit VaR ที่แตกต่างกัน:

1. **CreditMetrics** — จำลองการเปลี่ยนแปลง Credit Rating ของแต่ละบริษัทด้วย Monte Carlo Simulation ผ่าน Single-Factor Gaussian Copula แล้ว Revalue กระแสเงินสดใหม่ตาม Rating ที่เปลี่ยนไป
2. **KMV / Merton Model** — จำลองมูลค่าสินทรัพย์ของบริษัท (Asset Value) เทียบกับหนี้สิน (Debt) หากสินทรัพย์ต่ำกว่าหนี้สิน ณ วันครบกำหนด ถือว่า Default
3. **BIS / Basel IRB Formula** — สูตรคำนวณเงินกองทุนตามเกณฑ์ธนาคารกลาง (Regulatory Capital) แบบ Closed-form ไม่ใช่ Simulation

### ⚠️ ข้อควรระวังสำคัญ: การเปรียบเทียบ Alpha ระหว่างโมเดล

- **CreditMetrics** และ **KMV** เป็น Monte Carlo ทั้งคู่ — สามารถปรับ `alpha` (Confidence Level) ให้เท่ากันเพื่อเปรียบเทียบกันได้โดยตรง
- **BIS/Basel IRB** เป็นสูตรคณิตศาสตร์ตายตัวที่กำหนดโดยกฎเกณฑ์ธนาคารกลางไว้ที่ **99.9%** (`norm.ppf(0.999)` ถูกฝังอยู่ในสูตรโดยตรง) **ไม่สามารถปรับเปลี่ยนได้เหมือนอีกสองโมเดล** — หากปรับค่านี้ ผลลัพธ์ที่ได้จะไม่ใช่ตัวเลขเงินกองทุนตามเกณฑ์ Basel อีกต่อไป
- ดังนั้นการ "ปรับ Alpha ให้เหมือนกันทั้ง 3 โมเดล" ทำได้เต็มที่เฉพาะระหว่าง CreditMetrics กับ KMV เท่านั้น ส่วน BIS จะถูกแสดงแยกไว้ที่ 99.9% เสมอ พร้อมป้ายกำกับชัดเจนในโค้ดและ Notebook

---

## 🇬🇧 Project Overview (English)

This repository packages three independent credit risk models, each estimating portfolio Credit VaR
through a different methodology:

1. **CreditMetrics** — Monte Carlo simulation of firm-level credit rating migrations via a
   single-factor Gaussian copula, with cash flows revalued under each simulated rating outcome.
2. **KMV / Merton Model** — Structural model simulating firm asset value against debt via
   Geometric Brownian Motion; a firm defaults if simulated assets fall below debt at maturity.
3. **BIS / Basel IRB Formula** — The Basel Committee's closed-form Internal Ratings-Based capital
   formula. Not a simulation — a direct analytical calculation per exposure.

### ⚠️ Important: alpha is not comparable across all three models

- **CreditMetrics** and **KMV** are both Monte Carlo models — their confidence level (`alpha`) is a
  free parameter (an empirical loss percentile), so these two **can** be set to the same value and
  compared directly.
- **BIS/Basel IRB is a closed-form regulatory formula fixed at 99.9%** confidence
  (`norm.ppf(0.999)` is hardcoded into the Basel calibration) — it is **not** an adjustable
  parameter. Changing it would no longer represent Basel-compliant regulatory capital.
- So: "same alpha for all three" is achievable for CreditMetrics + KMV; BIS is reported alongside
  at its fixed 99.9%, clearly labeled as such rather than silently forced to match.

See [`notebooks/Credit_VaR_Models_Comparison.ipynb`](./notebooks/Credit_VaR_Models_Comparison.ipynb)
for a working example of this comparison, including a single `ALPHA` variable that drives both
Monte Carlo models consistently.

---

## Repository Structure

```
credit-risk-models/
├── creditmetrics-var/
│   └── creditmetrics_model.py     # Rating migration Monte Carlo Credit VaR
├── kmv-model/
│   └── kmv_model.py               # Structural (Merton/KMV) Monte Carlo Credit VaR
├── bis-irb-model/
│   └── bis_irb_model.py           # Basel IRB closed-form capital formula
├── notebooks/
│   └── Credit_VaR_Models_Comparison.ipynb   # Runs and compares all three models
├── requirements.txt
└── README.md
```

Each model folder is self-contained: import its functions directly, or run the file standalone
(`python creditmetrics_model.py`) for a quick demo with the module's default example portfolio.

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/credit-risk-models.git
cd credit-risk-models

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the Models

**Standalone (quick demo, uses each file's built-in example portfolio):**
```bash
python creditmetrics-var/creditmetrics_model.py
python kmv-model/kmv_model.py
python bis-irb-model/bis_irb_model.py
```

**Comparison notebook (recommended — runs all three together with a shared, adjustable `ALPHA`):**
```bash
jupyter notebook notebooks/Credit_VaR_Models_Comparison.ipynb
```

**As a library, in your own script:**
```python
from creditmetrics_model import run_full_model
result = run_full_model(alpha=0.99)
print(result["Credit VaR"])
```

---

## Keeping API Keys / Secrets Out of GitHub

None of the three models currently call an external API, but if you extend this project to pull
live market data (rates, spreads, ratings), follow this convention from the start:

1. **Never hardcode a key in a `.py` or `.ipynb` file.** Put it in a `.env` file instead:
   ```
   MARKET_DATA_API_KEY=abc123...
   ```
2. **`.env` is already in `.gitignore`** in this repo — Git will never stage it, so `git add .`
   cannot accidentally include it.
3. **Commit `.env.example` instead** (already included here) — a template with the variable
   *names* but no real values, so collaborators know what to set up locally.
4. **Load secrets at runtime** with `python-dotenv` (already in `requirements.txt`):
   ```python
   from dotenv import load_dotenv
   import os
   load_dotenv()
   api_key = os.getenv("MARKET_DATA_API_KEY")
   ```
5. **If a key is ever committed by accident:** revoke/rotate it immediately at the provider — do
   not rely on `git rm` alone. `git rm` removes the file going forward but the key is still
   readable in the commit history (and in any fork/clone made before the removal) unless you
   rewrite history with `git filter-repo` or the BFG Repo-Cleaner and force-push. Rotating the key
   is faster and safer than trying to scrub history.
6. **Before your first commit**, double check with `git status` that no `.env` or credential file
   shows up as staged — if it does, `git reset` it before committing.

---

## Model Caveats (read before treating outputs as final)

- **CreditMetrics** (`creditmetrics-var/creditmetrics_model.py`): the example portfolio has a few
  `payments_per_year` values that don't match their inline comments (flagged with `# TODO` in the
  code) — verify these against your intended contract terms before trusting the cash-flow timing.
  The model also reuses the 1-year transition matrix as an approximation for multi-year contracts
  rather than compounding multi-year transition probabilities.
- **KMV** (`kmv-model/kmv_model.py`): default confidence level was changed from an arbitrary
  `0.783276` (in the original script) to `0.999`, to align with the BIS model's regulatory standard
  and avoid an unexplained number. Adjust `DEFAULT_CONFIDENCE_LEVEL` as needed.
- **BIS/Basel IRB** (`bis-irb-model/bis_irb_model.py`): `lgd` and `pd` must be passed as **decimal
  fractions** (e.g. `0.40`, not `40`) — the function now raises a `ValueError` if you pass an
  out-of-range value, since the original script accepted `LGD=40` silently and produced meaningless
  output.
- All three models use **hypothetical / illustrative rate, spread, and portfolio data** — not live
  market data. Replace with real data sources before using outputs for any actual risk decision.

---

## License

Add a license of your choice (e.g. MIT) before publishing publicly. Not included by default here.
