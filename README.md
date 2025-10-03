# 🧩 GPT‑5 Prompt Designer (PySide6) — User Guide

> A desktop GUI to assemble clean, powerful prompts for GPT‑5.  
> Output is plain text you can paste directly into ChatGPT (GPT‑5) or your API client.  
> Original version was generated in one prompt using my **Code General** GPT project. (I'll share that.)  
> Second prompt generated this file when I asked for a comprehensive user manual. It also gave me the files
> in [presets](Docs/presets)
---

## 🧭 Overview
The app helps you compose prompts that reflect proven patterns from modern prompting practice:
- **Agentic controls**: set eagerness, persistence, progress narration, and tool disambiguation.
- **Coding flows**: enable planning, patch‑style edits, and code‑aware notes.
- **Intelligence steering**: choose verbosity, minimal reasoning, and Markdown guidance.
- **Metaprompting**: optimize a weak prompt with a self‑improvement template.
- **Few‑shot examples**: add inline exemplars for more reliable behavior.
- **Variables**: reuse values with `{NAME}` placeholders.
- **Appendices**: optional SWE‑style instructions and retail guardrails.
- **Output**: copy to clipboard or export to `.txt`. Save and load all settings as `.json`.

---

## ⚙️ Installation
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
# .venv\Scripts\activate
pip install PySide6
```

If you downloaded the repository artifacts from this guide, you already have:
- `gpt5_prompt_designer.py` (the app)
- `README.md` and `README.html` (this guide)
- `presets/*.json` (sample presets)

---

## 🚀 Launch
```bash
python gpt5_prompt_designer.py
```

---

## ⏱️ Quick start (60 seconds)
1. Pick a **Preset** at the top bar or stay on **Custom**.  
2. Fill **Basics → Task** and optional **Context**.  
3. Toggle **Agentic** and **Coding** options as needed.  
4. Add any **Variables** and **Few‑shot** examples.  
5. Click **Build prompt**.  
6. Click **Copy to clipboard** and paste into GPT‑5.

---

## 🗺️ UI map
### Basics
- **Role / Custom role**: persona for the assistant. Example: “Security code reviewer”.
- **Task**: the core instruction. This is wrapped with your chosen **Delimiters**.
- **Context**: extra background. Also wrapped and kept separate from Task.
- **Audience**: who will read the answer. Affects tone and depth.
- **Constraints**: one per line. Rendered as bullets.
- **Delimiters**: triple backticks, triple quotes, or XMLish tags.
- **Output format**: Plain text, Markdown, or JSON.  
  - JSON mode: optional **JSON Schema** inserted verbatim.
  
### Agentic
- **Agentic eagerness**: Low, Medium, or High. Controls proactivity.
- **Reasoning effort**: Default, Minimal, Medium, High.
- **Tool preamble**: ask the model to state goal, plan, next action before tools.
- **Persistence**: continue until the goal is achieved, no early stop.
- **Progress narration**: brief updates during long tasks.
- **Tool disambiguation**: paste tool rules and capabilities.

### Coding
- **Coding mode**: prefer verifiable steps and runnable output.
- **Planning snippet**: require a plan before final answer.
- **apply_patch instructions**: encourage unified diff blocks for edits.
- **Tool definitions**: tell the model that standard code tools are available.
- **Extra coding notes**: framework/domain specifics.

### Intelligence
- **Verbosity**: Default/Low/Medium/High. Add a textual **override** when needed.
- **Markdown guidance**: remind the model to use headings, lists, tables, and code fences.
- **Brief rationale**: start answer with 1–3 concise bullets. No chain‑of‑thought.

### Metaprompting
- **Metaprompt optimizer mode**: switches the builder into *“improve this prompt”* template with fields:
  - **Prompt to optimize**, **Desired behavior**, **Undesired behavior**.

### Few‑shot
- Table of example pairs (**User**, **Assistant**). Add/Remove. Insert a starter example.

### Variables & Appendices
- **Variables table**: `{NAME}` placeholders that get substituted on **Build**.
- **Appendices**: optional toggles
  - SWE‑Bench‑style developer instructions
  - Retail minimal‑reasoning guardrails

---

## 🍱 Build, copy, save
- **Build prompt** assembles the prompt into the bottom output box.
- **Copy to clipboard** places it on your clipboard.
- **Export .txt** saves the built prompt.
- **Save settings** writes every control to JSON.
- **Load settings** restores your workflow.

> Tip: Keep per‑project JSON settings in VCS for reproducible prompting.

---

## 🔧 Variables
- Use `{NAME}` inside Task, Context, Constraints, etc.
- Define `NAME → value` in **Variables & Appendices**.
- Substitution happens on **Build**.
- If a placeholder is undefined, the literal `{NAME}` remains.

Example:
```
Task:
Build an API in {LANG} with {FRAMEWORK} before {DEADLINE}.
Variables:
LANG=Python, FRAMEWORK=FastAPI, DEADLINE=2025-10-31
```

---

## 🧾 JSON output mode
Enable **Output format → JSON**. Optionally paste a **JSON Schema**. The builder will add:
- “Return a single JSON object…”
- If a schema is present, it is inserted verbatim and referenced.

**Recommendations**
- Avoid comments in JSON.
- If you need arrays, include them in the schema.
- Validate the output with your own code when consuming it.

---

## 🎚️ Presets
- **General task**: markdown guidance, medium verbosity, medium eagerness.
- **Agentic low‑eagerness**: persistence + tool preamble, minimal reasoning.
- **Agentic high‑eagerness**: persistence + preamble + progress + tool rules.
- **Coding workflow**: coding mode + planning + apply_patch + tool defs.
- **Metaprompt optimizer**: switches to metaprompting template.

You can still edit any field after applying a preset.

---

## 📚 Example use cases

### 1) Code refactor with patch output 💻
**Goal**: Migrate a function to async and update callers.  
**Steps**
1. Preset → **Coding workflow**.
2. Basics → Task: *“Refactor to async; update call sites; keep tests green.”*
3. Coding → Add notes: *“Project uses Trio; prefer nursery patterns.”*
4. Intelligence → Brief rationale ✔.
5. Build → Copy → Paste into GPT‑5.

**Resulting prompt (excerpt)**
```
You are Coding assistant.

Task ```
Refactor to async; update call sites; keep tests green.
```

Coding mode: enabled. Prefer small, verifiable steps and runnable outputs.
For code edits, prefer unified diffs in an apply_patch block...
```

### 2) Data analysis to JSON 📊
**Goal**: Return KPIs in strict JSON.  
**Steps**
1. Basics → Output format: **JSON**.
2. Paste a JSON Schema for numbers and ISO dates.
3. Intelligence → Verbosity: **Low**.
4. Build → Copy.

**Tip**: Paste the same schema into your validator for safety.

### 3) Metaprompt an existing prompt 🎯
**Goal**: Improve a rough prompt that yields meandering answers.  
**Steps**
1. Intelligence → **Metaprompt optimizer mode** ✔.
2. Paste your rough prompt.
3. Desired: *“Concise, bullet‑first.”* Undesired: *“Speculation, long digressions.”*
4. Build → Copy. Use the optimizer’s advice to update your original prompt.

### 4) Customer support summarizer with low eagerness 🛟
**Goal**: Summarize tickets without tool calls or extra probing.  
**Steps**
1. Preset → **Agentic low‑eagerness**.
2. Basics → Task: *“Summarize user ticket into 3 bullets plus sentiment.”*
3. Constraints: add any PII or compliance limits.
4. Build → Copy.

### 5) Educational content with Markdown 📝
**Goal**: Produce a tutorial with tables and headings.  
**Steps**
1. Basics → Output format: **Markdown**.
2. Intelligence → Markdown guidance ✔ and Verbosity **High**.
3. Few‑shot → add one example Q/A to set tone.
4. Build → Copy.

---

## 🧠 Tips and patterns
- Keep the **Task** short and concrete. Put text payloads into **Context**.
- Choose **Delimiters** that match your payload: backticks for code, quotes for prose.
- Use **Few‑shot** for format regularity. Even one example helps.
- Prefer **Brief rationale** over hidden chain‑of‑thought.
- Toggle **Minimal** reasoning for speed. Raise when tasks are fuzzy.
- Store **presets JSON** with your project to keep behavior stable.

---

## 🧪 Troubleshooting
- **Nothing copies**: build first, then copy. The box must not be empty.
- **JSON looks wrong**: ensure schema is valid JSON, not comments.
- **Variables unchanged**: define them in the Variables table; placeholders are `{NAME}` not `$NAME`.
- **Missing PySide6**: `pip install PySide6` in your active venv.
- **Cannot export**: check write permissions in the chosen folder.

---

## ❓ FAQ
**Does this call the OpenAI API?** No. It only builds text for pasting.  
**Where are settings stored?** Wherever you save the `.json` file. Nothing is written automatically.  
**Chain‑of‑thought?** Not requested. Use **Brief rationale** if you need a short, non‑sensitive summary.  
**Can I add my own presets?** Yes. Save a configuration as JSON and keep it in `presets/`.

---

## 📦 Version
App: `v{app_version}`

---

## ⚖️ License
MIT
