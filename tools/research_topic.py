"""
Researches a topic using Tavily and saves structured findings to .tmp/research.json.
Usage: python research_topic.py "<topic>" [num_results]
"""

import sys
import os
import json
from pathlib import Path
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()


def research(topic: str, num_results: int = 10, output_path: str | None = None) -> dict:
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    response = client.search(
        query=topic,
        search_depth="advanced",
        max_results=num_results,
        include_answer=True,
    )

    results = {
        "topic": topic,
        "answer": response.get("answer", ""),
        "sources": [
            {
                "title": r["title"],
                "url": r["url"],
                "content": r["content"],
                "score": r.get("score", 0),
            }
            for r in response.get("results", [])
        ],
    }

    if output_path is None:
        output_path = Path(".tmp") / "research.json"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Research complete: {len(results['sources'])} sources -> {output_path}")
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python research_topic.py "<topic>" [num_results]')
        sys.exit(1)
    topic = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    research(topic, n)
