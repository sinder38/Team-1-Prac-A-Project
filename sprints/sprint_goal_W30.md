Sprint Goal — Team 1A, Week 30

This sprint's primary goal is to harden the end-to-end pipeline around a single source of truth (SQLite) and finalise the prediction range so the system produces trustworthy, reproducible weekly predictions.

By end of sprint, the team should have:
- Local runtime state moved into the SQLite database, with all non-image artifacts (LLM outputs, Delta report, Final Prediction, Human Score) stored and re-exported from the database rather than messy files
- The prediction range (direction, percentage range, confidence) implemented 
- Reliable archive/history behaviour: reopening a past or interrupted run restores its true stage progress instead of showing false completion
- The Delta report exported from SQLite and integrated into the artifact pipeline (data/qa/delta_WXX.md)
- The full pipeline running successfully end-to-end, producing the complete prediction artifact for W30

The definition of done still includes the full prediction artifact (SPX, NDX, IWM direction, range, confidence), all four LLM responses in the evidence folder, Human Score table completed, chart screenshots committed, and a release tag before class.

This sprint is about consolidation and correctness: after last sprint's convergence into a working end-to-end system, W30 focuses on making the data layer authoritative, the archive trustworthy, and the prediction range complete, so the pipeline can be run and re-run without data drift.
