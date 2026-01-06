# VB to C#/Java Automated Migration Pipeline

## Overview
This repository implements an automated GitOps-based CI/CD pipeline for converting Visual Basic (.vb) code to C# or Java using Large Language Models (LLMs). The system enforces strict governance through pull requests, containerized compilation, and comprehensive audit trails.

## Quick Start

### Prerequisites
- GitHub repository with appropriate branch protection rules
- GitHub Secrets configured:
  - `LLM_API_KEY`: OpenAI or CodeLlama API key
  - `LLM_ENDPOINT`: API endpoint URL (optional)

### Branch Structure
- `vb_banking_v1`: Source VB code (protected)
- `cs_generated_v1`: C# generated code staging (protected)
- `java_generated_v1`: Java generated code staging (protected)
- `compiled_release_v1`: Production-ready compiled code (protected)

### Workflow
1. Push VB code changes to `vb_banking_v1`
2. Conversion pipeline automatically triggers
3. Review and approve the generated PR
4. Merge triggers compilation pipeline
5. Successful compilation creates release PR

## Documentation
See [TECHNICAL_DOCUMENTATION.md](./TECHNICAL_DOCUMENTATION.md) for comprehensive technical details.

## Local Development
Use the provided DevContainer for a consistent development environment:
```bash
code .
# Select "Reopen in Container" when prompted
```

## Testing Conversion Locally
```bash
python scripts/convert.py \
  --source src/original/example.vb \
  --target-lang CSHARP \
  --model gpt-4-turbo
```

## Security Notes
- Never commit API keys or secrets
- All generated code must be reviewed before merge
- Compilation occurs in isolated Docker containers
- Branch protection rules are mandatory

## Support
For issues or questions, refer to the technical documentation or contact the platform team.
