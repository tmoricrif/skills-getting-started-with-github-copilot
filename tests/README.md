# Test Commands Reference

## Run all tests
```bash
python -m pytest tests/ -v
```

## Run tests with coverage
```bash
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Run specific test file
```bash
python -m pytest tests/test_api.py -v
python -m pytest tests/test_edge_cases.py -v
```

## Run specific test class
```bash
python -m pytest tests/test_api.py::TestBasicEndpoints -v
python -m pytest tests/test_api.py::TestActivitySignup -v
```

## Run specific test
```bash
python -m pytest tests/test_api.py::TestBasicEndpoints::test_get_activities -v
```

## Generate HTML coverage report
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## Test Structure

### tests/test_api.py
- **TestBasicEndpoints**: Tests root redirect and activities endpoint
- **TestActivitySignup**: Tests participant registration functionality
- **TestActivityUnregister**: Tests participant unregistration functionality  
- **TestDataIntegrity**: Tests data structure validation and concurrent operations

### tests/test_edge_cases.py
- **TestEdgeCases**: Tests special characters and edge cases in inputs
- **TestActivityCapacity**: Tests capacity management and overflow scenarios
- **TestResponseFormats**: Tests API response format consistency

### Test Coverage
The test suite achieves 97% code coverage and includes:
- Happy path scenarios
- Error conditions and edge cases
- Data validation
- Capacity management
- Email format validation
- Concurrent operations
- Response format consistency