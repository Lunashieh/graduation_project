from config import PROMPTS_FINAL_DIR, PROMPTS_TUNING_DIR


def load_tuning_prompt(prompt_mode: str, prompt_version: str) -> str:
    prompt_path = PROMPTS_TUNING_DIR / prompt_mode / f"{prompt_version}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def load_final_prompt(prompt_name: str) -> str:
    prompt_path = PROMPTS_FINAL_DIR / f"{prompt_name}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def build_trace_evidence(case: dict, trace_mode: str) -> str:
    trace_text = case.get("trace_text", "").strip()

    if trace_mode == "trace_only":
        return trace_text if trace_text else "[Trace/log text is not available for this case.]"

    if trace_mode == "dot_only":
        return "[DOT text is not available in the current dataset format.]"

    if trace_mode == "trace_and_dot":
        trace_block = trace_text if trace_text else "[Trace/log text is not available for this case.]"
        dot_block = "[DOT text is not available in the current dataset format.]"
        return f"{trace_block}\n\n{dot_block}"

    raise ValueError(f"Unknown trace_mode: {trace_mode}")


def build_prompt_from_text(case: dict, prompt_text: str, trace_mode: str) -> str:
    evidence = build_trace_evidence(case, trace_mode)
    bug_pv = case.get("bug_pv", "").strip()

    return f"""
{prompt_text}

==============================
ACTUAL INPUT
==============================

Protocol family:
{case["protocol"]}

Bug case id:
{case["bug_id"]}

Sample id:
{case["id"]}

Buggy ProVerif file:
{bug_pv if bug_pv else '[pv_text is not available for this case.]'}

ProVerif trace/log evidence:
{evidence}

==============================
TASK
==============================

Analyze the buggy ProVerif case and produce three outputs:
1. Mermaid UML-style sequence diagram code
2. A short explanation of what goes wrong
3. A minimal patch suggestion

Stay grounded in the provided .pv file and ProVerif log/trace evidence.
Do not invent unsupported protocol steps, participants, or messages.

==============================
RESPONSE FORMAT
==============================

Return exactly one JSON object with exactly these keys:

{{
  "diagram_code": "...",
  "explanation": "...",
  "patch_suggestion": "...",
  "notes": "..."
}}

Extra requirements:
- "diagram_code" must be Mermaid sequence diagram code.
- "diagram_code" must start with "sequenceDiagram".
- "explanation" should focus on the failure shown by the given evidence.
- "patch_suggestion" should be minimal and directly relevant to the failure.
- "notes" can be an empty string if there is nothing special to mention.
- Do not output markdown fences.
- Do not output any text outside the JSON object.
""".strip()


def build_tuning_prompt(case: dict, prompt_mode: str, prompt_version: str, trace_mode: str) -> str:
    prompt_text = load_tuning_prompt(prompt_mode, prompt_version)
    return build_prompt_from_text(case, prompt_text, trace_mode)


def build_final_prompt(case: dict, prompt_name: str, trace_mode: str) -> str:
    prompt_text = load_final_prompt(prompt_name)
    return build_prompt_from_text(case, prompt_text, trace_mode)