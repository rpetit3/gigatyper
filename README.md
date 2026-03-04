# gigatyper

_Why choose one scheme when you can flex them all?_

![gigatyper logo](image.png)

## Inspiration

In order to meet the MLST reporting requirements of the [CDC Antimicrobial Resistance Laboratory Network (ARLN)](https://www.cdc.gov/antimicrobial-resistance-laboratory-networks/php/about/domestic.html),
we developed `gigatyper`. (_and we had some fun with it too!_)

`gigatyper` is a wrapper around Torsten Seemann's [mlst](https://github.com/tseemann/mlst)
tool, except with more! `mlst` has built-in auto-detection, that will run your sample against
the scheme that had the best hit. But for reasons I'm unaware of, some species have multiple MLST schemes,
and ARLN wants the results for all of them. `gigatyper` uses the auto-detected scheme to
determine if that species has alternate schemes, and if so, run those too.

## Main Steps

1. Run mlst for a given input
2. Determine if the detected scheme's species has other schemes
3. If alternate schemes exist, run them
4. Output the results to STDOUT in a tab-delimited format

## Quick Start

```bash
gigatyper --input ecoli.fna.gz > ecoli.txt
[16:31:46] INFO     gigatyper v1.0.0                                  gigatyper:287
[16:31:47] INFO     Running mlst (auto-detect)                        gigatyper:217
[16:31:49] INFO     Auto-detected scheme: ['ecoli_achtman_4']         gigatyper:347
           INFO     Running alternate scheme(s): ['ecoli']            gigatyper:261
           INFO     Running mlst --scheme ecoli                       gigatyper:217
```

## Installation

_Note: Bioconda install coming soon!_

```bash
conda create -n gigatyper -c conda-forge -c bioconda gigatyper
conda activate gigatyper
gigatyper --help
```

## Usage

```bash
bin/gigatyper --help
                                                                                                
 Usage: gigatyper [OPTIONS]                                                                     
                                                                                                
 Run MLST against all relevant schemes for an organism.                                         
                                                                                                
╭─ Required Options ───────────────────────────────────────────────────────────────────────────╮
│ --input  TEXT  Input FASTA file (supports .gz)                                               │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Helpful Options ────────────────────────────────────────────────────────────────────────────╮
│ --prefix   TEXT     Prefix to be used for naming results [default: gigatyper]                │
│ --threads  INTEGER  Number of threads for mlst [default: 1]                                  │
│ --species  TEXT     Force a species scheme (e.g. 'Escherichia coli')                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Additional Options ─────────────────────────────────────────────────────────────────────────╮
│ --verbose      Enable debug logging                                                          │
│ --silent       Suppress all log output                                                       │
│ --check        Run dependency checks and exit                                                │
│ --version  -V  Show the version and exit.                                                    │
│ --help         Show this message and exit.                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
```

| Option      | Description                                                       |
|-------------|-------------------------------------------------------------------|
| `--input`   | Input FASTA file (Uncompressed or Gzip compressed (_preferred!_)) |
| `--prefix`  | Sample name prefix for output (default: `gigatyper`)              |
| `--species` | Force a species (e.g. `"Escherichia coli"`)                       |

### Examples

```bash
# Auto-detect scheme and run all related schemes
gigatyper --input assembly.fna

# Specify a species to target its known schemes
gigatyper --input assembly.fna \
          --species "Escherichia coli"

# Gzipped input, custom prefix
gigatyper --input assembly.fna.gz \
          --prefix my_sample

# Verify mlst is installed
gigatyper --check
```

## Output

Here's example output for an _Escherichia coli_ assembly, run with `gigatyper`:
```
sample  file    scheme  st      status  score   alleles formatted_report
gigatyper       ecoli.fna.gz ecoli_achtman_4 10      PERFECT 100     adk(10);fumC(11);gyrB(4);icd(8);mdh(8);purA(8);recA(2)  MLST_10_Achtman
gigatyper       ecoli.fna.gz ecoli   262     PERFECT 100     dinB(8);icdA(118);pabB(7);polB(3);putP(7);trpA(1);trpB(4);uidA(2)       MLST_262_Pasteur
```

Results are printed to STDOUT in a tab-delimited format, with the following columns:

| Column | Description |
|--------|-------------|
| sample | Prefix (default: `gigatyper`, set with `--prefix`) |
| file | Input file path |
| scheme | MLST scheme name |
| st | Sequence type |
| status | Quality indicator (e.g. PERFECT, NOVEL, NONE) |
| score | Numerical score |
| alleles | Tab-separated allele calls (one per locus) |
| formatted_report | CDC ARLN-style report string (e.g. `MLST_131_Pasteur`) |

## FAQ

- _Why does this even exist?_

  We had to meet reporting requirements, and we wanted to have fun creating a tool to meet
  those requirements! It's the best.

- _Can I process multiple samples at once?_
  
  Nope, and you likely never will be able to! `gigatyper` is designed to process a single sample at a time, so that it can be easily implemented into workflow managers (e.g. [Bactopia](https://bactopia.github.io/) _shocker!_)

## Testing

Future Robert, this is how you run the tests with [pytest](https://docs.pytest.org/).

```bash
conda install -n gigatyper pytest
conda activate gigatyper
pytest tests/ -v
```

## Acknowledgements

This tool was developed with the assistance of [Claude Code](https://docs.anthropic.com/en/docs/claude-code).


## Citation
If you use this tool please cite the following:

__[gigatyper](https://github.com/rpetit3/gigatyper)__  
Petit III RA, Fearing T, Groves E [gigatyper: Why choose one scheme when you can flex them all?](https://github.com/rpetit3/gigatyper) (GitHub)  

__[mlst](https://github.com/tseemann/mlst)__   
Seemann T [mlst: Scan contig files against traditional PubMLST typing schemes](https://github.com/tseemann/mlst) (GitHub)  

## Author

* Robert A. Petit III
* Web: [https://www.robertpetit.com](https://www.robertpetit.com)
