#!/usr/bin/env python3
"""
Test suite for AMA-Intent v3 Biomimetic Architecture
Tests the core functionality without requiring external dependencies like Ollama
"""
import os
import sys
import sqlite3
import tempfile
import shutil
from pathlib import Path

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
        print("🔧 Setting up test environment...")
        self.test_dir = tempfile.mkdtemp()
        
        # Temporarily change DB path for testing
        from local_cortex import memory
        self.original_db_path = memory.DB_PATH
        memory.DB_PATH = os.path.join(self.test_dir, "test_ama_memory.db")
        
        print(f"✅ Test directory created: {self.test_dir}")

    def teardown(self):
        """Cleanup test environment"""
        print("\n🧹 Cleaning up test environment...")
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        # Restore original DB path
        if self.original_db_path:
            from local_cortex import memory
            memory.DB_PATH = self.original_db_path

    def run_test(self, test_name, test_func):
        """Run a single test"""
        try:
            print(f"\n📝 Running test: {test_name}")
            test_func()
            print(f"✅ PASSED: {test_name}")
            self.tests_passed += 1
            return True
        except AssertionError as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {e}")
            self.tests_failed += 1
            return False
        except Exception as e:
            print(f"❌ ERROR: {test_name}")
            print(f"   Unexpected error: {e}")
            self.tests_failed += 1
            return False

    def test_memory_init(self):
        """Test database initialization"""
        from local_cortex.memory import init_db, DB_PATH
        
        init_db()
        assert os.path.exists(DB_PATH), f"Database file not created at {DB_PATH}"
        
        # Verify table structure
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interactions'")
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None, "Interactions table not created"
        print("   ✓ Database initialized correctly")

    def test_memory_save_and_retrieve(self):
        """Test saving and retrieving thoughts"""
        from local_cortex.memory import init_db, save_thought, get_last_thoughts
        
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
        
        print(f"   ✓ Saved and retrieved 3 thoughts successfully")

    def test_memory_limit(self):
        """Test thought retrieval limit"""
        from local_cortex.memory import init_db, save_thought, get_last_thoughts
        
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
        
        print(f"   ✓ Limit parameter works correctly")

    def test_module_imports(self):
        """Test that all modules can be imported"""
        modules = [
            'local_cortex',
            'local_cortex.memory',
            'bridge',
        ]
        
        for module in modules:
            try:
                __import__(module)
                print(f"   ✓ {module} imported successfully")
            except ImportError as e:
                # Expected for modules requiring external dependencies
                if "ollama" in str(e) or "fasthtml" in str(e):
                    print(f"   ⚠️ {module} requires external dependency: {e}")
                else:
                    raise

    def test_directory_structure(self):
        """Test that required directories and files exist"""
        required_items = [
            ('file', 'start.py'),
            ('file', 'requirements.txt'),
            ('file', 'README.md'),
            ('file', '.gitignore'),
            ('file', '.env.example'),
            ('dir', 'local_cortex'),
            ('dir', 'bridge'),
            ('dir', 'data'),
            ('file', 'local_cortex/__init__.py'),
            ('file', 'local_cortex/thought.py'),
            ('file', 'local_cortex/memory.py'),
            ('file', 'bridge/__init__.py'),
            ('file', 'bridge/server.py'),
        ]
        
        for item_type, item_path in required_items:
            if item_type == 'file':
                assert os.path.isfile(item_path), f"Required file not found: {item_path}"
                print(f"   ✓ File exists: {item_path}")
            elif item_type == 'dir':
                assert os.path.isdir(item_path), f"Required directory not found: {item_path}"
                print(f"   ✓ Directory exists: {item_path}")

    def test_requirements(self):
        """Test that requirements.txt has correct minimal dependencies"""
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        required_deps = ['fasthtml', 'ollama', 'python-dotenv', 'uvicorn']
        
        for dep in required_deps:
            assert dep in content, f"Required dependency not found: {dep}"
            print(f"   ✓ Dependency found: {dep}")

    def test_start_script_syntax(self):
        """Test that start.py has valid Python syntax"""
        import py_compile
        
        try:
            py_compile.compile('start.py', doraise=True)
            print("   ✓ start.py has valid syntax")
        except py_compile.PyCompileError as e:
            raise AssertionError(f"Syntax error in start.py: {e}")

    def run_all_tests(self):
        """Run all tests"""
        print("=" * 70)
        print("🧪 AMA-Intent v3 Test Suite")
        print("=" * 70)
        
        self.setup()
        
        try:
            # Run all tests
            self.run_test("Directory Structure", self.test_directory_structure)
            self.run_test("Module Imports", self.test_module_imports)
            self.run_test("Requirements", self.test_requirements)
            self.run_test("Start Script Syntax", self.test_start_script_syntax)
            self.run_test("Memory Initialization", self.test_memory_init)
            self.run_test("Memory Save and Retrieve", self.test_memory_save_and_retrieve)
            self.run_test("Memory Limit", self.test_memory_limit)
            
        finally:
            self.teardown()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_failed}")
        print(f"📈 Success Rate: {self.tests_passed}/{self.tests_passed + self.tests_failed}")
        
        if self.tests_failed == 0:
            print("\n🎉 All tests passed! Architecture is working correctly.")
            return 0
        else:
            print(f"\n⚠️ {self.tests_failed} test(s) failed. Please review.")
            return 1


if __name__ == "__main__":
    tester = TestAMAv3()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
