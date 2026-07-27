# Test Fixtures

This directory contains fixtures used to verify the package at both unit and integration test level.

## Structure

Each fixture set contains two subdirectories:

- `mono`: a single mono macro that is the source of truth for the fixture group
- `set`: the corresponding split into a `main.mac` and category macro files

## Fixture Groups

- `full-stack`: all currently supported command types except Gate actor and digitizer commands,
  with `# BEGIN EXECUTE` / `# END EXECUTE` comments carried as plain text
- `partial-stack`: like `full-stack` but without the phantom
- `full-statc-without-text`: the `full-stack` simulation with all comments removed;
  proves that splitting works from command classification alone
- `partial-stack-actor-example`: hand-written J-PET example with an actor section,
  capitalized `/control/execute` references (`Geometry.mac`) resolving to lowercase files,
  and several categories intentionally left inline in `main.mac`

## Verified Directions

For `full-stack`, `partial-stack` and `full-statc-without-text` the `set` directories are the
canonical output of `unfold`, so tests verify both directions byte-for-byte:
`unfold(mono) == set` and `fold(set) == mono`.

`partial-stack-actor-example/set` is hand-written and cannot be reproduced by any deterministic
`unfold`; tests verify `fold(set) == mono` (including case-insensitive file resolution) and the
round trip `fold(unfold(mono)) == mono`.
