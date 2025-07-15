import json
import jsonschema
import sys
import argparse


def validate_json_file(schema_path, json_path):
    try:
        # Load schema
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Load JSON file
        with open(json_path, "r") as f:
            data = json.load(f)

        # Validate
        jsonschema.validate(data, schema)
        print(f"✅ {json_path} is valid!")
        return True

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {json_path}: {e}")
        return False
    except jsonschema.ValidationError as e:
        print(f"❌ Validation error in {json_path}:")
        print(f"   {e.message}")
        print(f"   At path: {' -> '.join(str(p) for p in e.absolute_path)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Validate JSON files against a JSON schema"
    )
    parser.add_argument(
        "--schema", "-s", required=True, help="Path to the JSON schema file"
    )
    parser.add_argument(
        "--json", "-j", required=True, help="Path to the JSON file to validate"
    )

    args = parser.parse_args()

    print("🔍 Starting JSON validation with Python...")
    success = validate_json_file(args.schema, args.json)

    if not success:
        sys.exit(1)

    print("🎉 All validations passed!")


if __name__ == "__main__":
    main()
