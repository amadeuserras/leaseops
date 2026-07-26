from __future__ import annotations

from leaseops.agent.graph import build_graph


def main() -> None:
    build_graph().get_graph().print_ascii()


if __name__ == "__main__":
    main()
