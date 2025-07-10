##!/usr/bin/env python3
"""
Test script to debug ChromaDB memory issues in Docker
"""
import os
import sys
from pathlib import Path
import asyncio

# Add current directory to path so we can import from server.py
sys.path.insert(0, str(Path(__file__).parent))


def test_memory_system():
    print("🧪 Testing memory system...")

    # Import here to avoid path issues
    try:
        from server import memory

        print("✓ Successfully imported memory system")
    except Exception as e:
        print(f"✗ Failed to import memory system: {e}")
        return False

    # Test 1: Add memory
    print("\n1. Testing memory addition...")
    try:
        idx = memory.add("Test memory: user loves diamonds")
        print(f"✓ Added memory with index: {idx}")
    except Exception as e:
        print(f"✗ Failed to add memory: {e}")
        return False

    # Test 2: Query memory directly using the MemoryStore
    print("\n2. Testing memory query...")
    try:
        # Query directly through the memory store
        print("   Generating embedding for 'diamond'...")
        vec = memory._embed("diamond")
        print(f"   ✓ Generated embedding (dim: {len(vec)})")

        collection_count = memory.col.count()
        print(f"   Collection has {collection_count} items")

        if collection_count == 0:
            print("   No memories in collection")
        else:
            k = min(3, collection_count)
            print(f"   Querying for top {k} matches...")

            hits = memory.col.query(
                query_embeddings=[vec], n_results=k, include=["metadatas", "distances"]
            )

            if hits["metadatas"] and hits["metadatas"][0]:
                print(f"✓ Query results: {len(hits['metadatas'][0])} items")
                for i, (m, d) in enumerate(
                    zip(hits["metadatas"][0], hits["distances"][0])
                ):
                    relevance = max(0.0, 1 - d)
                    print(f"   {i+1}. {m['text'][:50]}... (relevance: {relevance:.3f})")
            else:
                print("   No results found")
    except Exception as e:
        print(f"✗ Failed to query memory: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 3: Check database files
    print("\n3. Checking database files...")
    db_path = memory.db_path
    if db_path.exists():
        print(f"✓ Database directory exists: {db_path}")

        # Check permissions
        try:
            import stat

            st = os.stat(db_path)
            mode = stat.filemode(st.st_mode)
            print(f"   Permissions: {mode}, Owner: {st.st_uid}:{st.st_gid}")
        except:
            pass

        files = list(db_path.iterdir())
        print(f"   Files: {[f.name for f in files]}")

        # Check if we can write
        try:
            test_file = db_path / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            print("   ✓ Directory is writable")
        except Exception as e:
            print(f"   ✗ Directory is not writable: {e}")
    else:
        print(f"✗ Database directory missing: {db_path}")

    # Test 4: ChromaDB collection info
    print("\n4. ChromaDB collection info...")
    try:
        count = memory.col.count()
        print(f"✓ Collection has {count} items")

        # Show a few recent memories
        if count > 0:
            print("\n5. Recent memories:")
            all_items = memory.col.get(limit=5, include=["metadatas"])
            if all_items["metadatas"]:
                for i, meta in enumerate(all_items["metadatas"][:5]):
                    print(f"   #{meta.get('idx', '?')}: {meta['text'][:60]}...")
    except Exception as e:
        print(f"✗ Failed to get collection info: {e}")

    # Test 5: Test the get method
    print("\n6. Testing memory retrieval by index...")
    try:
        if idx >= 0:  # From test 1
            retrieved = memory.get(idx)
            if retrieved:
                print(f"✓ Retrieved memory #{idx}: {retrieved[:50]}...")
            else:
                print(f"✗ Could not retrieve memory #{idx}")
    except Exception as e:
        print(f"✗ Failed to retrieve memory: {e}")

    return True


if __name__ == "__main__":
    success = test_memory_system()
    if success:
        print("\n🎉 Memory system test completed!")
    else:
        print("\n💥 Memory system test failed!")
        sys.exit(1)
