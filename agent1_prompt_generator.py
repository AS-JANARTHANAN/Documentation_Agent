"""
╔══════════════════════════════════════════════════════════╗
║   AGENT 1 v2 — PROJECT DOCUMENTATION PROMPT GENERATOR   ║
╚══════════════════════════════════════════════════════════╝

WHAT WAS WRONG IN v1:
  - Ollama was replacing ALL subheadings including fixed ones
  - Each chapter only got 1 subheading (Ollama reduced them)
  - Chapters 1, 3, 4, 6, 7 are IDENTICAL for every project
  - Only Ch2 (study titles) and Ch5 (module names) change per topic

WHAT IS FIXED IN v2:
  - Chapters 1, 3, 4, 6, 7 are now HARDCODED with exact subheadings
  - Ollama ONLY customizes: Ch2 study titles + Ch5 module names
  - Structure exactly matches the FSD sample document
  - Every chapter now has the correct number of subheadings
  - Word targets are enforced per subheading, not per chapter

RUN:
    python agent1_prompt_generator_v2.py

REQUIREMENTS:
    pip install ollama
    ollama serve
    ollama pull llama3
"""

import ollama
import json
import sys
import re

# ═══════════════════════════════════════════════════════════════
#  FIXED STRUCTURE — Same for ALL projects (never changes)
# ═══════════════════════════════════════════════════════════════
#
#  KEY INSIGHT from FSD sample:
#   CH1 = Overview, Purpose, Scope, Significance  ← FIXED
#   CH2 = 5 literature study titles               ← OLLAMA customizes titles
#   CH3 = Existing, Disadvantages, Proposed, Advantages ← FIXED
#   CH4 = Architecture, Use Case, DFD diagrams    ← FIXED (image placeholders)
#   CH5 = 6 module names                          ← OLLAMA customizes names
#   CH6 = Appendices (sample code + screenshots)  ← FIXED
#   CH7 = Conclusion + Future Enhancement          ← FIXED
#   REF = References list                          ← FIXED
#
# ═══════════════════════════════════════════════════════════════

FIXED_CH1 = {
    "num": 1, "title": "INTRODUCTION",
    "subheadings": [
        {"tag": "1.1", "name": "OVERVIEW",               "words": 500},
        {"tag": "1.2", "name": "PURPOSE OF THE PROJECT",  "words": 450},
        {"tag": "1.3", "name": "SCOPE OF THE PROJECT",    "words": 400},
        {"tag": "1.4", "name": "SIGNIFICANCE OF THE PROJECT", "words": 400},
    ],
    "total_words": 1800
}

# Ch2 study titles are customized by Ollama — placeholders filled in
FIXED_CH2 = {
    "num": 2, "title": "LITERATURE SURVEY",
    "subheadings": [
        {"tag": "2.1", "name": "STUDY_1", "words": 500},
        {"tag": "2.2", "name": "STUDY_2", "words": 500},
        {"tag": "2.3", "name": "STUDY_3", "words": 500},
        {"tag": "2.4", "name": "STUDY_4", "words": 500},
        {"tag": "2.5", "name": "STUDY_5", "words": 500},
    ],
    "total_words": 2500
}

FIXED_CH3 = {
    "num": 3, "title": "EXISTING SYSTEM AND PROPOSED SYSTEM",
    "subheadings": [
        {"tag": "3.1",   "name": "EXISTING SYSTEM",     "words": 500},
        {"tag": "3.1.1", "name": "DISADVANTAGES",        "words": 300},
        {"tag": "3.2",   "name": "PROPOSED SYSTEM",      "words": 500},
        {"tag": "3.2.1", "name": "ADVANTAGES",           "words": 300},
    ],
    "total_words": 1800
}

FIXED_CH4 = {
    "num": 4, "title": "SYSTEM DESIGN",
    "subheadings": [
        {"tag": "4.1", "name": "ARCHITECTURE DIAGRAM",  "words": 400, "image": True},
        {"tag": "4.2", "name": "USE CASE DIAGRAM",      "words": 400, "image": True},
        {"tag": "4.3", "name": "DATA FLOW DIAGRAM",     "words": 400, "image": True},
    ],
    "total_words": 1500
}

# Ch5 module names are customized by Ollama
FIXED_CH5 = {
    "num": 5, "title": "MODULE DESCRIPTION",
    "subheadings": [
        {"tag": "5.1", "name": "MODULE_1", "words": 400},
        {"tag": "5.2", "name": "MODULE_2", "words": 400},
        {"tag": "5.3", "name": "MODULE_3", "words": 400},
        {"tag": "5.4", "name": "MODULE_4", "words": 400},
        {"tag": "5.5", "name": "MODULE_5", "words": 350},
        {"tag": "5.6", "name": "MODULE_6", "words": 350},
    ],
    "total_words": 2400
}

FIXED_CH6 = {
    "num": 6, "title": "APPENDICES",
    "subheadings": [
        {"tag": "6.1", "name": "SAMPLE CODING",   "words": 300},
        {"tag": "6.2", "name": "SCREENSHOTS",     "words": 400},
    ],
    "total_words": 1000
}

FIXED_CH7 = {
    "num": 7, "title": "CONCLUSION AND FUTURE ENHANCEMENT",
    "subheadings": [
        {"tag": "7.1", "name": "CONCLUSION",         "words": 400},
        {"tag": "7.2", "name": "FUTURE ENHANCEMENT", "words": 350},
    ],
    "total_words": 800
}

ALL_CHAPTERS = [FIXED_CH1, FIXED_CH2, FIXED_CH3, FIXED_CH4, FIXED_CH5, FIXED_CH6, FIXED_CH7]
TOTAL_WORDS  = sum(c["total_words"] for c in ALL_CHAPTERS)


# ═══════════════════════════════════════════════════════════════
#  CONTENT TAGS — Agent 2 parses these
# ═══════════════════════════════════════════════════════════════
TAG_REFERENCE = """
MANDATORY FORMATTING TAGS — you MUST use exactly these:

[CHAPTER: N | TITLE]                  → Chapter start (e.g. [CHAPTER: 1 | INTRODUCTION])
[SUBHEADING: X.X TITLE]               → Subheading (e.g. [SUBHEADING: 1.1 OVERVIEW])
[SUBHEADING_SUB: X.X.X TITLE]         → Sub-subheading (e.g. [SUBHEADING_SUB: 3.1.1 DISADVANTAGES])
[CONTENT]                              → One paragraph of body text (5-8 sentences minimum)
[IMAGE_PLACEHOLDER: Figure N.N - desc] → Diagram placeholder
[LIST_START]                           → Start bullet list
[LIST_ITEM: text]                      → One bullet point
[LIST_END]                             → End bullet list
[PAGE_BREAK]                           → Force new page
[REFERENCES_START]                     → Start references
[REFERENCE: text]                      → One reference entry
[REFERENCES_END]                       → End references
"""


# ═══════════════════════════════════════════════════════════════
#  OLLAMA CUSTOMIZER — only for Ch2 titles and Ch5 module names
# ═══════════════════════════════════════════════════════════════
class OllamaCustomizer:
    def __init__(self, model="llama3", host="http://localhost:11434"):
        self.model  = model
        self.client = ollama.Client(host=host)

    def get_literature_study_titles(self, topic: str, description: str) -> list:
        """Ask Ollama for 5 relevant research study titles for the literature survey."""
        print("[Agent 1] Asking Ollama for literature study titles...")
        prompt = f"""For a project called "{topic}", suggest exactly 5 academic research study titles
for a literature survey section.

Project description: {description[:400]}

Return ONLY a JSON array of 5 strings, nothing else. Example:
["STUDY ON PEER-TO-PEER BOOK EXCHANGE SYSTEMS",
 "RESEARCH ON TRUST MECHANISMS IN ONLINE MARKETPLACES",
 "STUDY ON COMMUNITY-BASED RESOURCE SHARING PLATFORMS",
 "RESEARCH ON RATING AND FEEDBACK SYSTEMS IN E-COMMERCE",
 "STUDY ON ROLE-BASED WEB APPLICATION DESIGN FOR CONTENT MANAGEMENT"]

The titles must be in ALL CAPS and be directly relevant to: {topic}"""

        try:
            resp = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.4}
            )
            raw = resp["message"]["content"].strip()
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            if start != -1 and end > start:
                titles = json.loads(raw[start:end])
                if len(titles) == 5:
                    print(f"[Agent 1] ✓ Got {len(titles)} literature study titles")
                    return [t.upper() for t in titles]
        except Exception as e:
            print(f"[Agent 1] ⚠ Ollama failed ({e}), using default study titles")

        # Fallback defaults
        return [
            f"STUDY ON EXISTING {topic.upper()} PLATFORMS AND THEIR LIMITATIONS",
            f"RESEARCH ON COMMUNITY-BASED {topic.upper()} SYSTEMS",
            "STUDY ON SECURE AUTHENTICATION AND USER MANAGEMENT IN WEB APPLICATIONS",
            "RESEARCH ON RATING AND FEEDBACK SYSTEMS IN ONLINE PLATFORMS",
            "STUDY ON ROLE-BASED WEB SYSTEMS FOR CONTENT MANAGEMENT",
        ]

    def get_module_names(self, topic: str, description: str) -> list:
        """Ask Ollama for 6 module names specific to this project."""
        print("[Agent 1] Asking Ollama for module names...")
        prompt = f"""For a project called "{topic}", list exactly 6 module names for a Module Description chapter.

Project description: {description[:400]}

Return ONLY a JSON array of 6 strings, nothing else. Example:
["USER REGISTRATION AND AUTHENTICATION MODULE",
 "BOOK LISTING AND MANAGEMENT MODULE",
 "SEARCH AND FILTER MODULE",
 "TRANSACTION AND RENTAL MANAGEMENT MODULE",
 "RATING AND REVIEW MODULE",
 "ADMIN CONTROL PANEL MODULE"]

Each name must be in ALL CAPS and describe a distinct feature of the project."""

        try:
            resp = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.4}
            )
            raw = resp["message"]["content"].strip()
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            if start != -1 and end > start:
                names = json.loads(raw[start:end])
                if len(names) == 6:
                    print(f"[Agent 1] ✓ Got {len(names)} module names")
                    return [n.upper() for n in names]
        except Exception as e:
            print(f"[Agent 1] ⚠ Ollama failed ({e}), using default module names")

        return [
            "USER REGISTRATION AND AUTHENTICATION MODULE",
            "CORE FEATURE MODULE 1",
            "CORE FEATURE MODULE 2",
            "DATA MANAGEMENT MODULE",
            "FEEDBACK AND RATING MODULE",
            "ADMIN CONTROL PANEL MODULE",
        ]


# ═══════════════════════════════════════════════════════════════
#  PROMPT BUILDER
# ═══════════════════════════════════════════════════════════════
def build_mega_prompt(topic, degree, college, department, guide,
                      description, study_titles, module_names):
    """
    Builds the complete mega-prompt with:
    - Exact structure from FSD sample document
    - 5 literature studies with customized titles
    - 6 modules with customized names
    - Image placeholders for Ch4
    - Appendices for Ch6
    - References at end
    """

    # Fill in customized titles
    ch2 = dict(FIXED_CH2)
    for i, sub in enumerate(ch2["subheadings"]):
        sub["name"] = study_titles[i]

    ch5 = dict(FIXED_CH5)
    for i, sub in enumerate(ch5["subheadings"]):
        sub["name"] = module_names[i]

    chapters = [FIXED_CH1, ch2, FIXED_CH3, FIXED_CH4, ch5, FIXED_CH6, FIXED_CH7]

    # ── Build chapter-by-chapter instructions
    chapter_instructions = ""

    for ch in chapters:
        subs_text = ""
        for sub in ch["subheadings"]:
            tag = sub["tag"]
            name = sub["name"]
            words = sub["words"]
            has_image = sub.get("image", False)

            # Decide tag type
            if "." in tag[1:]:  # e.g. 3.1.1
                tag_type = f"[SUBHEADING_SUB: {tag} {name}]"
            else:
                tag_type = f"[SUBHEADING: {tag} {name}]"

            image_instruction = ""
            if has_image:
                image_instruction = f"""
   → After writing 2 paragraphs, insert:
     [IMAGE_PLACEHOLDER: Figure {tag} - {name}]
   → Then write 1 more paragraph explaining what the diagram shows."""

            subs_text += f"""
  {tag_type}
     Minimum {words} words.{image_instruction}"""

        # Special instructions per chapter
        special = ""

        if ch["num"] == 2:
            special = """
  LITERATURE SURVEY RULES — for EVERY study (2.1 to 2.5) you MUST write:
    Paragraph 1: What the paper/study is about + its approach (3-4 sentences)
    Paragraph 2: Key contributions and methodology (3-4 sentences)
    Paragraph 3: Limitations and gaps in the study (3-4 sentences)
    Paragraph 4: How the proposed system improves upon it (3-4 sentences)
    After para 4 add a bullet list:
    [LIST_START]
    [LIST_ITEM: Advantage our system adds over this study]
    [LIST_ITEM: Second advantage]
    [LIST_ITEM: Third advantage]
    [LIST_END]
  Minimum 500 words per study."""

        elif ch["num"] == 3:
            special = """
  FOR 3.1 EXISTING SYSTEM:
    - Describe 4 categories of existing systems with sub-labels
    - Write 2-3 paragraphs of body text
  FOR 3.1.1 DISADVANTAGES:
    - Write 1 intro sentence, then a bullet list of minimum 8 disadvantages:
    [LIST_START]
    [LIST_ITEM: Lack of Verification — explanation]
    [LIST_ITEM: Risk of Unsafe Practices — explanation]
    ... (8+ items)
    [LIST_END]
  FOR 3.2 PROPOSED SYSTEM:
    - Write 3-4 paragraphs about the proposed system with sub-labels
    - Include: User Module, Admin Module, Verification, Interactive Features sections
  FOR 3.2.1 ADVANTAGES:
    - Write 1 intro sentence, then a bullet list of minimum 10 advantages:
    [LIST_START]
    [LIST_ITEM: Advantage 1 — explanation]
    ... (10+ items)
    [LIST_END]"""

        elif ch["num"] == 4:
            special = """
  FOR EACH DIAGRAM (4.1, 4.2, 4.3):
    - Write 2 paragraphs explaining the diagram BEFORE the placeholder
    - Insert the [IMAGE_PLACEHOLDER] tag
    - Write 1 paragraph explaining key observations from the diagram AFTER placeholder
  Use these exact placeholders:
    [IMAGE_PLACEHOLDER: Figure 4.1 - Architecture Diagram]
    [IMAGE_PLACEHOLDER: Figure 4.2 - Use Case Diagram]
    [IMAGE_PLACEHOLDER: Figure 4.3 - Data Flow Diagram]"""

        elif ch["num"] == 5:
            special = """
  FOR EACH MODULE (5.1 to 5.6) write:
    Paragraph 1: Purpose and objectives of the module (5 sentences)
    Paragraph 2: How the module works — input, process, output (5 sentences)
    Paragraph 3: Technical implementation details (5 sentences)
    Paragraph 4: How it connects to other modules (5 sentences)
    Paragraph 5 (short summary): Key benefits of this module (4 sentences)
  Minimum 400 words per module."""

        elif ch["num"] == 6:
            special = f"""
  FOR 6.1 SAMPLE CODING:
    - Write 2 paragraphs explaining the main code structure of {topic}
    - Then add this tag: [CODE_SAMPLE]
    - Then write 2 paragraphs about the code functionality

  FOR 6.2 SCREENSHOTS:
    - Describe 4 screenshots of the system's key pages
    - For each screenshot:
      [IMAGE_PLACEHOLDER: Figure 6.2.N - <Page Name> Screenshot]
      Write 1 paragraph (5 sentences) explaining what is shown in the screenshot"""

        elif ch["num"] == 7:
            special = """
  FOR 7.1 CONCLUSION:
    - Write 4-5 paragraphs summarizing all achievements
    - Cover: problem solved, features built, technologies used, community impact
  FOR 7.2 FUTURE ENHANCEMENT:
    - Write 3-4 paragraphs
    - List at least 6 specific future enhancements in bullet form:
    [LIST_START]
    [LIST_ITEM: Enhancement 1 — explanation]
    ... (6+ items)
    [LIST_END]"""

        chapter_instructions += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHAPTER {ch['num']}: {ch['title']}   (MINIMUM {ch['total_words']} WORDS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tag: [CHAPTER: {ch['num']} | {ch['title']}]
Subheadings:{subs_text}
{special}
End with: [PAGE_BREAK]
"""

    # ── Assemble full prompt
    prompt = f"""You are an expert academic technical writer for {degree} project documentation
at Indian engineering colleges affiliated to Anna University.

PROJECT TOPIC: {topic}
DEGREE: {degree}
DEPARTMENT: {department}
COLLEGE: {college or "[COLLEGE NAME]"}
GUIDE: {guide or "[GUIDE NAME]"}

PROJECT DESCRIPTION (use this context for ALL content — be specific, not generic):
{description}

{TAG_REFERENCE}

═══════════════════════════════════════════════════════════
YOUR TASK: Write PART 2 — ALL {len(chapters)} CHAPTERS of the documentation.
TOTAL MINIMUM: {TOTAL_WORDS} words
═══════════════════════════════════════════════════════════

{chapter_instructions}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REFERENCES SECTION (write after Chapter 7)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[REFERENCES_START]
[REFERENCE: Author, A., & Author, B. (Year). Title of the paper. Journal Name.]
... write 12-15 references in this format
[REFERENCES_END]

═══════════════════════════════════════════════════════════
GLOBAL WRITING RULES — APPLY TO EVERY PARAGRAPH:
═══════════════════════════════════════════════════════════

1. Every [CONTENT] paragraph = minimum 5 sentences. No one-liners.
2. No markdown — no **, no ##, no hyphens as bullets (use [LIST_ITEM] instead)
3. Write in formal academic English throughout
4. Be SPECIFIC to "{topic}" — do not write generic content
5. Do NOT stop until Chapter 7 + References are complete
6. Every chapter MUST meet its word target
7. Add [PAGE_BREAK] after every chapter

═══════════════════════════════════════════════════════════
START WITH [CHAPTER: 1 | INTRODUCTION] AND DO NOT STOP
UNTIL ALL 7 CHAPTERS AND REFERENCES ARE WRITTEN.
═══════════════════════════════════════════════════════════

BEGIN NOW:"""

    return prompt


# ═══════════════════════════════════════════════════════════════
#  MAIN AGENT
# ═══════════════════════════════════════════════════════════════
class PromptGeneratorAgentV2:
    def __init__(self, ollama_model="llama3", ollama_host="http://localhost:11434"):
        self.customizer = OllamaCustomizer(ollama_model, ollama_host)
        print(f"[Agent 1 v2] Initialized with model: {ollama_model}")

    def run(self):
        print("\n" + "="*60)
        print("  AGENT 1 v2 — PROJECT DOCUMENTATION PROMPT GENERATOR")
        print("="*60)
        print(f"  Fixed structure: 7 chapters, ~{TOTAL_WORDS} words")
        print("  Ollama customizes: Ch2 study titles + Ch5 module names")
        print("="*60 + "\n")

        # ── Collect inputs
        topic       = input("📌 Project Topic: ").strip()
        description = input("📝 Brief project description (what it does, tech stack): ").strip()
        degree      = input("🎓 Degree [BE/MCA] (default BE): ").strip() or "BE"
        dept        = input("🏢 Department (default: Information Technology): ").strip() or "Information Technology"
        college     = input("🏫 College Name: ").strip()
        guide       = input("👨🏫 Guide Name: ").strip()

        # ── Ollama customizes only Ch2 + Ch5
        study_titles = self.customizer.get_literature_study_titles(topic, description)
        module_names = self.customizer.get_module_names(topic, description)

        print("\n[Agent 1 v2] Literature survey titles:")
        for i, t in enumerate(study_titles):
            print(f"  2.{i+1} {t}")

        print("\n[Agent 1 v2] Module names:")
        for i, m in enumerate(module_names):
            print(f"  5.{i+1} {m}")

        # ── Build mega-prompt
        print("\n[Agent 1 v2] Building mega-prompt...")
        prompt = build_mega_prompt(
            topic=topic, degree=degree, college=college,
            department=dept, guide=guide, description=description,
            study_titles=study_titles, module_names=module_names
        )

        # ── Save
        safe_topic = re.sub(r"[^\w\s]", "", topic)[:30].replace(" ", "_").upper()
        fname = f"PROMPT_PART2_{safe_topic}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(prompt)

        print(f"\n[Agent 1 v2] ✅ Saved: {fname}")
        print(f"[Agent 1 v2] 📋 Copy the content of that file")
        print(f"[Agent 1 v2] 📋 Paste into ChatGPT / Gemini / Claude")
        print(f"[Agent 1 v2] 📋 Save the AI output as content_part2.txt")
        print(f"[Agent 1 v2] 📋 Then run agent2_formatter_v2.py\n")

        # Preview
        print("─" * 60)
        print("PROMPT PREVIEW (first 800 chars):")
        print("─" * 60)
        print(prompt[:800])
        print("...\n[see full file]")
        print("─" * 60)

        print(f"\nTotal chapters: 7  |  Target words: {TOTAL_WORDS}  |  Est. pages: {TOTAL_WORDS//300}+\n")


if __name__ == "__main__":
    agent = PromptGeneratorAgentV2(
        ollama_model="llama3",               # change to: mistral / phi3 / etc.
        ollama_host="http://localhost:11434"
    )
    agent.run()