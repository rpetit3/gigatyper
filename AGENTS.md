# gigatyper

Wrapper around `mlst` that runs every scheme relevant to one sample and emits CDC ARLN-style MLST reports. `mlst` auto-detection picks the initial scheme; this tool then runs the alternates. One sample per invocation by design, so workflow managers call it per sample.

## Commands

Always use the repo env. `PYTHONNOUSERSITE=1` is required: `~/.local` contains a `rich_click` that shadows the env copy.

```bash
conda env create -f environment.yml

# tests (no mlst or network needed)
PYTHONNOUSERSITE=1 conda run -n gigatyper-dev python -m pytest tests/ -v

# dependency check and CLI
conda run -n gigatyper-dev bin/gigatyper --check
conda run -n gigatyper-dev bin/gigatyper --help

# end-to-end with real mlst
PYTHONNOUSERSITE=1 conda run -n gigatyper-dev bin/gigatyper --input tests/data/ecoli.fna.gz --silent
```

`README.md` is the user-facing manual; keep it in sync with behavior.

## Architecture

- Single executable script `bin/gigatyper`, no `.py` extension and no package metadata or build step. `tests/conftest.py` imports it with `SourceFileLoader`.
- `--species` runs every scheme matching the name; otherwise `mlst` auto-detects and `get_alternate_schemes` adds alternates. Results are buffered and printed only at the end.
- stdout is the data product: header plus 8 TSV columns. Logs go to stderr.
- `mlst --full` emits ALLELES as one semicolon-joined field; keep it as one column.
- `.gz` input is decompressed to a `NamedTemporaryFile` and removed in `finally`.

## Invariants

- Fixed column order: `sample file scheme st status score alleles formatted_report`.
- `format_mlst_report`: `MLST_<st>_<display>`; `MLST_unnamed_<display>` when ST is `-`; empty when scheme is `-`.
- Scheme names group by the prefix before the first `_`; single-member groups get no alternates.
- Three hardcoded tables change report content; edit them deliberately:
  - `ADDITIONAL_SCHEMES`: `mabscessus` / `mycobacteria_2`
  - `SCHEME_DISPLAY_NAMES`: Pasteur, Achtman, Oxford
  - `GENUS_CORRECTIONS`: Escherichia and Enterobacter mis-detection
- Version lives in the `VERSION` constant, `CHANGELOG.md`, and the README example log; bump all three together.
- CI runs pytest only, on main push/pull request. No lint or type gate.

## Tests

- Function-level, mocking `subprocess.run` and `shutil.which`. They must not require `mlst`.
- `tests/data/` is manual e2e input only; the suite does not read it.
- `TestExecute` asserts `sys.exit` on a nonzero return code.