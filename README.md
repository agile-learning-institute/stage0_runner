# Stage0 Runner Container Repository

This repository contains the `stage0_runner` container, responsible for executing runbooks in an automated environment.

## Project Structure
```
.
├── Dockerfile               # Docker configuration for building the stage0_runner container
├── src/                     # Source code for the runner
├── schemas/                 # JSON/YAML schemas for runbooks and runbook executions
│   ├── runbook_schema.yaml  # Schema definition for runbooks
│   └── execution_schema.yaml # Schema definition for runbook executions
├── test/                    # Tests for the runner
│   └── stepci.yaml          # StepCI tests for integration and load testing
└── Pipfile                  # Pipenv dependencies and scripts
```

## Pipenv Automation Scripts

- **Clean temporary files:**
  ```sh
  pipenv run clean
  ```
- **Setup test folders and files:**
  ```sh
  pipenv run setup
  ```
- **Run locally with test folders:**
  ```sh
  pipenv run local
  ```
- **Build the Docker container:**
  ```sh
  pipenv run build
  ```
- **Run the container with test folders set:**
  ```sh
  pipenv run container
  ```

## Usage
- **Local Development:** Run `pipenv run local` for local execution.
- **Build Container:** Use `pipenv run build` to build the Docker image.
- **Clean Up:** Run `pipenv run clean` to remove temporary files.
- **Setup Tests:** Initialize test folders with `pipenv run setup`.
- **Deploy and Run Container:** Use `pipenv run container` to build and run the container with test data.

## Schemas
- **Runbook Schema:** Defines the structure of runbook metadata, input/output schemas, versioning, and scripts.
- **Runbook Execution Schema:** Defines the structure for tracking runbook executions, including input, output, status, and audit information.

For detailed schema definitions, see the `schemas/` directory.

## Contributing
- Ensure all code is tested before committing.
- Use `pipenv run build` before pushing to ensure the container builds correctly.
- Follow the project structure and maintain documentation for any new additions.

## License
This project is licensed under the MIT License.

---

*Happy automating with `stage0_runner`!* 🚀

