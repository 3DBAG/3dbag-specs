"""Sort JSON object keys recursively while preserving array order."""

import argparse
import json
from pathlib import Path

from bag3d.specs.validate_json import read_json


def sort_json_complete(input_file: Path, output_file: Path) -> None:
    data = read_json(input_file)
    output_file.write_text(
        json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", type=Path, required=True)
    parser.add_argument("--output", "-o", type=Path, required=True)
    args = parser.parse_args()
    sort_json_complete(args.input, args.output)


if __name__ == "__main__":
    main()
