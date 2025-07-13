#!/usr/bin/env python3
"""
Pytest version of core memory functionality tests
Combines best parts of test_memory.py and test_deep_analysis.py
"""
import pytest
from pathlib import Path


@pytest.mark.core
def test_memory_addition(clean_test_memory):
    """Test that memories can be added successfully"""
    memory = clean_test_memory
    
    idx = memory.add("Test memory: user loves diamonds")
    assert idx >= 0, "Memory addition should return valid index"
    
    # Verify memory was stored
    assert memory.next_index > idx, "Next index should be incremented"


@pytest.mark.core  
def test_memory_retrieval(clean_test_memory):
    """Test that memories can be retrieved by index"""
    memory = clean_test_memory
    
    test_content = "Test memory: user loves diamonds"
    idx = memory.add(test_content)
    
    retrieved = memory.get(idx)
    assert retrieved == test_content, "Retrieved memory should match stored content"


@pytest.mark.core
def test_memory_retrieval_nonexistent(clean_test_memory):
    """Test retrieval of non-existent memory returns None"""
    memory = clean_test_memory
    
    result = memory.get(999)  # Non-existent index
    assert result is None, "Non-existent memory should return None"


@pytest.mark.core
def test_embedding_generation(clean_test_memory):
    """Test that embeddings are generated correctly"""
    memory = clean_test_memory
    
    vec = memory._embed("diamond")
    assert len(vec) == 1536, "Should generate 1536-dimensional embedding"
    assert all(isinstance(x, float) for x in vec), "Embedding should be list of floats"


@pytest.mark.core
def test_basic_semantic_search(sample_test_memory):
    """Test basic semantic search functionality"""
    memory = sample_test_memory
    
    # Should find the diamond memory
    results = memory.query("diamond", k=1)
    assert len(results) > 0, "Should find at least one result"
    assert "diamond" in results[0]["text"].lower(), "Should find diamond-related memory"
    assert results[0]["relevance"] > 0.3, "Should have reasonable relevance score"


@pytest.mark.core
def test_case_preservation_in_search(sample_test_memory):
    """Test that case preservation affects search results (from test_deep_analysis.py)"""
    memory = sample_test_memory
    
    # Query with different cases
    result_upper = memory.query("Fallujah", k=1)[0]
    result_lower = memory.query("fallujah", k=1)[0] 
    
    # Should get different relevance scores due to case preservation
    assert abs(result_upper["relevance"] - result_lower["relevance"]) > 0.05, \
        "Case preservation should affect relevance scores"


@pytest.mark.core 
def test_high_quality_semantic_search(sample_test_memory):
    """Test that semantic search achieves high relevance scores (from test_deep_analysis.py)"""
    memory = sample_test_memory
    
    # Test queries with high overlap to the stored memory
    high_overlap_queries = [
        "User confesses killed",  # Many words from original
        "man M14 rifle Fallujah",  # Key terms  
        "confesses killed man M14 rifle"  # High overlap
    ]
    
    for query in high_overlap_queries:
        results = memory.query(query, k=1)
        assert len(results) > 0, f"Should find results for query: {query}"
        
        # Expect good to excellent relevance scores
        relevance = results[0]["relevance"]
        assert relevance > 0.5, f"Query '{query}' should have high relevance (got {relevance:.3f})"


@pytest.mark.core
def test_excellent_relevance_threshold(sample_test_memory):
    """Test that the memory fixes achieve excellent relevance scores"""
    memory = sample_test_memory
    
    # This specific query should achieve excellent relevance (>0.8)
    # This proves the Phase 0 fixes are working
    results = memory.query("confesses killed man M14 rifle Fallujah Iraq combat", k=1)
    
    assert len(results) > 0, "Should find results for comprehensive query"
    assert results[0]["relevance"] > 0.8, \
        f"Comprehensive query should achieve excellent relevance (got {results[0]['relevance']:.3f})"


@pytest.mark.core
def test_database_files_exist(clean_test_memory):
    """Test that database files are created correctly"""
    memory = clean_test_memory
    
    # Add a memory to ensure database is initialized
    memory.add("Test memory for database check")
    
    # Check database directory exists
    assert memory.db_path.exists(), "Database directory should exist"
    
    # Check for key files
    files = list(memory.db_path.iterdir())
    file_names = [f.name for f in files]
    
    assert "id_map.json" in file_names, "Should have id_map.json file"
    assert "chroma.sqlite3" in file_names, "Should have ChromaDB SQLite file"


@pytest.mark.core 
def test_database_write_permissions(clean_test_memory):
    """Test that database directory is writable"""
    memory = clean_test_memory
    
    # Try to write a test file
    test_file = memory.db_path / ".write_test"
    test_file.write_text("test")
    
    assert test_file.exists(), "Should be able to write test file"
    
    # Clean up
    test_file.unlink()


@pytest.mark.core
def test_collection_info(sample_test_memory):
    """Test ChromaDB collection information"""
    memory = sample_test_memory
    
    count = memory.col.count()
    assert count > 0, "Collection should have memories"
    assert count == 3, "Sample memory should have exactly 3 test memories"


@pytest.mark.core
def test_memory_index_mapping(clean_test_memory):
    """Test that memory index mapping works correctly"""
    memory = clean_test_memory
    
    # Add multiple memories
    idx1 = memory.add("First memory")
    idx2 = memory.add("Second memory") 
    
    assert idx2 == idx1 + 1, "Indices should be sequential"
    
    # Check id_map
    assert idx1 in memory.id_map, "First index should be in id_map"
    assert idx2 in memory.id_map, "Second index should be in id_map"
    
    # Verify we can retrieve both
    assert memory.get(idx1) == "First memory"
    assert memory.get(idx2) == "Second memory" 