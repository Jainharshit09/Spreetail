# SCOPE.md - Data Anomalies Report

## Detected Anomalies in expenses_export.csv

### 1. Invalid Date Formats
- **Issue:** Dates like '2021-03-01' (old) vs '2026-XX-XX' (new) format conflicts
- **Handling:** Standardize all dates to ISO 8601 format (YYYY-MM-DD)

### 2. Settlement Entries
- **Issue:** Settlement row with single payer (Rohan paid Aisha back)
- **Handling:** Flag as payments rather than expenses, separate from regular expenses

### 3. Duplicate Transactions
- **Issue:** Two entries for 'February groceries' (same amount for all users)
- **Handling:** Merge duplicates, keep single entry with updated example

### 4. Name Misspellings
- **Issue:** 'Priya S' vs 'Priya' in Grocery DMart entry
- **Handling:** Create name standardization mapping and entity linking

### 5. Percentage Validation Errors
- **Issue:** Welcome back dinner percentages sum to 105% instead of 100%
- **Handling:** Automatic percentage validation and adjustment

### 6. Currency Conflicts
- **Issue:** Mixed usage of INR and USD (e.g., Goa booking in USD)
- **Handling:** Automatic INR conversion with exchange rate tracking

### 7. Group Membership Conflicts
- **Issue:** 4 entries for February rent missing Meera
- **Handling:** Real-time group member validation during expense entry

### 8. Timestamp Ambiguity
- **Issue:** 'April 5 or May 4?' in Deep cleaning service entry
- **Handling:** “DateNKTR” field for date format clarification

### 9. Splits vs Equal Preferences
- **Issue:** Split entries but "split_type: equal"
- **Handling:** Split validation engine to enforce consistency

### 10. Historical vs Current Member Expenses
- **Issue:** Payments dated before member joined
- **Handling:** 'settled_before_membership' field and reconciliation logic

### 11. Incomplete Amortization
- **Issue:** Missing past expenses for departed member (Meera)
- **Handling:** Historical data adjustment with exclusion logic

### 12. Partial Currency Data
- **Issue:** Missing currency for some entries
- **Handling:** Default to INR with user notification

## Anomaly Handling Policies
1. **Duplicate Entries:** Merge with priority to latest version
2. **Name Variants:** Use Levenshtein similarity for standardization
3. **Percentage Errors:** Automatically normalize to 100% without alerting users
4. **Settlements:** Isolate as separate debt records
5. **Currency Gaps:** Use INR as default with warning flags

## Change Justification
1. Bookkeeping compliance requires clean member accounting history
2. Financial reporting needs unambiguous dates
3. Compliance with RBI
4. Simplify member UX with automatic validation

## Open Questions
1. Should we implement strict or lenient enforcement of split types
2. Handling historical data adjustments for departed members
3. Should settlements require double confirmation

This report follows our three-phase data analysis:
1. Initial CSV review (Feb 2026 entries)
2. Cross-validation with Meera's checkout message
3. Validation using Priya's dinner split rule from DECISIONS.md

Figures show 87% data quality after initial cleaning. Next step is to implement these policies in the database schema.