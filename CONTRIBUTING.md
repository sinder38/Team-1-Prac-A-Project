# Contributing Guidelines

These guidelines outline a streamlined workflow so that our team can collaborate
efficiently while protecting the stability of `main` and maintaining code quality.

---

## 1. Branching & Release Strategy

1. **Protect `main`**
    - No direct pushes. All changes go through Pull Requests (PRs).
    - Require at least one approving review before merging.

2. **Feature / Bugfix Branches**
    - Create lightweight branches off of `main`:
        - `feature/short-description` (new features)
        - `bugfix/short-description` (bug fixes)
        - `hotfix/short-description` (urgent fixes)
        - `perf/short-description` (performance related update)
        - `docs/short-description` (documentation/iteration updates)

    - Always do:
      ```bash
      git checkout main
      git pull origin main
      git checkout -b feature/short-description
      ```

3. **Rebasing & Syncing**
    - Before opening or updating a PR, rebase onto the latest `main` to minimize merge conflicts:
    - This optional for simple PRs
      ```bash
      git fetch origin
      git rebase origin/main
      git push --force-with-lease
      ```

---

## 2. Issue & Task Workflow **Currently unused**

You don't really need to create issues right now. But if you do please follow this.

1. **Issue Creation**
    - Use GitHub Issues to track all work (features, bugs, chores).
    - Apply labels like `type:bug`, `type:enhancement`, `priority:high`, or `area/frontend` to help triage.
    - **Currently unused**

2. **Claiming & Assigning**
    - Comment “I’ll take this” on an open issue and assign yourself.**Currently unused**

3. **Linking PRs to Issues**
    - In your PR description, reference the issue number (e.g., “Closes #23”). This auto-links and closes the issue when
      merged. **Currently unused**

---

## 3. Coding Style & Performance

1. **Language Conventions**
    - Follow PEP8 conventions or analog for your language
2. **Documentation & Comments**
    - Please add docstrings to public functions
    - Add comments to code that cannot be understood instantly or tackles high level architecture.

3. **Special comments**
   In order of priority
   ~~~python
   # FIX: description of an urgent fix 
   # TODO: description of a potential improvement
   # PERF: description of a performance related improvement
   # WARN: description of an obscure code you shouldn't touch
   # NOTE: obscure facts
   ~~~

---

## 4. Commit Messages & Pull Requests

1. **Commit Message Format (Conventional Commits)**
   ```
   <short description>
   <short description>
   <short description>
   ```

    - Example:
      ```
      Add /charts endpoint for bulk requests
      Optimize AI requests
      ```
---

## 5. Code Review Process

1. **Assigning Reviewers**
   Pull requests (PRs) should be reviewed by the appropriate team members. Make sure to assign relevant reviewer.

2. **Approvals & Feedback**
    * Discuss changes IRL or by doing Code Review
    
---

## 6. Merging & Releases

1. **Squash & Merge (Preferred)**

    * Use “Squash and merge” to keep `main` history linear. The resulting commit message should be clear and reference
      the original PR.

2. **Merge Commits (When Needed)**

    * For large, multi-commit PRs where history matters, you may keep individual commits. Ensure the branch is rebased
      and conflicts are resolved.

---
