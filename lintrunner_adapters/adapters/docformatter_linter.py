# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: MIT
"""Adapter for https://github.com/PyCQA/docformatter"""

import argparse
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from lintrunner_adapters import (
    LintMessage,
    LintSeverity,
    add_default_options,
    run_command,
)

LINTER_CODE = "DOCFORMATTER"


def check_file(
    filename: str,
    retries: int,
    config: str,
) -> list[LintMessage]:
    tmp_path: Optional[Path] = None

    try:
        path = Path(filename)
        original = path.read_text(encoding="utf-8")

        # Docformatter cannot print the would-be results to stdout, so
        # formatting must be applied in-place to an actual file. A temp file is
        # used for this.
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        shutil.copyfile(path, tmp_path)

        args = ["docformatter"]
        if config is not None:
            args += ["--config", config]
        args += ["--in-place", str(tmp_path)]

        run_command(args, retries=retries, check=False)

        replacement = tmp_path.read_text(encoding="utf-8")
    except Exception as err:
        return [
            LintMessage(
                path=None,
                line=None,
                char=None,
                code=LINTER_CODE,
                severity=LintSeverity.ERROR,
                name="command-failed",
                original=None,
                replacement=None,
                description=(f"Failed due to {err.__class__.__name__}:\n{err}"),
            )
        ]
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)

    if original == replacement:
        return []

    return [
        LintMessage(
            path=filename,
            line=None,
            char=None,
            code=LINTER_CODE,
            name="format",
            original=original,
            replacement=replacement,
            severity=LintSeverity.WARNING,
            description="Run `lintrunner -a` to apply this patch.",
        )
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Docstring formatter. Linter code: {LINTER_CODE}.",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "--config",
        required=False,
        help="location of docformatter config",
    )
    add_default_options(parser)
    args = parser.parse_args()

    lint_messages: list[LintMessage] = []
    for filename in args.filenames:
        lint_messages.extend(check_file(filename, args.retries, args.config))

    for lint_message in lint_messages:
        lint_message.display()


if __name__ == "__main__":
    main()
