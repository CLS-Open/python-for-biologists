"""Tests for composition statistics.

Every number here is checked by hand in the comment next to the assertion. Where
an independent tool exists (Biopython's molecular weight), the value is also
compared in ``scripts/validate_against_biopython.py`` — a hand-computed value and
a citable reference are two different kinds of evidence and we want both.
"""

from __future__ import annotations

import math

import pytest

from seqreport.composition import (
    AMBIGUOUS_WITHOUT_MASS,
    RESIDUE_MASSES,
    WATER,
    at_skew,
    composition,
    gc_content,
    gc_skew,
    kmer_counts,
    molecular_weight,
    shannon_entropy,
    windowed_gc,
)


class TestComposition:
    def test_counts(self):
        # A:2 C:2 G:2 T:2 N:2
        assert composition("ACGTACGTNN") == {"A": 2, "C": 2, "G": 2, "N": 2, "T": 2}

    def test_sorted_by_count_then_alphabetically(self):
        assert list(composition("TTTAG")) == ["T", "A", "G"]

    def test_case_and_whitespace_insensitive(self):
        assert composition("ac gt") == composition("ACGT")

    def test_excluding_ambiguous(self):
        assert composition("ACGTNN", include_ambiguous=False) == {"A": 1, "C": 1, "G": 1, "T": 1}

    def test_empty(self):
        assert composition("") == {}


class TestGcContent:
    def test_hand_computed(self):
        # 6 of 9 residues are G or C
        assert gc_content("GGGCCCATA") == pytest.approx(6 / 9)

    def test_n_is_excluded_from_acgt_denominator(self):
        # GC = 4, unambiguous = 4 -> 1.0
        assert gc_content("GGCCNNNN") == 1.0

    def test_n_is_counted_in_all_denominator(self):
        # GC = 4, all residues = 8 -> 0.5
        assert gc_content("GGCCNNNN", denominator="all") == 0.5

    def test_the_two_denominators_differ(self):
        seq = "GGCCNNNN"
        assert gc_content(seq) != gc_content(seq, denominator="all")

    def test_rna_counts_u_as_unambiguous(self):
        # GC = 2 (G, C); unambiguous denominator counts U as well -> 2/4
        assert gc_content("GCUU") == 0.5

    def test_all_gc(self):
        assert gc_content("GCGC") == 1.0

    def test_no_gc(self):
        assert gc_content("ATAT") == 0.0

    def test_empty_sequence_is_undefined_not_zero(self):
        # Returning 0.0 would be a claim about a sequence that does not exist.
        with pytest.raises(ValueError, match="undefined"):
            gc_content("")

    def test_all_n_is_undefined(self):
        with pytest.raises(ValueError, match="undefined"):
            gc_content("NNNN")

    def test_bad_denominator_raises(self):
        with pytest.raises(ValueError, match="denominator"):
            gc_content("ACGT", denominator="everything")

    def test_range(self):
        for seq in ("ACGT", "AAAA", "GGGG", "ANNN"):
            assert 0.0 <= gc_content(seq) <= 1.0


class TestSkew:
    def test_gc_skew_zero_when_balanced(self):
        assert gc_skew("GGGCCCAA") == 0.0

    def test_gc_skew_hand_computed(self):
        # (4 - 2) / (4 + 2) = 1/3
        assert gc_skew("GGGGCC") == pytest.approx(1 / 3)

    def test_gc_skew_negative(self):
        # (1 - 3) / 4 = -0.5
        assert gc_skew("GCCC") == pytest.approx(-0.5)

    def test_gc_skew_undefined_without_g_and_c(self):
        assert gc_skew("AATT") is None

    def test_at_skew_hand_computed(self):
        # (4 - 2) / 6 = 1/3
        assert at_skew("AAAATT") == pytest.approx(1 / 3)

    def test_at_skew_undefined(self):
        assert at_skew("GGCC") is None

    def test_at_skew_treats_u_as_t(self):
        assert at_skew("AAUU") == 0.0


class TestMolecularWeight:
    def test_single_residue_has_no_peptide_bond(self):
        assert molecular_weight("A") == pytest.approx(89.0932, abs=1e-4)

    def test_dipeptide_loses_one_water(self):
        # 2 x 89.0932 - 18.0153 = 160.1711
        assert molecular_weight("AA") == pytest.approx(160.1711, abs=1e-4)

    def test_tripeptide_loses_two_waters(self):
        m = 3 * RESIDUE_MASSES["G"] - 2 * WATER
        assert molecular_weight("GGG") == pytest.approx(m, abs=1e-9)

    def test_specific_peptide(self):
        # M + A - water = 149.2113 + 89.0932 - 18.0153 = 220.2892
        assert molecular_weight("MA") == pytest.approx(220.2892, abs=1e-4)

    def test_case_insensitive(self):
        assert molecular_weight("ma") == molecular_weight("MA")

    def test_unknown_residue_is_refused_by_default(self):
        with pytest.raises(ValueError, match="no tabulated mass"):
            molecular_weight("MEEPX")

    def test_unknown_residue_skipped_when_asked(self):
        # The X is skipped, so this is the mass of MEEP only.
        assert molecular_weight("MEEPX", strict=False) == pytest.approx(
            molecular_weight("MEEP"), abs=1e-9)

    def test_corrupt_character_is_also_caught(self):
        # Real damaged files contain digits, not just ambiguity codes.
        with pytest.raises(ValueError, match="no tabulated mass"):
            molecular_weight("MEEP1")

    def test_stop_residue_has_no_mass(self):
        assert "*" in AMBIGUOUS_WITHOUT_MASS
        with pytest.raises(ValueError):
            molecular_weight("M*")

    def test_empty_is_undefined(self):
        with pytest.raises(ValueError, match="undefined"):
            molecular_weight("")

    def test_only_unknown_residues_raises_even_when_not_strict(self):
        with pytest.raises(ValueError, match="no residues"):
            molecular_weight("XXX", strict=False)

    def test_mass_increases_with_length(self):
        assert molecular_weight("A" * 10) < molecular_weight("A" * 20)


class TestKmers:
    def test_counts_overlap(self):
        # AC, CG, GT, TA, AC -> AC twice
        assert kmer_counts("ACGTAC", 2) == {"AC": 2, "CG": 1, "GT": 1, "TA": 1}

    def test_total_is_length_minus_k_plus_one(self):
        assert sum(kmer_counts("ACGTACGT", 3).values()) == 6

    def test_k_longer_than_sequence(self):
        assert kmer_counts("AC", 3) == {}

    def test_k_of_one(self):
        assert kmer_counts("AAC", 1) == {"A": 2, "C": 1}

    def test_bad_k(self):
        with pytest.raises(ValueError, match="k must be"):
            kmer_counts("ACGT", 0)


class TestWindowedGc:
    def test_non_overlapping_by_default(self):
        # 8 residues, window 4 -> two windows, both pure GC
        assert [w["gc"] for w in windowed_gc("GGGGCCCC", window=4)] == [1.0, 1.0]

    def test_partial_last_window_is_kept_and_flagged(self):
        windows = windowed_gc("GGGGCC", window=4)
        assert windows[-1]["end"] == 6
        assert windows[-1]["start"] == 4
        assert windows[-1]["complete"] is False
        assert windows[0]["complete"] is True

    def test_short_sequence_gives_one_short_window(self):
        assert windowed_gc("GGGG", window=8) == [
            {"start": 0, "end": 4, "gc": 1.0, "complete": False}
        ]

    def test_overlapping_step(self):
        windows = windowed_gc("ACGTACGT", window=4, step=2)
        assert [w["start"] for w in windows] == [0, 2, 4, 6]

    def test_window_of_all_n_is_none_not_zero(self):
        windows = windowed_gc("NNNNGGGG", window=4)
        assert windows[0]["gc"] is None
        assert windows[1]["gc"] == 1.0

    def test_empty_sequence(self):
        assert windowed_gc("", window=10) == []

    def test_bad_window(self):
        with pytest.raises(ValueError, match="window must be"):
            windowed_gc("ACGT", window=0)

    def test_bad_step(self):
        with pytest.raises(ValueError, match="step must be"):
            windowed_gc("ACGT", window=2, step=0)

    def test_windows_cover_every_position_once_with_default_step(self):
        seq = "ACGT" * 10
        covered = []
        for w in windowed_gc(seq, window=5):
            covered.extend(range(w["start"], w["end"]))
        assert covered == list(range(len(seq)))


class TestEntropy:
    def test_four_equally_frequent_bases_give_two_bits(self):
        assert shannon_entropy("ACGT") == pytest.approx(2.0)

    def test_single_letter_has_no_entropy(self):
        assert shannon_entropy("AAAA") == pytest.approx(0.0)

    def test_repeat_is_less_entropic_than_varied(self):
        assert shannon_entropy("AAAAACGT") < shannon_entropy("ACGTACGT")

    def test_empty_is_undefined(self):
        with pytest.raises(ValueError, match="undefined"):
            shannon_entropy("")

    def test_bounded_by_log2_of_alphabet(self):
        assert shannon_entropy("ACGTACGTAC") <= 2.0 + 1e-12

    def test_dinucleotide_entropy_of_homopolymer_is_zero(self):
        assert shannon_entropy("AAAAA", k=2) == pytest.approx(0.0)


class TestMassTable:
    def test_twenty_standard_residues_plus_extras(self):
        standard = set("ACDEFGHIKLMNPQRSTVWY")
        assert standard <= set(RESIDUE_MASSES)

    def test_table_is_positive(self):
        assert all(m > 0 for m in RESIDUE_MASSES.values())

    def test_water_mass_is_sane(self):
        assert 18.0 < WATER < 18.1

    def test_isoleucine_and_leucine_have_equal_mass(self):
        # Real: they are isomers. A "difference" here would be a table error.
        assert RESIDUE_MASSES["I"] == RESIDUE_MASSES["L"]

    def test_entropy_of_protein_alphabet_never_exceeds_log2_20(self):
        assert shannon_entropy("ACDEFGHIKLMNPQRSTVWY") == pytest.approx(math.log2(20))
