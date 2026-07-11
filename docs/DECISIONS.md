# DECISIONS.md - Architecture Decision Log

## Decision 1: Split Type Validation Strategy

**Date:** 2026-07-11

**Context:** The CSV contains inconsistent split types (e.g., equal with share values, percentages summing to >100%).

**Options Considered:**
1. Strict validation - Reject any inconsistent entry
2. Lenient validation - Auto-correct inconsistencies

**Chosen:** Lenient validation with user notification

**Rationale:** 
- Users prioritize data preservation over strict correctness
- Auto-correction reduces friction
- Notifications maintain transparency without blocking workflows
- Matches Aisha's requirement for "just one number"

**Implementation:**
```javascript
const validateSplit = (expense) => {
  // Equal split validation
  if (expense.split_type === 'equal') {
    if (expense.split_details) {
      return { valid: true, corrected: normalizeToEqual(expense) };
    }
  }
};
```

---

## Decision 2: Currency Conversion Approach

**Date:** 2026-07-11

**Context:** Some expenses in USD but treated as INR (Priya's concern).

**Options Considered:**
1. Static conversion rate (e.g., $1 = ₹82)
2. API-based real-time rates
3. User-defined rates per expense

**Chosen:** Static rate with INR base, user override option

**Rationale:**
- Simple deterministic behavior for testing
- Easy to verify calculations
- Allows override for edge cases
- Matches Priya's requirement for accuracy

**Rate Source:** Current USD/INR rate embedded in config, updated monthly.

---

## Decision 3: Settlement Entry Handling

**Date:** 2026-07-11

**Context:** "Rohan paid Aisha back" appears as expense, not settlement (Meera's concern).

**Options Considered:**
1. Treat as negative expense
2. Separate settlement table
3. Auto-detect and convert

**Chosen:** Separate settlements table with auto-detection

**Rationale:**
- Clear separation of concepts (spending vs settling)
- Enables proper balance calculations
- Supports Rohan's "no magic numbers" requirement
- Users can audit settlements independently

---

## Decision 4: Member Join/Leave Handling

**Date:** 2026-07-11

**Context:** Sam joined mid-April, Meera left end of March (Sam's concern).

**Options Considered:**
1. Static membership snapshots per expense
2. Dynamic lookup at time of expense
3. Pro-rated split adjustments

**Chosen:** Timestamp-based membership with pro-rated adjustments

**Rationale:**
- Most accurate cost attribution
- Handles mid-month joins properly
- Supports audit trails
- Matches Sam's concern about March electricity

**Implementation:** Each expense validates participants were active on that date.

---

## Decision 5: Duplicate Detection

**Date:** 2026-07-11

**Context:** "Dinner - marina" duplicate, same amount different description (Meera's concern).

**Options Considered:**
1. Exact match detection only
2. Fuzzy matching (Levenshtein + amount tolerance)
3. AI-powered semantic similarity

**Chosen:** Fuzzy matching with configurable thresholds

**Rationale:**
- Balances accuracy with performance
- User approval workflow satisfies Meera's concern
- Handles common entry errors (typos, extra spaces)

**Thresholds:**
- Date: exact match
- Description: 80% similarity
- Amount: ±2% tolerance
- Participants: exact match

---

## Decision 6: Database Schema Design

**Date:** 2026-07-11

**Context:** Need to track expenses, splits, members, and settlements.

**Chosen Schema:**

### Tables Created:
- **users**: Authentication and identity
- **groups**: Expense groups (flat, trip, etc.)
- **memberships**: Join/leave timestamps (temporal data)
- **expenses**: Core expense records
- **expense_splits**: Individual split amounts per expense
- **settlements**: Payment records between users
- **import_logs**: Track CSV import anomalies
- **currencies**: Currency conversion rates

**Rationale:**
- Temporal memberships enable accurate historical tracking
- Normalized splits allow flexible split types
- Import logs satisfy audit requirements

---

## Decision 7: Import Workflow

**Date:** 2026-07-11

**Context:** Must import CSV without manual editing (requirement #4).

**Options Considered:**
1. Direct CSV → DB import
2. Preview → Review → Import workflow
3. Background import with email report

**Chosen:** Preview → Review → Import workflow

**Rationale:**
- Matches Meera's requirement to approve deletions/changes
- Prevents incorrect data from entering system
- Provides transparency for debugging later

---

## Decision 8: Balance Calculation Engine

**Date:** 2026-07-11

**Context:** Need to provide "one number per person" (Aisha) and "explain how" (Rohan).

**Implementation:**
- Running balances per user per group
- Snapshot of individual contributions
- Detailed breakdown view for each member

## Decision 9: Date Ambiguity Resolution
**Date:** 2026-07-11  
**Context:** The `Deep cleaning service` entry questions `April 5 or May 4?`  
**Chosen:** Parse with regex and present both options, accepting the extracted date if present, otherwise flagging for review.  
**Rationale:** Keeps historical timeline correct; matches Meera's need to review changes.

## Decision 10: Currency Default Strategy
**Date:** 2026-07-11  
**Context:** Groceries DMart in March lacks currency specification  
**Chosen:** Default to INR, flag for review in import log  
**Rationale:** Maintains traceability; aligns with requirement to detect/surface problems.

## Decision 11: Split Type Consistency
**Date:** 2026-07-11  
**Context:** `Furniture for common room` notes `split_type says equal but someone added shares anyway`  
**Chosen:** Use split_details if provided; treat as `exact` split  
**Rationale:** Preserves cost structure; satisfies Rohan's "no magic numbers" rule.

## Decision 12: Settlement Isolation
**Date:** 2026-07-11  
**Context:** `Rohan paid Aisha back` logged as expense, not settlement  
**Chosen:** Create `settlements` table, exclude from balances  
**Rationale:** Separates genuine expenses from debt clearing; matches Meera's request to remove duplicates without losing track.
```

## Key Stakeholder Requirements Mapping

| Stakeholder | Requirement | How Addressed |
|------------|-------------|---------------|
| Aisha | One number per person | Balance summary page |
| Rohan | See which expenses create balance | Detailed expense view with contributions |
| Priya | Dollar/rupee distinction | Currency conversion with USD handling |
| Sam | March expenses shouldn't affect him | Temporal membership validation |
| Meera | Approve deletions/changes | Import preview workflow |

## Next Steps

1. Implement database schema
2. Build import pipeline with anomaly detection
3. Create balance calculation engine
4. Develop frontend interfaces