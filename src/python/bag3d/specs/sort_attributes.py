import argparse
import json


def sort_json_complete(input_file, output_file):
    """
    Read a JSON file, sort the main keys alphabetically, and sort the properties
    of each object according to a specific order.

    Args:
        input_file (str): Path to the input JSON file
        output_file (str): Path to the output JSON file
    """
    # Define the desired property order from the schema's required array
    property_order = [
        "description",
        "semanticType",
        "source",
        "type",
        "unit",
        "precision",
        "scale",
        "valueFormat",
        "values",
        "nullable",
        "appliesTo",
    ]

    def sort_object_properties(obj):
        """Sort object properties according to the defined order."""
        if not isinstance(obj, dict):
            return obj

        # Create ordered dict with properties in the specified order
        ordered_obj = {}

        # First, add properties in the specified order if they exist
        for prop in property_order:
            if prop in obj:
                ordered_obj[prop] = obj[prop]

        # Then add any remaining properties that weren't in the order list
        for key, value in obj.items():
            if key not in ordered_obj:
                ordered_obj[key] = value

        return ordered_obj

    try:
        # Read the JSON file
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Sort the main dictionary by keys alphabetically
        sorted_data = dict(sorted(data.items()))

        # Sort each object's properties according to the schema order
        for key, value in sorted_data.items():
            sorted_data[key] = sort_object_properties(value)

        # Write the sorted data to the output file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sorted_data, f, indent=2, ensure_ascii=False)

        print(
            f"Successfully sorted JSON from '{input_file}' and saved to '{output_file}'"
        )
        print("- Main keys sorted alphabetically")
        print("- Object properties ordered according to schema")

    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{input_file}'")
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Sort the attributes.json file")
    parser.add_argument(
        "--input", "-i", required=True, help="Path to the input attributes.json"
    )
    parser.add_argument(
        "--output", "-o", required=True, help="Path to the output attributes.json"
    )

    args = parser.parse_args()
    sort_json_complete(args.input, args.output)


if __name__ == "__main__":
    main()
