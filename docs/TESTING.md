# Testing Guide

## Overview

This project uses:
- **Frontend**: Vitest for unit testing
- **Backend**: pytest for unit and integration testing

## Running Tests

### All Tests

```bash
./scripts/run-tests.sh
```

### Frontend Tests

```bash
cd frontend

# Run tests in watch mode
pnpm test:unit

# Run tests once
pnpm test:unit --run

# Run with coverage
pnpm test:coverage
```

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_proxy.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run tests matching pattern
pytest -k "test_health"
```

## Writing Tests

### Frontend Tests

Create test files with `.test.ts` or `.spec.ts` extension:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MyComponent from '../components/MyComponent.vue'

describe('MyComponent', () => {
  it('renders correctly', () => {
    const wrapper = mount(MyComponent)
    expect(wrapper.text()).toContain('Hello')
  })
})
```

### Backend Tests

Create test files with `test_` prefix:

```python
import pytest
from httpx import AsyncClient


class TestMyEndpoint:
    """Test class for endpoint."""

    @pytest.mark.asyncio
    async def test_get_endpoint(self, client: AsyncClient):
        """Test GET endpoint."""
        response = await client.get("/my-endpoint")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
```

## Test Structure

### Frontend

```
frontend/
├── components/
│   └── __tests__/
│       └── MyComponent.test.ts
├── composables/
│   └── __tests__/
│       └── useMyComposable.test.ts
└── vitest.config.ts
```

### Backend

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Shared fixtures
│   ├── test_proxy.py
│   └── test_endpoints.py
└── pyproject.toml         # pytest configuration
```

## Coverage Reports

### Frontend

Coverage reports are generated in `frontend/coverage/`:
- `coverage/index.html` - HTML report
- `coverage/coverage-final.json` - JSON report

### Backend

Coverage reports are generated in `backend/htmlcov/`:
- `htmlcov/index.html` - HTML report

## CI Integration

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests

Check the GitHub Actions tab for test results.

## Troubleshooting

### Common Issues

1. **Import errors in tests**: Ensure you're in the correct directory
2. **Async tests failing**: Check that `pytest-asyncio` is installed
3. **Coverage not working**: Ensure test files match the pattern in config

### Reset Test Environment

```bash
# Clear pytest cache
pytest --cache-clear

# Reinstall dependencies
cd frontend && pnpm install
cd backend && pip install -r requirements.txt
```
