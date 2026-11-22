# Ghost Warehouse dashboard

Generate data first:

```bash
python -m unittest discover -s tests -v
python scripts/run_fulfillment.py
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

The app reads generated `data/fulfillment_*.csv` files, and displays order throughput, inventory reconciliation, employee task assignments and order-level event history. The UI is intentionally labeled synthetic. Route geometry and access-aware navigation are not yet included.

**Validation status:** The GitHub Actions workflow was committed, but no successful run has been independently confirmed. Do not treat these dashboard figures as validated until the workflow passes.
