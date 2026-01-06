# Technical Specification: Automated VB to C#/Java LLM Conversion Pipeline

## 1. Overview & Goals

This document details the technical architecture and operational procedures for an automated GitOps-based CI/CD pipeline designed to migrate legacy Visual Basic (.vb) codebases to modern languages (C# or Java). The system leverages Large Language Models (LLMs) such as OpenAI or CodeLlama for code translation, wrapped within a rigid governance framework to ensure code quality, security, and auditability.

 **Primary Goals:**
*   **Automated Modernization:** Reduce manual effort in translating legacy code.
*   **Deterministic Governance:** Enforce strict review processes via Pull Requests (PRs) and containerized validation.
*   **Auditability:** Maintain a complete trace of source code, AI prompts, raw AI outputs, and final reviewed code.
*   **Safety:** Treat LLM outputs as untrusted entities requiring compilation and human verification before release.

## 2. Architecture & Design Principles

The architecture follows a strict "Trust but Verify" model. LLMs are utilized solely as transformation engines, not decision makers.

**Core Principles:**
*   **Immutable Infrastructure:** All build and validation steps occur in ephemeral Docker containers.
*   **GitOps Driven:** All state changes (code generation, validation success, release) are recorded as Git commits or PRs.
*   **Sequential Processing:** To manage rate limits and ensure fault isolation, LLM calls are executed serially per file.
*   **Security First:** No direct pushes to generated or release branches. All changes must pass through CI/CD gates.
*   **Platform:** Exclusively uses GitHub-hosted runners (`ubuntu-latest`) to eliminate infrastructure maintenance overhead.

## 3. End-to-End Workflow Diagram

```mermaid
graph TD
    subgraph "Phase 1: Source & Trigger"
        VB[vb_banking_v1 (Source)] -->|Push/Trigger| GHA[GitHub Actions Runner]
    end

    subgraph "Phase 2: Conversion Pipeline"
        GHA -->|Read .vb file| SCRIPT[Conversion Script (Python)]
        SCRIPT -->|Fetch Prompt Template| PROMPTS[./prompts/*.txt]
        SCRIPT -->|API Call (Sequential)| LLM[LLM Endpoint (OpenAI/CodeLlama)]
        LLM -->|Raw Code| SCRIPT
        SCRIPT -->|Syntax/Static Check| VALIDATE[Local Validation]
        VALIDATE -- Fail --> FAIL_LOG[Log Failure & Notify]
        VALIDATE -- Pass --> NEW_BRANCH[Create Feature Branch]
    end

    subgraph "Phase 3: Governance & Review"
        NEW_BRANCH -->|Auto-Create PR| PR[Pull Request to generated_v1]
        PR -->|Human Review| APPROVE[Approval]
        APPROVE -->|Merge| TARGET[cs_generated_v1 / java_generated_v1]
    end

    subgraph "Phase 4: Compilation & Release"
        TARGET -->|Trigger| BUILD_FLOW[Compilation Workflow]
        BUILD_FLOW -->|Spin up Docker| DOCKER[Docker Container (SDK)]
        DOCKER -->|Compile| ARTIFACT[Build Artifact]
        ARTIFACT -- Success --> RELEASE_PR[PR to compiled_release_v1]
        ARTIFACT -- Fail --> NOTIFY[Developer Notification]
    end
```

## 4. Repository Structure

The repository is structured to separate source, infrastructure, and generated artifacts.

```text
/
├── .github/
│   ├── workflows/
│   │   ├── conversion_pipeline.yml  # Triggers on changes to vb_banking_v1
│   │   └── compilation_pipeline.yml # Triggers on changes to *_generated_v1
├── .devcontainer/                   # DevContainer config for local debugging
├── src/
│   ├── original/                    # Legacy VB source code
│   └── generated/                   # Placeholder for local testing (not committed)
├── scripts/
│   ├── convert.py                   # Main orchestration script for LLM interaction
│   └── validate.sh                  # Pre-commit static analysis script
├── prompts/
│   ├── system_prompt.txt            # Persona and constraint definitions
│   └── task_prompt.txt              # Specific translation instructions
├── docker/
│   ├── Dockerfile.build_cs          # .NET SDK container definition
│   └── Dockerfile.build_java        # JDK/Maven container definition
└── README.md
```

## 5. Branching & GitOps Strategy

The branching strategy protects code integrity and enforces the review process.

| Branch Name | Purpose | Protection Rules |
| :--- | :--- | :--- |
| `vb_banking_v1` | **Source Truth**. Contains legacy VB code. | Protected. Requires PR to update. |
| `cs_generated_v1` | **Staging (C#)**. Accumulated valid AI output. | **Restricted**. No direct push. PR required. |
| `java_generated_v1`| **Staging (Java)**. Accumulated valid AI output. | **Restricted**. No direct push. PR required. |
| `compiled_release_v1` | **Production**. Verified, compiled artifacts. | **Frozen**. Only automated PRs from CI/CD can merge. |
| `feat/ai-conversion-*` | Temporary branch for a single AI conversion run. | Deleted after merge. |

## 6. Secrets & Configuration Management

Sensitive data is managed via GitHub Secrets. Configuration is strictly separated from code.

**Required Secrets:**
*   `LLM_API_KEY`: API authentication token (OpenAI/Azure/Other).
*   `LLM_ENDPOINT`: URL for the inference API.
*   `APP_ID` / `PRIVATE_KEY`: GitHub App credentials for bypassing branch protection if necessary (preferred over PAT).

**Environment Variables (Workflow Level):**
*   `TARGET_LANG`: `CSHARP` or `JAVA`.
*   `MODEL_VERSION`: e.g., `gpt-4-turbo` or `codellama-70b`.
*   `MAX_RETRIES`: Integer (default: 3).

## 7. GitHub Actions Workflows

### 7.1. Conversion Pipeline (`conversion_pipeline.yml`)
**Trigger:** `push` on `vb_banking_v1`.
**Runner:** `ubuntu-latest`.

**Steps:**
1.  **Checkout:** Clone repository.
2.  **Identify Changes:** Use `git diff` to find modified `.vb` files.
3.  **Setup Environment:** Install Python dependencies for the orchestration script.
4.  **Execute Conversion (Loop):**
    *   For each changed file, invoke `scripts/convert.py`.
    *   **Sequential Processing:** Files are processed one by one to monitor API rate limits.
    *   **Context Loading:** Read `prompts/system_prompt.txt` and the target `.vb` file.
    *   **LLM Invocation:** Send payload to API.
    *   **Retry Logic:** If API fails (5xx) or output is malformed, retry up to `MAX_RETRIES`.
5.  **Validation:** Run basic syntax check on generated code (e.g., `dotnet build --no-restore` in dry-run mode or basic parsing).
6.  **PR Creation:**
    *   Create a new branch `feat/ai-conversion-[timestamp]`.
    *   Commit generated files.
    *   Open a Pull Request targeting `cs_generated_v1` or `java_generated_v1`.
    *   Assign to human reviewers.

### 7.2. Compilation Pipeline (`compilation_pipeline.yml`)
**Trigger:** `push` (merge) to `cs_generated_v1` or `java_generated_v1`.
**Runner:** `ubuntu-latest`.

**Steps:**
1.  **Checkout:** Clone the generated branch.
2.  **Build Container:** Docker build using `docker/Dockerfile.build_cs` (or Java eq).
3.  **Compile:** Run the build command *inside* the container.
    *   `docker run --rm -v $(pwd):/app build_image dotnet build /app`
4.  **Test:** Execute unit tests if available.
5.  **Release Gate:**
    *   **If Success:** Create a PR to `compiled_release_v1` with the build log attached.
    *   **If Failure:** Post a comment on the merge commit and notify the developer/owner via email/Slack.

## 8. LLM Conversion Logic

The `scripts/convert.py` script acts as the conversion engine.

**Logic Flow:**
1.  **Input:** Path to `.vb` file.
2.  **Prompt Assembly:** Concatenate `system_prompt` + `task_prompt` + `source_code`.
    *   *Technique:* Use Chain-of-Thought (CoT) prompting to ask the model to plan the conversion before outputting code.
3.  **Governance Headers:** Inject comments into the generated code:
    ```csharp
    // AUTO-GENERATED by Pipeline ID: <RUN_ID>
    // Source: <FILE_PATH>
    // Model: <MODEL_NAME>
    // Date: <TIMESTAMP>
    ```
4.  **Response Parsing:** Extract code blocks from Markdown (triple backticks). Ignore conversational filler.
5.  **Sanity Check:** Ensure the output file interacts with the filesystem correctly (filenames match class names if required by language).

## 9. Prompt Governance & Versioning

Prompts are code. They influence the output behavior and must be versioned.

*   **Storage:** All prompts reside in the `prompts/` directory.
*   **Versioning:** Changes to prompts require a PR.
*   **Traceability:** The git commit hash of the prompt file used during conversion is logged in the pipeline output and injected into the generated code header.
*   **Locking:** During critical migration phases, the `prompts/` directory should be locked via `CODEOWNERS` to prevent unauthorized changes.

## 10. Validation Layer

Validation occurs at two stages:

1.  **pre-PR (Machine):** Syntactic validation.
    *   The script attempts to parse the generated code.
    *   Simple heuristic checks: "Does it have a class structure?", "Are brackets balanced?"
2.  **PR Review (Human):** Semantic validation.
    *   Engineers review the diff.
    *   Focus on logic errors, hallucinations (calls to non-existent libraries), and security flaws.
3.  **post-Merge (Machine):** Compilation validation.
    *   Full compile in Docker.
    *   Ensures dependencies are resolved and type safety is maintained.

## 11. Compilation & Container Strategy

To ensure reproducibility and isolation, compilation never happens directly on the runner.

**Strategy:**
*   **One Container Per Runtime:** Specific Dockerfiles for .NET SDK and JDK.
*   **Volume Mounting:** Source code is mounted into the container at runtime.
*   **No Network Checks:** Where possible, dependency restoration should verify lock files.
*   **Environment Parity:** The Docker image used in CI is available for developers to pull and use locally for debugging.

**Example `Dockerfile.build_cs`:**
```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0
WORKDIR /app
COPY . .
ENTRYPOINT ["dotnet", "build"]
```

## 12. Failure Handling & Notification Flow

**Failure Types:**
1.  **API Failure (LLM):** network timeouts, rate limits.
    *   *Action:* Exponential backoff retry. If max retries types, skip file and log error. Fail workflow at end.
2.  **Validation Failure (Syntax):**
    *   *Action:* Discard generated code. Log "Validation Failed" artifact. Do not open PR.
3.  **Compilation Failure (Build):**
    *   *Action:* Mark CI run as failed. Notify team. Block promotion to `compiled_release_v1`.

**Notification:**
*   GitHub Actions Summary view populated with detailed report.
*   Integration with Slack/Teams webhook (optional) for "Build Failed" alerts.

## 13. Security, Cost, and Operational Controls

**Security:**
*   **Secret Injection:** Secrets are injected only into the `convert.py` process, never printed to logs.
*   **Code Isolation:** Untrusted AI code is isolated in a separate branch until reviewed.
*   **Audit Trail:** Every line of code in `compiled_release_v1` can be traced back to a specific PR, Workflow Run, and Source Commit.

**Cost Control:**
*   **Sequential processing** prevents massive parallel API spikes.
*   **Token limits** in API calls prevent runaway costs from infinite loops in generation.
*   **Budget alerts** configured on the LLM provider side.

## 14. Known Limitations & Non-Goals

*   **Non-Goal:** 100% perfect compilation without human intervention. The system is an *accelerator*, not a replacement for engineers.
*   **Limitation:** Complex dependencies or proprietary VB libraries may inherently fail conversion and require manual refactoring.
*   **Limitation:** LLMs may "hallucinate" APIs that do not exist in the target framework version.
*   **Non-Goal:** Converting GUI forms (WinForms) to Web formats automatically. This pipeline focuses on business logic / backend code.

## 15. Operational Rules & Guardrails

1.  **Golden Rule:** Never force-merge into `compiled_release_v1`.
2.  **Review Rule:** At least one senior engineer must approve AI-generated PRs.
3.  **Prompt Rule:** Do not include PII or sensitive hard-coded secrets in prompts (scrub source code before sending if necessary).
4.  **Override:** If the AI is stuck on a file, a human engineer can manually push the converted file to the generated branch, bypassing the AI script but not the compilation check.

## 16. Summary

This system provides a robust, auditable factory for modernizing legacy code. By strictly separating the generation (AI) from the verification (Compiler/Human), it mitigates the stochastic nature of LLMs while harnessing their speed. The dependency on standard GitHub-hosted runners and Docker ensures the pipeline is portable, maintainable, and resilient to environment drift.
