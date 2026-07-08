import csv
import re
import sqlite3
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

CSV_PATH = Path(__file__).parent / "cards.csv"
DB_PATH = Path(__file__).parent / "card-data.db"
IMAGES_PATH = Path(__file__).parent.parent / "riftbound-images"
HEADER = ["name", "set", "quantity", "type", "color", "altArt", "overnumbered", "image"]

# Mappings from DB to CSV format
COLOR_MAPPING = {
    "calm": "CALM",
    "fury": "FURY",
    "mind": "MIND",
    "body": "BODY",
    "chaos": "CHAOS",
    "order": "ORDER",
}
TYPE_MAPPING = {
    "unit": "UNIT",
    "spell": "SPELL",
    "rune": "RUNE",
    "gear": "GEAR",
    "battlefield": "BATTLEFIELD",
    "landmark": "BATTLEFIELD",
}


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def normalize_db_color_input(domains: str) -> str:
    """Convert domain string from DB to our color format"""
    if not domains:
        return "NONE"
    domain_list = domains.split("&")
    colors = [
        COLOR_MAPPING.get(d.lower())
        for d in domain_list
        if COLOR_MAPPING.get(d.lower())
    ]
    return "&".join(sorted(list(set(colors)))) or "NONE"


def load_cards() -> list[dict[str, str]]:
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=HEADER)
            writer.writeheader()
        return []
    with CSV_PATH.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        # Filter out empty rows
        return [row for row in reader if any(row.values())]


def save_cards(cards: list[dict[str, str]]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(cards)


def normalize_card_key(card: dict[str, str]) -> tuple[str, str, str, str, str, str]:
    return (
        (card.get("name", "") or "").strip().lower(),
        (card.get("set", "") or "").strip().lower(),
        (card.get("type", "") or "").strip().lower(),
        (card.get("color", "") or "").strip().lower(),
        str(card.get("altArt", "false")).strip().lower(),
        str(card.get("overnumbered", "false")).strip().lower(),
    )


def find_existing_card_index(
    cards: list[dict[str, str]], new_card: dict[str, str]
) -> int | None:
    new_key = normalize_card_key(new_card)
    for index, card in enumerate(cards):
        if normalize_card_key(card) == new_key:
            return index
    return None


def build_image_filename(
    name: str, set_code: str, alt_art: bool, overnumbered: bool
) -> str:
    image = f"{slugify(name)}-{slugify(set_code)}"
    if alt_art:
        image += "-a"
    if overnumbered:
        image += "-o"
    return f"{image}.avif"


def search_db_for_card(search_term: str) -> list[dict]:
    """Search the database for cards with a name matching the search term."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Use LIKE for partial matching
            cursor.execute(
                "SELECT * FROM cards WHERE name LIKE ?", (f"%{search_term}%",)
            )
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []


def download_and_convert_image(image_url: str, output_path: Path) -> bool:
    """Download image from URL and convert to AVIF"""
    if not image_url:
        print("  ✗ No image URL provided.")
        return False

    if output_path.exists():
        print(f"  ✓ Image already exists: {output_path.name}")
        return True

    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))
        # Handle transparency for PNGs
        if img.mode in ("RGBA", "LA", "P"):
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(
                img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None
            )
            img = rgb_img

        output_path.parent.mkdir(exist_ok=True)
        img.save(output_path, format="AVIF", quality=85)
        print(f"  ✓ Downloaded and converted image: {output_path.name}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to download or convert image: {e}")
        return False


def add_card():
    """Handler to search for a card and add it to the collection."""
    search_term = input("Enter card name to search: ").strip()
    if not search_term:
        print("Search term cannot be empty.")
        return

    results = search_db_for_card(search_term)

    if not results:
        print(f"No card found with the name '{search_term}'.")
        return

    print("Found matching cards:")
    for i, card in enumerate(results):
        collector_info = (
            f" #{card['collector_number']}" if card.get("collector_number") else ""
        )
        print(
            f"  {i + 1}: {card['name']} ({card['set_id']}{collector_info}) - {card['type']}"
        )

    while True:
        try:
            choice = (
                input("Select a card to add (number), or 'c' to cancel: ")
                .strip()
                .lower()
            )
            if choice == "c":
                return
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(results):
                selected_card = results[selected_index]
                break
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    card_type = TYPE_MAPPING.get(
        selected_card.get("type", "").lower(), selected_card.get("type", "").upper()
    )
    card_color = normalize_db_color_input(selected_card.get("domain", ""))
    alt_art = bool(selected_card.get("alternate_art", False))
    overnumbered = bool(selected_card.get("overnumbered", False))

    while True:
        try:
            quantity_to_add = int(input("Enter quantity to add (1 or more): ").strip())
            if quantity_to_add >= 1:
                break
            else:
                print("Quantity must be 1 or more.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    new_card = {
        "name": selected_card["name"],
        "set": selected_card["set_id"],
        "quantity": str(quantity_to_add),
        "type": card_type,
        "color": card_color,
        "altArt": str(alt_art).lower(),
        "overnumbered": str(overnumbered).lower(),
        "image": build_image_filename(
            selected_card["name"], selected_card["set_id"], alt_art, overnumbered
        ),
    }

    cards = load_cards()
    existing_index = find_existing_card_index(cards, new_card)

    if existing_index is not None:
        existing_card = cards[existing_index]
        quantity = int(existing_card.get("quantity", "0") or "0") + quantity_to_add
        existing_card["quantity"] = str(quantity)
        print(
            f"Updated quantity for {existing_card['name']} ({existing_card['set']}). New quantity: {quantity}"
        )
    else:
        # This is a new card, so we download the image.
        image_url = selected_card.get("image_url")
        image_path = IMAGES_PATH / new_card["image"]

        if download_and_convert_image(image_url, image_path):
            cards.append(new_card)
            print(f"Added new card: {new_card['name']} ({new_card['set']})")
        else:
            print(
                f"Skipping adding card {new_card['name']} due to image download failure."
            )
            return  # Stop if image fails

    save_cards(cards)


def remove_card():
    """Handler to search for a card in the collection and remove it."""
    search_term = input("Enter card name to remove: ").strip()
    if not search_term:
        print("Search term cannot be empty.")
        return

    all_cards = load_cards()
    # Find all cards in the collection that match the search term, case-insensitively
    matching_cards = [
        card
        for card in all_cards
        if search_term.lower() in card.get("name", "").lower()
    ]

    if not matching_cards:
        print(f"No card found in your collection with the name '{search_term}'.")
        return

    print("Found matching cards in your collection:")
    for i, card in enumerate(matching_cards):
        print(
            f"  {i + 1}: {card['name']} ({card['set']}) - Quantity: {card['quantity']}"
        )

    while True:
        try:
            choice = (
                input("Select a card to remove (number), or 'c' to cancel: ")
                .strip()
                .lower()
            )
            if choice == "c":
                return
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(matching_cards):
                card_to_remove = matching_cards[selected_index]
                break
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    current_quantity = int(card_to_remove.get("quantity", "0") or "0")

    while True:
        try:
            quantity_to_remove_str = (
                input(f"How many to remove (1-{current_quantity}), or 'all': ")
                .strip()
                .lower()
            )
            if quantity_to_remove_str == "all":
                quantity_to_remove = current_quantity
                break

            quantity_to_remove = int(quantity_to_remove_str)
            if 1 <= quantity_to_remove <= current_quantity:
                break
            else:
                print(f"Please enter a number between 1 and {current_quantity}.")
        except ValueError:
            print("Invalid input. Please enter a number or 'all'.")

    # Find the original card in the main list to modify/remove it
    # This is safer than modifying the `matching_cards` subset
    for i, card in enumerate(all_cards):
        if normalize_card_key(card) == normalize_card_key(card_to_remove):
            new_quantity = current_quantity - quantity_to_remove
            if new_quantity > 0:
                all_cards[i]["quantity"] = str(new_quantity)
                print(
                    f"Removed {quantity_to_remove}x {card['name']}. New quantity: {new_quantity}"
                )
            else:
                del all_cards[i]
                print(
                    f"Removed all {quantity_to_remove}x {card['name']} from collection."
                )
            break  # Exit loop once card is found and handled

    save_cards(all_cards)


def main_menu():
    """Display the main menu and handle user choices."""
    while True:
        print("--- Collection Manager ---")
        print("1. Add Card")
        print("2. Remove Card")
        print("3. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_card()
        elif choice == "2":
            remove_card()
        elif choice == "3":
            print("Exiting.")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main_menu()
