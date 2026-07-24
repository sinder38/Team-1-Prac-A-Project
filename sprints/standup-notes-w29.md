# standup-notes-w29.md

# Scrum Master

## Main - Whitley

## Support - Shary

### What have you completed or contributed so far?

I coordinated the sprint by following up with team members and tracking their progress.
I updated the Scrum documentation, Kanban board, standup notes, and sprint retrospective.
I monitored pull requests and review progress.
I communicated with developers to identify blockers.
I helped keep the sprint organised.

### Did you face any blockers or challenges?

The main challenge was receiving timely updates from all team members.
Some responses were delayed during the sprint.
Several pull requests required multiple review rounds before they were ready to be merged.
This made it more difficult to track the overall sprint progress.

### What went well during this sprint?

Team communication improved as the sprint progressed.
More pull requests were submitted and reviewed.
Regular follow-ups kept everyone informed of the project's progress.
The Scrum documentation remained up to date throughout the sprint.

### Is there anything we can improve as a team?

Provide more regular progress updates.
Request pull request reviews earlier.
Resolve blockers as soon as they arise.
Keep everyone informed throughout the sprint to improve collaboration and reduce delays.

---

# Developers

## Georgii

### What have you completed or contributed so far?

Merged pull requests.
Reviewed pull requests.
Fixed pull request issues.
Added the Ollama local option.
Explained tasks to the team in the voice channel.
Committed the Product Owner artefacts.
Handled project management tasks.

### Did you face any blockers or challenges?

Some pull requests took too much time to review.
I had limited time available this week.
Some pull requests were too complex to review and merge quickly.
Some team members were inactive or submitted low-quality work.

### What went well during this sprint?

The core development team worked well together.
The Scrum Master took over some of the management responsibilities.

### Is there anything we can improve as a team?

Using CODEOWNERS could help with pull request reviews.
However, it may be unnecessary for a project of this size.

---

## Oakkar

### What have you completed or contributed so far?

I worked on the frontend to improve the user interface.
I updated the model list so it reads from the server instead of using hardcoded names.
I reviewed teammates' pull requests and provided feedback.

### Did you face any blockers or challenges?

Some pull requests looked correct locally but still had product or documentation mismatches.
Some team members were inactive, making it difficult to know whether they were still working on their assigned tasks.

### What went well during this sprint?

The application successfully connected to real data instead of mock data.
Most team members contributed more than they did last sprint.

### Is there anything we can improve as a team?

Encourage all team members to contribute consistently.
Maintain regular communication throughout the sprint.

---

## Naing Phone Pyae

### What have you completed or contributed so far?

Implemented the Agent, LLM, and Human Score outputs with the database.
Resolved merge conflicts for the Micro Agent.

### Did you face any blockers or challenges?

The database implementation still requires further fixes.

### What went well during this sprint?

Some parts of the database implementation ran successfully.
The updated Macro Agent was merged.

### Is there anything we can improve as a team?

Improve communication during database integration.
Coordinate implementation changes earlier.

---

## Henry

### What have you completed or contributed so far?

Updated the project README documentation.
Removed the duplicated prediction argument from the codebase.
Improved both the documentation and code quality.

### Standup

No standup update was provided.
Progress was confirmed through the submitted pull request and repository activity.

---

## Sai Ko

### What have you completed or contributed so far?

Completed the path cleanup task by centralising shared paths in `backend/agents/paths.py`.
Replaced scattered `REPO_ROOT`, `Path(file).resolve().parents[...]`, and unnecessary `sys.path` code across multiple backend files.
Fixed the Matplotlib headless backend issue.
Confirmed that all 53 tests passed.

### Did you face any blockers or challenges?

I originally continued from another feature branch instead of creating my branch directly from `main`.
This caused extra commits and merge conflicts when preparing the final pull request.
I also encountered missing dependency errors and a Tcl/Tk chart-generation issue during testing.

### What went well during this sprint?

The path cleanup was completed successfully across multiple backend modules.
The existing functionality remained unaffected.
I resolved the merge conflict in `stages.py`.
I excluded unrelated database work from my branch.
I verified the final changes using the full test suite.

---

## Zaw Latt Naung

### What have you completed or contributed so far?

Wrote integration tests for the Almanac Agent covering five real trading weeks and one fallback case.
Cross-checked the test assertions against the Stock Trader's Almanac 2026 PDF.
Verified that the expected values matched an external reference instead of only the encoded data.
Resolved CI issues including Pyright type errors and a runtime AttributeError.

### Did you face any blockers or challenges?

The CI version of `stages.py` changed the configuration parameter without exporting the required type.
I used `SimpleNamespace` with `# type: ignore` as a temporary workaround.
The Almanac data differed between my branch and the CI branch.
The test assertions had to match whichever data version the pipeline was using.

### What went well during this sprint?

Cross-checking with the Almanac book greatly improved the reliability of the tests.
The page references make verification easier for reviewers.
The helper function tests now include inline source references.

### Is there anything we can improve as a team?

Help each other more during development and testing.

---

## Jason

### What have you completed or contributed so far?

Continued developing the Delta Engine.
Integrated the Delta Engine with the backend, frontend, and prediction pipeline.

### Standup

No standup update was provided.
Progress was confirmed through the submitted pull request and repository activity.

---

# Presentation

## Shary

### What have you completed or contributed so far?

Prepared the presentation slides for the sprint.
Collected the team's progress and key updates.
Organised the presentation into a clear sprint summary.

### Did you face any blockers or challenges?

Keeping the slides accurate was difficult because tasks and pull request statuses changed frequently.
Review delays and the pipeline rate-limit issue also slowed progress.

### What went well during this sprint?

Team collaboration remained strong.
Communication stayed consistent throughout the sprint.
More pull requests were submitted during the sprint.

### Is there anything we can improve as a team?

Request pull request reviews earlier.
Respond to reviews sooner.
Follow up on blockers before they delay tasks.

---

## Minghao

### What have you completed or contributed so far?

Finalised the presentation slides.
Prepared the speaker notes for tomorrow's presentation.

### Did you face any blockers or challenges?

Some team members responded late.
This delayed the completion of the presentation.

### What went well during this sprint?

The team was more productive than before.
Most backend and frontend development tasks were completed.

### Is there anything we can improve as a team?

Georgii currently handles too many pull request reviews.
More experienced developers should help review pull requests before final approval.
This would reduce the review workload and improve team efficiency.

---

# Human Score

## Aeron

### Status

The Human Score task was not completed.
No standup update was provided.
The assigned team member did not submit the Human Score review during Sprint W29.
