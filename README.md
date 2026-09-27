# PyHX

Web apps with Python and [HTMX](https://htmx.org/).

📖 **Documentation:** https://cokeschlumpf.github.io/pyhx/

## Development

```bash
poetry install --all-extras --with docs
poetry run poe check        # linting, type checks and tests (same as CI)
poetry run poe fix          # auto-fix lint issues and format code
poetry run poe docs         # serve the documentation locally on http://localhost:8090
poetry run poe docs-build   # strict build into site/ (same as CI)
```

## Pipelines

The workflows in `.github/workflows/` only call the shared, reusable workflows from
[core--devops-workflows](https://github.com/cokeSchlumpf/core--devops-workflows), which also documents their inputs.
The GitHub settings this repository needs (squash merging, workflow permissions, Pages, rulesets, `OPENAI_API_KEY`) are
listed in its [setup checklist](https://github.com/cokeSchlumpf/core--devops-workflows#setting-up-a-repository).

| Workflow | Runs on | Does |
| --- | --- | --- |
| **Check** | push to `feature/**` and `fix/**` | `poe check` and `poe docs-build` |
| **Docs** | push to `main` | builds the documentation and deploys it to GitHub Pages |
| **Release** | push to `main` | maintains the Release PR; merging it creates the release |
| **PR Title** | pull requests | fails if the PR title isn't a conventional commit |

## Releases

Releases are automated with [release-please](https://github.com/googleapis/release-please) and based on
[Conventional Commits](https://www.conventionalcommits.org/). See the [changelog](CHANGELOG.md) for all releases.

- **Tags** `vX.Y.Z` (e.g. `v0.2.0`), each with a GitHub Release.
- **Branches** `versions/<major>` (e.g. `versions/0`) always point to the latest release of that major version.
- **`version`** in `pyproject.toml` and **`CHANGELOG.md`** (newest release on top) are updated automatically.

### PR titles are commit messages

PRs are squash-merged, so the **PR title** becomes the commit on `main` and decides the next version.

| PR title | Release | In changelog |
| --- | --- | --- |
| `feat: …` | minor | Features |
| `fix: …`, `perf: …`, `deps: …` | patch | Bug Fixes, Performance Improvements, Dependencies |
| `feat!: …` or a `BREAKING CHANGE: …` line in the PR description | major | as above, marked as breaking |
| `docs: …`, `revert: …` | patch | Documentation, Reverts |
| `ci:`, `chore:`, `test:`, `build:`, `style:`, `refactor:` | none on their own | hidden |

### How a release happens

1. Every merge to `main` creates or updates a single **Release PR** (`chore(main): release X.Y.Z`) with the version
   bump and the new changelog section.
2. **Merge the Release PR whenever you want to release.** Merging it creates the tag, the GitHub Release and moves
   `versions/<major>`.

The Release PR is regenerated on every push to `main`, so manual edits to it are overwritten. If the repo secret
`OPENAI_API_KEY` is set, the release notes of the Release PR are additionally polished by an LLM.

### Fixing versions and release notes

- **Force a version:** add `Release-As: 1.0.0` as the last line of a PR description before merging it.
- **Fix a wrongly titled PR after merging:** edit the merged PR's description and add the corrected message:

  ```
  BEGIN_COMMIT_OVERRIDE
  feat: the corrected commit message
  END_COMMIT_OVERRIDE
  ```
