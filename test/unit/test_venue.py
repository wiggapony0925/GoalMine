"""
Test script to verify venue matching logic.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.scripts.data import get_venue_info, VENUES_DB


def test_venue_matching():
    """Test various venue name formats."""

    print("🧪 Testing Venue Matching Logic\n")
    print(f"📊 Total venues in database: {len(VENUES_DB)}\n")

    test_cases = [
        # Exact matches
        ("Estadio Azteca, Mexico City", "Should match exactly"),
        ("BC Place, Vancouver", "Should match exactly"),
        # Legacy ID format (with underscores)
        ("Azteca_Mexico", "Legacy format with underscore"),
        ("SoFi_Los_Angeles", "Legacy format with underscores"),
        # Partial matches
        ("Azteca", "Partial stadium name"),
        ("SoFi", "Partial stadium name"),
        ("MetLife", "Partial stadium name"),
        # City matches
        ("Vancouver", "City name only"),
        ("Miami", "City name only"),
        # Edge cases
        ("", "Empty string"),
        ("NonExistentStadium", "Invalid venue"),
        ("estadio azteca", "Lowercase exact"),
    ]

    print("=" * 70)
    for venue_input, description in test_cases:
        matched_key, venue_data = get_venue_info(venue_input)

        status = "✅" if venue_data else "❌"
        print(f"{status} Input: '{venue_input}'")
        print(f"   Description: {description}")
        print(f"   Matched: '{matched_key}'")

        if venue_data:
            print(f"   Elevation: {venue_data.get('elevation')}m")
            print(f"   Timezone: UTC{venue_data.get('tz_offset')}")
            print(f"   June Climate: {venue_data.get('climate_june', {}).get('desc')}")

        print("-" * 70)

    print("\n✅ Venue matching test complete!")


if __name__ == "__main__":
    test_venue_matching()
