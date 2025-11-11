# Job Reference - OpenSAM

**Purpose**: Links OpenSAM back to its source - the Applied Medical SAM Analyst job posting

---

## What's in This Folder

- **source-posting.txt** - Original job posting from Applied Medical
- **feature-mapping.md** - How each OpenSAM feature maps to a job requirement
- **gap-analysis.md** - What we built vs. what we didn't (and why)

---

## Why This Exists

AppForge Labs builds tools from real job requirements. This folder provides **traceability**:

1. **Validates our methodology** - Every feature traces back to a real need
2. **Justifies scope decisions** - Documents what we built and what we saved for Pro
3. **Marketing narrative** - "Built from a real SAM Analyst job posting"
4. **Quality assurance** - Ensures we didn't add random features (scope creep)

---

## How to Use This

### For Development
Before adding a new feature to OpenSAM, check:
- Is it in the job posting? → Add it
- Does it enhance a core feature? → Probably add it (document in feature-mapping.md)
- Is it completely unrelated? → Skip it or save for Pro version

### For Marketing
When pitching OpenSAM:
- "Built by analyzing real SAM Analyst job requirements from Applied Medical"
- "91% coverage of key responsibilities mentioned in the posting"
- "Every feature solves a real workflow need"

### For Transparency
If someone asks "Why doesn't OpenSAM have feature X?":
- Check gap-analysis.md for the answer
- Might be: Too complex for MVP, saved for Pro, or not in original requirements

---

## Key Stats

**Source Job**: Applied Medical - Software Asset Management Analyst
**Salary Range**: $65K-$90K
**Requirements Coverage**: 91% of key responsibilities
**Build Time**: 1 week
**Deployment**: https://opensam.streamlit.app

---

## File Summaries

### source-posting.txt
The original job posting, verbatim. Includes:
- Company background
- Role description
- Key responsibilities (8 items)
- Position requirements
- Preferred skills
- Benefits

### feature-mapping.md
Maps every OpenSAM feature to job requirements:
- 5 core features (Portfolio, Renewals, Allocation, Drilldown, Scenarios)
- 8 polish features (exports, alerts, ServiceNow integration, etc.)
- Justification for each feature
- What we didn't build and why

### gap-analysis.md
Comprehensive analysis:
- ✅ What we built (11 of 12 key responsibilities)
- ⚠️ What we partially built (collaboration features)
- ❌ What we skipped (live APIs, SAP-specific features)
- Decisions and trade-offs
- Lessons learned

---

## Updating This Folder

**When adding features to OpenSAM**:
1. Update `feature-mapping.md` with new feature → requirement mapping
2. Update `gap-analysis.md` if closing a gap
3. Document why the feature is justified (job requirement or enhancement)

**When creating new projects**:
- Copy this folder structure to new project
- Replace source-posting.txt with new job posting
- Create new feature-mapping and gap-analysis
- Maintain traceability for every project

---

**Built by AppForge Labs**
Forging solutions from real-world requirements
