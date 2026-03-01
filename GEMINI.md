# Project Mandates

- **Git Workflow:** You MUST use `git worktree` for any significant feature work, bug fixes, or architectural changes. Always isolate your development from the main branch.
- **Branch Naming:** All new branches MUST include a reference to the corresponding `TODO.md` item.
    - Format: `[type]/[todo-keyword]-[short-description]` (e.g., `feat/legacy-api-integration`, `fix/recursive-rag-latency`).
- **Skill Activation:** At the start of any new development task, you MUST activate the `using-git-worktrees` skill to guide the isolation process.
- **TODO Management:** After completing any significant task, feature, or identifying technical debt, you MUST update the `TODO.md` file at the root of the project. 
- **Logging Requirements:** For each item, you must track and log:
    - **Dates:** Relevant timestamps for `Created`, `Updated`, `Completed`, or `Aborted`.
    - **PR Reference:** Link or reference the Pull Request associated with the task once created.
- **Refinement:** Mark completed items with `[x]` and add new items with appropriate priority and effort estimation (Small/Medium/Large).
