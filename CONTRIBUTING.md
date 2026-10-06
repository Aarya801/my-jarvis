# Contributing to J.A.R.V.I.S.

J.A.R.V.I.S. is a personal engineering project, but the repository is structured so that improvements are understandable and reviewable.

## Before changing code

- Read docs/ARCHITECTURE.md.
- Keep the local bridge loopback-only.
- Never commit tokens, credentials, private files, or generated local state.
- Prefer small, explainable changes over unnecessary frameworks.

## Suggested workflow

1. Describe the problem or improvement.
2. Make the smallest change that solves it.
3. Test the affected browser flow manually.
4. For bridge changes, test status, authentication, read/write, and timeout behavior.
5. Update documentation when behavior or setup changes.

## Good first contributions

- Browser compatibility improvements.
- Accessibility improvements.
- Better structured command schemas.
- Safer permission controls for bridge operations.
- Automated browser smoke tests.
- UI performance improvements.

See docs/TESTING.md for the current release checklist.
