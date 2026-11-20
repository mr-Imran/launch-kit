# Contributing

envdiff is one file, `envdiff.py`, and uses only the Python standard library. The tests are in `tests/` and need pytest.

## Run it locally

From a clone of the repository:

```sh
python3 envdiff.py examples/dev.env examples/prod.env
```

## Run the tests

```sh
python3 -m pip install pytest
python3 -m pytest
```

## Send a change

- For a bug, open an issue with the two files that show it (replace the values with made-up ones) and the output you got.
- For a pull request, add or update a test in `tests/test_envdiff.py` for the behaviour you changed, and say which commands you ran.
- If the change affects what the tool prints, update the examples in `README.md` so they still match.
