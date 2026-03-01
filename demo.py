from __future__ import annotations

import json
from typing import Any, Dict

from tool import ToolResult, business_text_tool


class SimpleAgent:
    """
    Minimal, framework-free agent used to demonstrate tool integration.

    The agent receives a user message, decides whether the custom tool
    should be used, invokes it, and then formats a response based on the
    structured result.
    """

    def __init__(self) -> None:
        self.tool = business_text_tool

    def handle_message(self, message: str) -> Dict[str, Any]:
        """
        Decide whether to call the tool and return a structured response.

        Decision rule (intentionally simple for the demo):
        if the user asks to analyze some text, or mentions common news
        phrases such as "news" or "report", the agent calls the tool.
        """
        lowered = message.lower()
        should_use_tool = any(
            phrase in lowered
            for phrase in (
                "analyze this",
                "please analyze",
                "news",
                "report",
                "business update",
            )
        )

        if not should_use_tool:
            return {
                "agent_message": (
                    "I did not detect a request for business/news analysis. "
                    "Ask me to 'analyze this news' to see the tool in action."
                ),
                "tool_used": False,
            }

        result: ToolResult = self.tool.execute(text=message, top_n_keywords=5)
        if not result.get("ok"):
            return {
                "agent_message": (
                    "I tried to analyze your text, but something went wrong: "
                    f"{result.get('error_message')}"
                ),
                "tool_used": True,
                "tool_error": {
                    "type": result.get("error_type"),
                    "message": result.get("error_message"),
                },
            }

        data = result["data"]
        sentiment = data["sentiment"]

        summary_lines = [
            "Here is a quick analysis of your business/news text:",
            f"- Characters: {data['char_count']}",
            f"- Words: {data['word_count']} "
            f"(unique: {data['unique_word_count']})",
            f"- Sentences: {data['sentence_count']} "
            f"(avg. length: {data['avg_sentence_length']:.1f} words)",
            f"- Sentiment: {sentiment['label']} (score: {sentiment['score']})",
        ]

        top_keywords = data["top_keywords"]
        if top_keywords:
            keyword_str = ", ".join(
                f"{item['keyword']} ({item['count']})" for item in top_keywords
            )
            summary_lines.append(f"- Top keywords: {keyword_str}")

        return {
            "agent_message": "\n".join(summary_lines),
            "tool_used": True,
            "raw_tool_result": data,
        }


def demo_success_case() -> None:
    """
    Run a demo where the tool is used successfully on a realistic input.

    This simulates an earnings-news style message that an analyst or
    business user might ask the agent to summarize.
    """
    agent = SimpleAgent()
    news_text = (
        "Please analyze this earnings news: The company reported strong profit "
        "growth in the fourth quarter, beating analyst expectations. Management "
        "remains optimistic about future opportunities despite some macro "
        "uncertainty."
    )
    print("=== SUCCESS CASE ===")
    print("User:", news_text)
    response = agent.handle_message(news_text)
    print("\nAgent response:")
    print(response["agent_message"])
    print("\nRaw tool payload (JSON):")
    print(json.dumps(response.get("raw_tool_result", {}), indent=2))
    print()


def demo_error_case() -> None:
    """
    Run a demo that deliberately passes invalid parameters to show error handling.

    In a real agent framework, such errors would normally surface as a
    structured failure that the agent can turn into a user-friendly message.
    """
    print("=== ERROR CASE ===")
    print(
        "Calling the tool with invalid parameters: text=123 (non-string) "
        "and top_n_keywords=-1 (non-positive)."
    )

    # We bypass the agent here to focus purely on tool-level validation and
    # error reporting, which is what many frameworks surface back to users.
    result = business_text_tool.execute(text=123, top_n_keywords=-1)  # type: ignore[arg-type]
    print("\nStructured error result (JSON):")
    print(json.dumps(result, indent=2))
    print()


if __name__ == "__main__":
    demo_success_case()
    demo_error_case()

