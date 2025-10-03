# GPT-5 Prompt Designer (PySide6)

A desktop GUI to assemble prompts for GPT‑5. Aligns with OpenAI's GPT‑5 Prompting Guide topics:
- Agentic workflow tuning: eagerness, tool preambles, persistence, progress narration, tool disambiguation.
- Coding prompts: planning snippet, apply_patch instructions, tool definitions.
- Intelligence controls: verbosity overrides, minimal reasoning toggle, Markdown guidance.
- Metaprompting template to improve weak prompts.
- Few‑shot examples and variable substitution.
- Output window with Copy and Export.

## Install
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install PySide6
```

## Run
```bash
python gpt5_prompt_designer.py
```

## Notes
- Variable placeholders use `{NAME}` syntax. Define them on the Variables tab. Rendering occurs on Build.
- JSON output mode can include an optional JSON Schema. The app injects schema text verbatim into the prompt.
- The brief‑rationale option requests 1–3 concise bullets at the start of the final answer, not hidden chain‑of‑thought.
- Presets provide starting configurations for common flows.

## License
MIT
