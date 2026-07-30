"""
============================================================
TODAY'S UPSC ISSUES
DISTRIBUTION RUNNER
Distribution Engine V1.0
============================================================

PURPOSE

Runs all active distribution generators using one command.

ACTIVE OUTPUTS

1. Social postcard
2. YouTube Shorts scripts
3. YouTube Shorts metadata

NORMAL COMMAND

python src/distribution/distribution_runner.py
============================================================
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


class DistributionRunnerError(RuntimeError):
    """Raised when a distribution stage fails."""


@dataclass(frozen=True)
class DistributionStage:
    """Represents one distribution generation stage."""

    number: int
    name: str
    script_path: Path


def run_stage(
    stage: DistributionStage,
    total_stages: int,
    project_root: Path,
) -> float:
    """
    Run one distribution generator.

    Returns:
        Elapsed stage time in seconds.

    Raises:
        DistributionRunnerError if the generator fails.
    """

    print()
    print("-" * 72)
    print(f"[{stage.number}/{total_stages}] {stage.name}")
    print("-" * 72)

    if not stage.script_path.exists():
        raise DistributionRunnerError(
            f"Generator not found: {stage.script_path}"
        )

    started_at = time.perf_counter()

    result = subprocess.run(
        [
            sys.executable,
            str(stage.script_path),
        ],
        cwd=project_root,
        check=False,
    )

    elapsed = time.perf_counter() - started_at

    if result.returncode != 0:
        raise DistributionRunnerError(
            f"{stage.name} failed with exit code "
            f"{result.returncode}."
        )

    print(f"COMPLETED: {stage.name}")
    print(f"TIME     : {elapsed:.2f} seconds")

    return elapsed


def build_stages(
    project_root: Path,
) -> list[DistributionStage]:
    """Return the active Distribution Engine stages."""

    distribution_root = (
        project_root
        / "src"
        / "distribution"
    )

    return [
        DistributionStage(
            number=1,
            name="Generating Social Postcard",
            script_path=(
                distribution_root
                / "postcard_generator.py"
            ),
        ),
        DistributionStage(
            number=2,
            name="Generating YouTube Shorts Scripts",
            script_path=(
                distribution_root
                / "youtube"
                / "shorts_script_generator.py"
            ),
        ),
        DistributionStage(
            number=3,
            name="Generating YouTube Shorts Metadata",
            script_path=(
                distribution_root
                / "youtube"
                / "metadata_generator.py"
            ),
        ),
    ]


def main() -> int:
    """Run the complete Distribution Engine."""

    project_root = Path(__file__).resolve().parents[2]
    stages = build_stages(project_root)

    started_at = time.perf_counter()

    print()
    print("=" * 72)
    print("TODAY'S UPSC ISSUES")
    print("DISTRIBUTION ENGINE V1.0")
    print("=" * 72)
    print(f"Project : {project_root}")
    print(f"Stages  : {len(stages)}")

    try:
        for stage in stages:
            run_stage(
                stage=stage,
                total_stages=len(stages),
                project_root=project_root,
            )

        elapsed = time.perf_counter() - started_at

        print()
        print("=" * 72)
        print("DISTRIBUTION COMPLETED SUCCESSFULLY")
        print("=" * 72)
        print(f"Stages completed : {len(stages)}")
        print(f"Total time       : {elapsed:.2f} seconds")
        print("=" * 72)

        return 0

    except (
        DistributionRunnerError,
        OSError,
    ) as exc:
        elapsed = time.perf_counter() - started_at

        print()
        print("=" * 72)
        print("DISTRIBUTION ENGINE FAILED")
        print("=" * 72)
        print(f"Reason       : {exc}")
        print(f"Elapsed time : {elapsed:.2f} seconds")
        print("=" * 72)

        return 1


if __name__ == "__main__":
    sys.exit(main())