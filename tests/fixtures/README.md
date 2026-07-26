# Test Fixtures

This directory contains fixtures used to verify the package at both unit and integration test level.

## Structure

Each fixture set contains two subdirectories:

- `mono`: a single mono macro that should be transformed into the corresponding files in `set`
- `set`: the files that should be produced from `mono`

This layout makes it possible to confirm that the package performs the expected transformations in both directions.

## Fixture Groups

- `full-stack`: includes all currently supported command types, except Gate actor and digitizer commands
- `partial-stack`: excludes the phantom

Each group follows the same `mono` / `set` split described above.