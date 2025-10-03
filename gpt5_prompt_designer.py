#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT-5 Prompt Designer (PySide6)
- Build high-quality prompts for GPT-5 using controls aligned with OpenAI's GPT-5 Prompting Guide.
- Outputs a single composite prompt ready to paste into GPT-5 (chat or API).
- Features: presets, agentic controls, coding templates, verbosity and minimal reasoning toggles,
  Markdown guidance, metaprompt generator, few-shot examples, variable substitution, copy and save,
  export/import of settings.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QCheckBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox, QFormLayout,
    QSplitter, QSizePolicy
)

APP_TITLE = "GPT-5 Prompt Designer"
APP_VERSION = "1.0.0"

# ---------- Utilities ----------

def clamp_text(s: str) -> str:
    return re.sub(r'\n{3,}', '\n\n', s).strip()

def replace_vars(text: str, mapping: Dict[str, str]) -> str:
    def repl(m):
        key = m.group(1)
        return mapping.get(key, m.group(0))
    return re.sub(r"\{([A-Za-z0-9_]+)\}", repl, text)

def safe_json(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)

# ---------- Prompt assembly ----------

@dataclass
class PromptOptions:
    # Basics
    role: str = "General assistant"
    custom_role: str = ""
    task: str = ""
    audience: str = ""
    constraints: str = ""
    delimiters: str = "triple backticks"
    output_format: str = "Plain text"
    json_schema: str = ""
    additional_context: str = ""

    # Agentic
    eagerness: str = "Medium"
    reasoning_effort: str = "Default"
    include_tool_preamble: bool = False
    include_persistence: bool = False
    include_progress_narration: bool = False
    include_tool_disambiguation: bool = False
    tool_context: str = ""

    # Coding
    coding_mode: bool = False
    include_planning: bool = False
    planning_snippet: str = ""
    include_apply_patch_instr: bool = False
    include_tool_defs: bool = False
    coding_notes: str = ""

    # Intelligence
    verbosity: str = "Default"
    verbosity_override: str = ""
    markdown_guidance: bool = False
    ask_brief_rationale: bool = False  # summary bullets at start of final answer

    # Metaprompting
    meta_mode: bool = False
    meta_prompt: str = ""
    meta_desired: str = ""
    meta_undesired: str = ""

    # Few-shot
    examples: List[Tuple[str, str]] = field(default_factory=list)  # list of (user, assistant)

    # Variables
    variables: Dict[str, str] = field(default_factory=dict)

    # Appendices
    include_swe_bench: bool = False
    include_retail_min_reason: bool = False

class PromptBuilder:
    def __init__(self, opts: PromptOptions):
        self.o = opts

    def _delim(self) -> Tuple[str, str]:
        d = self.o.delimiters
        if d == "triple backticks":
            return ("```", "```")
        if d == "triple quotes":
            return ('"""', '"""')
        if d == "XML tags":
            return ("<content>", "</content>")
        return ("```", "```")

    def _role_line(self) -> str:
        role = self.o.custom_role.strip() if self.o.role == "Custom" else self.o.role
        if not role:
            role = "General assistant"
        return f"You are {role}."

    def _audience_line(self) -> str:
        aud = self.o.audience.strip()
        return f"Target audience: {aud}." if aud else ""

    def _constraints_block(self) -> str:
        cons = clamp_text(self.o.constraints)
        return f"Constraints:\n- {cons.replace(os.linesep, os.linesep+'- ')}" if cons else ""

    def _formatting_block(self) -> str:
        parts = []
        if self.o.output_format == "Markdown" or self.o.markdown_guidance:
            parts.append("Format the final answer in Markdown where semantically correct. Use inline code, fenced code blocks, lists, and tables appropriately.")
            parts.append("When naming files or code elements, use backticks; use \\( \\) for inline math and \\[ \\] for block math.")
        if self.o.output_format == "JSON":
            schema = clamp_text(self.o.json_schema)
            if schema:
                parts.append("Return a single JSON object that exactly follows this JSON Schema:")
                parts.append(schema)
            else:
                parts.append("Return a single valid JSON object with keys appropriate to the task. No extra commentary.")
        return "\n".join(parts)

    def _verbosity_block(self) -> str:
        v = self.o.verbosity
        if v == "Default":
            return self.o.verbosity_override.strip()
        return f"Verbosity: {v.lower()}." + (f" {self.o.verbosity_override.strip()}" if self.o.verbosity_override.strip() else "")

    def _reasoning_block(self) -> str:
        r = self.o.reasoning_effort
        if r == "Default":
            return ""
        return f"Reasoning effort: {r.lower()}."

    def _agentic_controls(self) -> str:
        lines = []
        e = self.o.eagerness
        if e == "Low":
            lines.append("Agentic eagerness: low. Avoid tangential tool calls. Ask at most one clarifying question only if blocking.")
        elif e == "High":
            lines.append("Agentic eagerness: high. Be proactive. Decompose the task and use available tools when helpful.")
        else:
            lines.append("Agentic eagerness: medium. Balance proactivity with directness.")
        if self.o.include_tool_preamble:
            lines.append("Before tools: emit a short tool preamble that restates the goal, the plan, and the next action.")
        if self.o.include_progress_narration:
            lines.append("During long tasks: include brief progress updates and what remains.")
        if self.o.include_persistence:
            lines.append("Agentic persistence: continue until the user's goal is fully achieved. Do not stop early.")
        if self.o.include_tool_disambiguation:
            tc = clamp_text(self.o.tool_context)
            if tc:
                lines.append("Tool instructions: follow these disambiguated tool rules:")
                lines.append(tc)
        return "\n".join(lines)

    def _planning_block(self) -> str:
        if not self.o.include_planning:
            return ""
        snippet = clamp_text(self.o.planning_snippet or
                             "Plan the steps before producing the final answer. Verify each step. Do not yield until all sub-tasks are complete.")
        return f"Planning:\n{snippet}"

    def _coding_block(self) -> str:
        if not self.o.coding_mode:
            return ""
        lines = ["Coding mode: enabled. Prefer small, verifiable steps and runnable outputs."]
        if self.o.include_apply_patch_instr:
            lines.append("For code edits, prefer unified diffs in an apply_patch block: begin with '*** Begin Patch' and end with '*** End Patch'.")
        if self.o.include_tool_defs:
            lines.append("Assume standard code tools are available as defined by the host environment. Use them when appropriate.")
        notes = clamp_text(self.o.coding_notes)
        if notes:
            lines.append(notes)
        return "\n".join(lines)

    def _examples_block(self) -> str:
        if not self.o.examples:
            return ""
        open_d, close_d = self._delim()
        lines = ["Few-shot examples:"]
        for i, (u, a) in enumerate(self.o.examples, 1):
            u = clamp_text(u)
            a = clamp_text(a)
            lines.append(f"Example {i} - user {open_d}\n{u}\n{close_d}")
            lines.append(f"Example {i} - assistant {open_d}\n{a}\n{close_d}")
        return "\n".join(lines)

    def _appendix_block(self) -> str:
        lines = []
        if self.o.include_swe_bench:
            lines.append("Appendix: When editing code, use an apply_patch block with a unified diff. Verify changes thoroughly and consider hidden tests.")
        if self.o.include_retail_min_reason:
            lines.append("Appendix: Retail domain guardrails. Authenticate the user first. Only act for the authenticated user. Before database changes, summarize the action and get explicit confirmation.")
        return "\n".join(lines)

    def _meta_prompt(self) -> str:
        # Build metaprompt text
        open_d, close_d = self._delim()
        base = clamp_text(self.o.meta_prompt)
        desired = clamp_text(self.o.meta_desired)
        undesired = clamp_text(self.o.meta_undesired)
        lines = [
            "Optimize the following prompt. Explain what minimal edits or additions would encourage the desired behavior and reduce undesired behavior.",
            f"Desired behavior: {desired}" if desired else "Desired behavior: (not provided)",
            f"Undesired behavior: {undesired}" if undesired else "Undesired behavior: (not provided)",
            f"Prompt {open_d}\n{base}\n{close_d}"
        ]
        return "\n".join(lines)

    def build(self) -> str:
        if self.o.meta_mode:
            composed = self._meta_prompt()
            return clamp_text(replace_vars(composed, self.o.variables))

        parts = []
        parts.append(self._role_line())
        if self.o.task.strip():
            open_d, close_d = self._delim()
            parts.append(f"Task {open_d}\n{clamp_text(self.o.task)}\n{close_d}")
        if self.o.additional_context.strip():
            open_d, close_d = self._delim()
            parts.append(f"Context {open_d}\n{clamp_text(self.o.additional_context)}\n{close_d}")

        for piece in [
            self._audience_line(),
            self._constraints_block(),
            self._verbosity_block(),
            self._reasoning_block(),
            self._agentic_controls(),
            self._planning_block(),
            self._coding_block(),
            self._examples_block(),
            self._formatting_block(),
            self._appendix_block(),
        ]:
            if piece.strip():
                parts.append(piece.strip())

        if self.o.ask_brief_rationale:
            parts.append("Begin the final answer with 1-3 concise bullets summarizing key factors. Do not include private chain-of-thought.")

        composed = clamp_text("\n\n".join(p for p in parts if p.strip()))
        composed = replace_vars(composed, self.o.variables)
        return composed

# ---------- GUI ----------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE} v{APP_VERSION}")
        self.resize(1200, 800)

        self.opts = PromptOptions()
        self._init_ui()
        self._wire_actions()

    # ---- UI construction ----

    def _init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Top preset bar
        top_bar = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Custom",
            "General task",
            "Agentic low-eagerness",
            "Agentic high-eagerness",
            "Coding workflow",
            "Metaprompt optimizer",
        ])
        self.load_preset_btn = QPushButton("Apply preset")
        self.load_btn = QPushButton("Load settings")
        self.save_btn = QPushButton("Save settings")
        top_bar.addWidget(QLabel("Preset:"))
        top_bar.addWidget(self.preset_combo)
        top_bar.addWidget(self.load_preset_btn)
        top_bar.addStretch(1)
        top_bar.addWidget(self.load_btn)
        top_bar.addWidget(self.save_btn)
        main_layout.addLayout(top_bar)

        # Tabs + Output
        self.tabs = QTabWidget()
        self._init_tab_basics()
        self._init_tab_agentic()
        self._init_tab_coding()
        self._init_tab_intelligence()
        self._init_tab_examples()
        self._init_tab_variables()
        main_layout.addWidget(self.tabs, stretch=1)

        # Output area and controls
        out_bar = QHBoxLayout()
        self.build_btn = QPushButton("Build prompt")
        self.copy_btn = QPushButton("Copy to clipboard")
        self.export_btn = QPushButton("Export .txt")
        self.clear_btn = QPushButton("Reset")
        out_bar.addWidget(self.build_btn)
        out_bar.addWidget(self.copy_btn)
        out_bar.addWidget(self.export_btn)
        out_bar.addStretch(1)
        out_bar.addWidget(self.clear_btn)
        main_layout.addLayout(out_bar)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Built prompt will appear here...")
        main_layout.addWidget(self.output, stretch=2)

        self.statusBar().showMessage("Ready")

        # Menu minimal
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        act_export = QAction("Export .txt", self)
        act_export.triggered.connect(self._export_txt)
        file_menu.addAction(act_export)

    def _init_tab_basics(self):
        w = QWidget()
        layout = QFormLayout(w)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["General assistant", "Coding assistant", "Data analyst", "Writing coach", "Custom"])
        self.custom_role = QLineEdit()
        self.task_edit = QTextEdit()
        self.task_edit.setPlaceholderText("Describe the task to perform...")
        self.context_edit = QTextEdit()
        self.context_edit.setPlaceholderText("Optional additional context...")
        self.audience_edit = QLineEdit()
        self.constraints_edit = QTextEdit()
        self.constraints_edit.setPlaceholderText("Bullet list of constraints, one per line...")

        self.delim_combo = QComboBox()
        self.delim_combo.addItems(["triple backticks", "triple quotes", "XML tags"])

        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["Plain text", "Markdown", "JSON"])
        self.json_schema_edit = QTextEdit()
        self.json_schema_edit.setPlaceholderText('Optional JSON Schema to enforce.')
        self.json_schema_edit.setFixedHeight(120)

        layout.addRow("Role", self.role_combo)
        layout.addRow("Custom role", self.custom_role)
        layout.addRow("Task", self.task_edit)
        layout.addRow("Context", self.context_edit)
        layout.addRow("Audience", self.audience_edit)
        layout.addRow("Constraints", self.constraints_edit)
        layout.addRow("Delimiters", self.delim_combo)
        layout.addRow("Output format", self.output_format_combo)
        layout.addRow("JSON Schema", self.json_schema_edit)

        self.tabs.addTab(w, "Basics")

    def _init_tab_agentic(self):
        w = QWidget()
        layout = QFormLayout(w)

        self.eager_combo = QComboBox()
        self.eager_combo.addItems(["Low", "Medium", "High"])

        self.reasoning_combo = QComboBox()
        self.reasoning_combo.addItems(["Default", "Minimal", "Medium", "High"])

        self.chk_tool_preamble = QCheckBox("Include tool preamble (goal, plan, next action)")
        self.chk_persistence = QCheckBox("Agentic persistence until goal is achieved")
        self.chk_progress = QCheckBox("Progress narration for long tasks")
        self.chk_tool_rules = QCheckBox("Include tool disambiguation")
        self.tool_rules_edit = QTextEdit()
        self.tool_rules_edit.setPlaceholderText("Describe tool rules, capabilities, and constraints...")
        self.tool_rules_edit.setFixedHeight(120)

        layout.addRow("Agentic eagerness", self.eager_combo)
        layout.addRow("Reasoning effort", self.reasoning_combo)
        layout.addRow(self.chk_tool_preamble)
        layout.addRow(self.chk_persistence)
        layout.addRow(self.chk_progress)
        layout.addRow(self.chk_tool_rules)
        layout.addRow("Tool rules", self.tool_rules_edit)

        self.tabs.addTab(w, "Agentic")

    def _init_tab_coding(self):
        w = QWidget()
        layout = QFormLayout(w)

        self.chk_coding = QCheckBox("Enable coding mode")
        self.chk_planning = QCheckBox("Include planning snippet")
        self.planning_edit = QTextEdit()
        self.planning_edit.setPlaceholderText("Plan steps before acting. Verify outputs. Finish all sub-tasks before yielding...")
        self.planning_edit.setFixedHeight(100)

        self.chk_apply_patch = QCheckBox("Include apply_patch instructions")
        self.chk_tool_defs = QCheckBox("Reference coding tool definitions available in host")
        self.coding_notes = QTextEdit()
        self.coding_notes.setPlaceholderText("Optional coding notes, frameworks, or domain specifics...")
        self.coding_notes.setFixedHeight(100)

        layout.addRow(self.chk_coding)
        layout.addRow(self.chk_planning)
        layout.addRow("Planning snippet", self.planning_edit)
        layout.addRow(self.chk_apply_patch)
        layout.addRow(self.chk_tool_defs)
        layout.addRow("Extra coding notes", self.coding_notes)

        self.tabs.addTab(w, "Coding")

    def _init_tab_intelligence(self):
        w = QWidget()
        layout = QFormLayout(w)

        self.verbosity_combo = QComboBox()
        self.verbosity_combo.addItems(["Default", "Low", "Medium", "High"])
        self.verbosity_override = QLineEdit()
        self.verbosity_override.setPlaceholderText("Optional override in natural language, e.g., 'Use high verbosity for code tool outputs only.'")

        self.chk_markdown = QCheckBox("Add Markdown guidance")
        self.chk_brief_rationale = QCheckBox("Start answer with 1-3 concise bullets summarizing key factors")
        self.chk_brief_rationale.setToolTip("Requests a short summary, not chain-of-thought.")

        # Metaprompt section
        self.chk_meta_mode = QCheckBox("Metaprompt optimizer mode")
        self.meta_prompt = QTextEdit()
        self.meta_prompt.setPlaceholderText("Paste the prompt to optimize...")
        self.meta_desired = QLineEdit()
        self.meta_undesired = QLineEdit()

        layout.addRow("Verbosity", self.verbosity_combo)
        layout.addRow("Verbosity override", self.verbosity_override)
        layout.addRow(self.chk_markdown)
        layout.addRow(self.chk_brief_rationale)
        layout.addRow(self.chk_meta_mode)
        layout.addRow("Prompt to optimize", self.meta_prompt)
        layout.addRow("Desired behavior", self.meta_desired)
        layout.addRow("Undesired behavior", self.meta_undesired)

        self.tabs.addTab(w, "Intelligence")

    def _init_tab_examples(self):
        w = QWidget()
        v = QVBoxLayout(w)

        self.examples_table = QTableWidget(0, 2)
        self.examples_table.setHorizontalHeaderLabels(["User", "Assistant"])
        self.examples_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.examples_table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.examples_table.horizontalHeader().setStretchLastSection(True)
        v.addWidget(self.examples_table)

        btns = QHBoxLayout()
        self.add_example_btn = QPushButton("Add example")
        self.del_example_btn = QPushButton("Remove selected")
        self.insert_example_btn = QPushButton("Insert starter example")
        btns.addWidget(self.add_example_btn)
        btns.addWidget(self.del_example_btn)
        btns.addStretch(1)
        btns.addWidget(self.insert_example_btn)
        v.addLayout(btns)

        self.tabs.addTab(w, "Few-shot")

    def _init_tab_variables(self):
        w = QWidget()
        v = QVBoxLayout(w)

        self.vars_table = QTableWidget(0, 2)
        self.vars_table.setHorizontalHeaderLabels(["name", "value"])
        self.vars_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.vars_table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.vars_table.horizontalHeader().setStretchLastSection(True)
        v.addWidget(self.vars_table)

        btns = QHBoxLayout()
        self.add_var_btn = QPushButton("Add variable")
        self.del_var_btn = QPushButton("Remove selected")
        self.insert_var_btn = QPushButton("Insert starter vars")
        v.addLayout(btns)
        btns.addWidget(self.add_var_btn)
        btns.addWidget(self.del_var_btn)
        btns.addStretch(1)
        btns.addWidget(self.insert_var_btn)

        # Appendices toggles
        self.chk_swe = QCheckBox("Include SWE-Bench-style developer instructions")
        self.chk_retail = QCheckBox("Include Retail minimal-reasoning guardrails")
        v.addWidget(self.chk_swe)
        v.addWidget(self.chk_retail)

        self.tabs.addTab(w, "Variables & Appendices")

    # ---- Event wiring ----

    def _wire_actions(self):
        self.build_btn.clicked.connect(self._build_prompt)
        self.copy_btn.clicked.connect(self._copy_prompt)
        self.clear_btn.clicked.connect(self._reset_all)
        self.export_btn.clicked.connect(self._export_txt)

        self.load_preset_btn.clicked.connect(self._apply_preset)
        self.add_example_btn.clicked.connect(self._add_example_row)
        self.del_example_btn.clicked.connect(self._del_example_row)
        self.insert_example_btn.clicked.connect(self._insert_starter_example)

        self.add_var_btn.clicked.connect(self._add_var_row)
        self.del_var_btn.clicked.connect(self._del_var_row)
        self.insert_var_btn.clicked.connect(self._insert_starter_vars)

        self.load_btn.clicked.connect(self._load_settings)
        self.save_btn.clicked.connect(self._save_settings)

    # ---- Data marshaling ----

    def _collect_options(self) -> PromptOptions:
        o = PromptOptions()
        # Basics
        o.role = self.role_combo.currentText()
        o.custom_role = self.custom_role.text()
        o.task = self.task_edit.toPlainText()
        o.additional_context = self.context_edit.toPlainText()
        o.audience = self.audience_edit.text()
        o.constraints = self.constraints_edit.toPlainText()
        o.delimiters = self.delim_combo.currentText()
        o.output_format = self.output_format_combo.currentText()
        o.json_schema = self.json_schema_edit.toPlainText()

        # Agentic
        o.eagerness = self.eager_combo.currentText()
        o.reasoning_effort = self.reasoning_combo.currentText()
        o.include_tool_preamble = self.chk_tool_preamble.isChecked()
        o.include_persistence = self.chk_persistence.isChecked()
        o.include_progress_narration = self.chk_progress.isChecked()
        o.include_tool_disambiguation = self.chk_tool_rules.isChecked()
        o.tool_context = self.tool_rules_edit.toPlainText()

        # Coding
        o.coding_mode = self.chk_coding.isChecked()
        o.include_planning = self.chk_planning.isChecked()
        o.planning_snippet = self.planning_edit.toPlainText()
        o.include_apply_patch_instr = self.chk_apply_patch.isChecked()
        o.include_tool_defs = self.chk_tool_defs.isChecked()
        o.coding_notes = self.coding_notes.toPlainText()

        # Intelligence
        o.verbosity = self.verbosity_combo.currentText()
        o.verbosity_override = self.verbosity_override.text()
        o.markdown_guidance = self.chk_markdown.isChecked()
        o.ask_brief_rationale = self.chk_brief_rationale.isChecked()

        # Metaprompt
        o.meta_mode = self.chk_meta_mode.isChecked()
        o.meta_prompt = self.meta_prompt.toPlainText()
        o.meta_desired = self.meta_desired.text()
        o.meta_undesired = self.meta_undesired.text()

        # Few-shot
        o.examples = []
        for r in range(self.examples_table.rowCount()):
            u_item = self.examples_table.item(r, 0)
            a_item = self.examples_table.item(r, 1)
            u = u_item.text() if u_item else ""
            a = a_item.text() if a_item else ""
            if u.strip() or a.strip():
                o.examples.append((u, a))

        # Variables
        o.variables = {}
        for r in range(self.vars_table.rowCount()):
            k_item = self.vars_table.item(r, 0)
            v_item = self.vars_table.item(r, 1)
            if k_item and v_item:
                k = k_item.text().strip()
                v = v_item.text()
                if k:
                    o.variables[k] = v

        # Appendices
        o.include_swe_bench = self.chk_swe.isChecked()
        o.include_retail_min_reason = self.chk_retail.isChecked()

        return o

    def _apply_options(self, o: PromptOptions):
        # Basics
        idx = self.role_combo.findText(o.role)
        self.role_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.custom_role.setText(o.custom_role)
        self.task_edit.setPlainText(o.task)
        self.context_edit.setPlainText(o.additional_context)
        self.audience_edit.setText(o.audience)
        self.constraints_edit.setPlainText(o.constraints)
        self.delim_combo.setCurrentText(o.delimiters)
        self.output_format_combo.setCurrentText(o.output_format)
        self.json_schema_edit.setPlainText(o.json_schema)

        # Agentic
        self.eager_combo.setCurrentText(o.eagerness)
        self.reasoning_combo.setCurrentText(o.reasoning_effort)
        self.chk_tool_preamble.setChecked(o.include_tool_preamble)
        self.chk_persistence.setChecked(o.include_persistence)
        self.chk_progress.setChecked(o.include_progress_narration)
        self.chk_tool_rules.setChecked(o.include_tool_disambiguation)
        self.tool_rules_edit.setPlainText(o.tool_context)

        # Coding
        self.chk_coding.setChecked(o.coding_mode)
        self.chk_planning.setChecked(o.include_planning)
        self.planning_edit.setPlainText(o.planning_snippet)
        self.chk_apply_patch.setChecked(o.include_apply_patch_instr)
        self.chk_tool_defs.setChecked(o.include_tool_defs)
        self.coding_notes.setPlainText(o.coding_notes)

        # Intelligence
        self.verbosity_combo.setCurrentText(o.verbosity)
        self.verbosity_override.setText(o.verbosity_override)
        self.chk_markdown.setChecked(o.markdown_guidance)
        self.chk_brief_rationale.setChecked(o.ask_brief_rationale)

        # Metaprompt
        self.chk_meta_mode.setChecked(o.meta_mode)
        self.meta_prompt.setPlainText(o.meta_prompt)
        self.meta_desired.setText(o.meta_desired)
        self.meta_undesired.setText(o.meta_undesired)

        # Few-shot
        self.examples_table.setRowCount(0)
        for u, a in o.examples:
            r = self.examples_table.rowCount()
            self.examples_table.insertRow(r)
            self.examples_table.setItem(r, 0, QTableWidgetItem(u))
            self.examples_table.setItem(r, 1, QTableWidgetItem(a))

        # Variables
        self.vars_table.setRowCount(0)
        for k, v in o.variables.items():
            r = self.vars_table.rowCount()
            self.vars_table.insertRow(r)
            self.vars_table.setItem(r, 0, QTableWidgetItem(k))
            self.vars_table.setItem(r, 1, QTableWidgetItem(v))

        # Appendices
        self.chk_swe.setChecked(o.include_swe_bench)
        self.chk_retail.setChecked(o.include_retail_min_reason)

    # ---- Actions ----

    def _build_prompt(self):
        opts = self._collect_options()
        builder = PromptBuilder(opts)
        prompt = builder.build()
        self.output.setPlainText(prompt)
        self.statusBar().showMessage("Prompt built.")

    def _copy_prompt(self):
        text = self.output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Copy", "Nothing to copy.")
            return
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage("Copied to clipboard.")

    def _export_txt(self):
        text = self.output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Export", "Build a prompt first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Prompt", "prompt.txt", "Text Files (*.txt);;All Files (*)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.statusBar().showMessage(f"Exported to {path}")

    def _reset_all(self):
        self._apply_options(PromptOptions())
        self.output.clear()
        self.statusBar().showMessage("Reset.")

    def _apply_preset(self):
        which = self.preset_combo.currentText()
        o = PromptOptions()
        if which == "General task":
            o.role = "General assistant"
            o.markdown_guidance = True
            o.verbosity = "Medium"
            o.eagerness = "Medium"
            o.delimiters = "triple backticks"
        elif which == "Agentic low-eagerness":
            o.include_persistence = True
            o.include_tool_preamble = True
            o.eagerness = "Low"
            o.reasoning_effort = "Minimal"
            o.ask_brief_rationale = False
            o.markdown_guidance = True
            o.verbosity = "Low"
        elif which == "Agentic high-eagerness":
            o.include_persistence = True
            o.include_tool_preamble = True
            o.include_progress_narration = True
            o.include_tool_disambiguation = True
            o.eagerness = "High"
            o.reasoning_effort = "Medium"
            o.markdown_guidance = True
            o.verbosity = "Medium"
        elif which == "Coding workflow":
            o.role = "Coding assistant"
            o.coding_mode = True
            o.include_planning = True
            o.include_apply_patch_instr = True
            o.include_tool_defs = True
            o.markdown_guidance = True
            o.verbosity = "Medium"
            o.reasoning_effort = "Medium"
            o.include_persistence = True
            o.eagerness = "Medium"
        elif which == "Metaprompt optimizer":
            o.meta_mode = True
            o.verbosity = "Low"
            o.markdown_guidance = False
            o.eagerness = "Low"
        self._apply_options(o)
        self.statusBar().showMessage(f"Applied preset: {which}")

    def _add_example_row(self):
        r = self.examples_table.rowCount()
        self.examples_table.insertRow(r)
        self.examples_table.setItem(r, 0, QTableWidgetItem("User input here"))
        self.examples_table.setItem(r, 1, QTableWidgetItem("Assistant reply here"))

    def _del_example_row(self):
        rows = sorted(set(idx.row() for idx in self.examples_table.selectedIndexes()), reverse=True)
        for r in rows:
            self.examples_table.removeRow(r)

    def _insert_starter_example(self):
        r = self.examples_table.rowCount()
        self.examples_table.insertRow(r)
        self.examples_table.setItem(r, 0, QTableWidgetItem("Summarize this article for a technical audience."))
        self.examples_table.setItem(r, 1, QTableWidgetItem("Summary focused on architecture decisions and trade-offs."))

    def _add_var_row(self):
        r = self.vars_table.rowCount()
        self.vars_table.insertRow(r)
        self.vars_table.setItem(r, 0, QTableWidgetItem("PROJECT_NAME"))
        self.vars_table.setItem(r, 1, QTableWidgetItem("MyApp"))

    def _del_var_row(self):
        rows = sorted(set(idx.row() for idx in self.vars_table.selectedIndexes()), reverse=True)
        for r in rows:
            self.vars_table.removeRow(r)

    def _insert_starter_vars(self):
        for k, v in {"LANG":"Python", "FRAMEWORK":"FastAPI", "DEADLINE":"2025-10-31"}.items():
            r = self.vars_table.rowCount()
            self.vars_table.insertRow(r)
            self.vars_table.setItem(r, 0, QTableWidgetItem(k))
            self.vars_table.setItem(r, 1, QTableWidgetItem(v))

    def _save_settings(self):
        o = self._collect_options()
        data = json.dumps(o, default=lambda x: x.__dict__, indent=2, ensure_ascii=False)
        path, _ = QFileDialog.getSaveFileName(self, "Save Settings", "prompt_settings.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
            self.statusBar().showMessage(f"Saved settings to {path}")

    def _load_settings(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Settings", "", "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            o = PromptOptions(**data)
            self._apply_options(o)
            self.statusBar().showMessage(f"Loaded settings from {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load: {e}")

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
