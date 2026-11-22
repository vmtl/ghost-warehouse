# Phase 5 — workforce and suppliers

All identities, pay, lead times, supplier performance targets, and purchasing thresholds are **synthetic**, not BMW or market data.

## Workforce

75 employees across 9 departments, with stable employee IDs, job titles, shift assignments, illustrative hourly rates and active status. A and B are simulated shift teams; start/end times are placeholders for later scheduling logic, not a complete labor roster. Employee names are fictional test records.

## Procurement

30 supplier records: 5 fictional catalog manufacturers plus 25 fictional distributors. The `primary_manufacturer` field matches one of the five manufacturer values in `data/products.csv`. Supplier lead times range from 4 to 21 days, and delivery percentages are targets, not measured outcomes. Future purchase orders will select a supplier by product manufacturer and business rules.

## Checks

- Unique employee and supplier IDs
- 75 employees; 30 suppliers
- 9 workforce departments
- Supplier manufacturer values match product catalog
- No real customer, employee, or supplier personal data

## Next milestone

Create synthetic retail and wholesale customers, purchase orders, receiving events, and outbound orders. Later introduce scheduled employee shifts and observed performance separately from master data.
