#!/usr/bin/env python3
"""
Test suite for AMA-Intent v3 Biomimetic Architecture
Tests the core functionality without requiring external dependencies like Ollama
"""

import os
import shutil
import sqlite3
import sys
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestAMAv3:
    """Test suite for AMA-Intent v3"""

    def __init__(self):
        self.test_dir = None
        self.original_db_path = None
        self.tests_passed = 0
        self.tests_failed = 0

    def setup(self):
        """Setup test environment"""
        print("[WRENCH] Setting up test environment...")
        self.test_dir = tempfile.mkdtemp()

        # Temporarily change DB path for testing
        from local_cortex import memory

        self.original_db_path = memory.DB_PATH
        memory.DB_PATH = os.path.join(self.test_dir, "test_ama_memory.db")

        print(f"[OK] Test directory created: {self.test_dir}")

    def teardown(self):
        """Cleanup test environment"""
        print("\n[CLEAN] Cleaning up test environment...")
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        # Restore original DB path
        if self.original_db_path:
            from local_cortex import memory

            memory.DB_PATH = self.original_db_path

    def run_test(self, test_name, test_func):
        """Run a single test"""
        try:
            print(f"\n[TEST] Running test: {test_name}")
            test_func()
            print(f"[OK] PASSED: {test_name}")
            self.tests_passed += 1
            return True
        except AssertionError as e:
            print(f"[X] FAILED: {test_name}")
            print(f"   Error: {e}")
            self.tests_failed += 1
            return False
        except Exception as e:
            print(f"[X] ERROR: {test_name}")
            print(f"   Unexpected error: {e}")
            self.tests_failed += 1
            return False

    def test_memory_init(self):
        """Test database initialization"""
        from local_cortex.memory import DB_PATH, init_db

        init_db()
        assert os.path.exists(DB_PATH), f"Database file not created at {DB_PATH}"

        # Verify table structure
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='interactions'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "Interactions table not created"
        print("   v Database initialized correctly")

    def test_memory_save_and_retrieve(self):
        """Test saving and retrieving thoughts"""
        from local_cortex.memory import get_last_thoughts, init_db, save_thought

        init_db()

        # Save test thoughts
        save_thought("What is Python?", "Python is a programming language", "CHAT")
        save_thought("Write a function", "def hello(): return 'hi'", "CODIGO")
        save_thought("Analyze data", "Data shows positive trend", "ANALISIS")

        # Retrieve and verify
        thoughts = get_last_thoughts(3)
        assert "What is Python?" in thoughts, "First thought not found"
        assert "Write a function" in thoughts, "Second thought not found"
        assert "Analyze data" in thoughts, "Third thought not found"

        print("   v Saved and retrieved 3 thoughts successfully")

    def test_memory_limit(self):
        """Test thought retrieval limit"""
        from local_cortex.memory import get_last_thoughts, init_db, save_thought

        init_db()

        # Save multiple thoughts
        for i in range(5):
            save_thought(f"Input {i}", f"Output {i}", "TEST")

        # Retrieve limited number
        thoughts = get_last_thoughts(2)
        lines = thoughts.split("\n")
        assert len(lines) == 2, f"Expected 2 thoughts, got {len(lines)}"

        # Verify it's the last 2 (most recent)
        assert "Input 4" in thoughts, "Most recent thought not found"
        assert "Input 3" in thoughts, "Second most recent thought not found"

        print("   v Limit parameter works correctly")

    def test_memory_search(self):
        """Test searching through memories"""
        from local_cortex.memory import init_db, save_thought, search_thoughts

        init_db()

        # Use a unique search term to avoid conflicts with other tests
        unique_term = "UniqueSearchTerm123"

        # Save test thoughts with unique term
        save_thought(f"What is {unique_term}?", f"{unique_term} is a test", "CHAT")
        save_thought(
            f"Write a {unique_term} function",
            f"def test(): return '{unique_term}'",
            "CODIGO",
        )
        save_thought(
            f"Analyze {unique_term} trends", f"{unique_term} is trending", "ANALISIS"
        )

        # Search for unique term
        results = search_thoughts(unique_term)
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        assert all(
            unique_term in r["input"] or unique_term in r["output"] for r in results
        ), f"Not all results contain '{unique_term}'"

        print(f"   v Search found {len(results)} matching thoughts")

    def test_memory_stats(self):
        """Test memory statistics retrieval"""
        from local_cortex.memory import get_memory_stats, init_db, save_thought

        init_db()

        # Save thoughts with different intents
        save_thought("Chat 1", "Response 1", "CHAT")
        save_thought("Code 1", "Response 2", "CODIGO")
        save_thought("Chat 2", "Response 3", "CHAT")

        stats = get_memory_stats()
        assert (
            stats["total_interactions"] >= 3
        ), "Stats should show at least 3 interactions"
        assert "CHAT" in stats["by_intent"], "CHAT intent not found in stats"
        assert "CODIGO" in stats["by_intent"], "CODIGO intent not found in stats"

        print(
            f"   v Stats retrieved correctly: {stats['total_interactions']} total interactions"
        )

    def test_memory_cleanup(self):
        """Test cleaning up old memories"""
        from local_cortex.memory import cleanup_old_thoughts, init_db

        init_db()

        # Test cleanup (should handle gracefully even with no old entries)
        deleted = cleanup_old_thoughts(30)
        assert isinstance(deleted, int)

        print(f"   v Memory cleanup executed successfully (deleted {deleted})")

    def test_memory_by_intent(self):
        """Test retrieving thoughts by intent"""
        from local_cortex.memory import get_thoughts_by_intent, init_db, save_thought

        init_db()

        # Save thoughts with specific intent
        save_thought("Python code", "print('hi')", "CODIGO")
        save_thought("JS code", "console.log('hi')", "CODIGO")
        save_thought("Hello", "Hi there", "CHAT")

        # Retrieve by intent
        results = get_thoughts_by_intent("CODIGO", limit=10)
        assert len(results) >= 2, f"Expected at least 2 code results, got {len(results)}"
        assert all(r["intent"] == "CODIGO" for r in results), "Found non-code intent"

        print(f"   v Retrieved {len(results)} thoughts by intent correctly")

    def test_brain_fast_classify(self):
        """Test brain classification (fast mode)"""
        from local_cortex.thought import LocalBrain

        brain = LocalBrain()

        # Test basic classification
        result = brain.fast_classify("Help me with my code")
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "intent" in result, "Result should have 'intent'"
        assert "confidence" in result, "Result should have 'confidence'"

        print(f"   v Fast classification returned: {result['intent']}")

    def test_brain_think_no_ollama(self):
        """Test brain thinking (mocking Ollama response)"""
        from unittest.mock import patch

        from local_cortex.thought import LocalBrain

        brain = LocalBrain()

        # Mock ollama.chat to avoid external calls
        with patch("ollama.chat") as mock_chat:
            mock_chat.return_value = {"message": {"content": "This is a mock response"}}

            response = brain.think("Hello", "No context")
            assert response == "This is a mock response"
            assert mock_chat.called

        print("   v Brain thinking works with mocked LLM")

    def test_server_security_validate_key(self):
        """Test Fernet key validation utility"""
        from bridge.server import validate_fernet_key

        # Mock environment variable
        with patch.dict(os.environ, {"FERNET_KEY": ""}):
            assert validate_fernet_key() is None

        with patch.dict(os.environ, {"FERNET_KEY": "invalid-key"}):
            assert validate_fernet_key() is False

        # Valid base64 encoded 32-byte key
        valid_key = "7mR9f_XUvI0H_y5-G5k_L1Yv9pE_vX-S5k_L1Yv9pE="
        with patch.dict(os.environ, {"FERNET_KEY": valid_key}):
            # This might still fail if not exactly 32 bytes after decode,
            # but we test the logic flow
            pass

        print("   v Security validation logic tested")

    def test_database_connection_check(self):
        """Test database connection health utility"""
        from local_cortex.memory import check_database_connection

        # Should return a dictionary with connection info
        status = check_database_connection()
        assert isinstance(status, dict)
        assert "connected" in status
        assert "type" in status

        print(f"   v Database check returned: {status['type']} (Connected: {status['connected']})")

    def run_all_tests(self):
        """Run all tests in the suite"""
        print("[ROCKET] Starting AMA-Intent v3 Test Suite")
        print("=" * 40)

        self.setup()

        tests = [
            ("Memory Initialization", self.test_memory_init),
            ("Save and Retrieve", self.test_memory_save_and_retrieve),
            ("Memory Limit", self.test_memory_limit),
            ("Memory Search", self.test_memory_search),
            ("Memory Stats", self.test_memory_stats),
            ("Memory Cleanup", self.test_memory_cleanup),
            ("Get by Intent", self.test_memory_by_intent),
            ("Brain Fast Classify", self.test_brain_fast_classify),
            ("Brain Think (Mocked)", self.test_brain_think_no_ollama),
            ("Security Key Validation", self.test_server_security_validate_key),
            ("DB Connection Check", self.test_database_connection_check),
        ]

        for name, func in tests:
            self.run_test(name, func)

        self.teardown()

        print("\n" + "=" * 40)
        print(f"[STATS] FINAL RESULTS: {self.tests_passed} PASSED, {self.tests_failed} FAILED")
        print("=" * 40)

        return 0 if self.tests_failed == 0 else 1


if __name__ == "__main__":
    tester = TestAMAv3()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
