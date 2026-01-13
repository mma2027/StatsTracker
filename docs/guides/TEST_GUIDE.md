# StatsTracker Testing Guide

Complete guide for running and debugging tests.

## 🚀 Quick Start

### Run All Tests
```bash
# Run from project root directory
python -m pytest tests/ -v

# Expected output:
# 55 passed ✅
```

### Run Tests for Specific Modules
```bash
# Email notifier tests (48 tests)
python -m pytest tests/email_notifier/ -v

# Player database tests (7 tests)
python -m pytest tests/player_database/ -v
```

## 📝 Test Command Reference

### Basic Commands

| Command | Description |
|---------|-------------|
| `pytest tests/` | Run all tests (concise output) |
| `pytest tests/ -v` | Verbose mode (show each test name) |
| `pytest tests/ -vv` | Extra verbose mode (show more details) |
| `pytest tests/ -q` | Quiet mode (minimal output) |

### Selective Execution

```bash
# Run specific file
pytest tests/email_notifier/test_notifier.py -v

# Run all tests in a specific class
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier -v

# Run specific test function
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_init -v

# Use keyword matching for test names
pytest tests/ -k "email" -v          # Run tests with "email" in name
pytest tests/ -k "smtp" -v           # Run tests with "smtp" in name
pytest tests/ -k "not slow" -v       # Run tests without "slow" in name
```

### Debugging and Output

```bash
# Show print output
pytest tests/ -v -s

# Show local variables (for debugging failed tests)
pytest tests/ -v -l

# Enter debugger on failure
pytest tests/ --pdb

# Stop after first failure
pytest tests/ -x

# Allow maximum N failures
pytest tests/ --maxfail=3
```

### Re-run Failed Tests

```bash
# Only run tests that failed last time
pytest --lf

# Run failed tests first, then others
pytest --ff
```

### Test Coverage

```bash
# Generate coverage report (requires pytest-cov)
pip install pytest-cov

# Check coverage for email_notifier
pytest tests/email_notifier/ --cov=src/email_notifier --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
# Then open htmlcov/index.html to view
```

## 🎯 Email Notifier Test Examples

### Scenario 1: Run Tests Before Developing New Features
Ensure existing functionality works:
```bash
pytest tests/email_notifier/ -v
```

### Scenario 2: Quick Verification After Code Changes
```bash
# Run only related tests
pytest tests/email_notifier/test_notifier.py -v

# Or use keywords
pytest tests/ -k "notifier" -v
```

### Scenario 3: Debug Failed Tests
```bash
# Verbose output + show print statements + show local variables
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_send_test_email_success -vv -s -l
```

### Scenario 4: Test Error Handling
```bash
# Run all error handling related tests
pytest tests/ -k "error or exception" -v
```

## 📂 Test File Structure

```
tests/
├── email_notifier/              # Email module tests
│   ├── __init__.py
│   ├── test_notifier.py         # EmailNotifier class tests (22 tests)
│   ├── test_templates.py        # EmailTemplate class tests (26 tests)
│   └── README.md               # Detailed test documentation
├── player_database/            # Database module tests
│   ├── __init__.py
│   └── test_database.py        # PlayerDatabase tests (7 tests)
└── (Other module tests will be added in the future)
```

## ✅ Testing Best Practices

### 1. Run Tests Before Committing Code
```bash
# Ensure all tests pass
pytest tests/ -v

# Check the module you modified
pytest tests/email_notifier/ -v
```

### 2. TDD Workflow for New Features
```bash
# 1. Write test first (it will fail)
# 2. Run test to confirm failure
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_new_feature -v

# 3. Implement feature
# 4. Run test again until it passes
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_new_feature -v

# 5. Run all tests to ensure nothing broke
pytest tests/ -v
```

### 3. Bug Fix Workflow
```bash
# 1. Write a test that reproduces the bug (should fail)
# 2. Fix the bug
# 3. Run test to confirm fix
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_bug_fix -v

# 4. Run all related tests
pytest tests/email_notifier/ -v
```

## 🔍 Understanding Test Output

### Successful Test
```
tests/email_notifier/test_notifier.py::TestEmailNotifier::test_init PASSED [  1%]
```
- `PASSED` = Test passed ✅
- `[  1%]` = Progress percentage

### Failed Test
```
tests/email_notifier/test_notifier.py::TestEmailNotifier::test_init FAILED [ 1%]

================================== FAILURES ===================================
_________________________ TestEmailNotifier.test_init _________________________

    def test_init(self):
>       assert result == expected
E       AssertionError: assert 'actual' == 'expected'

tests/email_notifier/test_notifier.py:75: AssertionError
```
- Shows where the failure occurred
- Shows actual vs expected assertion values
- Helps you quickly locate the issue

### Test Error
```
tests/email_notifier/test_notifier.py::TestEmailNotifier::test_init ERROR [ 1%]
```
- `ERROR` = Test errored before running (usually import error or fixture issue)

## 🛠️ Common Issues and Solutions

### Issue 1: Module Not Found
```bash
ModuleNotFoundError: No module named 'src'
```

**Solution**: Ensure you're running tests from the project root directory
```bash
cd /Users/zero_legend/StatsTracker
python -m pytest tests/ -v
```

### Issue 2: Import Error
```bash
ImportError: cannot import name 'EmailNotifier'
```

**Solution**: Check that `__init__.py` correctly exports the classes
```python
# src/email_notifier/__init__.py
from .notifier import EmailNotifier
from .templates import EmailTemplate
```

### Issue 3: Missing Test Dependencies
```bash
ModuleNotFoundError: No module named 'pytest'
```

**Solution**: Install test dependencies
```bash
pip install pytest pytest-mock
# Or install all dependencies
pip install -r requirements.txt
```

## 📊 Current Test Status

```
✅ Total: 55 tests
   ├── Email Notifier: 48 tests
   │   ├── test_notifier.py: 22 tests
   │   └── test_templates.py: 26 tests
   └── Player Database: 7 tests
       └── test_database.py: 7 tests

Status: All passing ✅
```

## 🎓 Learning Resources

### Pytest Documentation
- Official docs: https://docs.pytest.org/
- Fixtures: https://docs.pytest.org/en/stable/fixture.html
- Parametrize: https://docs.pytest.org/en/stable/parametrize.html

### Project-Specific Test Documentation
- Email Notifier test details: [tests/email_notifier/README.md](tests/email_notifier/README.md)
- Covers what features are tested, how to use fixtures, testing strategies, etc.

## 💡 Command Aliases

You can add aliases to `.bashrc` or `.zshrc`:

```bash
# Test aliases
alias test-all="python -m pytest tests/ -v"
alias test-email="python -m pytest tests/email_notifier/ -v"
alias test-db="python -m pytest tests/player_database/ -v"
alias test-quick="python -m pytest tests/ -q"
alias test-failed="python -m pytest --lf -v"
```

Then you can simply run:
```bash
test-all       # Run all tests
test-email     # Run email tests
test-failed    # Re-run failed tests
```

## 🚦 CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
```

## 📈 Next Steps

1. **Install Coverage Tools**
   ```bash
   pip install pytest-cov
   pytest tests/ --cov=src --cov-report=html
   ```

2. **Add Tests for Other Modules**
   - milestone_detector
   - gameday_checker
   - website_fetcher

3. **Add Integration Tests**
   - Test module interactions
   - End-to-end tests

4. **Performance Testing**
   - Use `pytest-benchmark`
   - Test large dataset processing

---

**Quick Reference Card**

| I want to... | Command |
|--------------|---------|
| Run all tests | `pytest tests/ -v` |
| Run email tests | `pytest tests/email_notifier/ -v` |
| Run single test | `pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_init -v` |
| Debug failed test | `pytest tests/ -vv -s -l` |
| Re-run failed only | `pytest --lf` |
| Check coverage | `pytest tests/ --cov=src` |
| Filter by name | `pytest tests/ -k "email" -v` |
| Stop on first failure | `pytest tests/ -x` |
