# Captured negative proposals

`null-test-reference.json` is an actual synthetic Gemma proposal captured on
2 October 2026 by the final-loop evaluation. It supplied two calculated
observations with `test_ref: null`. Before the required-reference repair this
escaped validation. The application regression binds only the test request's
envelope/source identity, preserving the offending proposal content.

This is a negative validator fixture, not authored evidence of semantic quality
or a live-model test. The full original trace remains in the ignored evaluation
directory.
