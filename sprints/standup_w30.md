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



## Oakkar

### What have you completed or contributed so far?

Implemented the Final Prediction user interface.
Fixed archive loading issues and improved the week picker so newly generated weeks remain selectable.
Reviewed teammates' pull requests and provided feedback.

### Did you face any blockers or challenges?

Managing the archive and new-run states was challenging because cached data carried over between runs.
The week selector also lost newly generated weeks after viewing archived results.

### What went well during this sprint?

Code review feedback was clear and helpful, making it easier to improve the implementation and resolve issues.

### Is there anything we can improve as a team?

Reply to pull request comments after addressing the requested changes so reviewers know when the pull request is ready for another review.



## Georgii

### What have you completed or contributed so far?

Implemented local persistence using SQLite.
Reviewed, merged, and fixed pull requests.
Assigned development tasks to team members.
Identified several issues, including continuity errors, incomplete deliveries, and unstable AI models.
Prepared the sprint goal and acceptance criteria.
Fixed the weekly pipeline before the final run.

### Did you face any blockers or challenges?

Migrating the project to SQLite persistence was more complex than expected and introduced several issues during implementation.
Some work was completed very close to the deadline, leaving limited time for review and integration.

### What went well during this sprint?

The core development team worked well together and understood the project workflow.
Most development tasks were completed earlier than in previous sprints.
Most of the planned sprint objectives were successfully completed.

### Is there anything we can improve as a team?

Complete assigned tasks earlier to allow sufficient time for testing and code review.
Maintain a high standard of work before submitting pull requests for review.



## Naing Phone Pyae

### What have you completed or contributed so far?

Implemented the prediction range feature in both the backend and frontend.
Updated the Almanac Agent and Macro Agent to retrieve seasonal data and future events based on the selected prediction range.
Modified the LLM prompts to generate predictions according to the selected prediction horizon.
Updated the encoded Almanac data to support additional future weeks.

### Did you face any blockers or challenges?

Implementing the prediction range across both the backend and frontend was challenging.
Testing the LLM integration also required additional effort to ensure the prompts and outputs worked as expected.

### What went well during this sprint?

The prediction range feature is working as intended across all agents.
The updated LLM prompts correctly generate predictions based on the selected prediction horizon.
The implementation has been submitted as a pull request and is awaiting review and merge.

### Is there anything we can improve as a team?

The team showed stronger participation throughout this sprint.
We should continue maintaining this level of collaboration and communication in future sprints.



## Aeron

### What have you completed or contributed so far?

Completed the Human Score and Final Prediction tasks.
Researched additional free AI models to replace rate-limited models and support the project pipeline.
Assisted with the final project deliverables.

### Did you face any blockers or challenges?

I did not encounter any major technical blockers.
The main challenge was editing the project demonstration video because the original recording exceeded the file size limit.

### What went well during this sprint?

I became more familiar with the development workflow and codebase.
I communicated with the development team to better understand the implementation and complete my assigned tasks.

### Is there anything we can improve as a team?

I participated more actively during this sprint than in previous weeks.
We should continue encouraging active participation and collaboration across the team.



## Minghao

### What have you completed or contributed so far?

Finalised most of the presentation slides and speaker notes for the sprint presentation.
Assisted in researching alternative free LLM models to replace rate-limited models and support the project pipeline.

### Did you face any blockers or challenges?

Some pull requests were submitted later than expected, making it difficult to finalise the presentation early.
The presentation content had to be updated continuously as development tasks and pull request statuses changed.

### What went well during this sprint?

Most team members were more productive compared to previous sprints.
Many development tasks were completed earlier than expected, allowing the presentation to progress more smoothly.

### Is there anything we can improve as a team?

Assign team roles and tasks earlier so deadlines can be planned more effectively.
Continue monitoring task progress throughout the sprint to reduce delays and ensure work is completed on time.




**Henry**
actual work -
Created all wiki
Updated README
not more not less

**Zaw Latt Naung**
hes improvement suggestion is irrelevant, its his responsobility, and is just a consequence of fast development and his slow progress
