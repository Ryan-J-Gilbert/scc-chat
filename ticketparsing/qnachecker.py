import json
import argparse
from pathlib import Path


def extract_qa_to_text(input_file: Path, output_file: Path, skip_field: str = 'skip'):
    """
    Extract all QA pairs from JSONL to a simple text format.
    
    Format:
    QUESTION
    ANSWER
    [blank line]
    ...
    
    Args:
        input_file: Path to input JSONL file
        output_file: Path to output text file
        skip_field: Field name to check if entry should be skipped
    """
    total_pairs = 0
    skipped_entries = 0
    
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
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
                qa_pairs = result.get('qa_pairs', [])
                if qa_pairs is None:
                    print("NONE!", line_num)
                    continue
                
                # Write each QA pair
                for qa_pair in qa_pairs:
                    question = qa_pair.get('question', '').strip()
                    answer = qa_pair.get('answer', '').strip()
                    
                    if question and answer:
                        outfile.write(f"{question}\n")
                        outfile.write(f"{answer}\n")
                        outfile.write("\n")
                        total_pairs += 1
                
            except json.JSONDecodeError as e:
                print(f"Warning: Line {line_num}: JSON decode error - {e}")
                continue
            except Exception as e:
                print(f"Error on line {line_num}: {e}")
                raise
    
    print(f"\nExtraction complete!")
    print(f"Total QA pairs extracted: {total_pairs}")
    print(f"Skipped entries: {skipped_entries}")
    print(f"Output file: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract all QA pairs from JSONL to simple text format for manual review'
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
        help='Output text file path (default: input_file.qa.txt)'
    )
    
    args = parser.parse_args()
    
    # Set default output path
    output_file = args.output or args.input_file.with_suffix('.qa.txt')
    
    # Extract QA pairs
    extract_qa_to_text(args.input_file, output_file)


if __name__ == '__main__':
    main()
