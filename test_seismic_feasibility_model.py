"""
Test suite for the Seismic Feasibility Model (MESA Standard Validator).

Covers AcquisitionGeometry derived totals, every MESAValidator check
(pass / warn / fail paths and zero-guard edge cases), StatisticsCalculator
outputs, ReportGenerator text/HTML rendering, and PlotGenerator file output.
"""

import math

import matplotlib

# Use a non-interactive backend so plotting tests run headless.
matplotlib.use("Agg")

import pytest

from seismic_feasibility_model import (
    AcquisitionGeometry,
    MESAValidator,
    StatisticsCalculator,
    ReportGenerator,
    PlotGenerator,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_geometry(**overrides):
    """Build an AcquisitionGeometry from a healthy baseline, with overrides."""
    params = dict(
        # Receiver parameters
        num_rec_lines=20,
        rec_line_azimuth_min=30,
        rec_line_azimuth_max=210,
        rec_line_spacing=360,
        rec_line_length=12210,
        rec_channels_per_line=408,
        rec_channel_interval=30,
        # Source parameters
        num_src_lines=20,
        src_line_azimuth_min=120,
        src_line_azimuth_max=300,
        src_line_spacing=360,
        src_line_length=3570,
        src_points_per_line=120,
        src_point_interval=30,
        # Fold and offset parameters
        nominal_fold=170,
        max_offset=8022,
        max_in_line_offset=6105,
        max_x_line_offset=5175,
        bin_size=(15, 15),
    )
    params.update(overrides)
    return AcquisitionGeometry(**params)


@pytest.fixture
def geometry():
    return _make_geometry()


@pytest.fixture
def validator(geometry):
    return MESAValidator(geometry)


@pytest.fixture
def calculator(geometry):
    return StatisticsCalculator(geometry)


# ---------------------------------------------------------------------------
# AcquisitionGeometry
# ---------------------------------------------------------------------------

class TestAcquisitionGeometry:
    def test_derived_totals(self, geometry):
        assert geometry.total_receivers == 20 * 408
        assert geometry.total_sources == 20 * 120
        assert geometry.total_traces == geometry.total_receivers * geometry.total_sources

    def test_totals_track_overrides(self):
        geom = _make_geometry(num_rec_lines=2, rec_channels_per_line=3,
                              num_src_lines=4, src_points_per_line=5)
        assert geom.total_receivers == 6
        assert geom.total_sources == 20
        assert geom.total_traces == 120


# ---------------------------------------------------------------------------
# MESAValidator
# ---------------------------------------------------------------------------

class TestFoldUniformity:
    def test_pass_when_above_threshold(self):
        # Few CDPs -> very high expected fold -> ratio well above threshold.
        geom = _make_geometry(nominal_fold=1, bin_size=(12210, 3570))
        result = MESAValidator(geom).validate_fold_uniformity()
        assert result["passed"]
        assert result["status"] == "PASS"
        assert result["uniformity_ratio"] >= MESAValidator.FOLD_UNIFORMITY_THRESHOLD

    def test_warn_when_below_threshold(self):
        # Huge nominal fold makes the ratio collapse below threshold.
        geom = _make_geometry(nominal_fold=10**9)
        v = MESAValidator(geom)
        result = v.validate_fold_uniformity()
        assert not result["passed"]
        assert result["status"] == "WARN"
        assert any("Fold uniformity" in w for w in v.warnings)

    def test_zero_nominal_fold_does_not_divide(self):
        geom = _make_geometry(nominal_fold=0)
        result = MESAValidator(geom).validate_fold_uniformity()
        assert result["uniformity_ratio"] == 0
        assert not result["passed"]


class TestOffsetDistribution:
    def test_pass(self, validator):
        result = validator.validate_offset_distribution()
        theoretical = math.hypot(6105, 5175)
        assert result["theoretical_max"] == round(theoretical, 2)
        assert result["passed"]
        assert result["status"] == "PASS"

    def test_fail_records_error(self):
        # Tiny max_offset relative to the inline/xline extents -> low ratio.
        geom = _make_geometry(max_offset=100)
        v = MESAValidator(geom)
        result = v.validate_offset_distribution()
        assert not result["passed"]
        assert result["status"] == "FAIL"
        assert any("Offset distribution" in e for e in v.errors)

    def test_zero_theoretical_offset(self):
        geom = _make_geometry(max_in_line_offset=0, max_x_line_offset=0)
        result = MESAValidator(geom).validate_offset_distribution()
        assert result["coverage_ratio"] == 0
        assert not result["passed"]


class TestAzimuthCoverage:
    def test_pass(self, validator):
        result = validator.validate_azimuth_coverage()
        # Both ranges are 180 -> coverage 1.0
        assert result["coverage_ratio"] == 1.0
        assert result["passed"]
        assert result["status"] == "PASS"

    def test_warn_when_narrow(self):
        geom = _make_geometry(rec_line_azimuth_min=0, rec_line_azimuth_max=10)
        v = MESAValidator(geom)
        result = v.validate_azimuth_coverage()
        assert not result["passed"]
        assert result["status"] == "WARN"
        assert any("Azimuth coverage" in w for w in v.warnings)


class TestCDPSpacing:
    def test_pass(self, validator, geometry):
        result = validator.validate_cdp_spacing()
        assert result["inline_bins"] == int(geometry.rec_line_length / 15)
        assert result["xline_bins"] == int(geometry.src_line_length / 15)
        assert result["total_cdps"] == result["inline_bins"] * result["xline_bins"]
        assert result["passed"]

    def test_fail_when_bins_too_large(self):
        geom = _make_geometry(bin_size=(100000, 100000))
        result = MESAValidator(geom).validate_cdp_spacing()
        assert result["total_cdps"] == 0
        assert not result["passed"]
        assert result["status"] == "FAIL"


class TestLineParameters:
    def test_pass(self, validator, geometry):
        result = validator.validate_line_parameters()
        assert result["passed"]
        assert result["total_receivers"] == geometry.total_receivers
        assert result["total_sources"] == geometry.total_sources

    def test_fail_records_error(self):
        geom = _make_geometry(num_rec_lines=0)
        v = MESAValidator(geom)
        result = v.validate_line_parameters()
        assert not result["passed"]
        assert result["status"] == "FAIL"
        assert "Invalid line parameters detected" in v.errors


class TestOffsetBalance:
    def test_pass_when_balanced(self, validator):
        result = validator.validate_offset_balance()
        # 5175/6105 ~= 0.847 >= 0.5
        assert result["passed"]
        assert result["status"] == "PASS"

    def test_warn_when_unbalanced(self):
        geom = _make_geometry(max_in_line_offset=8000, max_x_line_offset=100,
                              max_offset=8002)
        result = MESAValidator(geom).validate_offset_balance()
        assert not result["passed"]
        assert result["status"] == "WARN"

    def test_zero_max_offset(self):
        geom = _make_geometry(max_offset=0)
        result = MESAValidator(geom).validate_offset_balance()
        assert result["balance_ratio"] == 0
        assert not result["passed"]


class TestValidateAll:
    def test_returns_all_sections(self, validator):
        results = validator.validate_all()
        expected = {
            "fold_uniformity",
            "offset_distribution",
            "azimuth_coverage",
            "cdp_spacing",
            "line_parameters",
            "offset_balance",
        }
        assert set(results) == expected
        assert validator.validation_results == results

    def test_baseline_statuses(self, validator):
        # The baseline geometry passes every check except fold uniformity,
        # which warns (expected fold ~101 vs nominal 170).
        results = validator.validate_all()
        assert results["fold_uniformity"]["status"] == "WARN"
        for name in ("offset_distribution", "azimuth_coverage", "cdp_spacing",
                     "line_parameters", "offset_balance"):
            assert results[name]["passed"], name
        assert validator.errors == []
        assert any("Fold uniformity" in w for w in validator.warnings)


# ---------------------------------------------------------------------------
# StatisticsCalculator
# ---------------------------------------------------------------------------

class TestStatisticsCalculator:
    def test_calculate_all_sections(self, calculator):
        stats = calculator.calculate_all()
        assert set(stats) == {
            "geometry_stats", "fold_stats", "offset_stats", "coverage_stats"
        }

    def test_geometry_statistics(self, calculator, geometry):
        g = calculator.geometry_statistics()
        assert g["total_traces"] == geometry.total_traces
        assert g["total_receivers"] == geometry.total_receivers

    def test_fold_statistics(self, calculator, geometry):
        f = calculator.fold_statistics()
        bin_x, bin_y = geometry.bin_size
        cdp = int((geometry.rec_line_length / bin_x) * (geometry.src_line_length / bin_y))
        assert f["total_cdps"] == cdp
        assert f["average_fold"] == round(geometry.total_traces / cdp, 2)

    def test_offset_statistics_ratio(self, calculator):
        o = calculator.offset_statistics()
        expected = round(8022 / math.hypot(6105, 5175), 4)
        assert o["offset_distance_ratio"] == expected

    def test_coverage_statistics(self, calculator):
        c = calculator.coverage_statistics()
        assert c["receiver_azimuth_range"] == 180
        assert c["source_azimuth_range"] == 180


# ---------------------------------------------------------------------------
# ReportGenerator
# ---------------------------------------------------------------------------

class TestReportGenerator:
    def _build(self, geometry):
        validator = MESAValidator(geometry)
        validator.validate_all()
        calculator = StatisticsCalculator(geometry)
        return ReportGenerator(geometry, validator, calculator)

    def test_text_report_contents(self, geometry):
        report = self._build(geometry).generate_text_report()
        assert "MESA VALIDATION REPORT" in report
        assert "VALIDATION SUMMARY" in report
        assert "ACQUISITION STATISTICS" in report
        assert "fold_uniformity" in report

    def test_text_report_writes_file(self, geometry, tmp_path):
        path = tmp_path / "report.txt"
        report = self._build(geometry).generate_text_report(str(path))
        assert path.exists()
        assert path.read_text() == report

    def test_html_report_contents(self, geometry):
        html = self._build(geometry).generate_html_report()
        assert html.startswith("<!DOCTYPE html>")
        assert "<table>" in html
        assert "MESA VALIDATION REPORT" in html

    def test_html_report_writes_file(self, geometry, tmp_path):
        path = tmp_path / "report.html"
        html = self._build(geometry).generate_html_report(str(path))
        assert path.exists()
        assert path.read_text() == html

    def test_report_surfaces_warnings(self):
        geom = _make_geometry(rec_line_azimuth_min=0, rec_line_azimuth_max=10)
        report = self._build(geom).generate_text_report()
        assert "WARNINGS" in report


# ---------------------------------------------------------------------------
# PlotGenerator
# ---------------------------------------------------------------------------

class TestPlotGenerator:
    def test_generate_all_plots(self, geometry, calculator, tmp_path):
        stats = calculator.calculate_all()
        PlotGenerator(geometry, stats).generate_all_plots(str(tmp_path))
        for name in (
            "acquisition_layout.png",
            "fold_distribution.png",
            "offset_distribution.png",
            "azimuth_coverage.png",
            "summary_statistics.png",
        ):
            out = tmp_path / name
            assert out.exists() and out.stat().st_size > 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
