# Releasing

1. Update `VERSION` in `hightouch/htevents/version.py` and `version` in `pyproject.toml` to the new version.
2. Make a new tag that exactly matches the new version. Push everything up to github. Merge to master.
3. Choose this tag while making a new release: https://github.com/ht-sdks/events-sdk-python/releases/new
4. Publish the release; this will trigger a github action `ci-release`
5. Watch the github action to confirm a successful release to pypi.
6. Confirm on pypi: https://pypi.org/project/events-sdk-python/
