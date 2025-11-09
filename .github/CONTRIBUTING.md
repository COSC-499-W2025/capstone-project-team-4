# 📝 Development Guidelines
This guide will help you get started with contributing to our project.

## Branch Naming
Use descriptive branch names with the following format:

```
type/<descriptive-name>

Examples:
feature/user-authentication
fix/database-connection-timeout
docs/api-documentation-update
test/login-validation-tests
```

## Commit Messages
Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): description

Examples:
feat: add user authentication
fix: resolve database connection issue
docs: update API documentation
test: add unit tests for validation
```

**Types:**
- `feat` - New features
- `fix` - Bug fixes  
- `docs` - Documentation only
- `test` - Adding/updating tests
- `refactor` - Code restructuring
- `style` - Formatting changes
- `chore` - Maintenance tasks
- `perf` - Performance improvements

### Testing
- Add unit tests for new functionality
- Place tests in the `tests/` directory
- Run tests: `pytest`
- Check coverage: `pytest --cov=src`
- All tests must pass before merging

### Commits & Pull Requests
- Use descriptive commit messages
- Reference issue numbers (e.g., "Fix #123: Add language detection")
- Follow the PR template checklist
- Link related issues in PR description

## 📋 Pre-Commit Checklist

Before submitting a PR, ensure:
- [ ] All tests pass with `pytest`
- [ ] New functionality has tests or plan tests for future
- [ ] Documentation is updated
- [ ] PR template is completed

## 🐛 Reporting Issues

When reporting bugs:
- Use a clear, descriptive title
- Include steps to reproduce
- Provide system information (OS, Python version)
- Include relevant error messages/logs



