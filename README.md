# gigatyper

Why choose one scheme when you can flex them all?

## Installation

```bash
conda create -n gigatyper 'python=3.12' rich-click mlst
conda activate gigatyper
wget https://raw.githubusercontent.com/rpetit3/gigatyper/refs/heads/main/bin/gigatyper
chmod 755 gigatyper
./gigatyper --help
```

## Usage

```bash
# Auto-detect scheme and run all related schemes
gigatyper --input assembly.fna

# Specify a species to target its known schemes
gigatyper --input assembly.fna --species "Escherichia coli"

# Gzipped input, custom prefix, multiple threads
gigatyper --input assembly.fna.gz --prefix my_sample --threads 4

# Verify mlst is installed
gigatyper --check
```

### Output

Results are printed as tab-separated values to stdout:

| Column | Description |
|--------|-------------|
| sample | Prefix (default: `gigatyper`, set with `--prefix`) |
| file | Input file path |
| scheme | MLST scheme name |
| st | Sequence type |
| status | Quality indicator (e.g. PERFECT, NOVEL, NONE) |
| score | Numerical score |
| alleles | Tab-separated allele calls (one per locus) |
| formatted_report | CDC/PHL-style report string (e.g. `MLST_131_Pasteur`) |

### Options

| Option | Description |
|--------|-------------|
| `--input` | Input FASTA file (supports `.gz`) |
| `--prefix` | Sample name prefix for output (default: `gigatyper`) |
| `--threads` | Number of threads for mlst (default: `1`) |
| `--species` | Force a species (e.g. `"Escherichia coli"`) |
| `--verbose` | Enable debug logging |
| `--silent` | Suppress all log output |
| `--check` | Verify dependencies and exit |
| `--version` | Show version |

## Testing

Tests use [pytest](https://docs.pytest.org/) and don't require `mlst` to be installed (subprocess calls are mocked).

```bash
conda install -n gigatyper pytest
conda activate gigatyper
pytest tests/ -v
```
