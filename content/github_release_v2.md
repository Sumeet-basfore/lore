# Internal notes for a future release (not approved for publication)

These notes are a working draft. No package or GitHub release has been published. Confirm the merged code, version, and install instructions before preparing release notes.

## Beta readiness changes in this branch

- Publishing results distinguish provider-confirmed publication, compose hand-off, simulation, and failure. The current CLI does not expose a publishing command.
- Package metadata uses the distribution name `lore-dev-content`; the command remains `lore`.
- Python metadata requires Python 3.12 or newer. Source installation is documented in the README and beta guide.
- Configuration output redacts API keys. Generation stops with an error when the selected model fails instead of saving canned example text.
- The README and beta guide describe the scan-to-draft inputs and privacy limits. The standalone DLP scanner is not connected to the normal CLI workflow.

## Verification to record after merge

Add the final test, build, and clean-install results here only after they have been run against the release candidate. Do not state that every generated claim is verified or that all secrets are detected.
