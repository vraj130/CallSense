#!/usr/bin/env python3
"""
Debug script to test state manager functionality
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.state_manager import StateManager
from utils.models import TranscriptEntry, Speaker


async def test_state_manager():
    """Test the state manager functionality"""
    print("=== Testing State Manager ===")

    # Create state manager
    state_manager = StateManager()

    # Test 1: Check initial state
    print(
        f"Initial transcript length: {len(state_manager.get_state().transcript)}"
    )

    # Test 2: Add a transcript entry
    test_entry = TranscriptEntry(
        speaker=Speaker.CUSTOMER,
        text="Hello, this is a test message",
        timestamp=datetime.now(),
    )

    print("Adding test entry...")
    await state_manager.add_transcript_entry(test_entry)

    # Test 3: Check state after adding
    state_after = state_manager.get_state()
    print(f"Transcript length after adding: {len(state_after.transcript)}")

    if state_after.transcript:
        last_entry = state_after.transcript[-1]
        print(f"Last entry: {last_entry.speaker.value}: {last_entry.text}")

    # Test 4: Add multiple entries
    for i in range(3):
        entry = TranscriptEntry(
            speaker=Speaker.CUSTOMER if i % 2 == 0 else Speaker.AGENT,
            text=f"Test message {i+1}",
            timestamp=datetime.now(),
        )
        await state_manager.add_transcript_entry(entry)

    final_state = state_manager.get_state()
    print(f"Final transcript length: {len(final_state.transcript)}")

    print("\nAll entries:")
    for i, entry in enumerate(final_state.transcript):
        print(f"  {i+1}: {entry.speaker.value}: {entry.text}")

    print("=== State Manager Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_state_manager())
