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



# Henry (TOBI)

## What have you completed or contributed so far?

- Updated the project Wiki to reflect the latest Week 9 implementation.
- Updated documentation for the current LLM configurations, local Ollama setup, CI pipeline, Flask backend, system architecture, and Delta Engine.
- Started working on removing the duplicated `prediction_date` argument from `render_md()`.
- Updated the shared `BaseAgent` interface, LLM implementation, and multi-model runner so the date is read from `output.prediction_date`.

## Did you face any blockers or challenges?

- The current task affects multiple files, so a small interface change impacts several implementations and call sites.
- Ensuring all files remain consistent while removing outdated `render_md(output, prediction_date)` calls required careful review.
- The available task information was limited, so additional code review, discussions with teammates, and the task checklist were needed to understand the full scope.

## What went well during this sprint?

- The Wiki and README are now better organized and accurately reflect the latest project updates.
- Feedback and the task checklist helped clarify the duplicated `prediction_date` issue and identify the safest implementation approach.
- Gained a better understanding of how the Base Agent, LLM Agent, and Multi-Model Runner interact with each other.

## Is there anything we can improve as a team?

- Clearly summarize interface, model, or configuration changes in pull request descriptions, especially when they affect multiple related files.
- Provide sufficient implementation details when assigning tasks to reduce the time spent understanding the required changes.
- Continue keeping documentation aligned with code changes throughout the sprint.



# Naing Phone Pyae

## What have you completed or contributed so far?

- Completed two TODO tasks from the repository:
  - Updated `max_retries` to handle each model independently.
  - Added error handling to raise an exception if the macro fetch is not completed instead of continuing execution.
- Contributed to preparing part of the project presentation slides.

## Did you face any blockers or challenges?

- The main challenge was finding new development tasks because most major features had already been completed and were functioning correctly.
- Focused on smaller improvements and presentation support after the primary development work was finished.

## What went well during this sprint?

- Successfully completed and merged all assigned tasks into the main branch.
- Contributed to completing the presentation slides with the available project data.

## Is there anything we can improve as a team?

- Hold more technical discussions on implementation approaches and coding challenges.
- Encourage knowledge sharing among team members to improve technical skills and support smoother collaboration.




# Minghao

## What have you completed or contributed so far?

- Worked on preparing the project presentation.
- Fixed bugs in the project pipeline.
- Made minor updates to the README documentation.
- Helped remind and follow up with team members on their assigned tasks.

## Did you face any blockers or challenges?

- The main challenge was the programming tasks, as they required working with areas that were technically difficult.

## What went well during this sprint?

- Development tasks were completed efficiently.
- Additional hidden bugs within the pipeline were identified and resolved.
- The team made steady progress toward preparing the project for the final presentation.

## Is there anything we can improve as a team?

- Continue improving technical knowledge and collaboration on complex development tasks.
- Make greater use of repository packaging and analysis tools (e.g., Repomix and Gitingest) to better understand the overall project structure and implementation details.



# Georgii

## What have you completed or contributed so far?

- Deployed the project codebase to **sinder.dev**.
- Reviewed and merged pull requests.
- Assigned sprint tasks to team members.
- Fixed the Delta CI pipeline.
- Added a frontend check to the CI workflow.
- Prepared the Product Owner artifacts and sprint documentation.

## Did you face any blockers or challenges?

- Encountered the usual development and coordination challenges, with no major new blockers during the sprint.

## What went well during this sprint?

- The sprint progressed smoothly and was easier to manage compared to previous weeks.
- The overall product reached a stable and polished state.
- More team members actively contributed to the project, improving overall team productivity.

## Is there anything we can improve as a team?

- Continue enforcing the pull request guidelines to maintain code quality and consistency.
- As the team gains more experience, ensure everyone follows the established development and review process more consistently.



# Oakkar

## What have you completed or contributed so far?

- Worked on the final user interface improvements.
- Updated charts with the correct week numbers and actual results.
- Improved the About page.
- Polished various dashboard components, including the week snapshot, theme, and Final Prediction section.
- Resolved merge-related issues after synchronizing with the `main` branch to ensure the application built and ran successfully.

## Did you face any blockers or challenges?

- Merge conflicts were the main challenge throughout the sprint.
- Pulling updates from `main` occasionally introduced issues such as blank pages, duplicate forms, and CI not running on the latest commit.
- Additional time was required to resolve these issues and restore a stable build.

## What went well during this sprint?

- Once the merge issues were resolved, the application became more cohesive, with the pipeline, scores, charts, and actual results working together correctly.
- Code reviews helped identify and fix bugs before pull requests were merged, improving the overall quality of the project.

## Is there anything we can improve as a team?

- Check in with teammates more frequently when someone is experiencing difficulties.
- Continue supporting each other to resolve issues more efficiently and maintain steady sprint progress.



# Sai Ko

## What have you completed or contributed so far?

- Improved the **TechnicalAgent** regression tests.
- Successfully reviewed and merged the regression test pull request into the `main` branch (PR #49).
- Developed regression tests that compare auto-fetched agent output with manual W22 and W23 technical reports, including prices, EMA structure, bias, and confidence.
- Completed the W31 acceptance criteria for TechnicalAgent regression test coverage.

## Did you face any blockers or challenges?

- Initially waited for the pull request review and merge before the task could be completed.
- Adjusted the regression tests to fit the project structure after the codebase reorganization.
- Updated import paths and refined manual versus live-fetch comparisons to ensure stable and reliable test results.
- Required several iterations to handle tolerances and differences between the W22 and W23 EMA data before the tests were ready to merge.

## What went well during this sprint?

- Successfully completed and merged the regression test implementation into the `main` branch.
- Review feedback was clear and helped improve the quality of the implementation.
- Using historical manual reports as a baseline made the regression tests more meaningful and reliable than basic smoke tests.

## Is there anything we can improve as a team?

- Provide faster review and feedback for testing-related pull requests to avoid blocking progress.
- Maintain clear documentation of regression test expectations, including baseline weeks and validation criteria, so future contributors can extend the test coverage more efficiently.



# Aeron

## What have you completed or contributed so far?

- Completed the Human Score evaluation.
- Prepared the Final Prediction for the assigned runs.
- Worked with teammates to verify and update the project outputs.

## Did you face any blockers or challenges?

- One of the four LLM models (Laguna) intermittently failed due to rate limits, causing inconsistent results across different runs.
- Accidentally placed the output in the wrong location, which affected the team's workflow.
- Worked with teammates to identify the issue and corrected the output placement.

## What went well during this sprint?

- Successfully completed the assigned Human Score and Final Prediction tasks.
- Received feedback from teammates and resolved the output placement issue.
- Improved understanding of the project's workflow and output requirements through collaboration.

## Is there anything we can improve as a team?

- Discuss a long-term strategy for handling rate limits on free OpenRouter models, such as selecting more stable models or considering a paid tier if the issue continues to affect Stage 3 pipeline runs.
- Continue reviewing outputs together before submission to reduce mistakes and improve overall accuracy.
