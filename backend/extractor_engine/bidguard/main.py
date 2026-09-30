"""Interactive CLI for the BidGuard document extraction engine."""

import json
import sys
from pathlib import Path

from extractors.registry import DOCUMENT_TYPE_MENU, REGISTRY
from pipeline import process_document


def prompt_for_file() -> str:
    while True:
        file_path = input("Enter the path to the PDF file: ").strip().strip('"').strip("'")

        if not file_path:
            print("Please enter a file path.")
            continue

        path = Path(file_path)
        if not path.exists():
            print(f"File not found: {file_path}")
            continue
        if not path.is_file():
            print(f"That path is not a file: {file_path}")
            continue

        return str(path)


def prompt_for_document_type() -> str:
    print("What type of document are you uploading?")
    for i, item in enumerate(DOCUMENT_TYPE_MENU, start=1):
        print(f"  {i}. {item['label']}")

    while True:
        choice = input("Enter number: ").strip()
        try:
            index = int(choice) - 1
            key = DOCUMENT_TYPE_MENU[index]["key"]
        except (ValueError, IndexError):
            print("Invalid choice. Please enter a valid number.")
            continue

        if key == "OTHER":
            print("The 'Other' document type is not implemented yet.")
            continue

        if key not in REGISTRY:
            print(f"'{key}' extractor is not implemented yet.")
            continue

        return key


def main():
    print("\n=== BIDGUARD DOCUMENT EXTRACTION ENGINE ===\n")

    pdf_path = prompt_for_file()
    document_type_key = prompt_for_document_type()

    print("\nExtracting document...\n")

    try:
        result = process_document(pdf_path, document_type_key)
    except Exception as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
