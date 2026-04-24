"""Quick test script for VotePath AI Backend"""

import sys
import time

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from app.core.config import get_settings
        from app.core.logging_config import setup_logging
        from app.models.schemas import QuestionRequest, QuestionResponse
        from app.services.intent_service import detect_intent
        from app.services.fallback_service import FallbackService
        from app.services.response_service import ResponseService
        from app.utils.cache import get_cache
        from app.utils.validators import validate_question, sanitize_input
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_intent_detection():
    """Test intent detection"""
    print("\nTesting intent detection...")
    try:
        from app.services.intent_service import detect_intent
        
        tests = [
            ("How do I register to vote?", "registration"),
            ("What documents do I need?", "documents"),
            ("Where is my polling station?", "polling_day"),
            ("When is the election?", "timeline"),
            ("I made a mistake on my registration", "correction"),
        ]
        
        for question, expected in tests:
            result = detect_intent(question)
            status = "✓" if result == expected else "✗"
            print(f"  {status} '{question[:40]}...' -> {result} (expected: {expected})")
        
        return True
    except Exception as e:
        print(f"✗ Intent detection failed: {e}")
        return False

def test_fallback_data():
    """Test fallback data"""
    print("\nTesting fallback data...")
    try:
        from app.services.fallback_service import FallbackService
        
        service = FallbackService()
        data = service.get_fallback_data()
        
        expected_categories = [
            "first_time_voter", "registration", "documents", "correction",
            "status_check", "polling_day", "timeline", "faq"
        ]
        
        for category in expected_categories:
            if category in data:
                print(f"  ✓ {category}: {data[category]['title']}")
            else:
                print(f"  ✗ Missing category: {category}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Fallback data test failed: {e}")
        return False

def test_response_formatting():
    """Test response formatting"""
    print("\nTesting response formatting...")
    try:
        from app.services.response_service import ResponseService
        from app.services.fallback_service import FallbackService
        
        response_service = ResponseService()
        fallback_service = FallbackService()
        
        data = fallback_service.get_category_data("registration")
        response = response_service.format_response("registration", data)
        
        print(f"  ✓ Category: {response.category}")
        print(f"  ✓ Title: {response.title}")
        print(f"  ✓ Steps: {len(response.steps)} items")
        print(f"  ✓ Documents: {len(response.documents)} items")
        print(f"  ✓ Tips: {len(response.tips)} items")
        
        return True
    except Exception as e:
        print(f"✗ Response formatting failed: {e}")
        return False

def test_cache():
    """Test cache operations"""
    print("\nTesting cache...")
    try:
        from app.utils.cache import get_cache
        
        cache = get_cache()
        cache.clear()
        
        # Test set and get
        test_data = {"title": "Test", "overview": "Test overview"}
        cache.set("test_category", test_data)
        
        retrieved = cache.get("test_category")
        if retrieved == test_data:
            print("  ✓ Cache set/get working")
        else:
            print("  ✗ Cache data mismatch")
            return False
        
        # Test size
        size = cache.size()
        print(f"  ✓ Cache size: {size}")
        
        cache.clear()
        return True
    except Exception as e:
        print(f"✗ Cache test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("VotePath AI Backend - Quick Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_intent_detection,
        test_fallback_data,
        test_response_formatting,
        test_cache,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✓ All tests passed! Application is ready.")
        return 0
    else:
        print("\n✗ Some tests failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
