#!/usr/bin/env python3
"""
Phase 3: Cleanup Production Memory Database
==========================================

Simple utility to remove test data contamination from production memory.
Focuses on the main contamination patterns we identified.
"""

import os
import sys
import json
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def cleanup_old_backups(db_path: Path, keep_count: int = 2):
    """Remove old backup directories, keeping only the most recent ones"""
    backup_pattern = "closer_memory_db_backup_*"
    backup_dirs = list(db_path.parent.glob(backup_pattern))

    if len(backup_dirs) <= keep_count:
        return

    # Sort by timestamp (newest first)
    backup_dirs.sort(key=lambda x: x.name.split("_")[-1], reverse=True)

    # Remove old backups
    for old_backup in backup_dirs[keep_count:]:
        print(f"  Removing old backup: {old_backup.name}")
        shutil.rmtree(old_backup)


def is_test_contamination(text: str) -> bool:
    """
    Simple detection: identify obvious test data patterns
    """
    test_patterns = [
        "test memory",
        "user loves diamonds",
        "test data",
        "testing memory",
        "garbage data",
        "test contamination",
        "memory test",
        "unit test",
        "test case",
    ]

    text_lower = text.lower()
    return any(pattern in text_lower for pattern in test_patterns)


def main():
    """
    5-Step Cleanup Process
    """
    print("🧹 Phase 3: Production Memory Cleanup")
    print("=" * 50)

    # Step 1: Connect to production database
    print("\n1. Connecting to production database...")
    try:
        from server import create_production_memory_store

        memory = create_production_memory_store()
        print(f"✓ Connected to: {memory.db_path}")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False

    # Step 2: Identify contamination
    print("\n2. Scanning for contamination...")
    contaminated = []

    # Get all memories from the collection
    try:
        collection = memory.col
        # Get everything from the collection
        all_data = collection.get()

        if not all_data["metadatas"]:
            print("✓ No memories found in database")
            return True

        # Scan through all memories and identify contaminated ones
        for i, metadata in enumerate(all_data["metadatas"]):
            text = metadata.get("text", "")
            if is_test_contamination(text):
                contaminated.append(
                    {
                        "chroma_id": all_data["ids"][i],  # Use ChromaDB's internal ID
                        "idx": metadata.get("idx"),
                        "text": text[:100] + "..." if len(text) > 100 else text,
                    }
                )

        print(f"✓ Found {len(contaminated)} contaminated memories")

        # Show examples
        if contaminated:
            print("\nContamination examples:")
            for i, item in enumerate(contaminated[:5]):
                print(f"  {i+1}. {item['text']}")

    except Exception as e:
        print(f"✗ Error scanning database: {e}")
        return False

    # Step 3: Backup database
    print("\n3. Creating backup...")
    try:
        backup_path = (
            memory.db_path.parent / f"closer_memory_db_backup_{int(time.time())}"
        )
        shutil.copytree(memory.db_path, backup_path)
        print(f"✓ Backup created: {backup_path}")

        # Clean up old backups
        cleanup_old_backups(memory.db_path)

    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return False

    # Step 4: Remove contamination
    if not contaminated:
        print("\n4. ✓ No contamination to remove")
        return True

    print(f"\n4. Removing {len(contaminated)} contaminated memories...")

    # Confirm before deletion
    confirm = input(f"Remove {len(contaminated)} contaminated memories? (y/N): ")
    if confirm.lower() != "y":
        print("✗ Cleanup cancelled")
        return False

    try:
        removed_count = 0
        for item in contaminated:
            chroma_id = item["chroma_id"]
            idx = item["idx"]
            print(f"  Removing memory (chroma_id: {chroma_id}, idx: {idx})")

            if chroma_id:
                # Remove from ChromaDB
                memory.col.delete(ids=[chroma_id])
                # Remove from index if it exists
                if idx in memory.id_map:
                    del memory.id_map[idx]
                removed_count += 1
                print(f"    ✓ Removed memory (chroma_id: {chroma_id})")
            else:
                print(f"    ✗ Memory (chroma_id: {chroma_id}) not found")

        # Save updated index
        memory._save_index()
        print(f"✓ Removed {removed_count} contaminated memories")

        # Add a small delay to ensure ChromaDB processes the deletions
        time.sleep(1)

    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 5: Verify cleanup
    print("\n5. Verifying cleanup...")
    try:
        # Re-scan for contamination
        remaining_data = collection.get(include=["metadatas"])
        remaining_contamination = 0
        remaining_items = []

        if remaining_data["metadatas"]:
            for metadata in remaining_data["metadatas"]:
                text = metadata.get("text", "")
                if is_test_contamination(text):
                    remaining_contamination += 1
                    remaining_items.append(
                        {
                            "idx": metadata.get("idx"),
                            "text": text[:100] + "..." if len(text) > 100 else text,
                        }
                    )

        print(f"✓ Remaining contamination: {remaining_contamination}")

        # Show remaining contaminated memories
        if remaining_items:
            print("\nRemaining contaminated memories:")
            for i, item in enumerate(remaining_items):
                print(f"  {i+1}. {item['text']}")

        if remaining_contamination == 0:
            print("✓ Production database is clean!")
            return True
        else:
            print(f"⚠ {remaining_contamination} contaminated memories remain")
            return False

    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False


if __name__ == "__main__":
    success = main()

    if success:
        print("\n🎉 Cleanup completed successfully!")
        print("Production memory database is now clean.")
    else:
        print("\n❌ Cleanup failed!")
        print("Check the backup if needed.")
