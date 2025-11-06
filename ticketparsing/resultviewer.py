import json
import sys
import os

# Configuration: Set to False to view all tickets including already labeled ones
SKIP_LABELED_TICKETS = True

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

def filter_unlabeled_tickets(tickets, accepted_ids, rejected_ids):
    """Filter out tickets that have already been labeled"""
    if not SKIP_LABELED_TICKETS:
        return tickets
    
    labeled_ids = accepted_ids | rejected_ids
    unlabeled = [t for t in tickets if t.get('ticket_number', 'N/A') not in labeled_ids]
    return unlabeled

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def render_ticket(ticket, idx, total, accepted_ids, rejected_ids, showing_filtered, unsaved_changes):
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

    filter_note = " (unlabeled only)" if showing_filtered else " (all tickets)"
    unsaved_note = f" * {unsaved_changes} unsaved" if unsaved_changes > 0 else ""
    header = f"Ticket {idx+1}/{total}{filter_note} | {ticket_num} | {'SKIP' if skip else 'PROCESS'}{status}{unsaved_note}"
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
    all_tickets = load_jsonl(filename)
    
    # Load existing results
    accepted_ids, rejected_ids = load_existing_results()
    
    # Filter tickets based on configuration
    tickets = filter_unlabeled_tickets(all_tickets, accepted_ids, rejected_ids)
    
    # Display filtering info
    if SKIP_LABELED_TICKETS:
        skipped_count = len(all_tickets) - len(tickets)
        print(f"Loaded {len(all_tickets)} total tickets")
        print(f"Skipping {skipped_count} already labeled tickets ({len(accepted_ids)} accepted, {len(rejected_ids)} rejected)")
        print(f"Showing {len(tickets)} unlabeled tickets")
        if len(tickets) == 0:
            print("\nAll tickets have been labeled! Set SKIP_LABELED_TICKETS = False to review all tickets.")
            return
        input("\nPress Enter to continue...")
    else:
        print(f"Loaded {len(all_tickets)} tickets (showing all, including {len(accepted_ids)} accepted and {len(rejected_ids)} rejected)")
        input("\nPress Enter to continue...")
    
    idx = 0
    total = len(tickets)
    unsaved_changes = 0

    while True:
        clear()
        render_ticket(tickets[idx], idx, total, accepted_ids, rejected_ids, SKIP_LABELED_TICKETS, unsaved_changes)
        print("\n[A] Accept | [S] Reject | [n] next | [p] previous | [w] save | [q] quit")
        choice = input("Choice: ").strip().lower()
        
        ticket_num = tickets[idx].get('ticket_number', 'N/A')
        
        if choice == "a":
            # Accept ticket
            accepted_ids.add(ticket_num)
            rejected_ids.discard(ticket_num)  # Remove from rejected if it was there
            unsaved_changes += 1
            # Auto-advance to next ticket
            if idx < total - 1:
                idx += 1
        elif choice == "s":
            # Reject ticket
            rejected_ids.add(ticket_num)
            accepted_ids.discard(ticket_num)  # Remove from accepted if it was there
            unsaved_changes += 1
            # Auto-advance to next ticket
            if idx < total - 1:
                idx += 1
        elif choice == "w":
            # Save results
            save_results(accepted_ids, rejected_ids)
            unsaved_changes = 0
            print("✓ Results saved!")
            input("Press Enter to continue...")
        elif choice == "n" and idx < total-1:
            idx += 1
        elif choice == "p" and idx > 0:
            idx -= 1
        elif choice == "q":
            if unsaved_changes > 0:
                print(f"\nYou have {unsaved_changes} unsaved changes.")
                confirm = input("Save before quitting? [y/n]: ").strip().lower()
                if confirm == 'y':
                    save_results(accepted_ids, rejected_ids)
                    print("✓ Results saved!")
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python resultviewer.py <file.jsonl>")
    else:
        main(sys.argv[1])