---
name: docs-helper
description: Generates documentation for code, APIs, and projects. Use for README files, docstrings, API docs, and technical writing.
triggers:
  - document
  - documentation
  - readme
  - api docs
  - docstring
  - jsdoc
  - javadoc
  - comment
  - describe
  - write docs
priority: 8
category: documentation
---

# Documentation Helper Skill

A specialized skill for creating clear, comprehensive, and well-structured documentation.

## Core Capabilities

### 1. README Generation
When creating README files:
- Include project title and description
- Add installation/setup instructions
- Provide usage examples
- Document configuration options
- Include contribution guidelines
- Add license information
- Use badges for build status, version, etc.

### 2. API Documentation
When documenting APIs:
- Describe each endpoint's purpose
- List all parameters with types and descriptions
- Show request/response examples
- Document error codes and messages
- Include authentication requirements
- Provide curl/code examples

### 3. Code Comments & Docstrings
When adding documentation to code:
- Write clear function/method descriptions
- Document all parameters and return values
- Include usage examples in docstrings
- Add type hints where applicable
- Note any exceptions that may be raised
- Follow language-specific documentation conventions

### 4. Technical Writing
When writing technical documentation:
- Use clear, concise language
- Structure content with headers
- Include diagrams when helpful (Mermaid, ASCII art)
- Provide step-by-step instructions
- Add cross-references to related topics

## Documentation Formats

### Python (Google Style)
```python
def function_name(param1: str, param2: int = 0) -> bool:
    """Short description of function.

    Longer description if needed, explaining the function's
    purpose and behavior in more detail.

    Args:
        param1: Description of param1.
        param2: Description of param2. Defaults to 0.

    Returns:
        Description of return value.

    Raises:
        ValueError: If param1 is empty.

    Example:
        >>> function_name("hello", 42)
        True
    """
```

### JavaScript (JSDoc)
```javascript
/**
 * Short description of function.
 * 
 * @param {string} param1 - Description of param1.
 * @param {number} [param2=0] - Description of param2.
 * @returns {boolean} Description of return value.
 * @throws {Error} If param1 is empty.
 * @example
 * functionName("hello", 42);
 * // => true
 */
```

### TypeScript
```typescript
/**
 * Short description of function.
 * 
 * @param param1 - Description of param1.
 * @param param2 - Description of param2. Defaults to 0.
 * @returns Description of return value.
 * @throws Error if param1 is empty.
 */
function functionName(param1: string, param2: number = 0): boolean {
```

## Best Practices

1. **Be concise but complete** - Cover all important details without redundancy
2. **Use examples** - Concrete examples aid understanding
3. **Keep it current** - Documentation should match current code
4. **Consider the audience** - Adjust complexity for target readers
5. **Use consistent formatting** - Follow established conventions
