import argparse
from pathlib import Path

from settings import RunFileNames
from workflow import run_experiment


ROOT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the standalone Manim AI workflow experiment."
    )
    parser.add_argument(
        "--request",
        type=Path,
        default=Path("inputs/function_translation_request.txt"),
        help="Path to the model-facing teacher request text.",
    )
    parser.add_argument(
        "--plan",
        type=Path,
        default=None,
        help="Optional existing plan.txt to reuse for codegen experiments.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Run folder name under runs/. Defaults to a timestamp.",
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Run the workflow with fake LLM calls and overwrite runs/e2e.",
    )
    return parser.parse_args()


def resolve_input_path(path: Path | None) -> Path | None:
    if path is None or path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return cwd_path
    return ROOT_DIR / path


def main() -> None:
    args = parse_args()
    if args.e2e and args.name is not None:
        raise SystemExit("--e2e always writes runs/e2e and cannot be combined with --name.")
    if args.e2e and args.plan is not None:
        raise SystemExit("--e2e uses fake local planning and cannot be combined with --plan.")

    request_path = resolve_input_path(args.request)
    if request_path is None:
        raise RuntimeError("--request is required.")
    run_dir = run_experiment(
        request_path=request_path,
        name=args.name,
        provided_plan_path=resolve_input_path(args.plan),
        e2e=args.e2e,
    )
    print(f"Run complete: {run_dir}")
    print(f"Summary: {run_dir / RunFileNames.SUMMARY}")


if __name__ == "__main__":
    main()
