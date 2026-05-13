"""
Aiwrite — AI writing assistant powered by Claude.

12 task modes: improve / grammar / title / continue / summarize / expand /
paraphrase / translate / tone / simplify / outline / custom.

Streaming output via Server-Sent Events.
"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import anthropic
import os
import json

app = Flask(__name__)

# 默认模型。前端可以覆盖(Haiku 快/便宜,Opus 慢/最强)
DEFAULT_MODEL = "claude-sonnet-4-6"
ALLOWED_MODELS = {
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6",
    "claude-opus-4-7",
}

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ──────────────────────────────────────────────────────────────────────
# 任务定义。每个任务有 system prompt + 一个生成 user prompt 的函数。
# ──────────────────────────────────────────────────────────────────────

def _improve(text, **_):
    return (
        "You are a skilled editor. Improve the following text: fix awkward "
        "phrasing, tighten verbose sentences, and make it flow naturally. "
        "Keep the original meaning and language. Return only the improved version.",
        text,
    )

def _grammar(text, **_):
    return (
        "You are a grammar tutor. List grammar, spelling, and punctuation issues "
        "in the text below. For each issue: quote the original, explain briefly, "
        "and show the fix. If there are no issues, say so.",
        text,
    )

def _title(text, **_):
    return (
        "You generate compelling titles. Return exactly 5 title options for the "
        "content below, one per line, no numbering, no extra commentary. "
        "Mix styles (descriptive, intriguing, listicle, question, direct).",
        text,
    )

def _continue(text, **_):
    return (
        "Continue the following text seamlessly. Match the existing tone, voice, "
        "and language. Do not repeat what's already written; just keep going for "
        "1-2 paragraphs.",
        text,
    )

def _summarize(text, **_):
    return (
        "Summarize the following text in one tight paragraph. Preserve key facts "
        "and conclusions, drop fluff. Match the original language.",
        text,
    )

def _expand(text, **_):
    return (
        "Expand the following text with additional detail, examples, and context. "
        "Keep the original tone and language. Roughly 2-3x the original length.",
        text,
    )

def _paraphrase(text, **_):
    return (
        "Rewrite the text below saying exactly the same thing but with different "
        "wording and sentence structure. Preserve all facts and the original language. "
        "Return only the paraphrased version.",
        text,
    )

def _translate(text, target_language="English", **_):
    return (
        f"Translate the following text to {target_language}. If the source is "
        f"already in {target_language}, translate to whichever language fits best "
        "as a contrast. Preserve meaning, tone, and formatting. Return only the translation.",
        text,
    )

def _tone(text, tone="professional", **_):
    return (
        f"Rewrite the following text in a {tone} tone. Preserve the original "
        "meaning and language. Return only the rewritten version.",
        text,
    )

def _simplify(text, **_):
    return (
        "Rewrite the following text in simple, plain language. Avoid jargon, "
        "long sentences, and complex words. A 12-year-old should understand it. "
        "Match the original language.",
        text,
    )

def _outline(text, **_):
    return (
        "Create a clear, structured outline from the content below. Use headings "
        "and indented bullet points. If the input is a topic rather than existing "
        "text, generate a fresh outline for that topic. Match the input language.",
        text,
    )

def _custom(text, custom_prompt="", **_):
    if not custom_prompt:
        return (
            "You are a helpful writing assistant.",
            text,
        )
    return (
        custom_prompt,
        text,
    )


TASKS = {
    "improve":    {"label": "Improve",    "fn": _improve},
    "grammar":    {"label": "Grammar",    "fn": _grammar},
    "title":      {"label": "Title",      "fn": _title},
    "continue":   {"label": "Continue",   "fn": _continue},
    "summarize":  {"label": "Summarize",  "fn": _summarize},
    "expand":     {"label": "Expand",     "fn": _expand},
    "paraphrase": {"label": "Paraphrase", "fn": _paraphrase},
    "translate":  {"label": "Translate",  "fn": _translate},
    "tone":       {"label": "Tone",       "fn": _tone},
    "simplify":   {"label": "Simplify",   "fn": _simplify},
    "outline":    {"label": "Outline",    "fn": _outline},
    "custom":     {"label": "Custom",     "fn": _custom},
}


# ──────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    task_meta = [{"key": k, "label": v["label"]} for k, v in TASKS.items()]
    return render_template("index.html", tasks=task_meta)


@app.route("/api/health")
def health():
    return jsonify({
        "ok": True,
        "has_api_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
    })


@app.route("/api/generate", methods=["POST"])
def generate():
    """Non-streaming fallback. Useful for clients that can't do SSE."""
    data = request.get_json(silent=True) or {}
    try:
        system, user = _build_prompt(data)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    model = data.get("model", DEFAULT_MODEL)
    if model not in ALLOWED_MODELS:
        model = DEFAULT_MODEL
    temperature = _clamp_temp(data.get("temperature", 0.7))

    try:
        msg = client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return jsonify({"success": True, "result": msg.content[0].text})
    except anthropic.APIError as e:
        return jsonify({"success": False, "error": f"Claude API error: {e}"}), 502
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stream", methods=["POST"])
def stream():
    """Streaming endpoint via SSE. Frontend uses this by default."""
    data = request.get_json(silent=True) or {}
    try:
        system, user = _build_prompt(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    model = data.get("model", DEFAULT_MODEL)
    if model not in ALLOWED_MODELS:
        model = DEFAULT_MODEL
    temperature = _clamp_temp(data.get("temperature", 0.7))

    @stream_with_context
    def event_stream():
        try:
            with client.messages.stream(
                model=model,
                max_tokens=2000,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            ) as s:
                for chunk in s.text_stream:
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except anthropic.APIError as e:
            yield f"data: {json.dumps({'error': f'Claude API error: {e}'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _build_prompt(data):
    text = (data.get("text") or "").strip()
    task = data.get("task") or "improve"
    if not text and task != "custom":
        raise ValueError("Input text is empty.")
    if task not in TASKS:
        raise ValueError(f"Unknown task: {task}")
    return TASKS[task]["fn"](
        text,
        target_language=data.get("target_language", "English"),
        tone=data.get("tone", "professional"),
        custom_prompt=(data.get("custom_prompt") or "").strip(),
    )


def _clamp_temp(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.7
    return max(0.0, min(1.0, f))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
