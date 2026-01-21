---
name: testing-helper
description: Generates unit tests, integration tests, and test strategies. Use for test creation, mocking, and coverage improvement.
triggers:
  - test
  - unit test
  - integration test
  - mock
  - coverage
  - pytest
  - jest
  - junit
  - testing
  - test case
  - assertion
priority: 8
category: testing
---

# Testing Helper Skill

A specialized skill for creating comprehensive and maintainable tests.

## Core Capabilities

### 1. Unit Test Generation
When creating unit tests:
- Test one thing at a time (single responsibility)
- Follow Arrange-Act-Assert (AAA) pattern
- Use descriptive test names that explain intent
- Cover happy path and edge cases
- Test boundary conditions
- Include negative test cases

### 2. Integration Test Creation
When creating integration tests:
- Test component interactions
- Set up and tear down test environments
- Handle external dependencies appropriately
- Test realistic scenarios
- Consider data consistency

### 3. Mocking & Stubbing
When creating mocks:
- Mock external dependencies, not the SUT
- Use appropriate mocking library for the language
- Verify mock interactions when relevant
- Keep mocks simple and focused
- Document mock behavior

### 4. Test Coverage Analysis
When improving coverage:
- Identify untested code paths
- Prioritize critical functionality
- Suggest meaningful tests, not just coverage numbers
- Consider mutation testing for quality assessment

## Testing Patterns by Language

### Python (pytest)
```python
import pytest
from unittest.mock import Mock, patch

class TestUserService:
    """Tests for UserService class."""

    @pytest.fixture
    def user_service(self):
        """Create a UserService with mocked dependencies."""
        db = Mock()
        return UserService(db)

    def test_create_user_with_valid_data_returns_user(self, user_service):
        """Test that creating a user with valid data succeeds."""
        # Arrange
        user_data = {"name": "John", "email": "john@example.com"}
        
        # Act
        result = user_service.create_user(user_data)
        
        # Assert
        assert result.name == "John"
        assert result.email == "john@example.com"

    def test_create_user_with_invalid_email_raises_error(self, user_service):
        """Test that invalid email raises ValidationError."""
        # Arrange
        user_data = {"name": "John", "email": "invalid"}
        
        # Act & Assert
        with pytest.raises(ValidationError):
            user_service.create_user(user_data)

    @pytest.mark.parametrize("email", [
        "",
        "no-at-sign",
        "@no-local.com",
        "no-domain@",
    ])
    def test_create_user_rejects_invalid_emails(self, user_service, email):
        """Test various invalid email formats are rejected."""
        user_data = {"name": "John", "email": email}
        with pytest.raises(ValidationError):
            user_service.create_user(user_data)
```

### JavaScript (Jest)
```javascript
describe('UserService', () => {
  let userService;
  let mockDb;

  beforeEach(() => {
    mockDb = {
      save: jest.fn(),
      find: jest.fn(),
    };
    userService = new UserService(mockDb);
  });

  describe('createUser', () => {
    it('should create user with valid data', async () => {
      // Arrange
      const userData = { name: 'John', email: 'john@example.com' };
      mockDb.save.mockResolvedValue({ id: 1, ...userData });

      // Act
      const result = await userService.createUser(userData);

      // Assert
      expect(result.name).toBe('John');
      expect(mockDb.save).toHaveBeenCalledWith(userData);
    });

    it('should throw error for invalid email', async () => {
      // Arrange
      const userData = { name: 'John', email: 'invalid' };

      // Act & Assert
      await expect(userService.createUser(userData))
        .rejects.toThrow('Invalid email');
    });
  });
});
```

## Test Naming Conventions

Use one of these patterns for test names:

1. **Should/When Pattern**
   - `should_return_user_when_valid_id_provided`
   - `should_throw_error_when_email_is_invalid`

2. **Given/When/Then Pattern**
   - `given_valid_user_when_save_then_returns_id`
   - `given_duplicate_email_when_create_then_throws`

3. **Descriptive Pattern**
   - `test_create_user_with_valid_data_succeeds`
   - `test_login_with_wrong_password_fails`

## Best Practices

1. **Fast execution** - Unit tests should run in milliseconds
2. **Isolation** - Tests should not depend on each other
3. **Repeatability** - Tests should produce same results every run
4. **Self-validating** - Tests should have clear pass/fail
5. **Timely** - Write tests before or alongside code
6. **Meaningful names** - Test names should describe the scenario

## Output Format

When generating tests, provide:

```markdown
## Test Strategy
[Brief explanation of testing approach]

## Test Cases
[List of test scenarios to cover]

## Generated Tests
[Actual test code]

## Running Instructions
[How to run the tests]

## Coverage Notes
[What's covered and any gaps]
```
