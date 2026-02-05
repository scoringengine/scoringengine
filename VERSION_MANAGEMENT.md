# Version Management

This project uses [bump-my-version](https://github.com/callowayproject/bump-my-version) for semantic versioning.

## Semantic Versioning

We follow [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** version (X.0.0) - Incompatible API changes or breaking changes
- **MINOR** version (0.X.0) - New features, backward compatible
- **PATCH** version (0.0.X) - Bug fixes, backward compatible

## Setup

Install development dependencies:

```bash
pip install -r tests/requirements.txt
```

## Bumping Versions

### Patch Release (Bug Fixes)

For backward-compatible bug fixes:

```bash
bump-my-version bump patch
```

Example: `1.0.0` → `1.0.1`

### Minor Release (New Features)

For new features that are backward-compatible:

```bash
bump-my-version bump minor
```

Example: `1.0.0` → `1.1.0`

### Major Release (Breaking Changes)

For incompatible API changes or breaking changes:

```bash
bump-my-version bump major
```

Example: `1.0.0` → `2.0.0`

## What Happens Automatically

When you run a bump command, the following happens automatically:

1. **Version updated** in these files:
   - `pyproject.toml`
   - `scoring_engine/version.py`

2. **Git commit created** with message: `Bump version: X.Y.Z → X.Y.Z+1`

3. **Git tag created** in format `vX.Y.Z` (e.g., `v1.2.3`)

## Complete Workflow

### 1. Make Your Changes

```bash
# Create a feature branch
git checkout -b feature/my-new-feature

# Make your changes
# ... code changes ...

# Commit your changes
git add .
git commit -m "Add my new feature"
```

### 2. Bump the Version

```bash
# Bump version (creates commit + tag)
bump-my-version bump minor  # or patch/major
```

### 3. Push to Remote

```bash
# Push commits
git push origin feature/my-new-feature

# Push tags (triggers CI/CD)
git push --tags
```

### 4. Create Pull Request

After your PR is merged to master, the tag will trigger the Docker image build and publish workflow.

## CI/CD Integration

The `.github/workflows/publish-images.yml` workflow automatically:

- Builds Docker images when tags matching `v*` are pushed
- Tags images with the version number (e.g., `v1.2.3`)
- Publishes to GitHub Container Registry

## Manual Version Check

To see the current version:

```bash
python -c "from scoring_engine.version import version; print(version)"
```

Or:

```bash
bump-my-version show current_version
```

## Dry Run

To preview what will happen without making changes:

```bash
bump-my-version bump --dry-run --verbose patch
```

## Configuration

Version bumping is configured in `pyproject.toml` under `[tool.bumpversion]`. This section specifies:

- Current version
- Files to update
- Commit and tag settings
- Tag name format

## Best Practices

1. **Always bump versions on the main/master branch** or in a release branch
2. **Push tags immediately** after bumping to trigger CI/CD
3. **Use conventional commit messages** for clarity:
   - `fix:` for patch releases
   - `feat:` for minor releases
   - `BREAKING CHANGE:` for major releases
4. **Document changes** in pull request descriptions
5. **Test thoroughly** before bumping versions

## Troubleshooting

### Already tagged version

If you need to re-tag (not recommended):

```bash
git tag -d v1.2.3  # Delete local tag
git push origin :refs/tags/v1.2.3  # Delete remote tag
```

### Wrong version bumped

```bash
git reset --hard HEAD~1  # Undo the version bump commit
git tag -d v1.2.3  # Delete the tag
```

Then bump to the correct version.

### Files out of sync

If version files get out of sync, manually edit the `current_version` in the `[tool.bumpversion]` section of `pyproject.toml`, then run a bump.
