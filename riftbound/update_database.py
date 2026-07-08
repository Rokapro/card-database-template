import sqlite3
import time
from pathlib import Path

import requests

API_BASE = "https://api.riftcodex.com"
DB_PATH = Path(__file__).parent / "card-data.db"
SETS = ["OGN", "SFD", "UNL"]  # Manually define sets as a fallback


def get_all_sets():
    """Fetch all sets from the API."""
    try:
        response = requests.get(f"{API_BASE}/sets", timeout=10)
        response.raise_for_status()
        sets_data = response.json().get("items", [])
        return [s["set_id"] for s in sets_data]
    except requests.RequestException as e:
        print(f"Could not fetch sets from API: {e}. Using fallback list: {SETS}")
        return SETS


def get_cards_for_set(set_id):
    """Fetch all cards for a given set."""
    cards = []
    page = 1
    while True:
        try:
            params = {"set_id": set_id, "page": page, "size": 100}
            print(f"Fetching page {page} for set {set_id}...")
            response = requests.get(f"{API_BASE}/cards", params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            page_cards = data.get("items", [])
            if not page_cards:
                break
            cards.extend(page_cards)
            page += 1
            time.sleep(0.5)  # Respectful API polling
        except requests.RequestException as e:
            print(f"Error fetching cards for set {set_id} on page {page}: {e}")
            break
    return cards


def create_database_table(conn):
    """Create the cards table, dropping it if it exists."""
    cursor = conn.cursor()
    print("Creating 'cards' table...")
    cursor.execute("DROP TABLE IF EXISTS cards")
    cursor.execute("""
        CREATE TABLE cards (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            set_id TEXT NOT NULL,
            set_name TEXT,
            collector_number INTEGER,
            type TEXT,
            domain TEXT,
            alternate_art BOOLEAN,
            overnumbered BOOLEAN,
            image_url TEXT,
            rarity TEXT
        )
    """)
    conn.commit()
    print("Table 'cards' created successfully.")


def insert_cards_into_db(conn, cards):
    """Insert a list of cards into the database."""
    cursor = conn.cursor()
    print(f"Preparing to insert {len(cards)} cards...")
    cards_to_insert = []
    for card in cards:
        classification = card.get("classification", {})
        metadata = card.get("metadata", {})
        set_data = card.get("set", {})
        media = card.get("media", {})

        card_data = (
            card["id"],
            card.get("name"),
            set_data.get("set_id"),
            set_data.get("label"),
            card.get("collector_number"),
            classification.get("type"),
            "&".join(classification.get("domain", [])),
            metadata.get("alternate_art", False),
            metadata.get("overnumbered", False),
            media.get("image_url"),
            classification.get("rarity"),
        )
        cards_to_insert.append(card_data)

    cursor.executemany(
        """
        INSERT OR REPLACE INTO cards (
            id, name, set_id, set_name, collector_number, type, domain, 
            alternate_art, overnumbered, image_url, rarity
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        cards_to_insert,
    )
    conn.commit()
    print(f"Successfully inserted/replaced {len(cards_to_insert)} cards.")


def main():
    """Main function to update the database."""
    print("Starting card database update...")
    all_cards = []

    # It's more efficient to get all cards at once if the API supports it
    # The /cards endpoint seems to list all cards, paginated.
    page = 1
    while True:
        try:
            params = {"page": page, "size": 100}
            print(f"Fetching all cards, page {page}...")
            response = requests.get(f"{API_BASE}/cards", params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            page_cards = data.get("items", [])
            if not page_cards:
                break
            all_cards.extend(page_cards)
            if len(page_cards) < 100:  # Last page
                break
            page += 1
            time.sleep(0.5)
        except requests.RequestException as e:
            print(f"Error fetching all cards on page {page}: {e}")
            break

    if not all_cards:
        print("No cards fetched. Attempting set-by-set.")
        # Fallback to fetching set by set if getting all cards fails
        sets = get_all_sets()
        for set_id in sets:
            print(f"--- Processing Set: {set_id} ---")
            cards = get_cards_for_set(set_id)
            all_cards.extend(cards)
            print(f"Found {len(cards)} cards in {set_id}.")

    if all_cards:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                create_database_table(conn)
                insert_cards_into_db(conn, all_cards)
            print("\nDatabase update complete!")
        except sqlite3.Error as e:
            print(f"\nAn error occurred with the database: {e}")
    else:
        print("\nCould not fetch any card data. Database not updated.")


if __name__ == "__main__":
    main()
