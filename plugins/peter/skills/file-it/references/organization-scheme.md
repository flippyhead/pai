# ~/Documents Organization Scheme

Established by the 2026 reorganization (`~/Documents/REORGANIZATION-PLAN.md` is the original plan; this file is the living summary). If AI Brain has a newer "Documents organization scheme" reference, that wins.

## Folder map

### Properties/
All owned or managed real estate. One subfolder per property, named by street number:
`5808`, `18289`, `1920`, `1422`, `2634`, `3406`, `474`, `617`, `740` (the hangar property), `J-4`, plus `licensing/` for rental/business licensing.

Files inside a property folder: leases, tenant communication, inspection reports, photos of the property, contractor estimates, utility setup. Tenant files may contain SSNs — flag them.

A document mentioning a street address probably belongs here. New property → create a new street-number folder and note it in AI Brain.

### Aviation/
- `N224JK/` — everything about the aircraft itself: insurance policies, annual inspections, maintenance invoices, certificates, endorsements, authorization letters
- `Hangar/` — hangar facility docs (the hangar *property* purchase is `Properties/740/`)
- `flight-plans/` — saved routes
- `reference/` — training PDFs, course certificates, FAA advisory circulars, airport brochures, study sheets
- `insurance/` — broker proposals (issued policies for the plane go in `N224JK/`)

Pilot medical certificates and FAA applications: `Aviation/` root or `N224JK/`.

### Finance/
- `taxes/` — one folder per year (2013–present), plus `older/`
- `investments/` — angel investments, equity memos, capital account statements (Pure Watercraft/PWC, Accolade, etc.)
- `insurance/` — health/auto insurance cards and statements (aviation insurance → Aviation/, property insurance → that property's folder)
- root — expense trackers (.numbers), payment confirmations, employee benefit packets

Subject beats format: an invoice for plane maintenance is Aviation, a property tax bill is Properties. Finance is for finance-qua-finance.

### Personal/
- `identity/` — **SENSITIVE**: passport, driver's license scans, signature images, official headshot (`peter-headshot.jpg`), trusted-traveler docs
- `security/` — **SENSITIVE**: recovery codes, anything credential-like (and suggest moving secrets to a password manager)
- `legal/` — court documents, agreements, affidavits; `legal/estate/` for trust and will documents (Brown family trust, etc.)
- `medical/` — medical records
- `writing/` — Scrivener projects, manuscripts
- `events/` — event tickets/docs (Burning Man, etc.)
- `car/` — vehicle documents, police reports
- `friends/` — docs relating to friends

Resumes (peter-travis-brown.pdf) live at `Personal/` root.

### Projects/
Non-code business ventures, one folder each: `Pathable` (incl. acquisition/Community Brands), `Brown Town Spa`, `SJPA` (San Juan Pilots Assn), `CSI`, `UrbanX`, `Fetching`. New venture → new folder here (COPA Commander, Already.dev, Curb-to-Close, etc. if they accumulate documents).

**Code projects do NOT go in ~/Documents.** Anything with source code, node_modules, a git repo → `~/Development/`.

### Foster/
Foster Realty Co business (includes a OneDrive-synced folder). Real-estate-brokerage files go here, not Properties/ (Properties is for owned/managed buildings).

### Claude/
Managed by Claude (Artifacts, Projects, Scheduled). **Never file into it, never reorganize it.**

### Archive/
Historical or inactive material:
- `travel/` — past-trip receipts and docs, by destination (Japan, Brazil, Mexico, London, NYC, Hawaii, India, `misc/`)
- `screenshots/` — old screenshots, exported images with no lasting value
- `recordings/` — old Zoom/QuickTime recordings
- `misc/` — one-off keepsakes, old tickets, anything kept-but-inactive
- `review/` — **triage inbox**: files whose identity is unclear; revisit later
- `to-delete/` — staged for deletion; user deletes manually. Nothing is ever deleted directly.
- `development/` — old code archives (legacy; new code → ~/Development)

Active vs archive: if it relates to something ongoing (current property, the plane, an active project), it goes in the subject folder even if old. Archive is for closed chapters.

## Naming conventions

- Rename cryptic names (social-media export hashes, `IMG_xxxx`, `Untitled N`, download IDs) to descriptive kebab-case: `peter-headshot.jpg`, `n224jk-prop-overhaul-invoice-2026.pdf`
- Keep already-meaningful names, even if their style differs
- Include the year for time-bound docs (invoices, policies, tax docs)
- Never change extensions

## Sensitive-content checklist

Flag in the report and file appropriately:
- SSNs (tenant files, tax docs) → keep in place but call out
- Credentials, recovery codes, connection strings → `Personal/security/`, suggest password manager + deletion
- Identity documents, signatures → `Personal/identity/`
- Production secrets found in old code → call out explicitly
