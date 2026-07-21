# AutoPaste — GitHub Cheat Sheet

Quick reference for the day-to-day commands. Everything assumes you're running
from the repository root:

```
C:\Users\dyoder\Documents\Cursor Projects\AutoPaste\AutoPaste
```

- **Repo:** https://github.com/YoderMW/AutoPaste
- **Branch you work on:** `main`
- **Releases trigger:** pushing a tag like `v2.0.1` builds the exe automatically.

---

## Glossary (plain English)

| Term | What it means |
|------|---------------|
| **commit** | A saved snapshot of your changes, with a message describing them. Local only until you push. |
| **push** | Upload your commits to GitHub. |
| **tag** | A label pinned to a commit, e.g. `v2.0.0`. Pushing a `v*` tag is what publishes a release. |
| **release / "cut a release"** | Publishing a new version — for us, just pushing a version tag. GitHub Actions then builds `AutoPaste.exe`. |
| **origin** | The nickname for the GitHub copy of the repo. |
| **staging (`git add`)** | Marking which changes go into the next commit. |

---

## 1. Everyday: save your work to GitHub

After you've changed some code:

```bash
git status            # see what changed (nothing is saved yet)
git diff              # see the exact line-by-line changes
git add -A            # stage ALL changes for the next commit
git commit -m "Describe what you changed"
git push              # upload to GitHub (origin/main)
```

Shortcut once you're comfortable: `git add -A && git commit -m "msg" && git push`

---

## 2. Publish a new version (build + release the .exe)

Version numbers follow `MAJOR.MINOR.PATCH` (see below). Two steps:

```bash
# 1. Make sure everything is committed and pushed first
git push

# 2. Create the version tag and push it — THIS starts the build
git tag v2.0.1
git push origin v2.0.1
```

Then watch it build: **GitHub → AutoPaste → Actions tab**. When it turns green,
`AutoPaste.exe` appears under **Releases**, and coworkers get it on next launch
via the auto-updater.

> Keep the tag number and `AutoPasteV1.1/version.py` in sync. The build stamps
> the version from the tag, so the tag is the source of truth — but bumping
> `version.py` to match keeps local runs honest.

### Picking the number

| Change | Bump | Example |
|--------|------|---------|
| Bug fix | PATCH | `2.0.0 → 2.0.1` |
| New parser / feature (nothing breaks) | MINOR | `2.0.0 → 2.1.0` |
| Big or breaking change | MAJOR | `2.x → 3.0.0` |

---

## 3. Check the current state

```bash
git status                    # what's modified / staged / untracked
git log --oneline -10         # last 10 commits (short)
git branch --show-current     # which branch you're on (should be: main)
git remote -v                 # confirm origin -> YoderMW/AutoPaste
git tag                       # list all version tags
```

---

## 4. Undo / fix mistakes

```bash
# Unstage a file (keep the edits, just don't commit it yet)
git restore --staged path/to/file

# Throw away uncommitted edits in a file (CAUTION: can't undo)
git restore path/to/file

# Change the message of the most recent commit (only if NOT pushed yet)
git commit --amend -m "New message"

# Pull the latest from GitHub (e.g. if you committed from another machine)
git pull
```

### Redo a tag you pushed to the wrong commit

```bash
git tag -d v2.0.1                      # delete the tag locally
git push origin :refs/tags/v2.0.1      # delete the tag on GitHub
# then re-tag the right commit and push again (see section 2)
```

Also delete the matching Release on the website if one was created:
**Releases → the release → Delete**.

---

## 5. Typical full workflow (change → release)

```bash
# 1. Edit code in AutoPasteV1.1\ ...

# 2. Save it to GitHub
git add -A
git commit -m "Add Foo Cabinetry parser"
git push

# 3. Bump AutoPasteV1.1\version.py to the new number (e.g. 2.1.0)
#    then commit that too
git add AutoPasteV1.1/version.py
git commit -m "Bump version to 2.1.0"
git push

# 4. Publish the release
git tag v2.1.0
git push origin v2.1.0

# 5. Watch GitHub -> Actions until green -> Release appears with AutoPaste.exe
```

---

## 6. New computer only: first-time auth

If Git ever asks you to log in, GitHub no longer accepts your account password on
the command line. Easiest fix: install **GitHub CLI** once and run:

```bash
gh auth login
```

(Your current machine is already authenticated, so this is only relevant on a
brand-new computer.)
