#!/usr/bin/env python3

import json
import time
import requests
import sys
from typing import List, Dict, Any

TEST_QUERIES = [
    {
        "name": "Basic Cypher Query",
        "prompt": "Generate a Cypher query to find all Person nodes with name 'John'",
        "expected_keywords": ["MATCH", "Person", "name", "John", "RETURN"]
    },
    {
        "name": "Relationship Query",
        "prompt": "Create a Cypher query to find all movies that an actor named 'Tom Hanks' has acted in",
        "expected_keywords": ["MATCH", "Actor", "ACTED_IN", "Movie", "Tom Hanks"]
    },
    {
        "name": "Complex Pattern",
        "prompt": "Write a Cypher query to find users who have similar preferences to a given user",
        "expected_keywords": ["MATCH", "User", "LIKES", "WHERE", "RETURN"]
    }
]

class MemoryReplayTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def generate_query(self, prompt: str) -> Dict[str, Any]:
        payload = {
            "prompt": prompt,
            "max_tokens": 256,
            "temperature": 0.1,
            "top_p": 0.9
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def validate_response(self, response: Dict[str, Any], expected_keywords: List[str]) -> bool:
        if "error" in response:
            return False
            
        try:
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            content_upper = content.upper()
            
            found_keywords = [kw for kw in expected_keywords if kw.upper() in content_upper]
            coverage = len(found_keywords) / len(expected_keywords)
            
            return coverage >= 0.6  # At least 60% keyword coverage
        except Exception:
            return False
    
    def run_tests(self) -> Dict[str, Any]:
        print("=== Memory Replay Test Suite ===")
        
        if not self.test_health():
            return {"status": "failed", "error": "Health check failed"}
        
        print("✅ Health check passed")
        
        results = []
        total_time = 0
        
        for i, test in enumerate(TEST_QUERIES, 1):
            print(f"\n🧪 Test {i}/{len(TEST_QUERIES)}: {test['name']}")
            print(f"Prompt: {test['prompt']}")
            
            start_time = time.time()
            response = self.generate_query(test['prompt'])
            end_time = time.time()
            
            test_time = end_time - start_time
            total_time += test_time
            
            is_valid = self.validate_response(response, test['expected_keywords'])
            
            result = {
                "name": test['name'],
                "prompt": test['prompt'],
                "response": response,
                "time_taken": test_time,
                "valid": is_valid,
                "expected_keywords": test['expected_keywords']
            }
            
            results.append(result)
            
            if is_valid:
                print(f"✅ Test passed ({test_time:.2f}s)")
            else:
                print(f"❌ Test failed ({test_time:.2f}s)")
                print(f"Response: {response}")
        
        passed = sum(1 for r in results if r['valid'])
        total = len(results)
        
        summary = {
            "status": "passed" if passed == total else "failed",
            "tests_passed": passed,
            "tests_total": total,
            "total_time": total_time,
            "average_time": total_time / total if total > 0 else 0,
            "results": results
        }
        
        print(f"\n=== Test Summary ===")
        print(f"Status: {summary['status'].upper()}")
        print(f"Tests passed: {passed}/{total}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time: {summary['average_time']:.2f}s")
        
        return summary

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Replay Test Suite")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    tester = MemoryReplayTester(args.url)
    results = tester.run_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to {args.output}")
    
    sys.exit(0 if results['status'] == 'passed' else 1)

if __name__ == "__main__":
    main()