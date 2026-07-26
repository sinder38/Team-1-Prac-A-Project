# Scrum Master

## Main - Whitley

## Support - Shary

### What have you completed or contributed so far?

I coordinated the sprint by following up with team members about their assigned tasks and current progress.
I updated the Scrum documentation, standup notes, sprint backlog, and sprint retrospective throughout the sprint.
I monitored pull requests, review progress, merge conflicts, and repository activity.
I communicated with developers and the Product Owner to clarify task assignments and identify blockers.
I collected progress updates from the team and coordinated the Scrum Master section for the sprint presentation.

### Did you face any blockers or challenges?

Some team members were busy with internships or other assignment deadlines, so progress updates were sometimes delayed.
There was occasional confusion about task ownership when priorities changed, which required additional clarification.
Several pull requests required multiple review rounds before they were ready to be merged.
Keeping the sprint documentation up to date was challenging because development and review statuses changed frequently.

### What went well during this sprint?

Team members continued making steady progress on their assigned tasks.
Communication between the Scrum team and developers helped identify blockers and track sprint progress.
Documentation and sprint tracking remained organised throughout the sprint.
The team worked together to prepare both the project deliverables and presentation materials.

### Is there anything we can improve as a team?

Provide progress updates more consistently throughout the sprint.
Clarify task ownership whenever new tasks or priorities are introduced.
Address pull request feedback as early as possible to reduce review delays.
Communicate blockers promptly so the team can provide support when needed.



# Development Tean

## Henry

### What have you completed or contributed so far?

Reviewed and updated the project documentation for Week 8.
Updated the README with the latest project structure and active LLM configurations.
Clarified the difference between local Ollama testing and the four-model CI pipeline.
Added the Flask server commands and `server.toml` setup instructions.
Documented the Delta Engine.
Reorganised the documentation by shortening the README and moving detailed content into GitHub Wiki pages.

### Did you face any blockers or challenges?

Keeping the documentation consistent with the latest code changes was challenging because several parts of the project changed during development.
I also needed to separate the pipeline architecture from the overall system architecture and decide what information should remain in the README versus the GitHub Wiki.

### What went well during this sprint?

The project documentation became clearer, more accurate, and easier for new contributors to understand.
Reviewer feedback helped improve the documentation quality.
The pull request was updated successfully after addressing the review comments.

### Is there anything we can improve as a team?

Communicate major code and configuration changes earlier so documentation can be updated throughout the sprint.
Agree on naming conventions, architecture diagrams, and feature status before the final documentation review.



## Zaw Latt Naung

### What have you completed or contributed so far?

My previous Almanac Agent test task was successfully merged into the main branch.
I continued working on my second assigned task and addressed the review feedback by making the requested changes.
The pull request is now ready to be merged.

### Did you face any blockers or challenges?

Several files and parts of the codebase changed during development, which resulted in merge conflicts that needed to be resolved before updating the pull request.

### What went well during this sprint?

The structural refactoring was completed successfully without changing the existing logic.
The Almanac tests continue to be validated using real reference data with page citations, making the implementation easier for reviewers to verify.

### Is there anything we can improve as a team?

Keep local branches up to date with the main branch before starting larger refactoring tasks to reduce merge conflicts.



## Sai Ko

### What have you completed or contributed so far?

Updated the Technical Agent regression test pull request (#49).
Redesigned the regression tests to compare the manual W22/W23 technical reports with the agent's automatically generated output.
Moved the tests into `backend/tests/` and updated the imports to follow the project structure.
Cleaned up the test code, merged the latest changes from the main branch, and pushed the updated pull request.
Verified that all six regression tests passed successfully.

### Did you face any blockers or challenges?

I initially misunderstood the testing objective and focused on unit testing internal helper methods instead of comparing manual and automated outputs.
Some manual EMA values did not exactly match the computed EMAs, so the tests were redesigned to validate price data, EMA structure, bias, and confidence instead of exact EMA values.
My branch was also behind the main branch, requiring a merge before the pull request could be updated.

### What went well during this sprint?

The review feedback clearly explained the required testing approach, making it easier to improve the implementation.
Once the testing objective was clarified, the regression tests were completed smoothly.
Using real historical data from Weeks 22 and 23 improved the reliability and usefulness of the regression test suite.

### Is there anything we can improve as a team?

Continue providing clear review feedback and communicate task expectations early.
Maintain the team's active participation and collaboration throughout the sprint.



## Jason

### What have you completed or contributed so far?

Continued developing the Delta Engine and integrated it with the pipeline, backend, and frontend.
Implemented the Delta report export from the SQLite database to Markdown.
Fixed the history page so partially completed pipeline runs are no longer displayed as fully completed.
Verified the implementation through backend tests, frontend tests, type checking, and browser testing.

### Did you face any blockers or challenges?

Understanding how the Delta Engine should integrate with the existing application without affecting other components was challenging.
I also resolved branch conflicts and ensured that partially completed pipeline progress was restored correctly after refreshing the page.

### What went well during this sprint?

The Delta Engine is now better integrated with the application.
Automated testing helped identify issues before the pull request was ready for review.
Team feedback clarified the expected behaviour and helped improve the implementation.

### Is there anything we can improve as a team?

Define the expected inputs, outputs, and integration points more clearly before development begins.
Communicate branch updates and changes earlier, especially when multiple pull requests modify the same files.
















