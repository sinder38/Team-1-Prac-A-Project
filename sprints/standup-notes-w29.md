Scrum Master
Main-Whitley
Support - Shary

What have you completed or contributed so far?
I coordinated the sprint by following up with team members, tracking their progress, and updating the Scrum documentation, Kanban board, standup notes, and sprint retrospective. 
I also monitored pull requests, communicated with developers to identify blockers, and helped keep the sprint organised.
Did you face any blockers or challenges?
The main challenge was receiving timely updates from all team members, as some responses were delayed. 
In addition, several pull requests required multiple review rounds before they were ready to be merged, which made it more difficult to track the overall sprint progress.
What went well during this sprint?
Team communication improved as the sprint progressed, and more pull requests were submitted and reviewed. 
Regular follow-ups helped keep everyone informed of the project's progress, and the Scrum documentation remained up to date throughout the sprint.
Is there anything we can improve as a team?
We can improve by providing more regular progress updates, requesting pull request reviews earlier, and resolving blockers as soon as they arise. 
Keeping everyone informed throughout the sprint will help improve collaboration and reduce delays.


Developers

Georgii 
What have you completed or contributed so far?
Merge PRs
Review PRs
Fix PRs
Add Ollama local option
Explain how to do tasks in Voice channel
Commit PO artifacts
Some management 
Did you face any blockers or challenges?
My time is wasted on some PRs
I don't have a lot of time this week
Some PRs are way too complex for me to review and merge in time.
Some team members are inactive or their work is low quality.
What went well during this sprint?
Core team of developers works well
Scrum master does some of the managemnt work I used to
Is there anything we can improve as a team?
I dunno, maybe codeowners. But thats overkill for this project.


Oakkar
What have you completed or contributed so far?
I worked on the frontend side to improve the UI. I also helped fix the model list so it reads from the server instead of hardcoded names. And I reviewed a few teammate PRs and left feedback.
Did you face any blockers or challenges?
On reviews, some PRs looked green locally but still had product/doc mismatches. Some team member dont inactive and we don’t know whether he is really doing the work or not.
What went well during this sprint?
We got the app talking to real data, not just mock stuff. Most of the team members contribute more than last week, which is good. 
Is there anything we can improve as a team?
Asking other member to contribute more and effectiveness and keep in touch with the team.


Naing Phone Pyae
What i contributed so far:
Implement agents, llm and human_score outputs with database. Fix the micro agent merge conflicts.
Blockers/challenges:
database implementation needs to be fixed. 
What went well during the sprint?
Some parts of the database implementation   run successfully. Updated macro agent is merged now


Henery
Henry updated the project README documentation and removed the duplicated prediction argument from the codebase, helping improve both the documentation and code quality.
(No standup update was provided. Progress was confirmed through the submitted pull request and repository activity.)


Sai Ko
What have you completed or contributed so far?
I completed the path cleanup task by centralizing shared paths in backend/agents/paths.py. 
I replaced scattered REPO_ROOT, Path(file).resolve().parents[...], and unnecessary sys.path code across multiple backend files. 
I also fixed the Matplotlib headless backend issue and confirmed that all 53 tests passed.
Did you face any blockers or challenges?
The main challenge was that I originally continued from another feature branch instead of creating my branch directly from main. 
This caused extra commits and merge conflicts when preparing the final PR. I also faced missing dependency errors and a Tcl/Tk chart-generation issue during testing.
What went well during this sprint?
The path cleanup was completed successfully across many backend modules without breaking the current main functionality. 
I resolved the merge conflict in stages.py, kept unrelated database work out of my branch, and verified the final changes with the full test suite


Zaw Latt Naung
What have you completed or contributed so far?
I wrote integration tests for the Almanac agent (test_almanac_agent.py) covering 5 real trading weeks across May-July 2026, plus a fallback case. 
I cross-checked test assertions against the actual Stock Trader's Almanac 2026 PDF (pages 87, 89, 97, 99, 108) so the expected values have an external ground truth, 
not just self-referential comparisons against the agent's own encoded data. I also resolved CI issues (pyright type errors, runtime AttributeError) to get the test file passing on the pipeline.
Did you face any blockers or challenges?
Main blocker: the CI version of stages.py changed the config parameter from dict to PipelineConfig without exporting the type for tests. 
I can't import something that doesn't exist in my branch. The workaround (SimpleNamespace + # type: ignore) keeps things running but isn't clean. 
Also, the encoded data in almanac_data.py was updated on my branch to match the book, but the CI branch still has the old values — so the test assertions had to match 
whichever version of the data the pipeline was actually running against.
What went well during this sprint?
The book validation was the strongest part. Having the actual PDF to cross-reference turned the tests from "checking if the code is consistent with itself" into "checking if the code matches the almanac." 
The comment blocks with page numbers make it easy for any reviewer to verify. The unit tests for helpers (_week_of_month, _week_bounds, _format_period) also gained inline source references.
Is there anything we can improve as a team?
help each other



Jason
Jason continued developing the Delta Engine and focused on integrating it with the backend, frontend, and prediction pipeline to improve the overall system workflow. (he 
(No standup update was provided. Progress was confirmed through the submitted pull request and repository activity.)



Presentation

Shary
What have you completed or contributed so far?
I've been preparing the presentation slides for the sprint, pulling together the team's progress and key updates so we have a clear summary to present.
Did you face any blockers or challenges?
The main challenge was keeping the slides accurate as task and PR statuses changed quickly during the sprint. Some review delays and the pipeline rate-limit issue also made progress harder to capture clearly.
What went well during this sprint?
Collaboration and communication stayed strong — the team shared updates consistently and more PRs were submitted throughout the sprint.
Is there anything we can improve as a team?
We could request and respond to reviews sooner, and follow up on blockers earlier so tasks don't stall.


Minghao
What have you completed or contributed so far?
Finalizating Presentation Slides and Speaker Notes for tommorrow.
Did you face any blockers or challenges?
Some roles still have a delay in their respond, thus preventing the early accomplishment of all slides
What went well during this sprint?
Everyone is more productive than before, most of back-end/front-end developing tasks has been addressed.
Is there anything we can improve as a team?
George handles too much of work on merging PRs. We still have a deficiency in manpower that can handle troubleshooting and checking for PRs. 
Adding more people to help with PRs before the final confirmation checks of George may significantly reduce his stress and make the team even more productive&efficient if possible. 
But ensuring the adequate code-developing capability of those people(so that they can solve instead of create problems in PRs) will be a new impending issue.



Human Score
Aeron
Status: Not completed.
The assigned team member did not provide the Human Score review during Sprint W29.
