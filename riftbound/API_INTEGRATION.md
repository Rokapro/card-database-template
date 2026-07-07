# Riftcodex API Integration Guide

## Quick Start

The new `cardadd-api.py` script lets you add cards much faster by searching the Riftcodex API instead of entering data manually.

```bash
python3 cardadd-api.py
```

## Features

- **Search by card name**: Find cards instantly from the Riftcodex database
- **Auto-populate fields**: All card details are filled automatically
- **Image download**: Card images are automatically downloaded and converted to AVIF format
- **Bulk-friendly**: Add multiple cards in one session
- **Customizable**: Modify colors, types, or set before saving

## How It Works

1. **Select a set** (or search across all sets)
2. **Search for a card** by name
3. **Choose from results** - the script shows up to 10 matches
4. **Review details** - card type, color, rarity, etc.
5. **Optionally customize** - change color, type, or other details
6. **Confirm and save** - image downloads automatically

## Comparison: Manual vs API

### Manual (old way)
```
python3 cardadd-sfd.py
→ Enter color
→ Enter type
→ Enter card name
→ Manually add image file
→ Repeat for each card
```

### API Integration (new way)
```
python3 cardadd-api.py
→ Pick set
→ Search card name
→ Select from results
→ Confirm
→ Done! (images auto-download)
```

## Set Codes

Available sets from Riftcodex:
- `SFD` - Spiritforged
- `OGN` - Origins
- `UNL` - Unleashed
- `VEN` - Vendetta
- `OGS` - Origins: Proving Grounds
- And others...

## Features Comparison

| Feature | cardadd.py | cardadd-api.py |
|---------|-----------|-----------------|
| Manual entry | ✓ | ✗ |
| Search by name | ✗ | ✓ |
| Auto image download | ✗ | ✓ |
| Auto populate type | ✗ | ✓ |
| Auto populate color | ✗ | ✓ |
| Handle alt art | ✗ | ✓ |
| Handle overnumbered | ✗ | ✓ |

## Troubleshooting

**"No cards found"**: The search is case-insensitive but looks for exact name matches. Try just the first word.

**"Image download failed"**: The card will still be added. You can manually add the image later.

**"Connection error"**: Check your internet connection. The API requires network access.

## Image Format

Images are automatically:
- Downloaded from Riftcodex
- Converted to AVIF format
- Named correctly (e.g., `card-name-sfd.avif`)
- Saved to `riftbound-images/`

## Dependencies

- `requests` - for API calls
- `pillow` - for image conversion

These are automatically installed when needed.
