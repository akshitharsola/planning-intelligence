"""Start the planning Q&A agent demo on http://localhost:8020 (standalone; not the main web app).

Usage:
    python scripts/run_agent_demo.py [--port 8020]

Set AGENT_USE_OLLAMA=0 to never call Ollama (by default it is used only if it is running).
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--port", type=int, default=8020)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    uvicorn.run("src.agent.demo_app:app", host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
