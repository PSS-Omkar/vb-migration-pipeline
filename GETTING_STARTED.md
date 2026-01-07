# Getting Started: VB to C#/Java Migration Pipeline

This guide will walk you through setting up and running the automated VB-to-C# migration pipeline from scratch. Follow these steps in order to get your environment operational.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Repository Setup](#initial-repository-setup)
3. [Configure GitHub Secrets](#configure-github-secrets)
4. [Create Protected Branches](#create-protected-branches)
5. [Verify Workflows](#verify-workflows)
6. [Run Your First Conversion](#run-your-first-conversion)
7. [Local Development Setup](#local-development-setup)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

### Required Access
- [x] GitHub repository with **Admin** permissions
- [x] Access to an LLM API (OpenAI, Azure OpenAI, or CodeLlama)
- [x] API key for the LLM service

### Required Tools (for local development)
- [x] Git (version 2.30+)
- [x] Docker Desktop (for local compilation testing)
- [x] Python 3.9+ (for running conversion scripts locally)
- [x] Visual Studio Code with DevContainers extension (recommended)

### Knowledge Requirements
- Basic understanding of Git workflows
- Familiarity with GitHub Actions
- Understanding of Pull Request review processes

---

## Initial Repository Setup

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd vb-to-c#
```

### Step 2: Verify Repository Structure

Ensure your repository contains the following structure:

```
vb-to-c#/
├── .github/workflows/
│   ├── conversion_pipeline.yml
│   └── compilation_pipeline.yml
├── docker/
│   ├── Dockerfile.build_cs
│   └── Dockerfile.build_java
├── prompts/
│   ├── system_prompt.txt
│   └── task_prompt.txt
├── scripts/
│   ├── convert.py
│   └── validate.sh
├── src/
│   ├── original/
│   └── generated/
├── README.md
└── TECHNICAL_DOCUMENTATION.md
```

> [!TIP]
> If any directories are missing, create them now using `mkdir -p <directory-name>`.

---

## Configure GitHub Secrets

### Step 1: Navigate to Repository Settings

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### Step 2: Add Required Secrets

Add the following secrets:

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `LLM_API_KEY` | Your LLM API authentication token | `sk-proj-abc123...` |
| `LLM_ENDPOINT` | API endpoint URL (optional for OpenAI) | `https://api.openai.com/v1/chat/completions` |

> [!IMPORTANT]
> **Never commit these values to your repository.** Always use GitHub Secrets for sensitive data.

### Step 3: (Optional) Configure GitHub App for Branch Protection Bypass

If you need the CI/CD pipeline to bypass branch protection rules:

1. Create a GitHub App with repository write permissions
2. Install the app on your repository
3. Add these additional secrets:
   - `APP_ID`: Your GitHub App ID
   - `PRIVATE_KEY`: Your GitHub App private key (PEM format)

---

## Create Protected Branches

### Step 1: Create the Required Branches

Run the following commands to create all necessary branches:

```bash
# Create and push source branch
git checkout -b vb_banking_v1
git push -u origin vb_banking_v1

# Create and push C# generated branch
git checkout -b cs_generated_v1
git push -u origin cs_generated_v1

# Create and push Java generated branch
git checkout -b java_generated_v1
git push -u origin java_generated_v1

# Create and push release branch
git checkout -b compiled_release_v1
git push -u origin compiled_release_v1

# Return to main
git checkout main
```

### Step 2: Configure Branch Protection Rules

For **each branch** (`vb_banking_v1`, `cs_generated_v1`, `java_generated_v1`, `compiled_release_v1`):

1. Go to **Settings** → **Branches** → **Add branch protection rule**
2. Enter the branch name pattern (e.g., `vb_banking_v1`)
3. Enable the following settings:

   - ✅ **Require a pull request before merging**
     - ✅ Require approvals: **1**
   - ✅ **Require status checks to pass before merging**
   - ✅ **Do not allow bypassing the above settings**
   - ✅ **Restrict who can push to matching branches** (for `compiled_release_v1` only)

4. Click **Create**

> [!WARNING]
> **Critical:** The `compiled_release_v1` branch should only accept PRs from the GitHub Actions bot. Configure the restriction accordingly.

---

## Verify Workflows

### Step 1: Check Workflow Files

Verify that both workflow files exist:

```bash
ls -la .github/workflows/
```

You should see:
- `conversion_pipeline.yml`
- `compilation_pipeline.yml`

### Step 2: Validate Workflow Syntax

1. Go to **Actions** tab in your GitHub repository
2. Check for any syntax errors in the workflows
3. If errors exist, they will be displayed with line numbers

### Step 3: Enable GitHub Actions

1. Go to **Settings** → **Actions** → **General**
2. Under **Actions permissions**, select:
   - ✅ **Allow all actions and reusable workflows**
3. Under **Workflow permissions**, select:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
4. Click **Save**

---

## Run Your First Conversion

### Step 1: Add Sample VB Code

Create a simple VB file to test the pipeline:

```bash
# Switch to the source branch
git checkout vb_banking_v1

# Create a sample VB file
mkdir -p src/original
cat > src/original/Calculator.vb << 'EOF'
Public Class Calculator
    Public Function Add(ByVal a As Integer, ByVal b As Integer) As Integer
        Return a + b
    End Function
    
    Public Function Subtract(ByVal a As Integer, ByVal b As Integer) As Integer
        Return a - b
    End Function
End Class
EOF

# Commit and push
git add src/original/Calculator.vb
git commit -m "Add sample Calculator class for testing"
git push origin vb_banking_v1
```

### Step 2: Monitor the Conversion Pipeline

1. Go to the **Actions** tab in GitHub
2. You should see a new workflow run for **Conversion Pipeline**
3. Click on the run to view detailed logs
4. Wait for the workflow to complete (typically 2-5 minutes)

### Step 3: Review the Generated Pull Request

1. Go to the **Pull Requests** tab
2. You should see a new PR titled something like `AI Conversion - feat/ai-conversion-[timestamp]`
3. Click on the PR to review:
   - **Files changed**: Review the generated C# code
   - **Checks**: Ensure all validation checks passed
4. If the code looks correct, click **Approve** and **Merge**

### Step 4: Monitor the Compilation Pipeline

1. After merging, the **Compilation Pipeline** will automatically trigger
2. Go to **Actions** tab and monitor the compilation workflow
3. If successful, a new PR to `compiled_release_v1` will be created
4. Review and merge the release PR

> [!NOTE]
> The entire process from VB commit to compiled release should take approximately 5-10 minutes for a simple file.

---

## Local Development Setup

### Option 1: Using DevContainers (Recommended)

1. Open the repository in Visual Studio Code
2. Install the **Dev Containers** extension
3. Press `F1` and select **Dev Containers: Reopen in Container**
4. Wait for the container to build (first time only)
5. You now have a fully configured development environment

### Option 2: Manual Setup

#### Install Python Dependencies

```bash
cd scripts
pip install -r requirements.txt
```

> [!TIP]
> If `requirements.txt` doesn't exist, create it with common dependencies:
> ```
> openai>=1.0.0
> requests>=2.31.0
> python-dotenv>=1.0.0
> ```

#### Test Conversion Locally

```bash
# Set environment variables
export LLM_API_KEY="your-api-key-here"
export LLM_ENDPOINT="https://api.openai.com/v1/chat/completions"

# Run conversion
python scripts/convert.py \
  --source src/original/Calculator.vb \
  --target-lang CSHARP \
  --model gpt-4-turbo \
  --output src/generated/Calculator.cs
```

#### Test Compilation Locally

```bash
# Build the Docker image
docker build -f docker/Dockerfile.build_cs -t vb-migration-cs .

# Run compilation
docker run --rm -v $(pwd):/app vb-migration-cs
```

---

## Troubleshooting

### Issue: Workflow Not Triggering

**Symptoms:** Push to `vb_banking_v1` doesn't start the conversion pipeline.

**Solutions:**
1. Verify GitHub Actions is enabled (Settings → Actions)
2. Check workflow file syntax in `.github/workflows/conversion_pipeline.yml`
3. Ensure the trigger branch matches: `on: push: branches: [vb_banking_v1]`

---

### Issue: LLM API Errors

**Symptoms:** Conversion fails with "API authentication failed" or "Rate limit exceeded".

**Solutions:**
1. Verify `LLM_API_KEY` secret is correctly set
2. Check API key permissions and quota
3. Review `MAX_RETRIES` setting in workflow environment variables
4. For rate limits, reduce the number of files processed per run

---

### Issue: Compilation Failures

**Symptoms:** Generated code fails to compile in the Docker container.

**Solutions:**
1. Review the generated code for syntax errors
2. Check if the LLM hallucinated non-existent APIs
3. Verify the Dockerfile has the correct SDK version
4. Test compilation locally using the Docker command above
5. If persistent, manually fix the code and push to the generated branch

---

### Issue: Branch Protection Blocking Merges

**Symptoms:** Cannot merge PRs due to protection rules.

**Solutions:**
1. Ensure you have the required number of approvals
2. Check that all status checks are passing
3. Verify you have admin permissions or use the GitHub App bypass
4. Review branch protection settings for conflicts

---

### Issue: Missing Dependencies in Generated Code

**Symptoms:** Compilation fails with "namespace not found" errors.

**Solutions:**
1. Update the prompt templates to specify required dependencies
2. Add dependency installation steps to the Dockerfile
3. Create a `.csproj` or `pom.xml` file with explicit dependencies
4. Review the LLM output for incorrect namespace references

---

## Next Steps

Now that your pipeline is operational:

1. **Read the Technical Documentation**: Review [TECHNICAL_DOCUMENTATION.md](./TECHNICAL_DOCUMENTATION.md) for architectural details
2. **Customize Prompts**: Edit files in `prompts/` to improve conversion quality
3. **Add More VB Files**: Gradually migrate your codebase file by file
4. **Monitor Costs**: Track LLM API usage and set budget alerts
5. **Iterate on Failures**: Use failed conversions to refine your prompts

---

## Support and Resources

- **Technical Details**: [TECHNICAL_DOCUMENTATION.md](./TECHNICAL_DOCUMENTATION.md)
- **Quick Reference**: [README.md](./README.md)
- **Workflow Logs**: GitHub Actions tab
- **Issue Tracking**: GitHub Issues tab

> [!CAUTION]
> This pipeline is designed to **accelerate** migration, not replace human engineering. Always review AI-generated code before deploying to production.

---

**Last Updated:** 2026-01-07  
**Pipeline Version:** v1.0
