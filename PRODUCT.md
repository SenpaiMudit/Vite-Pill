# Product Specification: Vite Pill

## 1. Product Overview & Purpose
Vite Pill is a pharmaceutical anti-counterfeit verification system. Its mission is to eliminate counterfeit and falsified medications from global supply chains by assigning every physical blister pack and medicine container an unalterable, unit-level cryptographic identity (Micro-QR and 16-character hexadecimal UID).

---

## 2. Target Audiences & User Personas

### Persona A: The Patient / Consumer
* **Context**: Standing in a pharmacy or at home holding a medicine packet, seeking reassurance: *"Is this medicine authentic, safe, and unexpired?"*
* **Core Job**: Point a smartphone camera at the packaging micro-QR (or type the printed serial code) and immediately receive a clear, unambiguous authenticity status and full drug fact sheet.
* **Key Need**: Extreme simplicity, instant sub-second verification, zero app-installation friction, and emergency guidance if a counterfeit is detected.

### Persona B: The Retail Pharmacist & Field Clinical Inspector
* **Context**: Receiving drug inventory at a hospital dispensary, clinic, or border inspection checkpoint.
* **Core Job**: Rapidly audit inbound shipments at the individual blister level to ensure no diverted, fake, or recalled batches have penetrated inventory.
* **Key Need**: High-speed batch scanning, verification of active ingredients, manufacturing/expiry date audits, and offline-capable Android APK.

### Persona C: The Licensed Pharmaceutical Manufacturer
* **Context**: Quality Assurance and Production Operations teams at audited pharmaceutical corporations (e.g. Novartis, Pfizer, Cipla).
* **Core Job**: Input production run parameters (APIs, dosage strength, indications, dates) and generate cryptographic micro-QRs for laser-etching onto packaging lines.
* **Key Need**: Secure company dashboard, exportable high-density QR assets (.PNG), batch audit history, and prevention of duplicate batch submissions.

### Persona D: The Regulatory Master Administrator
* **Context**: Health authority regulators (e.g., FDA, EMA, CDSCO) and system platform governors.
* **Core Job**: Inspect pharmaceutical GMP licenses and manually provision secure manufacturer credentials.
* **Key Need**: Full oversight over who is authorized to register medicine batches, real-time audit ledger of all registered drugs, and instant revocation capability for compromised entities.

---

## 3. Core Workflows (Jobs To Be Done)

### Workflow 1: Regulatory Provisioning (Admin → Manufacturer)
1. Regulatory Admin logs into the restricted administrative console (`/admin`).
2. Admin reviews the pharmaceutical corporation's legal license and contact details.
3. Admin provisions an authorized manufacturer account with unique credentials.
4. The system stores the entity in the secure registry; credentials are transferred to the manufacturer representative.

### Workflow 2: Batch Serialization (Manufacturer → Supply Chain)
1. Manufacturer signs in at `/login` with admin-provisioned credentials.
2. Navigates to `/add` to register a new production batch:
   * Commercial & Generic Drug Name
   * Active Strength (mg)
   * Active Pharmaceutical Ingredients (APIs)
   * Clinical Indications & Directions
   * Manufacturing Date & Expiration Date
3. System verifies uniqueness against existing database records (duplicate collision guard).
4. System generates a unique 16-hex UID and a cryptographic Micro-QR linked to `https://<domain>/verify/<uid>`.
5. Manufacturer downloads high-density micro-QRs for industrial packaging application.

### Workflow 3: Consumer / Pharmacist Verification (Public → System)
1. User navigates to `/scan` on any device or scans the physical QR with a standard camera.
2. Optical matrix is decoded by the server (or user enters the printed serial code directly).
3. System checks the UID against the authenticated database:
   * **If Match Found**: Renders a clinical Certificate of Authenticity displaying active ingredients, manufacturer audit trail, dosage, and expiration status.
   * **If Match Not Found**: Triggers an emergency Counterfeit Warning with direct hotline dialing (`tel:`) and safety reporting guidance.

---

## 4. Fundamental Business Rules & Anti-Fraud Invariants

1. **Strictly No Public Self-Registration for Manufacturers**:
   Public user registration for manufacturers is permanently disabled. Fraudulent actors can never self-register to issue falsified QR codes. Only the Regulatory Admin can provision manufacturer accounts.
2. **Duplicate Batch Collision Guard**:
   The engine rejects batch registration attempts where the Drug Name, Strength, Manufacturing Date, and Expiration Date match an existing record.
3. **Unit-Level Cryptographic Traceability**:
   Every batch is permanently indexed under a 16-character hexadecimal UID linked to the issuing company name.
4. **Permanent Manufacturer Attribution**:
   Every registered batch permanently records `registered_by = session['company_name']`, establishing an immutable legal audit trail.

---

## 5. Technical Boundaries & Constraints

* **100% Zero-JavaScript Requirement**:
  The web application must function completely with zero client-side JavaScript. All interactive states (navigation menus, modals, tabs, form validations) are powered strictly by semantic HTML5 and CSS3 (`:target`, checkbox hacks, radio toggles).
* **Zero Client-Side Attack Surface**:
  With 0% JavaScript, client-side XSS and malicious script injection are technically impossible.
* **Universal Hardware Compatibility**:
  Must operate seamlessly on all legacy hospital terminals, basic smartphones, and browsers with JavaScript disabled.
* **Dual Deployment Model**:
  - Web Application: Hosted Flask application with instant universal access.
  - Mobile Field App: Standalone Android APK (`vite-pill.apk`, 753 KB) for mobile optical scanning.

---

## 6. Canonical Terminology

* **Serial UID**: The unique 16-character hexadecimal identifier assigned to each medicine unit.
* **Micro-QR**: The high-density optical 2D barcode imprinted onto blister pockets and bottles.
* **Authorized Entity**: A licensed pharmaceutical corporation audited and provisioned by the Regulatory Admin.
* **Duplicate Collision**: A fraudulent or accidental attempt to re-register an existing production batch.
* **Certificate of Authenticity**: The clinical verification spec sheet confirming manufacturer, active chemical ingredients, dosage, and expiry status.
