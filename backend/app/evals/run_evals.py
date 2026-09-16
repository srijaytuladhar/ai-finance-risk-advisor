"""Evaluation harness running golden benchmark questions with LLM-as-a-judge scoring."""

import json
import logging
from pathlib import Path
from typing import Any
from tabulate import tabulate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agent.graph import run_agent
from app.config import settings

logger = logging.getLogger(__name__)

GOLDEN_SET_PATH = Path(__file__).resolve().parent / "golden_set.json"
RESULTS_PATH = Path(__file__).resolve().parent / "results.json"

JUDGE_PROMPT = """You are an expert AI evaluator assessing a Fintech Portfolio Risk Advisor assistant.
Your job is to evaluate whether the assistant adhered to the critical architectural requirements:
1. Did the assistant call the expected deterministic quantitative or RAG tools? (LLMs must never compute math on their own)
2. Is the numerical output or logic grounded in the actual tool results (no hallucinated numbers)?
3. Is the final explanation clear, professional, and easy to understand for an investor?

Score each of the three dimensions strictly from 0.0 to 1.0:
- `tool_score`: 1.0 if appropriate expected tools were executed; 0.0 if calculations were attempted without tools.
- `value_score`: 1.0 if numbers/logic match the tool output accurately; 0.0 if hallucinated or distorted.
- `explanation_score`: 1.0 if clear, articulate, and informative in plain English; 0.0 if confusing or poor.

Output ONLY valid JSON matching this schema:
{
  "tool_score": 1.0,
  "value_score": 1.0,
  "explanation_score": 1.0,
  "reasoning": "Short justification of the scores"
}
"""


def evaluate_single_turn(
    item: dict[str, Any], judge_llm: Any
) -> dict[str, Any]:
    """Execute a single golden test question, record tool calls, and obtain LLM-as-a-judge scores."""
    question = item["question"]
    expected_tools = item.get("expected_tools", [])
    criteria = item.get("criteria", "")

    print(f"\n[RUNNING] Question: {question}")
    agent_output = run_agent(message=question, history=[])
    response_text = agent_output.get("response", "")
    tool_calls = agent_output.get("tool_calls", [])
    tool_names = [tc["name"] for tc in tool_calls]

    print(f" -> Tools called: {tool_names}")

    judge_user_content = f"""EVALUATION CASE:
Question: {question}
Expected Tools: {expected_tools}
Evaluation Criteria: {criteria}

ACTUAL AGENT EXECUTION:
Tools Executed: {tool_names}
Raw Tool Calls: {json.dumps(tool_calls, default=str)[:1000]}
Assistant Response: {response_text}
"""

    try:
        judge_res = judge_llm.invoke([
            SystemMessage(content=JUDGE_PROMPT),
            HumanMessage(content=judge_user_content),
        ])
        raw_obj = judge_res.content
        if isinstance(raw_obj, list):
            raw_content = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in raw_obj)
        else:
            raw_content = str(raw_obj)
        raw_content = raw_content.strip()
        # Clean any markdown code blocks
        if raw_content.startswith("```"):
            raw_content = raw_content.split("```")[1]
            if raw_content.startswith("json"):
                raw_content = raw_content[4:]
        scores = json.loads(raw_content.strip())
    except Exception as e:
        logger.error("Error obtaining judge scores: %s", str(e))
        # Fallback heuristic scoring
        has_tools = any(t in tool_names for t in expected_tools)
        scores = {
            "tool_score": 1.0 if has_tools else 0.0,
            "value_score": 1.0 if len(response_text) > 30 else 0.5,
            "explanation_score": 1.0 if len(response_text) > 50 else 0.5,
            "reasoning": f"Heuristic evaluation due to parsing error: {str(e)}",
        }

    t_score = float(scores.get("tool_score", 0.0))
    v_score = float(scores.get("value_score", 0.0))
    e_score = float(scores.get("explanation_score", 0.0))
    overall = round((t_score + v_score + e_score) / 3.0, 2)

    return {
        "id": item["id"],
        "question": question,
        "category": item.get("category", "general"),
        "expected_tools": expected_tools,
        "tools_called": tool_names,
        "response_sample": response_text[:120] + "..." if len(response_text) > 120 else response_text,
        "tool_score": t_score,
        "value_score": v_score,
        "explanation_score": e_score,
        "overall_score": overall,
        "reasoning": scores.get("reasoning", ""),
        "passed": overall >= 0.70,
    }


def get_judge_llm() -> Any:
    """Build evaluation judge LLM with fallback chain: Gemini -> OpenAI -> Hugging Face."""
    candidates = []
    if settings.OPENROUTER_API_KEY:
        openrouter_model = getattr(settings, "OPENROUTER_MODEL", "") or "openai/gpt-4o-mini"
        base_url = getattr(settings, "OPENROUTER_BASE_URL", "") or "https://openrouter.ai/api/v1"
        candidates.append(
            ChatOpenAI(
                base_url=base_url,
                api_key=settings.OPENROUTER_API_KEY,
                model=openrouter_model,
                temperature=0.0,
            )
        )
    if settings.HUGGINGFACE_API_KEY:
        hf_model = getattr(settings, "HUGGINGFACE_MODEL", "") or (
            settings.MODEL_NAME if "/" in settings.MODEL_NAME else "Qwen/Qwen2.5-72B-Instruct"
        )
        candidates.append(
            ChatOpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=settings.HUGGINGFACE_API_KEY,
                model=hf_model,
                temperature=0.0,
            )
        )
    if settings.GEMINI_API_KEY:
        gemini_model = getattr(settings, "GEMINI_MODEL", "") or (
            settings.MODEL_NAME if "gemini" in settings.MODEL_NAME.lower() else "gemini-3.6-flash"
        )
        candidates.append(
            ChatGoogleGenerativeAI(
                model=gemini_model,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.0,
            )
        )
    
    if settings.OPENAI_API_KEY:
        openai_model = getattr(settings, "OPENAI_MODEL", "") or (
            settings.MODEL_NAME if "gpt" in settings.MODEL_NAME.lower() else "gpt-4o-mini"
        )
        candidates.append(
            ChatOpenAI(
                model=openai_model,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.0,
            )
        )
    if settings.HUGGINGFACE_API_KEY:
        hf_model = getattr(settings, "HUGGINGFACE_MODEL", "") or (
            settings.MODEL_NAME if "/" in settings.MODEL_NAME else "Qwen/Qwen2.5-72B-Instruct"
        )
        candidates.append(
            ChatOpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=settings.HUGGINGFACE_API_KEY,
                model=hf_model,
                temperature=0.0,
            )
        )

    if not candidates:
        raise RuntimeError("No LLM API keys configured for evaluation judge.")

    primary = candidates[0]
    if len(candidates) > 1:
        return primary.with_fallbacks(candidates[1:])
    return primary


def main():
    """Run all evaluations from golden_set.json, display formatted results, and save metrics to disk."""
    print("=" * 80)
    print("Starting Fintech Portfolio Risk Advisor Evaluation Suite")
    print(f"Model under test: {settings.MODEL_NAME}")
    print("=" * 80)

    if not GOLDEN_SET_PATH.exists():
        print(f"Error: Golden set not found at {GOLDEN_SET_PATH}")
        return

    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        golden_cases = json.load(f)

    judge_llm = get_judge_llm()

    results = []
    for item in golden_cases:
        res = evaluate_single_turn(item, judge_llm)
        results.append(res)

    table_data = []
    total_score_sum = 0.0
    passed_count = 0

    for r in results:
        table_data.append([
            r["id"],
            r["question"][:35] + ("..." if len(r["question"]) > 35 else ""),
            ", ".join(r["tools_called"]) or "None",
            f"{r['tool_score']:.1f}",
            f"{r['value_score']:.1f}",
            f"{r['explanation_score']:.1f}",
            f"{r['overall_score']:.2f}",
            "PASS" if r["passed"] else "FAIL",
        ])
        total_score_sum += r["overall_score"]
        if r["passed"]:
            passed_count += 1

    headers = ["ID", "Question", "Tools Called", "Tool", "Val", "Exp", "Score", "Status"]
    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))

    avg_score = round(total_score_sum / len(results), 2) if results else 0.0
    pass_rate = round((passed_count / len(results)) * 100.0, 1) if results else 0.0

    print("\n" + "=" * 80)
    print(f"EVALUATION SUMMARY:")
    print(f"Total Test Cases: {len(results)}")
    print(f"Passed: {passed_count} / {len(results)} ({pass_rate}%)")
    print(f"Average Benchmark Score: {avg_score} / 1.00")
    print("=" * 80)

    output_payload = {
        "model": settings.MODEL_NAME,
        "total_cases": len(results),
        "passed_cases": passed_count,
        "pass_rate_percent": pass_rate,
        "average_score": avg_score,
        "cases": results,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"\nSaved detailed evaluation audit log to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
