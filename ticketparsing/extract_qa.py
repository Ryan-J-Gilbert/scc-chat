import json
import argparse
from pathlib import Path
from datetime import datetime


def extract_qa_to_json(input_file: Path, output_file: Path, skip_field: str = 'skip', version: str = '1.0'):
    """
    Extract all QA pairs from JSONL to a prettified JSON format.
    
    Output format:
    {
        "metadata": {
            "generated_at": "ISO timestamp",
            "version": "1.0",
            "source_file": "input.jsonl",
            "total_pairs": 123
        },
        "qa_pairs": [
            {
                "id": 0,
                "question": "...",
                "answer": "..."
            },
            ...
        ]
    }
    
    Args:
        input_file: Path to input JSONL file
        output_file: Path to output JSON file
        skip_field: Field name to check if entry should be skipped
        version: Version string for the output
    """
    qa_pairs = []
    skipped_entries = 0
    qa_id = 0
    
    with open(input_file, 'r') as infile:
        for line_num, line in enumerate(infile):
            try:
                # Parse JSON line
                data = json.loads(line.strip())
                
                # Check if this entry should be skipped
                result = data.get('result', {})
                if result.get(skip_field, False):
                    skipped_entries += 1
                    continue
                
                # Extract QA pairs
                qa_list = result.get('qa_pairs', [])
                
                # Skip if qa_list is None or empty
                if not qa_list:
                    continue
                
                # Add each QA pair to the list
                for qa_pair in qa_list:
                    question = qa_pair.get('question', '').strip()
                    answer = qa_pair.get('answer', '').strip()
                    
                    if question and answer:
                        qa_pairs.append({
                            'id': qa_id,
                            'question': question,
                            'answer': answer
                        })
                        qa_id += 1
                
            except json.JSONDecodeError as e:
                print(f"Warning: Line {line_num}: JSON decode error - {e}")
                continue
            except Exception as e:
                print(f"Error on line {line_num}: {e}")
                raise
    
    # Create output structure with metadata
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'version': version,
            'source_file': input_file.name,
            'total_pairs': len(qa_pairs),
            'skipped_entries': skipped_entries
        },
        'qa_pairs': qa_pairs
    }
    
    # Write prettified JSON to output file
    with open(output_file, 'w') as outfile:
        json.dump(output_data, outfile, indent=2, ensure_ascii=False)
    
    print(f"\nExtraction complete!")
    print(f"Total QA pairs extracted: {len(qa_pairs)}")
    print(f"Skipped entries: {skipped_entries}")
    print(f"Output file: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract all QA pairs from JSONL to prettified JSON format for manual review'
    )
    parser.add_argument(
        'input_file',
        type=Path,
        help='Input JSONL file path'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=Path,
        default=None,
        help='Output JSON file path (default: input_file.qa.json)'
    )
    parser.add_argument(
        '--version',
        '-v',
        type=str,
        default='1.0',
        help='Version string for the output (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    # Set default output path
    output_file = args.output or args.input_file.with_suffix('.qa.json')
    
    # Extract QA pairs
    extract_qa_to_json(args.input_file, output_file, version=args.version)


if __name__ == '__main__':
    main()