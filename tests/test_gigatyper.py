"""Tests for gigatyper."""
import gzip
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from conftest import gigatyper_mod

# Convenient aliases for functions under test
parse_mlst_line = gigatyper_mod.parse_mlst_line
parse_mlst_info = gigatyper_mod.parse_mlst_info
build_scheme_groups = gigatyper_mod.build_scheme_groups
build_scheme_pairs = gigatyper_mod.build_scheme_pairs
find_schemes_for_species = gigatyper_mod.find_schemes_for_species
get_display_name = gigatyper_mod.get_display_name
format_mlst_report = gigatyper_mod.format_mlst_report
get_alternate_schemes = gigatyper_mod.get_alternate_schemes
decompress_fasta = gigatyper_mod.decompress_fasta
check_dependencies = gigatyper_mod.check_dependencies
execute = gigatyper_mod.execute
run_mlst = gigatyper_mod.run_mlst

ADDITIONAL_SCHEMES = gigatyper_mod.ADDITIONAL_SCHEMES
GENUS_CORRECTIONS = gigatyper_mod.GENUS_CORRECTIONS


# ---------------------------------------------------------------------------
# parse_mlst_line
# ---------------------------------------------------------------------------
class TestParseMlstLine:
    # Parses a standard 6-column mlst --full output line into a dict
    def test_valid_line_single_allele(self):
        line = "sample.fna\tecoli\t131\tPERFECT\t100\tadk(10)"
        result = parse_mlst_line(line)
        assert result == {
            "file": "sample.fna",
            "scheme": "ecoli",
            "st": "131",
            "status": "PERFECT",
            "score": "100",
            "alleles": "adk(10)",
        }

    # All allele columns (parts[5:]) are joined with tabs, not just the first
    def test_valid_line_multiple_alleles(self):
        line = "sample.fna\tecoli\t131\tPERFECT\t100\tadk(10)\tfumC(11)\tgyrB(4)\ticd(8)"
        result = parse_mlst_line(line)
        assert result["alleles"] == "adk(10)\tfumC(11)\tgyrB(4)\ticd(8)"

    # The header row output by mlst --full should be skipped
    def test_header_line_skipped(self):
        line = "FILE\tSCHEME\tST\tSTATUS\tSCORE\tALLELES"
        assert parse_mlst_line(line) is None

    # Lines with fewer than 6 tab-separated fields are invalid
    def test_short_line_skipped(self):
        line = "sample.fna\tecoli\t131"
        assert parse_mlst_line(line) is None

    # Empty or nearly-empty lines should not produce a result
    def test_empty_line_skipped(self):
        assert parse_mlst_line("") is None
        assert parse_mlst_line("\t\t") is None

    # Leading/trailing whitespace and newlines are stripped before parsing
    def test_whitespace_stripped(self):
        line = "  sample.fna\tecoli\t131\tPERFECT\t100\tadk(10)  \n"
        result = parse_mlst_line(line)
        assert result["file"] == "sample.fna"
        assert result["alleles"] == "adk(10)"

    # When mlst can't assign an ST, it reports "-"; alleles may have ~ prefix
    def test_no_st_detected(self):
        line = "sample.fna\tecoli\t-\tNONE\t0\tadk(~10)\tfumC(~11)"
        result = parse_mlst_line(line)
        assert result["st"] == "-"
        assert result["alleles"] == "adk(~10)\tfumC(~11)"


# ---------------------------------------------------------------------------
# parse_mlst_info
# ---------------------------------------------------------------------------
class TestParseMlstInfo:
    # Parses `mlst --info` output into a {scheme_name: [locus_names]} dict
    def test_parses_scheme_loci(self):
        fake_output = textwrap.dedent("""\
            SCHEME\tLOCI\tTYPES\tALLELES\tDATE\tLOCI_NAMES
            abaumannii\t7\t2473\t15421\t2024-01-01\tgltA cpn60 gdhB gpi gyrB rpoD recA
            ecoli\t7\t12345\t67890\t2024-01-01\tadk fumC gyrB icd mdh purA recA
        """)
        with patch.object(gigatyper_mod, "execute", return_value=fake_output):
            result = parse_mlst_info()
        assert "abaumannii" in result
        assert result["abaumannii"] == ["gltA", "cpn60", "gdhB", "gpi", "gyrB", "rpoD", "recA"]
        assert result["ecoli"] == ["adk", "fumC", "gyrB", "icd", "mdh", "purA", "recA"]

    # Header row (starts uppercase) and lines with <6 columns are ignored
    def test_skips_header_and_short_lines(self):
        fake_output = "SCHEME\tLOCI\tTYPES\tALLELES\tDATE\tLOCI_NAMES\nshort\n"
        with patch.object(gigatyper_mod, "execute", return_value=fake_output):
            result = parse_mlst_info()
        assert len(result) == 0

    # Scheme names starting with uppercase are filtered out (header artifacts)
    def test_skips_uppercase_names(self):
        fake_output = "SCHEME\t7\t100\t500\t2024-01-01\tlocus1 locus2\n"
        with patch.object(gigatyper_mod, "execute", return_value=fake_output):
            result = parse_mlst_info()
        assert "SCHEME" not in result


# ---------------------------------------------------------------------------
# build_scheme_groups
# ---------------------------------------------------------------------------
class TestBuildSchemeGroups:
    # Schemes sharing a base prefix (before first "_") are grouped together
    def test_groups_related_schemes(self):
        names = {"abaumannii", "abaumannii_2", "ecoli", "ecoli_achtman_4", "kpneumoniae"}
        groups = build_scheme_groups(names)
        assert "abaumannii" in groups
        assert sorted(groups["abaumannii"]) == ["abaumannii", "abaumannii_2"]
        assert "ecoli" in groups
        assert sorted(groups["ecoli"]) == ["ecoli", "ecoli_achtman_4"]

    # Schemes with no shared prefix (singletons) are excluded from groups
    def test_excludes_singletons(self):
        names = {"kpneumoniae", "paeruginosa"}
        groups = build_scheme_groups(names)
        assert len(groups) == 0

    # Empty input produces no groups
    def test_empty_input(self):
        assert build_scheme_groups(set()) == {}


# ---------------------------------------------------------------------------
# build_scheme_pairs
# ---------------------------------------------------------------------------
class TestBuildSchemePairs:
    # Each scheme in a group maps to its alternates (the other group members)
    def test_pairs_from_groups(self):
        groups = {"abaumannii": ["abaumannii", "abaumannii_2"]}
        pairs = build_scheme_pairs(groups)
        assert pairs["abaumannii"] == ["abaumannii_2"]
        assert pairs["abaumannii_2"] == ["abaumannii"]

    # ADDITIONAL_SCHEMES entries (mabscessus <-> mycobacteria_2) are included
    # even when no group exists for them
    def test_additional_schemes_merged(self):
        groups = {}
        pairs = build_scheme_pairs(groups)
        assert "mycobacteria_2" in pairs["mabscessus"]
        assert "mabscessus" in pairs["mycobacteria_2"]

    # When a group already contains an ADDITIONAL_SCHEMES entry, it should
    # not be duplicated in the alternates list
    def test_additional_schemes_no_duplicates(self):
        groups = {"mabscessus": ["mabscessus", "mycobacteria_2"]}
        pairs = build_scheme_pairs(groups)
        assert pairs["mabscessus"].count("mycobacteria_2") == 1


# ---------------------------------------------------------------------------
# find_schemes_for_species
# ---------------------------------------------------------------------------
class TestFindSchemesForSpecies:
    def setup_method(self):
        self.all_names = {"ecoli", "ecoli_achtman_4", "abaumannii", "abaumannii_2", "kpneumoniae"}
        self.groups = build_scheme_groups(self.all_names)

    # "Escherichia coli" -> genus[0]+species = "ecoli" -> matches the ecoli group
    def test_genus_species_match(self):
        result = find_schemes_for_species("Escherichia coli", self.all_names, self.groups)
        assert "ecoli" in result
        assert "ecoli_achtman_4" in result

    # "Klebsiella pneumoniae" -> "kpneumoniae" matches a standalone scheme (no group)
    def test_standalone_match(self):
        result = find_schemes_for_species("Klebsiella pneumoniae", self.all_names, self.groups)
        assert result == ["kpneumoniae"]

    # Species with no matching scheme name returns an empty list
    def test_no_match(self):
        result = find_schemes_for_species("Unknown organism", self.all_names, self.groups)
        assert result == []

    # A single word (genus only, no species) is not enough to match
    def test_single_word_returns_empty(self):
        result = find_schemes_for_species("Escherichia", self.all_names, self.groups)
        assert result == []


# ---------------------------------------------------------------------------
# get_display_name
# ---------------------------------------------------------------------------
class TestGetDisplayName:
    # Schemes in SCHEME_DISPLAY_NAMES get their hardcoded display name
    def test_hardcoded_override(self):
        assert get_display_name("abaumannii", {}) == "Oxford"
        assert get_display_name("abaumannii_2", {}) == "Pasteur"
        assert get_display_name("ecoli", {}) == "Pasteur"
        assert get_display_name("ecoli_achtman_4", {}) == "Achtman"

    # When all loci share a common prefix (e.g. "abc_1", "abc_2"), use that prefix
    def test_loci_prefix_derivation(self):
        scheme_loci = {"myscheme": ["abc_1", "abc_2", "abc_3"]}
        assert get_display_name("myscheme", scheme_loci) == "abc"

    # When loci have different prefixes, fall back to the scheme name
    def test_mixed_prefixes_fallback(self):
        scheme_loci = {"myscheme": ["abc_1", "def_2"]}
        assert get_display_name("myscheme", scheme_loci) == "myscheme"

    # When loci have no underscore, prefix derivation can't work; fall back
    def test_no_underscore_in_loci_fallback(self):
        scheme_loci = {"myscheme": ["locus1", "locus2"]}
        assert get_display_name("myscheme", scheme_loci) == "myscheme"

    # When no loci data exists for the scheme, fall back to the scheme name
    def test_empty_loci_fallback(self):
        assert get_display_name("myscheme", {}) == "myscheme"


# ---------------------------------------------------------------------------
# format_mlst_report
# ---------------------------------------------------------------------------
class TestFormatMlstReport:
    # A known ST produces "MLST_{st}_{display_name}"
    def test_normal_st(self):
        assert format_mlst_report("ecoli", "131", {}) == "MLST_131_Pasteur"

    # When ST is "-" (unresolved), report uses "unnamed" placeholder
    def test_unnamed_st(self):
        assert format_mlst_report("ecoli", "-", {}) == "MLST_unnamed_Pasteur"

    # When scheme is "-" (no scheme detected), report is empty
    def test_no_scheme(self):
        assert format_mlst_report("-", "131", {}) == ""

    # Both scheme and ST missing still produces empty string
    def test_no_scheme_no_st(self):
        assert format_mlst_report("-", "-", {}) == ""


# ---------------------------------------------------------------------------
# get_alternate_schemes
# ---------------------------------------------------------------------------
class TestGetAlternateSchemes:
    # When mlst auto-detects a wrong scheme for a known genus (e.g. "aeromonas"
    # for Escherichia), GENUS_CORRECTIONS replaces it with the correct schemes
    def test_genus_correction_replaces(self):
        pairs = {}
        alternates, replace = get_alternate_schemes("aeromonas", "escherichia", pairs)
        assert replace is True
        assert alternates == ["ecoli", "ecoli_achtman_4"]

    # A correct scheme for the genus does not trigger replacement
    def test_genus_correction_not_triggered(self):
        pairs = {}
        alternates, replace = get_alternate_schemes("ecoli", "escherichia", pairs)
        assert replace is False
        assert alternates == []

    # When a scheme has paired alternates, return them without replacing
    def test_scheme_pairs(self):
        pairs = {"abaumannii": ["abaumannii_2"]}
        alternates, replace = get_alternate_schemes("abaumannii", "acinetobacter", pairs)
        assert replace is False
        assert alternates == ["abaumannii_2"]

    # Schemes with no corrections or pairs return empty alternates
    def test_no_alternates(self):
        pairs = {}
        alternates, replace = get_alternate_schemes("kpneumoniae", "klebsiella", pairs)
        assert replace is False
        assert alternates == []


# ---------------------------------------------------------------------------
# decompress_fasta
# ---------------------------------------------------------------------------
class TestDecompressFasta:
    # Plain .fna files are returned as-is with no temp file created
    def test_plain_fasta_passthrough(self, tmp_path):
        fasta = tmp_path / "test.fna"
        fasta.write_text(">seq1\nACGT\n")
        result_path, is_temp = decompress_fasta(fasta)
        assert result_path == fasta
        assert is_temp is False

    # .gz files are decompressed to a temp file; content matches the original
    def test_gzipped_fasta_decompressed(self, tmp_path):
        content = b">seq1\nACGT\n"
        gz_path = tmp_path / "test.fna.gz"
        with gzip.open(gz_path, "wb") as f:
            f.write(content)

        result_path, is_temp = decompress_fasta(gz_path)
        try:
            assert is_temp is True
            assert result_path != gz_path
            assert result_path.exists()
            assert result_path.read_text() == ">seq1\nACGT\n"
        finally:
            result_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# check_dependencies
# ---------------------------------------------------------------------------
class TestCheckDependencies:
    # When mlst is on PATH, --check exits 0 (success)
    def test_mlst_found(self):
        with patch("shutil.which", return_value="/usr/bin/mlst"):
            with pytest.raises(SystemExit) as exc_info:
                check_dependencies()
            assert exc_info.value.code == 0

    # When mlst is missing from PATH, --check exits 1 (failure)
    def test_mlst_not_found(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(SystemExit) as exc_info:
                check_dependencies()
            assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# execute
# ---------------------------------------------------------------------------
class TestExecute:
    # Successful commands return their stdout
    def test_successful_command(self):
        mock_result = MagicMock(returncode=0, stdout="output\n", stderr="")
        with patch("subprocess.run", return_value=mock_result):
            assert execute(["echo", "hello"]) == "output\n"

    # Non-zero exit codes trigger sys.exit with the same return code
    def test_failed_command_exits(self):
        mock_result = MagicMock(returncode=1, stdout="", stderr="error msg")
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                execute(["false"])
            assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# run_mlst
# ---------------------------------------------------------------------------
class TestRunMlst:
    # Without a scheme, builds: mlst --full --threads N <fasta>
    def test_auto_detect_command(self):
        with patch.object(gigatyper_mod, "execute", return_value="output") as mock_exec:
            result = run_mlst("/tmp/test.fna", 4)
        mock_exec.assert_called_once_with(["mlst", "--full", "--threads", "4", "/tmp/test.fna"])
        assert result == "output"

    # With a scheme, adds --scheme <name> to the command
    def test_with_scheme(self):
        with patch.object(gigatyper_mod, "execute", return_value="output") as mock_exec:
            result = run_mlst("/tmp/test.fna", 2, scheme="ecoli")
        mock_exec.assert_called_once_with(
            ["mlst", "--full", "--threads", "2", "--scheme", "ecoli", "/tmp/test.fna"]
        )
