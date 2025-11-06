import json
import sys
import os

def load_jsonl(filename):
    with open(filename, "r") as f:
        return [json.loads(line) for line in f]

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def render_ticket(ticket, idx, total):
    ticket_num = ticket.get('ticket_number', 'N/A')
    result = ticket.get('result', {})
    skip = result.get('skip', None)
    category = result.get('category', None)
    technical_summary = result.get('technical_summary', None)
    resolution_steps = result.get('resolution_steps', None)
    elapsed = ticket.get('elapsed', None)

    header = f"Ticket {idx+1}/{total} | {ticket_num} | {'SKIP' if skip else 'PROCESS'}"
    print("="*len(header))
    print(header)
    print("="*len(header))
    print(f"Category: {category}")
    print(f"Summary: {technical_summary}")
    print("Resolution Steps:")
    if resolution_steps:
        for step in resolution_steps:
            print(f"- {step}")
    else:
        print("None")
    print(f"\nElapsed: {elapsed}s")

def main(filename):
    tickets = load_jsonl(filename)
    idx = 0
    total = len(tickets)

    while True:
        clear()
        render_ticket(tickets[idx], idx, total)
        print("\n[n] next | [p] previous | [q] quit")
        choice = input("Choice: ").strip().lower()
        if choice == "n" and idx < total-1:
            idx += 1
        elif choice == "p" and idx > 0:
            idx -= 1
        elif choice == "q":
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python resultviewer.py <file.jsonl>")
    else:
        main(sys.argv[1])