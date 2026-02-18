"""프로젝트 루트 실행 편의 스크립트.

사용법:
    uv run python main.py
    또는
    uv run uvicorn backend.app.main:app --reload --port 8000
"""

import subprocess
import sys


def main():
    subprocess.run(
        [
            sys.executable, "-m", "uvicorn",
            "backend.app.main:app",
            "--reload",
            "--port", "8000",
            "--host", "0.0.0.0",
        ]
    )


if __name__ == "__main__":
    main()
