"""HR data layer — structured records and knowledge base dicts.

Structured data (EMPLOYEES, LEAVE_BALANCES, HR_METRICS) stays in-memory for
exact lookups.  Everything else (LEAVE_POLICY, BENEFITS, HOLIDAYS, HR_CONTACTS)
is the source-of-truth for Pinecone ingestion via ingest.py.
"""

# ── Structured data (exact lookups) ──────────────────────────────────────────

EMPLOYEES: dict[str, dict] = {
    "1001": {"name": "Aarav Mehta",  "department": "Sales",       "designation": "Sales Executive",   "manager": "Rohit Verma",    "joining_date": "2021-06-15", "status": "Active",   "country": "India"},
    "1002": {"name": "Neha Sharma",  "department": "HR",          "designation": "HR Analyst",        "manager": "Prakriti Mishra","joining_date": "2020-03-10", "status": "Active",   "country": "India"},
    "1003": {"name": "Rahul Iyer",   "department": "Engineering", "designation": "Software Engineer", "manager": "Anita Rao",      "joining_date": "2019-11-01", "status": "Active",   "country": "India"},
    "1004": {"name": "Priya Nair",   "department": "Sales",       "designation": "Account Manager",   "manager": "Rohit Verma",    "joining_date": "2018-08-22", "status": "Resigned", "country": "India"},
    "1005": {"name": "Karan Patel",  "department": "Finance",     "designation": "Finance Analyst",   "manager": "Sunil Shah",     "joining_date": "2022-01-05", "status": "Active",   "country": "India"},
    "2001": {"name": "Wei Zhang",    "department": "Engineering", "designation": "Senior Engineer",   "manager": "Liu Yang",       "joining_date": "2020-07-01", "status": "Active",   "country": "China"},
    "2002": {"name": "Mei Lin",      "department": "Sales",       "designation": "Sales Manager",     "manager": "Chen Fang",      "joining_date": "2018-03-15", "status": "Active",   "country": "China"},
    "2003": {"name": "Jian Wu",      "department": "Finance",     "designation": "Finance Lead",      "manager": "Sun Li",         "joining_date": "2021-09-01", "status": "Active",   "country": "China"},
}

LEAVE_BALANCES: dict[str, dict[str, int]] = {
    "1001": {"Annual Leave": 6,  "Sick Leave": 8},
    "1002": {"Annual Leave": 10},
    "1003": {"Annual Leave": 4},
    "1004": {"Annual Leave": 0},
    "1005": {"Annual Leave": 12},
    "2001": {"Annual Leave": 8},
    "2002": {"Annual Leave": 5, "Marriage Leave": 3},
    "2003": {"Annual Leave": 12},
}

HR_METRICS: list[dict] = [
    {"month": "Jan-2026", "hires": 12, "exits": 5, "attrition_pct": 8.0,  "avg_closure_days": 35},
    {"month": "Feb-2026", "hires": 15, "exits": 7, "attrition_pct": 10.2, "avg_closure_days": 38},
    {"month": "Mar-2026", "hires": 10, "exits": 9, "attrition_pct": 12.5, "avg_closure_days": 40},
    {"month": "Apr-2026", "hires": 18, "exits": 6, "attrition_pct": 9.1,  "avg_closure_days": 34},
    {"month": "May-2026", "hires": 20, "exits": 4, "attrition_pct": 7.5,  "avg_closure_days": 30},
]

# ── Knowledge base (ingested into Pinecone via ingest.py) ────────────────────

LEAVE_POLICY: dict[str, dict[str, dict[str, str]]] = {
    "India": {
        "Annual Leave": {
            "purpose":             "To enable employees to rest and recharge",
            "notice_required":     "Recommended at least 10 working days' notice for leave longer than 5 working days",
            "approval_process":    "Request via HR system; subject to manager approval based on business requirements",
            "carry_forward":       "Up to carry-forward limit; must be used within defined window or balance lapses",
            "encashment":          "Permitted only where required by local practice with Finance/HR approval",
            "public_holidays":     "Public holidays falling on a working day during annual leave are NOT deducted",
            "blackout_periods":    "Some functions may impose blackout periods during operational peaks",
            "leave_during_notice": "Subject to manager approval; may be restricted based on handover requirements",
        },
        "Sick Leave": {
            "purpose":         "For illness, injury, or medical treatment",
            "notification":    "Inform manager as early as possible on the first day of absence",
            "certification":   "Medical certificate may be required depending on duration and local practice",
            "return_to_work":  "Contact HR if reasonable adjustments are needed (e.g., phased return)",
            "fitness_to_work": "Company may request fitness-for-work confirmation for safety-sensitive roles",
            "confidentiality": "Medical information is handled confidentially; shared only on need-to-know basis",
        },
        "Maternity Leave": {
            "entitlement":     "Per statutory requirements (Maternity Benefit Act); HR will confirm exact entitlement",
            "eligibility":     "HR will confirm eligibility and documentation requirements",
            "notice_required": "Contact HR at least 8 weeks in advance where possible",
            "flexible_work":   "Temporary flexible work arrangements may be considered on return, subject to role feasibility",
            "contact":         "india-hr@xyz.example",
        },
        "Paternity Leave": {
            "purpose":         "Company programme to support bonding and caregiving following birth or adoption",
            "notice_required": "Contact HR in advance to confirm eligibility and required documentation",
            "contact":         "india-hr@xyz.example",
        },
        "Caregiver Leave": {
            "purpose":          "For urgent dependent care situations",
            "approval_process": "Discuss with your manager and HR before taking leave",
            "contact":          "india-hr@xyz.example",
        },
        "Bereavement Leave": {
            "entitlement":      "May be granted for death of an immediate family member",
            "extension":        "Additional unpaid leave may be approved at HR/manager discretion",
            "approval_process": "Notify manager and contact HR with relevant details",
        },
        "Marriage Leave": {
            "entitlement":   "May be granted once per employee during tenure",
            "documentation": "Documentation required; contact HR for details",
        },
        "Study / Exam Leave": {
            "eligibility":      "For job-relevant qualifications with prior manager and HR approval",
            "approval_process": "Submit request with details of the qualification and exam dates",
        },
        "Unpaid Leave": {
            "eligibility": "When paid leave is exhausted or a longer absence is needed",
            "request":     "Must include reason, dates, and a coverage/handover plan",
            "impact":      "May affect statutory contributions and benefits; HR will confirm impacts before approval",
            "sign_off":    "Extended durations may require additional management/HR sign-off",
            "contact":     "india-hr@xyz.example",
        },
    },
    "China": {
        "Annual Leave": {
            "entitlement":         "5–15 working days depending on service tenure band; HR confirms band",
            "accrual":             "Credited monthly, pro-rated for joiners; HR confirms tenure band at onboarding",
            "carry_forward":       "Up to 5 days with approval; must be used by 31 March of the following year or lapses",
            "encashment":          "Generally not practised; may apply at termination subject to payroll rules",
            "notice_required":     "Recommended at least 10 working days' notice for leave longer than 5 working days",
            "approval_process":    "Request via HR system; subject to manager approval",
            "blackout_periods":    "Some functions may impose blackout periods during operational peaks",
            "leave_during_notice": "Subject to manager approval; may be restricted based on handover needs",
            "public_holidays":     "Public holidays falling on a working day during annual leave are NOT deducted",
        },
        "Sick Leave": {
            "purpose":         "For illness, injury, or medical treatment",
            "notification":    "Inform manager as early as possible on the first day of absence",
            "certification":   "Medical/hospital documentation typically required, especially for multi-day absences",
            "return_to_work":  "Contact HR if reasonable adjustments are needed",
            "fitness_to_work": "Company may request fitness-for-work confirmation for safety-sensitive roles",
            "confidentiality": "Medical information is handled confidentially",
        },
        "Marriage Leave": {
            "entitlement":   "3 working days (illustrative); once per marriage event",
            "window":        "Must be taken within 12 months of the marriage event",
            "documentation": "Supporting documentation required with request",
        },
        "Maternity Leave": {
            "entitlement":     "Statutory baseline plus local additions (eligibility-based); HR will confirm",
            "eligibility":     "Per statutory eligibility; HR will confirm documentation and local administrative steps",
            "notice_required": "Contact HR early to confirm documentation and local requirements",
            "flexible_work":   "Phased return/transition plan may be considered where operationally feasible",
            "contact":         "cn-hr@xyz.example",
        },
        "Paternity Leave": {
            "entitlement": "10–15 days (region-specific, illustrative)",
            "window":      "Must be taken within the statutory window",
            "eligibility": "Per eligibility; HR will confirm documentation required",
            "contact":     "cn-hr@xyz.example",
        },
        "Bereavement Leave": {
            "entitlement":      "3 working days per event for immediate family members",
            "approval_process": "Notify manager and contact HR",
        },
        "Unpaid Leave": {
            "entitlement": "Up to 20 working days per year (approval-based)",
            "request":     "Must include reason, dates, and a coverage/handover plan",
            "impact":      "May affect statutory contributions and benefits; HR will confirm impacts before approval",
            "sign_off":    "Extended durations may require additional sign-off",
            "contact":     "cn-hr@xyz.example",
        },
    },
}

BENEFITS: dict[str, dict[str, dict]] = {
    "India": {
        "Health Insurance": {
            "coverage":                 "Group medical insurance covering inpatient and outpatient treatment",
            "cashless_hospitalisation": "Available at network providers (where available)",
            "reimbursement":            "Reimbursement option available for non-network providers",
            "preventive_checkups":      "Annual health check-ups may be included for eligible employees",
            "eligibility":              "Typically effective from start date or after a short waiting period",
            "dependents":               "Spouse/partner and children may be eligible subject to plan rules",
            "claims":                   "Submit with required documentation within plan timelines",
            "contact":                  "india-hr@xyz.example",
        },
        "Provident Fund (PF)": {
            "type":          "Statutory social security programme",
            "contributions": "Both employer and employee contributions as per statutory guidelines",
            "payslip":       "Contribution percentages are reflected on your monthly payslip",
            "eligibility":   "Applicable per statutory requirements; HR will confirm at onboarding",
            "contact":       "india-hr@xyz.example",
        },
        "Gratuity": {
            "type":        "Long-service benefit payable per applicable law",
            "eligibility": "Subject to minimum service requirements under applicable law",
            "calculation": "Calculated on eligible wage components; processed during final settlement after exit clearance",
            "contact":     "india-hr@xyz.example",
        },
        "Business Travel Reimbursement": {
            "pre_approval":     "Required before booking any travel",
            "travel_class":     "Economy class by default for all flights",
            "accommodation":    "Hotel stays should be reasonable and safe",
            "meal_allowance":   "INR 600 (breakfast) | INR 900 (lunch) | INR 1,200 (dinner) per person",
            "local_conveyance": "Taxis/rideshares reimbursed when public transport is impractical; include route and business purpose",
            "mobile_internet":  "Reimbursable where required for business with manager approval",
            "submission":       "Itemised receipts required; submit via HR portal",
            "contact":          "india-hr@xyz.example",
        },
    },
    "China": {
        "Health Insurance": {
            "coverage":        "Supplemental medical insurance complementing mandatory statutory healthcare",
            "inpatient":       "Inpatient treatment and selected outpatient services, subject to policy limits",
            "eligibility":     "Typically effective from start date or after a short waiting period",
            "dependents":      "Spouse/partner and children may be eligible subject to plan rules",
            "claims":          "Submit with required documentation within plan timelines",
            "confidentiality": "Personal health information processed per applicable privacy laws",
            "contact":         "cn-hr@xyz.example",
        },
        "Social Insurance & Housing Fund": {
            "type":          "Mandatory statutory social insurance and housing fund (五险一金)",
            "contributions": "Employer and employee contribution rates follow local regulations; processed through payroll",
            "payslip":       "Deductions and contributions are shown on your monthly payslip",
            "eligibility":   "Mandatory for all employees on local payroll; HR will confirm at onboarding",
            "contact":       "cn-hr@xyz.example",
        },
        "Business Travel Reimbursement": {
            "pre_approval":    "Required before booking any travel",
            "travel_options":  "Use cost-effective options and safe accommodations",
            "meal_allowance":  "CNY 40 (breakfast) | CNY 70 (lunch) | CNY 120 (dinner) per person",
            "local_transport": "Metro/public transport preferred; taxis reimbursable with justification",
            "submission":      "Submit within 30 days with itemised receipts and business purpose",
            "contact":         "cn-hr@xyz.example",
        },
    },
}

HOLIDAYS: dict[str, dict[str, list[dict[str, str]]]] = {
    "India": {
        "mandatory": [
            {"date": "2025-01-01", "name": "New Year's Day",               "type": "National"},
            {"date": "2025-01-14", "name": "Makar Sankranti / Pongal",     "type": "Festival"},
            {"date": "2025-01-26", "name": "Republic Day",                 "type": "National"},
            {"date": "2025-03-14", "name": "Holi",                         "type": "Festival"},
            {"date": "2025-04-14", "name": "Dr. B.R. Ambedkar Jayanti",    "type": "National"},
            {"date": "2025-04-18", "name": "Good Friday",                  "type": "Festival"},
            {"date": "2025-05-01", "name": "Maharashtra Day / Labour Day", "type": "National"},
            {"date": "2025-08-15", "name": "Independence Day",             "type": "National"},
            {"date": "2025-09-29", "name": "Dussehra",                     "type": "Festival"},
            {"date": "2025-10-02", "name": "Gandhi Jayanti",               "type": "National"},
            {"date": "2025-10-20", "name": "Diwali (Lakshmi Puja)",        "type": "Festival"},
            {"date": "2025-10-21", "name": "Diwali (Padwa)",               "type": "Festival"},
            {"date": "2025-11-05", "name": "Guru Nanak Jayanti",           "type": "Festival"},
            {"date": "2025-12-25", "name": "Christmas Day",                "type": "National"},
        ],
        "restricted": [
            {"date": "2025-03-31", "name": "Id-ul-Fitr (Eid)"},
            {"date": "2025-04-06", "name": "Ram Navami"},
            {"date": "2025-04-10", "name": "Mahavir Jayanti"},
            {"date": "2025-05-12", "name": "Buddha Purnima"},
            {"date": "2025-07-06", "name": "Eid-ul-Adha"},
            {"date": "2025-08-09", "name": "Muharram"},
            {"date": "2025-09-05", "name": "Onam"},
            {"date": "2025-11-01", "name": "Kannada Rajyotsava"},
            {"date": "2025-11-15", "name": "Guru Tegh Bahadur Martyrdom Day"},
        ],
    },
    "China": {
        "mandatory": [
            {"date": "2025-01-01", "name": "New Year's Day",                                          "type": "National"},
            {"date": "2025-01-28", "name": "Spring Festival — Day 1 (Chinese New Year)",              "type": "Traditional"},
            {"date": "2025-01-29", "name": "Spring Festival — Day 2",                                 "type": "Traditional"},
            {"date": "2025-01-30", "name": "Spring Festival — Day 3",                                 "type": "Traditional"},
            {"date": "2025-01-31", "name": "Spring Festival — Day 4",                                 "type": "Traditional"},
            {"date": "2025-02-01", "name": "Spring Festival — Day 5",                                 "type": "Traditional"},
            {"date": "2025-02-02", "name": "Spring Festival — Day 6",                                 "type": "Traditional"},
            {"date": "2025-02-03", "name": "Spring Festival — Day 7",                                 "type": "Traditional"},
            {"date": "2025-04-04", "name": "Qingming Festival — Day 1",                               "type": "Traditional"},
            {"date": "2025-04-05", "name": "Qingming Festival — Day 2 (Tomb Sweeping)",               "type": "Traditional"},
            {"date": "2025-04-06", "name": "Qingming Festival — Day 3",                               "type": "Traditional"},
            {"date": "2025-05-01", "name": "Labour Day — Day 1",                                      "type": "National"},
            {"date": "2025-05-02", "name": "Labour Day — Day 2",                                      "type": "National"},
            {"date": "2025-05-03", "name": "Labour Day — Day 3",                                      "type": "National"},
            {"date": "2025-05-04", "name": "Labour Day — Day 4",                                      "type": "National"},
            {"date": "2025-05-05", "name": "Labour Day — Day 5",                                      "type": "National"},
            {"date": "2025-05-31", "name": "Dragon Boat Festival — Day 1",                            "type": "Traditional"},
            {"date": "2025-06-01", "name": "Dragon Boat Festival — Day 2",                            "type": "Traditional"},
            {"date": "2025-06-02", "name": "Dragon Boat Festival — Day 3",                            "type": "Traditional"},
            {"date": "2025-10-01", "name": "National Day / Golden Week — Day 1",                      "type": "National"},
            {"date": "2025-10-02", "name": "National Day / Golden Week — Day 2",                      "type": "National"},
            {"date": "2025-10-03", "name": "National Day / Golden Week — Day 3",                      "type": "National"},
            {"date": "2025-10-04", "name": "National Day / Golden Week — Day 4",                      "type": "National"},
            {"date": "2025-10-05", "name": "National Day / Golden Week — Day 5",                      "type": "National"},
            {"date": "2025-10-06", "name": "National Day / Golden Week — Day 6 + Mid-Autumn Festival","type": "National"},
            {"date": "2025-10-07", "name": "National Day / Golden Week — Day 7",                      "type": "National"},
        ],
    },
}

HR_CONTACTS: dict[str, dict] = {
    "India": {
        "General HR": {
            "email":   "india-hr@xyz.example",
            "channel": "HR portal / ticketing system",
            "handles": "Policy questions, leave corrections, benefits support, documentation requests",
            "urgent":  "For urgent matters (safety, harassment, serious misconduct) contact Country HR Lead directly",
            "tip":     "Provide your Employee ID, location, dates, and a brief description when raising a ticket",
        },
        "Country HR Lead": {
            "contact":     "Country HR Lead (India)",
            "email":       "india-hr@xyz.example",
            "when_to_use": "Urgent issues involving safety, harassment, or serious misconduct",
        },
        "Escalation Path": [
            "Step 1 → Raise query via HR portal or email india-hr@xyz.example. Include Employee ID, location, dates, and description.",
            "Step 2 → If unresolved: Contact your HR Business Partner (HRBP) or line manager's HR contact.",
            "Step 3 → For urgent/serious matters (safety, harassment, misconduct): Contact Country HR Lead directly via india-hr@xyz.example.",
            "Step 4 → Formal grievance: Submit via HR portal with full details; handled confidentially.",
            "Step 5 → Retaliation against employees raising concerns in good faith is strictly prohibited.",
        ],
    },
    "China": {
        "General HR": {
            "email":   "cn-hr@xyz.example",
            "channel": "HR portal / ticketing system",
            "handles": "Policy questions, leave corrections, benefits support, documentation requests",
            "urgent":  "For urgent matters (safety, harassment, serious misconduct) escalate immediately using the channels below",
            "tip":     "Provide your Employee ID, location, dates, and a brief description when raising a ticket",
        },
        "Country HR Lead": {
            "contact":     "Country HR Lead (China)",
            "email":       "cn-hr@xyz.example",
            "when_to_use": "Unresolved issues after China HR Helpdesk; urgent safety or misconduct matters",
        },
        "Regional HR Head": {
            "contact":     "Regional HR Head — APAC",
            "when_to_use": "Escalation after Country HR Lead; issues unresolved within 5 working days",
        },
        "Escalation Path": [
            "Step 1 → Line Manager / People Manager. Target: within 2 working days.",
            "Step 2 → China HR Helpdesk (cn-hr@xyz.example). Target: within 3 working days.",
            "Step 3 → Country HR Lead – China. Target: within 5 working days.",
            "Step 4 → Regional HR Head – APAC (for unresolved issues). Target: within 7 working days.",
            "Step 5 → Retaliation against employees raising concerns in good faith is strictly prohibited.",
        ],
    },
}
