#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_memory_responsiveness():
    print(' Testing Memory Responsiveness BEFORE Fixes')
    print('=' * 50)
    
    from server import create_test_memory_store
    memory = create_test_memory_store()
    
    test_memory = 'User confesses: killed a man with M14 rifle in Fallujah, Iraq during combat'
    memory_idx = memory.add(test_memory)
    print(f'Added test memory: {test_memory[:50]}...')
    
    test_cases = [
        ('Fallujah', 'Should match Fallujah'),
        ('fallujah', 'Should match fallujah'), 
        ('killing a man', 'Should match exact phrase'),
        ('M14 rifle', 'Should match weapon type'),
    ]
    
    results = []
    for query, description in test_cases:
        print(f'   Testing: {query}')
        query_results = memory.query(query, k=3)
        
        if query_results:
            relevance = query_results[0].get('relevance', 0)
            distance = query_results[0].get('distance', 'N/A')
            status = 'GOOD' if relevance >= 0.6 else ('OKAY' if relevance >= 0.4 else 'POOR')
            print(f'   Result: {relevance:.3f} relevance - {status}')
            results.append((query, relevance, status))
        else:
            print(f'   Result: No matches')
            results.append((query, 0.0, 'FAIL'))
    
    good_count = sum(1 for _, _, status in results if status == 'GOOD')
    print(f'   SUCCESS RATE: {good_count}/{len(results)} = {good_count/len(results)*100:.1f}%')
    return results

if __name__ == '__main__':
    test_memory_responsiveness()
