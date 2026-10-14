# Contributing to SkyRelief

Thank you for your interest in contributing to SkyRelief! This project aims to save lives during disasters, and every contribution matters.

## How to Contribute

### Reporting Bugs
- Use the GitHub issue tracker
- Include Python/Node.js versions
- Provide minimal reproduction steps
- Share relevant logs (redact API keys!)

### Suggesting Features
- Check existing issues first
- Explain the use case (how does it help relief teams?)
- Consider bilingual implications (EN + HI)

### Pull Requests

1. **Fork and clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Sky-Relief.git
   cd Sky-Relief
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes**
   - Follow existing code style
   - Add tests for new features
   - Update documentation

4. **Test your changes**
   ```bash
   # Backend tests
   cd api
   pytest tests/ -v

   # Frontend linting
   cd web
   npm run lint
   ```

5. **Commit with clear messages**
   ```bash
   git commit -m "Add support for landslide detection"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints
- Docstrings for public functions
- Keep functions under 50 lines when possible

### TypeScript (Frontend)
- Use functional components
- Prefer const over let
- Type everything (avoid ny)
- Keep components under 200 lines

## Testing Requirements

- **Backend**: All new tools must have pytest coverage
- **Frontend**: Critical paths should have Playwright tests
- **Integration**: Test SSE streaming for new endpoints

## Documentation

- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update API docs if endpoints change
- Keep bilingual outputs in sync (EN + HI)

## Questions?

Open a GitHub Discussion or tag @peepladivye-eng in an issue.

---

**Remember**: This code helps real people in real disasters. Quality matters.
