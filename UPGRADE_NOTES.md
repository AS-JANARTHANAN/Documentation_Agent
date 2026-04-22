# 📄 AGENT SYSTEM v2 — UPGRADE NOTES & USAGE GUIDE
## What was broken in v1, what is fixed in v2, how to use

---

## ❌ WHAT WAS WRONG IN v1

### Agent 1 Bug — Only 1 subheading per chapter
The Ollama customization call was replacing ALL subheadings including
the fixed ones (Overview, Purpose, Scope...) and reducing them to just 1 per chapter.
For example, Chapter 2 Literature Survey was getting only "2.1 Study 1"
instead of 5 studies (2.1 to 2.5).

### Agent 2 Bug — Stopped at Chapter 3
The content from ChatGPT was incomplete because the Agent 1 prompt didn't
force the AI to write all chapters. Agent 2 can only format what it receives,
so if the content stops at Ch3, the document stops at Ch3.

### Formatting Issue — Header looked like a watermark
The header text was grey/faded, making it look like a background watermark
on every page instead of a clean page header.

---

## ✅ WHAT IS FIXED IN v2

### Agent 1 v2 Fixes
```
BEFORE: Ollama was customizing ALL subheadings → reduced everything to 1 sub per chapter
AFTER:  Ollama ONLY customizes:
          - Chapter 2: The 5 literature study titles
          - Chapter 5: The 6 module names
        Everything else is HARDCODED and FIXED

BEFORE: Chapter structure was wrong
AFTER:  Exact structure from the FSD sample document:
          CH1: 1.1 Overview, 1.2 Purpose, 1.3 Scope, 1.4 Significance
          CH2: 2.1 to 2.5 (5 literature studies)
          CH3: 3.1, 3.1.1 Disadvantages, 3.2, 3.2.1 Advantages
          CH4: 4.1 Architecture, 4.2 Use Case, 4.3 DFD (with [IMAGE_PLACEHOLDER])
          CH5: 5.1 to 5.6 (6 modules)
          CH6: 6.1 Sample Coding, 6.2 Screenshots
          CH7: 7.1 Conclusion, 7.2 Future Enhancement
          REF: 12-15 references

BEFORE: Prompt was too vague, AI stopped mid-way
AFTER:  Each chapter has detailed per-subheading word targets
        Each chapter has specific instructions (lit survey format, module format, etc.)
        Prompt explicitly says: "DO NOT STOP UNTIL ALL 7 CHAPTERS ARE COMPLETE"
```

### Agent 2 v2 Fixes
```
BEFORE: No [SUBHEADING_SUB] tag → 3.1.1 and 3.2.1 were not handled
AFTER:  [SUBHEADING_SUB: 3.1.1 DISADVANTAGES] → 12pt, bold, left-aligned

BEFORE: No [REFERENCES_START/END] or [REFERENCE:] tag support
AFTER:  Full references section with numbered entries

BEFORE: No [CODE_SAMPLE] support for Ch6
AFTER:  [CODE_SAMPLE] inserts a placeholder for code screenshots

BEFORE: Header was grey/faded (looked like watermark)
AFTER:  Header is black text with a clean bottom border line

BEFORE: Document stopped at Ch3
AFTER:  Handles all 7 chapters + References
```

---

## 📁 FILE STRUCTURE

```
your_project/
├── agent1_prompt_generator_v2.py    ← Run this first
├── agent2_formatter_v2.py           ← Run this after getting content
├── UPGRADE_NOTES.md                 ← This file
│
├── PROMPT_PART2_BOOK_SHARING.txt    ← Output from Agent 1
│
├── content_part2.txt                ← Paste ChatGPT/Gemini output here
│
└── Final_ProjectDoc.docx            ← Output from Agent 2
```

---

## 🚀 STEP-BY-STEP USAGE

### Step 1: Run Agent 1
```bash
python agent1_prompt_generator_v2.py
```
Enter:
- Project topic (e.g. "Book Sharing System")
- Brief description (mention key features and tech stack)
- Degree, Department, College, Guide name

It will:
1. Ask Ollama for 5 literature study titles relevant to your topic
2. Ask Ollama for 6 module names relevant to your topic
3. Generate the mega-prompt file: `PROMPT_PART2_<TOPIC>.txt`

### Step 2: Get Content from AI
1. Open the generated `PROMPT_PART2_*.txt` file
2. Copy ALL of it
3. Paste into ChatGPT / Gemini / Claude
4. Wait for the full response (it will be long — 7 full chapters)
5. Save the response as `content_part2.txt`

⚠ IMPORTANT: Make sure the AI writes ALL 7 chapters.
If it stops early, say: "Continue from where you stopped"
and paste the rest into the same content file.

### Step 3: Run Agent 2
```bash
python agent2_formatter_v2.py
```
Enter:
- Path to your content file
- All project details (title, student name, roll no, college, etc.)
- Output filename

It will:
1. Parse all the [CHAPTER], [SUBHEADING], [CONTENT] tags
2. Use Ollama to trim any overly long paragraphs (optional)
3. Build the .docx with all formatting specs
4. Save the final document

### Step 4: Manual Replacements
After opening the .docx in Microsoft Word:
- Replace each `[ARCHITECTURE DIAGRAM]` box with your actual diagram image
- Replace each `[USE CASE DIAGRAM]` box with your actual diagram image
- Replace each `[DATA FLOW DIAGRAM]` box with your actual diagram image
- Replace screenshot placeholders with actual screenshots
- Update the Table of Contents (if added): Ctrl+A → F9

---

## 📐 FORMATTING SPEC SUMMARY

| Element           | Format                                              |
|-------------------|-----------------------------------------------------|
| Font              | Times New Roman — entire document                   |
| Chapter heading   | 14pt, UPPERCASE, Center, Bold                       |
| Subheading (1.1)  | 14pt, UPPERCASE, Left, Bold                         |
| Sub-subheading    | 12pt, UPPERCASE, Left, Bold (for 3.1.1 etc.)        |
| Body paragraph    | 12pt, Justified, Tab indent on first line           |
| Line spacing      | 1.5 throughout                                      |
| Margins           | 1 inch all sides                                    |
| Header            | Project title centered, black text, bottom line     |
| Footer            | Page number centered (starts at 1)                  |
| Image placeholder | Grey bordered box with caption                      |
| List items        | Bullet (•), 12pt, 0.5 inch indent                  |
| References        | Numbered [1], [2]..., 12pt, hanging indent         |

---

## 🏷 CONTENT TAG REFERENCE (v2)

| Tag | Purpose |
|-----|---------|
| `[CHAPTER: N \| TITLE]` | Chapter heading |
| `[SUBHEADING: X.X TITLE]` | Section heading (e.g. 1.1, 2.3) |
| `[SUBHEADING_SUB: X.X.X TITLE]` | ★ Nested heading (e.g. 3.1.1) |
| `[CONTENT]` | One body paragraph |
| `[IMAGE_PLACEHOLDER: desc]` | Diagram placeholder with box |
| `[LIST_START]` | Begin bullet list |
| `[LIST_ITEM: text]` | One bullet point |
| `[LIST_END]` | End bullet list |
| `[REFERENCES_START]` | ★ Begin references section |
| `[REFERENCE: text]` | ★ One reference entry |
| `[REFERENCES_END]` | ★ End references section |
| `[CODE_SAMPLE]` | ★ Code placeholder |
| `[PAGE_BREAK]` | Force new page |

---

## 🤖 OLLAMA USAGE

Agent 1 uses Ollama for:
  - Generating 5 relevant literature study titles for Ch2
  - Generating 6 relevant module names for Ch5

Agent 2 uses Ollama for (optional):
  - Trimming paragraphs that are over 650 words

To use a different model, edit:
```python
ollama_model="llama3"   # → change to: mistral, phi3, gemma2, etc.
```

---

## ⚠ TROUBLESHOOTING

**"Ollama connection refused"**
→ Run `ollama serve` in a terminal first, then re-run the agent

**"Model not found"**
→ Run: `ollama pull llama3`  (or whichever model you want)

**"Document only has 3 chapters"**
→ The AI content file is incomplete. Open content.txt and check.
→ Re-paste the prompt into ChatGPT and tell it to continue.
→ Append the extra output to your content.txt file.

**"Tags not recognized"**
→ Each tag must be on its own line with no extra spaces inside [ ]
→ Check the AI didn't add markdown or remove tags

**"Header looks weird / double header"**
→ Open in Microsoft Word (not LibreOffice/Google Docs)
→ Right-click the header area → Edit Header → verify

**"Images not replacing properly"**
→ Click the grey placeholder box in Word
→ Press Delete key
→ Insert → Pictures → choose your diagram image
