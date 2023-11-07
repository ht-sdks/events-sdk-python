# Releasing

1. Update `VERSION` in `hightouch/analytics/version.py` to the new version.
2. `git commit -am "Release X.Y.Z."` (where X.Y.Z is the new version)
3. `git tag -a X.Y.Z -m "Version X.Y.Z"` (where X.Y.Z is the new version).
4. `git push && git push --tags`
5. `make release`.
