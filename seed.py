"""Seed the synthetic AcmeDesk history into Hindsight.
Run once after creating .env:  python seed.py
"""
import data
import memory

def main():
    print("Seeding customer banks...")
    for cid, customer in data.CUSTOMERS.items():
        bank=memory.customer_bank_id(cid)
        memory.ensure_bank(bank, mission="Private support history for one AcmeDesk customer: issues, attempted fixes, outcomes and preferences.")
        for ticket in data.TICKETS.get(cid, []):
            content=memory.format_ticket(customer["name"], ticket)
            memory.retain(bank, content, "seeded customer support ticket outcome", when=ticket["when"])
        print(f"  Seeded {customer['name']}: {len(data.TICKETS.get(cid, []))} tickets")
    print("Seeding shared playbook...")
    memory.ensure_bank(memory.PLAYBOOK_BANK, mission="Anonymized AcmeDesk support outcomes used to identify fixes that work or fail across similar cases.")
    for ticket in data.PLAYBOOK:
        memory.retain(memory.PLAYBOOK_BANK, memory.format_playbook(ticket), "seeded anonymized resolution record", when=ticket["when"])
    print(f"  Seeded playbook: {len(data.PLAYBOOK)} records")
    print("\nDone. Do not run seed.py repeatedly unless you intentionally want duplicate records.")

if __name__ == "__main__":
    main()
