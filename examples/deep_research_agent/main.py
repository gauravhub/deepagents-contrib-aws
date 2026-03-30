#!/usr/bin/env python3
"""Run the deep research agent interactively.

Usage: uv run main.py
"""

from __future__ import annotations

from graph import graph


def main() -> None:
    print("Deep Research Agent")
    print("Type 'quit' to exit.\n")

    config = {"configurable": {"thread_id": "demo"}}

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        response = graph.invoke(
            {"messages": [("human", user_input)]},
            config=config,
        )

        last_msg = response["messages"][-1]
        print(f"\nAgent: {last_msg.content}\n")


if __name__ == "__main__":
    main()
