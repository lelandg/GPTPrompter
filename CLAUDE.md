# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GPT-5 Prompt Designer** is a PySide6 desktop GUI application for assembling sophisticated prompts aligned with OpenAI's GPT-5 Prompting Guide. The application allows users to configure agentic workflows, coding prompts, intelligence controls, metaprompting, few-shot examples, and variable substitution.

## Environment Setup

### Virtual Environment
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install PySide6
```

### Running the Application
```bash
python gpt5_prompt_designer.py
```

## Architecture

### Single-File Application
The entire application is contained in `gpt5_prompt_designer.py` (~810 lines). This is an intentional design choice for simplicity and portability.

### Core Components

1. **Data Layer** (lines 48-95)
   - `PromptOptions`: Dataclass holding all configuration state (role, task, agentic controls, coding mode, intelligence settings, examples, variables)
   - All GUI state is marshaled through this dataclass

2. **Prompt Builder** (lines 100-264)
   - `PromptBuilder`: Transforms `PromptOptions` into final prompt text
   - Methods return text blocks for each prompt section (role, agentic controls, coding, formatting, etc.)
   - `build()`: Main assembly method that composes all sections
   - Variable substitution uses `{NAME}` syntax, replaced at build time

3. **GUI Layer** (lines 268-803)
   - `MainWindow`: PySide6 QMainWindow with tabbed interface
   - Tabs: Basics, Agentic, Coding, Intelligence, Few-shot, Variables & Appendices
   - Bi-directional data flow: `_collect_options()` reads GUI → dataclass, `_apply_options()` writes dataclass → GUI

### Key Design Patterns

- **Delimiters**: User-selectable delimiters (triple backticks, triple quotes, XML tags) wrap content blocks
- **Preset System**: Pre-configured `PromptOptions` for common workflows (general task, agentic low/high eagerness, coding, metaprompt)
- **Export/Import**: Settings can be saved/loaded as JSON via `_save_settings()` and `_load_settings()`

### Prompt Assembly Flow

1. User configures options across tabs
2. Click "Build prompt" → `_build_prompt()` → `_collect_options()` → `PromptBuilder(opts).build()`
3. Builder conditionally includes sections based on enabled features
4. Variable substitution happens last via `replace_vars()`
5. Output appears in read-only QTextEdit

## Important Implementation Details

### Variable Substitution
- Uses regex pattern `\{([A-Za-z0-9_]+)\}` to find placeholders
- Defined in Variables tab as key-value pairs
- Replacement occurs during `PromptBuilder.build()` after all sections are assembled

### Metaprompt Mode
- Completely overrides normal prompt assembly when `meta_mode` is enabled
- Outputs a metaprompt that asks GPT-5 to optimize a given prompt
- Requires: base prompt to optimize, desired behavior, undesired behavior

### Presets Directory
- Located in `Docs/presets/` (e.g., `agentic_low.json`, `coding_workflow.json`)
- JSON files containing serialized `PromptOptions`
- Can be loaded via "Load settings" button

### Output Modes
- **Plain text**: No special formatting
- **Markdown**: Adds guidance about proper Markdown usage (inline code, fenced blocks, math)
- **JSON**: Instructs model to return JSON; optional JSON Schema can be provided

## Development Notes

### Extending the Application
- To add new prompt sections: Add field to `PromptOptions`, create `_new_section_block()` method in `PromptBuilder`, add to `build()` assembly
- To add new tabs: Create `_init_tab_newname()` method, add to `_init_ui()`, update `_collect_options()` and `_apply_options()`
- GUI controls follow PySide6 patterns: QComboBox for dropdowns, QCheckBox for toggles, QTextEdit for multi-line, QLineEdit for single-line

### Testing
No automated tests are present. Manual testing involves:
1. Configure options across tabs
2. Build prompt and verify output
3. Test export/import of settings
4. Verify variable substitution
5. Check preset loading

### Code Style
- Uses dataclasses for options container
- Type hints on function signatures
- Utility functions prefixed with underscore for private methods
- Widget references stored as instance variables (e.g., `self.task_edit`)
