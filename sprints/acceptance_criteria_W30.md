For a sprint to be considered complete, the following acceptance criteria should be met:

Usual:
+ The sprint goal is written clearly in [sprint_goal_W30.md](./sprint_goal_W30.md)
+ The acceptance criteria are documented in acceptance_criteria_W30.md.
+ The prediction file is committed to GitHub before the deadline.
+ The prediction includes SPX, NDX, and IWM direction, percentage range, and confidence level.
+ All four LLM raw responses are stored in the evidence folder.
+ The Human Score table is completed with an override paragraph or clear justification.
+ Chart screenshots and market evidence are committed.
+ A release tag is created before class.
+ The team's work is ready to present without last-minute changes.

New:
+ All non-image local data is stored in the SQLite database, and parsing is part of the Agent base class 
+ Stored artifacts (Delta report, Final Prediction, Human Score) can be extracted from the database back into the data/ directory 
+ The Delta Engine report is exported from SQLite as data/qa/delta_WXX.md using the existing renderer
+ The prediction range is implemented in the Almanac, Technical, and Macro agents, fetching data up to the input date
+ Opening a past or interrupted run from history restores its real stage progress and does not show false completion

These criteria match the project's definition of done, which requires the prediction, LLM responses, Human Score, chart screenshot, actuals, calibration score, README update, and release tag to be completed every sprint.
