# Contributing

Thanks for considering a contribution.

This repository accepts code edits, bug reports, documentation improvements, and pull requests. Submissions may be reviewed before they are merged, and maintainers may request changes for clarity, test coverage, compatibility, or project scope.

Before submitting a change:

1. Keep examples generic and safe to share.
2. Do not commit secrets, private hostnames, local machine paths, personal notes, or generated run artifacts.
3. Run the available checks:

```bash
python -m compileall src scripts
pytest
```

For larger changes, include a brief explanation of the problem, the approach, and any validation performed.
