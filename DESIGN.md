# Design System Specification: Vite Pill

## 1. Aesthetic Direction: Clinical Pharmaceutical Trust
Grounded directly in the physical reality of medicine packaging, dispensary pharmacy environments, and health authority standards. The visual tone is calm, precise, authoritative, and sterile — avoiding both the generic "SaaS card kit" and sci-fi cyberpunk cliches.

---

## 2. Color System
A restrained, 5-token palette rooted in pharmaceutical verification:

| Token Name | Hex Value | Role & Usage |
|---|---|---|
| **Canvas** | `#f8fafc` | Sterile off-white background, soft on the eyes |
| **Surface** | `#ffffff` | Pure white clinical cards, certificate containers, and form panels |
| **Text Primary** | `#0f172a` | High-contrast slate for effortless reading under poor lighting |
| **Pharma Blue** | `#1d4ed8` | Authoritative regulatory blue for primary buttons and active indicators |
| **Verified Green** | `#15803d` | Pharmacy cross green for verified authentic batches |
| **Alert Red** | `#b91c1c` | High-visibility clinical red for counterfeit and tampering alerts |

---

## 3. Typography & Hierarchy
* **Primary Family**: `Plus Jakarta Sans` (400 regular, 500 medium, 600 semi-bold, 700 bold).
* **Guiding Principles**:
  * One single typeface family used across display titles, body copy, and data elements.
  * Line lengths strictly constrained to under 75 characters (`max-width: 72ch`) for maximum readability.
  * Sentence case on all headings and labels. No tracked-out all-caps eyebrows.
  * No artificial accent colors on individual words in headlines.

---

## 4. Spatial Composition & Structure
* **Hero Treatment**: Asymmetrical split layout. The left column presents the core human problem and direct primary actions; the right column features a live, tactile verification card simulating authentic vs. counterfeit checks.
* **Structural Meaning**: Dividers and outlines are used strictly to delineate data boundaries, not as decoration.
* **Card Hierarchy**: Distinct sizes and padding based on task importance; no cookie-cutter identical boxes.

---

## 5. Zero-JavaScript Mechanics
* **Responsive Mobile Menu**: Pure CSS checkbox hack (`.nav-toggle-input:checked ~ .nav-list`).
* **Enterprise Portal Modal**: Pure CSS `:target` pseudo-class (`#portal-modal:target`).
* **Verification Inspector Tabs**: Pure CSS radio controllers (`#tab-authentic:checked`).
* **Form Submissions**: Semantic HTML5 with native browser input constraints (`required`, `type="date"`, `type="number"`, `capture="environment"`).

---

## 6. Voice, Copywriting & Tone
* **Perspective**: Written directly from the end user's perspective (patients, pharmacists, regulators).
* **Active Voice**: Buttons declare exact actions ("Verify medicine", "Register batch", "Download APK").
* **No Filler**: Zero marketing hyperbole. Clear explanations of what the system does and why admin-only provisioning stops counterfeits.
* **Failure States**: Direct, factual instructions without apology ("Do not ingest this medication. Retain packaging and call the drug integrity hotline.").
