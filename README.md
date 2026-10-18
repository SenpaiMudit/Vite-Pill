<div align="center">

# 💊 Vite Pill

### _Cryptographic Unit-Level Drug Serialization & Anti-Counterfeit Verification System_

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Zero-JS](https://img.shields.io/badge/JavaScript-0%25%20(Pure%20HTML%2BCSS)-yellow?style=for-the-badge&logo=html5&logoColor=white)](#-the-zero-javascript-philosophy)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Android APK](https://img.shields.io/badge/Android%20App-753%20KB%20APK-3DDC84?style=for-the-badge&logo=android&logoColor=white)](vite-pill.apk)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**Vite Pill** is an anti-counterfeit pharmaceutical verification system engineered to combat fake medications across the global supply chain using unit-level micro-QR serialization and a **100% Zero-JavaScript** web architecture.

</div>

---

## 📌 Table of Contents

- [The Crisis We Solve](#-the-crisis-we-solve)
- [Core Architecture & Solution](#-core-architecture--solution)
- [⚡ The Zero-JavaScript Philosophy](#-the-zero-javascript-philosophy)
- [✨ Key Features](#-key-features)
- [📱 Android Field App (APK)](#-android-field-app-apk)
- [📐 System Flow & Verification Logic](#-system-flow--verification-logic)
- [🗂️ Project Structure](#️-project-structure)
- [🚀 Quickstart & Installation](#-quickstart--installation)
- [🌐 Deployment Guide](#-deployment-guide)
- [🎨 Frontend Standard Compliance Matrix](#-frontend-standard-compliance-matrix)
- [🔒 Security & Disclosures](#-security--disclosures)
- [📄 License & Contact](#-license--contact)

---

## 🌍 The Crisis We Solve

According to the **World Health Organization (WHO)**:
* Over **1,000,000 deaths occur annually** due to counterfeit and substandard pharmaceuticals.
* In developing nations, **1 in 10 medical products** is substandard or falsified.
* Traditional barcodes only track shipping pallets or warehouse boxes — **once individual blister packs reach retail pharmacies or rural clinics, patients have zero way to verify authenticity**.

Criminal networks exploit this gap by collecting empty authentic boxes and refilling them with contaminated or inert pills (e.g. chalk, starch, or toxic compounds).

**Vite Pill solves this at the unit level.** By imprinting unique cryptographic micro-QR codes directly onto blister pockets, each pill package carries an unforgeable digital identity linked directly to manufacturer production records.

---

## 💡 Core Architecture & Solution

Vite Pill operates as a three-pillar pharmaceutical verification network:

1. **Pharmaceutical Manufacturer Registry (`/add`)**:
   - Licensed pharmaceutical manufacturers securely input batch specifics: Active Pharmaceutical Ingredients (API), dosage strength (mg), clinical indications, manufacturing date, and expiry date.
   - Built-in duplicate detection blocks fraudulent attempts to re-register existing batch identifiers.
   - Generates a unique 16-hex cryptographic serial UID and high-density micro-QR code.

2. **Consumer & Pharmacy Verification Engine (`/scan`, `/verify/<uid>`)**:
   - Patients or pharmacists scan the blister pack's micro-QR with any camera or upload a photo.
   - The server decodes the optical matrix and executes a sub-millisecond query against the secured database.
   - Returns a high-visibility verified drug card:
     - 🟢 **Verified Authentic**: Displays exact chemical composition, indications, manufacturer, and expiry status.
     - 🔴 **Counterfeit Warning**: If the UID does not exist or has been cloned, triggers an immediate warning with hotlines to report the incident directly to health authorities.

3. **Master Regulatory Authority (`/admin`)**:
   - Provisioning portal for pharmaceutical enterprise accounts.
   - Real-time audit log of all registered medication batches.

---

## ⚡ The Zero-JavaScript Philosophy

**Vite Pill is strictly built with 0% JavaScript (Pure HTML5 + Vanilla CSS3).**

### Why Zero JavaScript?

| Vector | Traditional Web App (React/Vue/JS) | Vite Pill Zero-JS Architecture |
|---|---|---|
| **Client-Side XSS Vulnerabilities** | High — vulnerable to script injection & DOM exploits | **Zero** — no client script execution possible |
| **Device & Browser Compatibility** | Fails on older hospital terminals or feature phones | **100% universal** — works on any browser engine |
| **Bandwidth & Initial Load** | Heavy (1MB+ bundle parsing & execution) | **Sub-100ms** instant paint (~12 KB payload) |
| **Battery Consumption in Field** | CPU-intensive client re-rendering | Negligible battery draw for field inspectors |
| **State Management** | Complex client-side stores | Pure CSS `:target`, checkbox hacks & native HTTP POST/GET |

### How Pure CSS Powers Interactivity:
* **Mobile Drawer Navigation**: Pure CSS checkbox toggle hack (`input.nav-toggle:checked ~ nav`).
* **Modal Windows**: Pure CSS `:target` pseudo-class (`#admin-portal:target`).
* **Interactive Live Simulator**: Pure CSS radio tabs (`#tab-authentic:checked`).
* **Forms & Validation**: Native HTML5 form validation (`required`, `pattern`, `type="date"`, `type="number"`).

---

## ✨ Key Features

- **Unit-Level Cryptographic Serialization**: Unique 16-character hexadecimal identifier per batch or pill packet.
- **Server-Side QR Image Analysis**: Pyzbar + Pillow decode pipeline directly on the server.
- **Direct Serial Verification**: Immediate lookup via `https://domain/verify/<uid>` without needing proprietary apps.
- **Expiry Safety Guard**: Automatic alert highlighting expired or near-expiry authentic medications.
- **Duplicate Batch Collision Prevention**: Prevents duplicate production runs with identical metadata.
- **Role-Based Authentication**: Isolated Manufacturer Portal and Master Admin Dashboard.
- **Custom 404 & Safety Fallbacks**: Branded error handler preventing broken pages.

---

## 📱 Android Field App (APK)

For field drug inspectors, clinical dispensaries, and border control officers, Vite Pill includes a standalone Android APK:

* **File**: [`vite-pill.apk`](vite-pill.apk) (753 KB)
* **Compatibility**: Android 8.0+
* **Functionality**: Optical camera micro-QR scanner with zero external tracking libraries.

---

## 📐 System Flow & Verification Logic

```mermaid
flowchart TD
    A[Pharma Manufacturer] -->|Inputs Drug Details| B[Vite Pill Batch Registry]
    B -->|Check Duplicate Conditions| C{Exists in DB?}
    C -->|Yes| D[Block Duplicate & Alert]
    C -->|No| E[Generate Cryptographic 16-Hex UID]
    E --> F[Generate High-Density Micro-QR]
    F --> G[Imprint on Blister Pack]

    H[Patient / Pharmacist] -->|Scans Micro-QR / Enters UID| I[Server-Side Decoder]
    I --> J{UID in Registry?}
    J -->|Yes| K[🟢 Authentic Drug Spec Card]
    K --> L[Verify Ingredients, Expiry & Dosage]
    J -->|No| M[🔴 Counterfeit Alert Triggered]
    M --> N[Report to Drug Safety Hotline]
```

---

## 🗂️ Project Structure

```
vite_pill/
├── index.html                  # 100% Zero-JS High-Converting Landing Page
├── vite-pill.apk               # Android Mobile Verification Application (753 KB)
├── .gitignore                  # Git ignore rules for Python, SQLite & OS files
├── README.md                   # Comprehensive System Documentation
└── vite_pill/                  # Core Flask Application
    ├── app.py                  # Zero-JS Routes, Auth, QR Generation & Pyzbar Logic
    ├── requirements.txt        # Production Dependencies (Flask, Pyzbar, Pillow, Gunicorn)
    ├── Procfile                # One-Click Deployment for Render / Railway
    ├── static/
    │   ├── logo.svg            # Official Vite Pill Brand Vector
    │   ├── css/
    │   │   └── style.css       # Zero-JS Design System & Responsive Foundation
    │   └── qrcodes/            # Generated Cryptographic Micro-QR Assets
    └── templates/
        ├── base.html           # Master Layout (Pure CSS Mobile Menu, Header, Footer)
        ├── index.html          # Portal Hub & Live Statistics
        ├── scan_medicine.html  # Optical Scan & Manual UID Lookup
        ├── add_medicine.html   # Manufacturer Batch Registry & QR Generator
        ├── result.html         # Authentic vs Counterfeit Verified Specs Card
        ├── login.html          # Manufacturer Employee Sign In
        ├── admin_login.html    # Master Admin Authentication
        ├── admin_users.html    # Enterprise Account Management Dashboard
        └── 404.html            # Custom Zero-JS 404 Error Page
```

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/SenpaiMudit/Vite-Pill.git
cd Vite-Pill/vite_pill
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

> **Note on Pyzbar**: On Windows, pyzbar includes bundled zbar DLLs. On Linux distributions (Ubuntu/Debian), install the system C library:
> ```bash
> sudo apt-get update && sudo apt-get install -y libzbar0
> ```

### 4. Run the Application
```bash
python app.py
```
Visit `http://127.0.0.1:5000` in your browser.

---

## 🌐 Deployment Guide

### Deploying to Render / Railway / PaaS

1. Connect your GitHub repository: `https://github.com/SenpaiMudit/Vite-Pill`
2. **Build Command**: `pip install -r vite_pill/requirements.txt`
3. **Start Command**: `cd vite_pill && gunicorn app:app`
4. **Environment Variables**:
   * `SECRET_KEY`: Set a secure random string.
   * `PORT`: `5000` (auto-assigned by Render/Railway).

---

## 🎨 Frontend Standard Compliance Matrix

This project adheres strictly to modern web and usability standards:

| Requirement | Implementation Detail | Status |
|---|---|:---:|
| **0% JavaScript** | No `<script>` tags, no inline event handlers, pure CSS interactivity | ✅ Passed |
| **No Horizontal Scrolling** | `overflow-x: hidden`, strict max-width constraints on all viewports | ✅ Passed |
| **No Broken Links** | All internal routes, portals, and anchor IDs mapped and verified | ✅ Passed |
| **Pure CSS Mobile Menu** | Accessible hamburger navigation via pure CSS checkbox state | ✅ Passed |
| **Favicon** | High-definition SVG pill & cross mark embedded in `<head>` | ✅ Passed |
| **SEO Page Titles** | Descriptive, unique titles for every route | ✅ Passed |
| **Meta Descriptions** | High-relevance pharmaceutical and safety meta tags | ✅ Passed |
| **Footer & Copyright** | Fixed to **2026** with clean links across all views | ✅ Passed |
| **Custom 404 Page** | Informative branded error page with recovery buttons | ✅ Passed |
| **Clickable Phone** | Direct mobile dialing: `<a href="tel:+18005550199">` | ✅ Passed |
| **Clickable Email** | Pre-formatted support link: `<a href="mailto:verify@vitepill.io">` | ✅ Passed |
| **Clickable Logo** | Brand mark routes back to home hub | ✅ Passed |
| **Mobile Optimized** | 100% responsive fluid grid down to 320px screen width | ✅ Passed |

---

## 🔒 Security & Disclosures

* **Tamper-Evident Hashing**: Cryptographic serials prevent enumeration attacks.
* **Zero Client Scripts**: Immunizes the platform from browser extension tampering and XSS exploits.
* **Responsible Disclosure**: To report potential drug counterfeit rings or software vulnerabilities, contact `security@vitepill.io`.

---

## 📄 License & Contact

Distributed under the **MIT License**. See `LICENSE` for details.

- **Lead Maintainer**: [Mudit Misra (@SenpaiMudit)](https://github.com/SenpaiMudit)
- **Direct Phone**: [+1 (800) 555-0199](tel:+18005550199)
- **Official Inquiries**: [verify@vitepill.io](mailto:verify@vitepill.io)
- **Repository**: [https://github.com/SenpaiMudit/Vite-Pill](https://github.com/SenpaiMudit/Vite-Pill)
