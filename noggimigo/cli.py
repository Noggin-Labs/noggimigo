"""Command-line interface backed by the shared session manager."""
from __future__ import annotations
import argparse
from .curriculum import lesson_ids
from .session import NoggimigoSession

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Noggimigo local tutor")
    parser.add_argument("--lesson", choices=lesson_ids(), default="fractions_intro")
    args = parser.parse_args()
    session = NoggimigoSession(args.lesson)
    print("Noggimigo local tutor. Type 'hint', 'reset', or 'exit'.")
    while not session.complete:
        print(f"\n{session.current_prompt()}")
        answer = input("> ").strip()
        if answer.lower() == "exit":
            break
        if answer.lower() == "reset":
            session.reset()
            continue
        result = session.request_hint() if answer.lower() in {"hint", "help", "?"} else session.submit(answer)
        print(result["feedback"])

if __name__ == "__main__":
    main()
