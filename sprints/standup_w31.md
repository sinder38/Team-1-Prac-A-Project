# Stand up notes

# Scrum Master 

**Main Scrum Master:** Whitley  
**Support Scrum Master:** Shary

## What have you completed or contributed so far?

- I coordinated the sprint by following up with team members and monitoring their progress throughout the week.
- I updated the Scrum documentation, including the daily stand-up notes, mid-week check-in, sprint backlog, and retrospective.
- I tracked pull requests, followed up on pending reviews, and communicated with developers to identify blockers.
- I worked with the presentation team to prepare the Scrum Master slides.
- I ensured the sprint progress was properly documented.

## Did you face any blockers or challenges?

- The main challenge was receiving timely updates from some team members.
- A few tasks changed during the sprint, making it necessary to update the sprint documentation several times.
- Some pull requests required multiple review rounds before they were ready to merge.
- Tracking the overall sprint progress became more difficult as tasks continued to change.

## What went well during this sprint?

- Communication between the Product Owner, Scrum Masters, and most team members remained consistent throughout the sprint.
- Daily stand-ups and follow-ups helped track the team's progress.
- Most planned tasks were completed successfully.
- The team continued improving the project while preparing for the final presentation and release.

## Is there anything we can improve as a team?

- Continue providing regular progress updates throughout the sprint.
- Submit pull requests earlier to allow enough time for reviews and revisions.
- Report blockers as soon as they arise.
- Keep communication active so everyone stays informed of changes and project progress.




# Developers


# Jason (Junyi Qi)

## What have you completed or contributed so far?

- Fixed the Delta report week/run numbering.
- Made Final Predictions track each run independently.
- Implemented simple single-admin authentication.
- Enabled visitors to view results while restricting pipeline execution, file exports, and Human Score/Final Prediction editing to the administrator.
- Completed PR #112, with all backend and frontend tests passing and ready for review.

## Did you face any blockers or challenges?

- Identifying the root cause was challenging because some existing tests preserved the incorrect cross-run behaviour.
- Full manual pipeline testing was blocked at Stage 3 because Ollama was not installed or running locally.
- The blocker was related to the local development environment rather than the implemented changes.

## What went well during this sprint?

- Verified reported issues before implementing fixes.
- Kept the implementation simple and maintainable.
- Added regression tests for each fix.
- Used the existing database structure to support per-run Final Predictions without requiring a migration.
- Passed Ruff, Pyright, frontend build, automated tests, and CI successfully.

## Is there anything we can improve as a team?

- Define clearer acceptance criteria when assigning development tasks.
- Maintain a shared development environment for Ollama/OpenRouter to improve testing consistency.
- Run the complete frontend and backend workflow before code review.
- Keep model names in `server.toml` consistent with their corresponding model IDs.




# Zaw Latt Naung

## What have you completed or contributed so far?

- Decoupled LLMs, IO, Schemas, and Pipeline from the `agents/` directory into separate top-level modules (`core/`, `llm/`, and `pipeline/`).
- Refactored the `agents/` directory so it only contains domain agents (Almanac, Technical, Macro, Evidence, and Delta).
- Updated approximately 40 files with corrected import paths across the codebase.
- Preserved all existing agent logic with no functional changes during the structural reorganization.
- Successfully passed all 249 automated tests after the refactoring.

## Did you face any blockers or challenges?

- Keeping the branch synchronized with `main` was the biggest challenge.
- Rebasing after new merges into `main` sometimes overwrote the updated import paths.
- Merge conflict resolution occasionally reverted changes by accepting the wrong version.
- Learned to preserve the latest code from `main` while reapplying only the required import path changes.

## What went well during this sprint?

- Successfully achieved a clean separation between the project modules.
- Improved the dependency structure, making it clearer and easier to maintain.
- Once the correct merge conflict workflow was established, development progressed smoothly.
- The automated test suite quickly identified outdated import paths, helping ensure a successful refactor.

## Is there anything we can improve as a team?

- Synchronize long-running branches with `main` more frequently to reduce merge conflicts.
- Carefully review file-move pull requests to ensure they only contain structural changes and do not accidentally revert application logic.
