#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_memory_deep_analysis():
    print(' Deep Analysis of Memory Fixes')
    print('=' * 50)
    
    from server import create_test_memory_store
    memory = create_test_memory_store()
    
    # Add test memory 
    test_memory = 'User confesses: killed a man with M14 rifle in Fallujah, Iraq during combat'
    memory_idx = memory.add(test_memory)
    print(f'Added: {test_memory}')
    
    # Test case preservation (this should show the fix working)
    print(f'\n Testing case preservation:')
    result1 = memory.query('Fallujah', k=1)[0]
    result2 = memory.query('fallujah', k=1)[0]
    
    print(f'  "Fallujah"  {result1["relevance"]:.3f} (distance: {result1["distance"]:.3f})')
    print(f'  "fallujah"  {result2["relevance"]:.3f} (distance: {result2["distance"]:.3f})')
    
    if abs(result1['relevance'] - result2['relevance']) > 0.05:
        print('   Case preservation working - different scores for different cases')
    else:
        print('   Case preservation not working - scores too similar')
    
    # Test exact phrase matching
    print(f'\n Testing exact phrase matching:')
    phrases = [
        'killed a man',
        'M14 rifle', 
        'Fallujah Iraq',
        'during combat'
    ]
    
    for phrase in phrases:
        result = memory.query(phrase, k=1)[0]
        print(f'  "{phrase}"  {result["relevance"]:.3f} (distance: {result["distance"]:.3f})')
    
    # Test what makes a good match
    print(f'\n Testing for higher relevance scores:')
    high_overlap_queries = [
        'User confesses killed',  # Many words from original
        'man M14 rifle Fallujah',  # Key terms
        'confesses killed man M14 rifle Fallujah Iraq combat'  # Almost exact
    ]
    
    for query in high_overlap_queries:
        result = memory.query(query, k=1)[0]
        status = 'EXCELLENT' if result['relevance'] >= 0.8 else ('GOOD' if result['relevance'] >= 0.6 else 'OKAY' if result['relevance'] >= 0.4 else 'POOR')
        print(f'  "{query[:30]}..."  {result["relevance"]:.3f} - {status}')

if __name__ == '__main__':
    test_memory_deep_analysis()
