from config import PROMPTS_DIR


def load_prompt_template(prompt_mode: str) -> str:
    """
    Load the prompt template from prompts/<prompt_mode>.txt
    """
    prompt_path = PROMPTS_DIR / f"{prompt_mode}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def build_trace_evidence(case: dict, trace_mode: str) -> str:
    """
    Build the evidence block according to the selected trace mode.

    In your current dataset, only log_text is clearly available.
    It is normalized into case["trace_text"].
    """
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


def build_full_prompt(case: dict, prompt_mode: str, trace_mode: str) -> str:
    """
    Build one full prompt string for the selected case.

    Current dataset fields:
    - id
    - protocol
    - bug_id
    - bug_pv
    - trace_text
    """
    template = load_prompt_template(prompt_mode)
    evidence = build_trace_evidence(case, trace_mode)

    bug_pv = case.get("bug_pv", "").strip()

    prompt = f"""
{template}

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

    return prompt