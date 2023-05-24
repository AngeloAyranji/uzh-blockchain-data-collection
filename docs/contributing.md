# Contributing
todo: release-please, conventional commits, tests

1. `git clone` the repo and `cd` into it
2. (optional but highly recommended, CI will fail anyway) `pre-commit install`, or [install pre-commit](https://pre-commit.com/#install) first
  * If installing pre-commit on abacus3, you might need to check if you're using virtualenv v20.4.0 with `virtualenv --version`. If not, then `pip uninstall virtualenv -y` first and then check if the global packge is now v20.4.0. [This SO answer](https://stackoverflow.com/a/76317793/4249857) has more details.
3. fork the main branch and add your features or a fix
4. follow [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) to get automatic changelogs and release functionality
5. Open a PR and wait for CI checks and tests to pass.

## CI




Currently, only the `DatabaseManager` class is tested. These database manager tests require an active database connection so the configuration in `docker-compose.tests.yml` starts an in-memory postgresql database along with the testing container.

To start the tests:
```
$ bash scripts/tests/run-tests-db.sh
```

> Note: When running the tests locally, it might sometimes be necessary to `docker volume prune` in order for the database to restart properly.
