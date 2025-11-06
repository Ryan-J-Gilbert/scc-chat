import json
import sys
import os

def load_jsonl(filename):
    with open(filename, "r") as f:
        return [json.loads(line) for line in f]

def save_results(accepted_ids, rejected_ids):
    """Save accepted and rejected ticket IDs to separate files"""
    with open("accepted_tickets.txt", "w") as f:
        for ticket_id in accepted_ids:
            f.write(f"{ticket_id}\n")
    
    with open("rejected_tickets.txt", "w") as f:
        for ticket_id in rejected_ids:
            f.write(f"{ticket_id}\n")

def load_existing_results():
    """Load existing results if files exist"""
    accepted = set()
    rejected = set()
    
    if os.path.exists("accepted_tickets.txt"):
        with open("accepted_tickets.txt", "r") as f:
            accepted = set(line.strip() for line in f if line.strip())
    
    if os.path.exists("rejected_tickets.txt"):
        with open("rejected_tickets.txt", "r") as f:
            rejected = set(line.strip() for line in f if line.strip())
    
    return accepted, rejected

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def render_ticket(ticket, idx, total, accepted_ids, rejected_ids):
    ticket_num = ticket.get('ticket_number', 'N/A')
    result = ticket.get('result', {})
    skip = result.get('skip', None)
    category = result.get('category', None)
    technical_summary = result.get('technical_summary', None)
    resolution_steps = result.get('resolution_steps', None)
    elapsed = ticket.get('elapsed', None)
    
    # Determine current status
    status = ""
    if ticket_num in accepted_ids:
        status = " [ACCEPTED]"
    elif ticket_num in rejected_ids:
        status = " [REJECTED]"

    header = f"Ticket {idx+1}/{total} | {ticket_num} | {'SKIP' if skip else 'PROCESS'}{status}"
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
    
    # Load existing results
    accepted_ids, rejected_ids = load_existing_results()

    while True:
        clear()
        render_ticket(tickets[idx], idx, total, accepted_ids, rejected_ids)
        print("\n[a] Accept | [s] Reject | [n] next | [p] previous | [q] quit")
        choice = input("Choice: ").strip().lower()
        
        ticket_num = tickets[idx].get('ticket_number', 'N/A')
        
        if choice == "a":
            # Accept ticket
            accepted_ids.add(ticket_num)
            rejected_ids.discard(ticket_num)  # Remove from rejected if it was there
            save_results(accepted_ids, rejected_ids)
            # Auto-advance to next ticket
            if idx < total - 1:
                idx += 1
        elif choice == "s":
            # Reject ticket
            rejected_ids.add(ticket_num)
            accepted_ids.discard(ticket_num)  # Remove from accepted if it was there
            save_results(accepted_ids, rejected_ids)
            # Auto-advance to next ticket
            if idx < total - 1:
                idx += 1
        elif choice == "n" and idx < total-1:
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