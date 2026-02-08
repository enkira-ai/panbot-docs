---
title: Testing Guide
description: How to run and write tests for PanBot.
---

## Running Tests

```bash
pytest tests/                       # Run all tests
pytest tests/ -m unit               # Unit tests only
pytest tests/ -m "not integration"  # Skip integration tests
pytest tests/ -m "not slow"         # Skip slow tests
pytest tests/test_menu_format.py    # Single test file
```

## Test Organization

| Directory | Marker | Purpose |
|-----------|--------|---------|
| `tests/` | (all) | All tests |
| Unit tests | `@pytest.mark.unit` | Fast, isolated, no external deps |
| Integration tests | `@pytest.mark.integration` | Requires DB/Redis/external services |
| Slow tests | `@pytest.mark.slow` | Long-running tests |

## Testing Strategy

| Layer | Approach |
|-------|----------|
| Services | Unit test with mocked DB sessions and Redis |
| API endpoints | Integration test with TestClient |
| Agent tools | Unit test with mocked service methods |
| Common utilities | Unit test (pure functions) |

## Key Patterns

### Service Testing
```python
# Mock DB session and Redis for service tests
async def test_create_order(mock_db, mock_redis):
    service = OrderService(db=mock_db, cache=mock_redis)
    order = await service.create_order(order_data)
    assert order.id is not None
```

### API Testing
```python
# Use FastAPI TestClient for endpoint tests
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_business():
    response = client.get("/api/v1/businesses/my", headers=auth_headers)
    assert response.status_code == 200
```

## Desktop App Testing

Desktop app currently has no automated test suite. Testing is manual.

**Future**: Consider Playwright for E2E testing of the React UI and Tauri test harness for Rust commands.

## Web App Testing

Web app currently has no automated test suite.

**Future**: Consider Playwright or Cypress for E2E testing, React Testing Library for component tests.
