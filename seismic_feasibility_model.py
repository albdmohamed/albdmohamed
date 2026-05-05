"""
Seismic Feasibility Model - MESA Standard Validator
Validates acquisition geometry against MESA standards with statistical analysis and reporting.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import warnings


@dataclass
class AcquisitionGeometry:
    """Represents seismic acquisition geometry parameters."""

    # Receiver parameters
    num_rec_lines: int
    rec_line_azimuth_min: float
    rec_line_azimuth_max: float
    rec_line_spacing: float
    rec_line_length: float
    rec_channels_per_line: int
    rec_channel_interval: float

    # Source parameters
    num_src_lines: int
    src_line_azimuth_min: float
    src_line_azimuth_max: float
    src_line_spacing: float
    src_line_length: float
    src_points_per_line: int
    src_point_interval: float

    # Fold and offset parameters
    nominal_fold: int
    max_offset: float
    max_in_line_offset: float
    max_x_line_offset: float
    bin_size: Tuple[float, float]

    def __post_init__(self):
        self.total_receivers = self.num_rec_lines * self.rec_channels_per_line
        self.total_sources = self.num_src_lines * self.src_points_per_line
        self.total_traces = self.total_receivers * self.total_sources


class MESAValidator:
    """Validates seismic geometry against MESA standards."""

    # MESA standard thresholds
    FOLD_UNIFORMITY_THRESHOLD = 0.85  # Minimum acceptable fold uniformity (85% of nominal)
    OFFSET_DISTRIBUTION_RATIO = 0.90  # Expected ratio of covered offsets
    AZIMUTH_COVERAGE_MIN = 0.75  # Minimum azimuth coverage requirement
    CROSSLINE_OFFSET_TOLERANCE = 0.15  # ±15% tolerance for cross-line offset
    INLINE_OFFSET_TOLERANCE = 0.15  # ±15% tolerance for in-line offset

    def __init__(self, geometry: AcquisitionGeometry):
        self.geometry = geometry
        self.validation_results = {}
        self.warnings = []
        self.errors = []

    def validate_all(self) -> Dict:
        """Run all validations and return results."""
        self.validation_results = {
            'fold_uniformity': self.validate_fold_uniformity(),
            'offset_distribution': self.validate_offset_distribution(),
            'azimuth_coverage': self.validate_azimuth_coverage(),
            'cdp_spacing': self.validate_cdp_spacing(),
            'line_parameters': self.validate_line_parameters(),
            'offset_balance': self.validate_offset_balance(),
        }
        return self.validation_results

    def validate_fold_uniformity(self) -> Dict:
        """Validate fold uniformity across the survey."""
        nominal_fold = self.geometry.nominal_fold
        expected_cdps = self._calculate_cdp_count()
        expected_fold = self.geometry.total_traces / expected_cdps if expected_cdps > 0 else 0

        uniformity_ratio = expected_fold / nominal_fold if nominal_fold > 0 else 0
        passed = uniformity_ratio >= self.FOLD_UNIFORMITY_THRESHOLD

        if not passed:
            self.warnings.append(
                f"Fold uniformity below threshold: {uniformity_ratio:.2%} < {self.FOLD_UNIFORMITY_THRESHOLD:.2%}"
            )

        return {
            'passed': passed,
            'nominal_fold': nominal_fold,
            'expected_fold': round(expected_fold, 2),
            'uniformity_ratio': round(uniformity_ratio, 4),
            'threshold': self.FOLD_UNIFORMITY_THRESHOLD,
            'status': 'PASS' if passed else 'WARN'
        }

    def validate_offset_distribution(self) -> Dict:
        """Validate offset distribution coverage."""
        max_theoretical_offset = np.sqrt(
            self.geometry.max_in_line_offset**2 +
            self.geometry.max_x_line_offset**2
        )

        offset_ratio = self.geometry.max_offset / max_theoretical_offset if max_theoretical_offset > 0 else 0
        passed = offset_ratio >= self.OFFSET_DISTRIBUTION_RATIO

        if not passed:
            self.errors.append(
                f"Offset distribution inadequate: {offset_ratio:.2%} < {self.OFFSET_DISTRIBUTION_RATIO:.2%}"
            )

        return {
            'passed': passed,
            'max_offset': round(self.geometry.max_offset, 2),
            'theoretical_max': round(max_theoretical_offset, 2),
            'coverage_ratio': round(offset_ratio, 4),
            'threshold': self.OFFSET_DISTRIBUTION_RATIO,
            'status': 'PASS' if passed else 'FAIL'
        }

    def validate_azimuth_coverage(self) -> Dict:
        """Validate azimuth coverage."""
        rec_azimuth_range = self.geometry.rec_line_azimuth_max - self.geometry.rec_line_azimuth_min
        src_azimuth_range = self.geometry.src_line_azimuth_max - self.geometry.src_line_azimuth_min

        azimuth_coverage = min(rec_azimuth_range, src_azimuth_range) / 180.0
        passed = azimuth_coverage >= self.AZIMUTH_COVERAGE_MIN

        if not passed:
            self.warnings.append(
                f"Azimuth coverage below threshold: {azimuth_coverage:.2%} < {self.AZIMUTH_COVERAGE_MIN:.2%}"
            )

        return {
            'passed': passed,
            'rec_azimuth_range': round(rec_azimuth_range, 2),
            'src_azimuth_range': round(src_azimuth_range, 2),
            'coverage_ratio': round(azimuth_coverage, 4),
            'threshold': self.AZIMUTH_COVERAGE_MIN,
            'status': 'PASS' if passed else 'WARN'
        }

    def validate_cdp_spacing(self) -> Dict:
        """Validate CDP bin spacing."""
        bin_x, bin_y = self.geometry.bin_size
        inline_bin_count = int(self.geometry.rec_line_length / bin_x)
        xline_bin_count = int(self.geometry.src_line_length / bin_y)

        total_cdps = inline_bin_count * xline_bin_count
        passed = total_cdps > 0

        return {
            'passed': passed,
            'bin_size': (round(bin_x, 2), round(bin_y, 2)),
            'inline_bins': inline_bin_count,
            'xline_bins': xline_bin_count,
            'total_cdps': total_cdps,
            'status': 'PASS' if passed else 'FAIL'
        }

    def validate_line_parameters(self) -> Dict:
        """Validate line spacing and channel parameters."""
        rec_line_count = int(self.geometry.rec_line_length / self.geometry.rec_channel_interval)
        src_point_count = int(self.geometry.src_line_length / self.geometry.src_point_interval)

        passed = (
            rec_line_count > 0 and
            src_point_count > 0 and
            self.geometry.num_rec_lines > 0 and
            self.geometry.num_src_lines > 0
        )

        if not passed:
            self.errors.append("Invalid line parameters detected")

        return {
            'passed': passed,
            'receiver_lines': self.geometry.num_rec_lines,
            'source_lines': self.geometry.num_src_lines,
            'rec_channels_per_line': self.geometry.rec_channels_per_line,
            'src_points_per_line': self.geometry.src_points_per_line,
            'total_receivers': self.geometry.total_receivers,
            'total_sources': self.geometry.total_sources,
            'status': 'PASS' if passed else 'FAIL'
        }

    def validate_offset_balance(self) -> Dict:
        """Validate balance between inline and crossline offsets."""
        inline_offset_ratio = self.geometry.max_in_line_offset / self.geometry.max_offset if self.geometry.max_offset > 0 else 0
        xline_offset_ratio = self.geometry.max_x_line_offset / self.geometry.max_offset if self.geometry.max_offset > 0 else 0

        # Check if offsets are reasonably balanced
        balance_ratio = min(inline_offset_ratio, xline_offset_ratio) / max(inline_offset_ratio, xline_offset_ratio) if max(inline_offset_ratio, xline_offset_ratio) > 0 else 0
        passed = balance_ratio >= 0.5  # At least 50% balance

        return {
            'passed': passed,
            'inline_offset': round(self.geometry.max_in_line_offset, 2),
            'xline_offset': round(self.geometry.max_x_line_offset, 2),
            'balance_ratio': round(balance_ratio, 4),
            'inline_ratio': round(inline_offset_ratio, 4),
            'xline_ratio': round(xline_offset_ratio, 4),
            'status': 'PASS' if passed else 'WARN'
        }

    def _calculate_cdp_count(self) -> int:
        """Calculate total CDP count from geometry."""
        bin_x, bin_y = self.geometry.bin_size
        inline_bins = int(self.geometry.rec_line_length / bin_x)
        xline_bins = int(self.geometry.src_line_length / bin_y)
        return inline_bins * xline_bins


class StatisticsCalculator:
    """Calculate acquisition statistics."""

    def __init__(self, geometry: AcquisitionGeometry):
        self.geometry = geometry

    def calculate_all(self) -> Dict:
        """Calculate comprehensive statistics."""
        return {
            'geometry_stats': self.geometry_statistics(),
            'fold_stats': self.fold_statistics(),
            'offset_stats': self.offset_statistics(),
            'coverage_stats': self.coverage_statistics(),
        }

    def geometry_statistics(self) -> Dict:
        """Calculate geometry statistics."""
        return {
            'total_receivers': self.geometry.total_receivers,
            'total_sources': self.geometry.total_sources,
            'total_traces': self.geometry.total_traces,
            'receiver_line_length': round(self.geometry.rec_line_length, 2),
            'source_line_length': round(self.geometry.src_line_length, 2),
            'receiver_line_spacing': round(self.geometry.rec_line_spacing, 2),
            'source_line_spacing': round(self.geometry.src_line_spacing, 2),
            'channel_interval': round(self.geometry.rec_channel_interval, 2),
            'source_point_interval': round(self.geometry.src_point_interval, 2),
        }

    def fold_statistics(self) -> Dict:
        """Calculate fold statistics."""
        bin_x, bin_y = self.geometry.bin_size
        cdp_count = int((self.geometry.rec_line_length / bin_x) *
                        (self.geometry.src_line_length / bin_y))

        avg_fold = self.geometry.total_traces / cdp_count if cdp_count > 0 else 0
        fold_efficiency = avg_fold / self.geometry.nominal_fold if self.geometry.nominal_fold > 0 else 0

        return {
            'nominal_fold': self.geometry.nominal_fold,
            'average_fold': round(avg_fold, 2),
            'fold_efficiency': round(fold_efficiency, 4),
            'total_cdps': cdp_count,
            'bin_size_inline': round(bin_x, 2),
            'bin_size_xline': round(bin_y, 2),
        }

    def offset_statistics(self) -> Dict:
        """Calculate offset statistics."""
        return {
            'max_offset': round(self.geometry.max_offset, 2),
            'max_inline_offset': round(self.geometry.max_in_line_offset, 2),
            'max_xline_offset': round(self.geometry.max_x_line_offset, 2),
            'offset_distance_ratio': round(
                self.geometry.max_offset /
                np.sqrt(self.geometry.max_in_line_offset**2 + self.geometry.max_x_line_offset**2)
                if self.geometry.max_in_line_offset > 0 and self.geometry.max_x_line_offset > 0 else 0,
                4
            ),
        }

    def coverage_statistics(self) -> Dict:
        """Calculate coverage statistics."""
        rec_azimuth = self.geometry.rec_line_azimuth_max - self.geometry.rec_line_azimuth_min
        src_azimuth = self.geometry.src_line_azimuth_max - self.geometry.src_line_azimuth_min

        return {
            'receiver_azimuth_range': round(rec_azimuth, 2),
            'source_azimuth_range': round(src_azimuth, 2),
            'receiver_azimuth_min': round(self.geometry.rec_line_azimuth_min, 2),
            'receiver_azimuth_max': round(self.geometry.rec_line_azimuth_max, 2),
            'source_azimuth_min': round(self.geometry.src_line_azimuth_min, 2),
            'source_azimuth_max': round(self.geometry.src_line_azimuth_max, 2),
        }


class ReportGenerator:
    """Generate validation and statistical reports."""

    def __init__(self, geometry: AcquisitionGeometry, validator: MESAValidator,
                 calculator: StatisticsCalculator):
        self.geometry = geometry
        self.validator = validator
        self.calculator = calculator

    def generate_text_report(self, filename: Optional[str] = None) -> str:
        """Generate comprehensive text report."""
        report = []
        report.append("=" * 80)
        report.append("SEISMIC ACQUISITION GEOMETRY - MESA VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")

        # Validation Summary
        report.append("VALIDATION SUMMARY")
        report.append("-" * 80)
        for test_name, result in self.validator.validation_results.items():
            status = result.get('status', 'UNKNOWN')
            report.append(f"{test_name:.<50} {status}")
        report.append("")

        # Errors and Warnings
        if self.validator.errors:
            report.append("ERRORS")
            report.append("-" * 80)
            for error in self.validator.errors:
                report.append(f"  ✗ {error}")
            report.append("")

        if self.validator.warnings:
            report.append("WARNINGS")
            report.append("-" * 80)
            for warning in self.validator.warnings:
                report.append(f"  ⚠ {warning}")
            report.append("")

        # Detailed Results
        report.append("DETAILED VALIDATION RESULTS")
        report.append("-" * 80)
        for test_name, result in self.validator.validation_results.items():
            report.append(f"\n{test_name.upper()}:")
            for key, value in result.items():
                if key != 'status':
                    report.append(f"  {key:.<40} {value}")
        report.append("")

        # Statistics
        report.append("ACQUISITION STATISTICS")
        report.append("-" * 80)
        stats = self.calculator.calculate_all()

        for section, section_stats in stats.items():
            report.append(f"\n{section.upper()}:")
            for key, value in section_stats.items():
                report.append(f"  {key:.<40} {value}")

        report.append("")
        report.append("=" * 80)

        report_text = "\n".join(report)

        if filename:
            with open(filename, 'w') as f:
                f.write(report_text)

        return report_text

    def generate_html_report(self, filename: Optional[str] = None) -> str:
        """Generate HTML report."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<title>MESA Validation Report</title>")
        html.append("<style>")
        html.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        html.append("h1 { color: #333; border-bottom: 3px solid #0066cc; }")
        html.append("h2 { color: #0066cc; margin-top: 30px; }")
        html.append("table { border-collapse: collapse; width: 100%; margin: 15px 0; }")
        html.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html.append("th { background-color: #0066cc; color: white; }")
        html.append("tr:nth-child(even) { background-color: #f9f9f9; }")
        html.append(".pass { color: green; font-weight: bold; }")
        html.append(".fail { color: red; font-weight: bold; }")
        html.append(".warn { color: orange; font-weight: bold; }")
        html.append(".error-box { background-color: #ffe6e6; padding: 10px; margin: 10px 0; }")
        html.append(".warn-box { background-color: #fff3cd; padding: 10px; margin: 10px 0; }")
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")

        html.append("<h1>SEISMIC ACQUISITION GEOMETRY - MESA VALIDATION REPORT</h1>")

        # Validation Summary Table
        html.append("<h2>Validation Summary</h2>")
        html.append("<table>")
        html.append("<tr><th>Test</th><th>Status</th></tr>")
        for test_name, result in self.validator.validation_results.items():
            status = result.get('status', 'UNKNOWN')
            status_class = 'pass' if status == 'PASS' else 'fail' if status == 'FAIL' else 'warn'
            html.append(f"<tr><td>{test_name}</td><td class='{status_class}'>{status}</td></tr>")
        html.append("</table>")

        # Errors
        if self.validator.errors:
            html.append("<h2>Errors</h2>")
            for error in self.validator.errors:
                html.append(f"<div class='error-box'>✗ {error}</div>")

        # Warnings
        if self.validator.warnings:
            html.append("<h2>Warnings</h2>")
            for warning in self.validator.warnings:
                html.append(f"<div class='warn-box'>⚠ {warning}</div>")

        # Detailed Results
        html.append("<h2>Detailed Results</h2>")
        for test_name, result in self.validator.validation_results.items():
            html.append(f"<h3>{test_name.title()}</h3>")
            html.append("<table>")
            for key, value in result.items():
                if key != 'status':
                    html.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
            html.append("</table>")

        # Statistics
        html.append("<h2>Acquisition Statistics</h2>")
        stats = self.calculator.calculate_all()
        for section, section_stats in stats.items():
            html.append(f"<h3>{section.title()}</h3>")
            html.append("<table>")
            for key, value in section_stats.items():
                html.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
            html.append("</table>")

        html.append("</body>")
        html.append("</html>")

        html_text = "\n".join(html)

        if filename:
            with open(filename, 'w') as f:
                f.write(html_text)

        return html_text


class PlotGenerator:
    """Generate visualization plots."""

    def __init__(self, geometry: AcquisitionGeometry, statistics: Dict):
        self.geometry = geometry
        self.statistics = statistics

    def generate_all_plots(self, output_dir: str = '.'):
        """Generate all plots."""
        self.plot_acquisition_layout(f"{output_dir}/acquisition_layout.png")
        self.plot_fold_distribution(f"{output_dir}/fold_distribution.png")
        self.plot_offset_distribution(f"{output_dir}/offset_distribution.png")
        self.plot_azimuth_coverage(f"{output_dir}/azimuth_coverage.png")
        self.plot_summary_statistics(f"{output_dir}/summary_statistics.png")

    def plot_acquisition_layout(self, filename: str):
        """Plot acquisition geometry layout."""
        fig, ax = plt.subplots(figsize=(12, 8))

        # Plot receiver lines
        for i in range(self.geometry.num_rec_lines):
            y_pos = i * self.geometry.rec_line_spacing
            ax.plot([0, self.geometry.rec_line_length], [y_pos, y_pos], 'b-', alpha=0.6, linewidth=2)

        # Plot source lines
        for i in range(self.geometry.num_src_lines):
            x_pos = i * self.geometry.src_line_spacing
            ax.plot([x_pos, x_pos], [0, self.geometry.src_line_length], 'r-', alpha=0.6, linewidth=2)

        ax.set_xlabel('Inline (m)', fontsize=12)
        ax.set_ylabel('Crossline (m)', fontsize=12)
        ax.set_title('Acquisition Geometry Layout', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(['Receiver Lines', 'Source Lines'], loc='upper right')

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()

    def plot_fold_distribution(self, filename: str):
        """Plot fold distribution."""
        fig, ax = plt.subplots(figsize=(10, 6))

        fold_stats = self.statistics.get('fold_stats', {})
        nominal_fold = fold_stats.get('nominal_fold', 1)
        avg_fold = fold_stats.get('average_fold', 1)

        categories = ['Nominal Fold', 'Average Fold']
        values = [nominal_fold, avg_fold]
        colors = ['#0066cc', '#00cc66']

        bars = ax.bar(categories, values, color=colors, alpha=0.7, edgecolor='black')

        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(val)}', ha='center', va='bottom', fontsize=12, fontweight='bold')

        ax.set_ylabel('Fold', fontsize=12)
        ax.set_title('Fold Distribution', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()

    def plot_offset_distribution(self, filename: str):
        """Plot offset distribution."""
        fig, ax = plt.subplots(figsize=(10, 8))

        offset_stats = self.statistics.get('offset_stats', {})
        max_inline = offset_stats.get('max_inline_offset', 1)
        max_xline = offset_stats.get('max_xline_offset', 1)
        max_offset = offset_stats.get('max_offset', 1)

        # Draw offset distribution
        theta = np.linspace(0, 2*np.pi, 100)

        # Maximum offset circle
        x_circle = max_offset * np.cos(theta)
        y_circle = max_offset * np.sin(theta)
        ax.plot(x_circle, y_circle, 'r-', linewidth=2, label=f'Max Offset: {max_offset:.0f}m')

        # Inline and crossline extents
        ax.plot([-max_inline, max_inline], [0, 0], 'b-', linewidth=2, label=f'Inline: ±{max_inline:.0f}m')
        ax.plot([0, 0], [-max_xline, max_xline], 'g-', linewidth=2, label=f'Xline: ±{max_xline:.0f}m')

        ax.set_xlabel('Inline Offset (m)', fontsize=12)
        ax.set_ylabel('Crossline Offset (m)', fontsize=12)
        ax.set_title('Offset Vector Distribution', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.axis('equal')
        ax.legend(loc='upper right')

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()

    def plot_azimuth_coverage(self, filename: str):
        """Plot azimuth coverage."""
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

        cov_stats = self.statistics.get('coverage_stats', {})
        rec_min = np.radians(cov_stats.get('receiver_azimuth_min', 0))
        rec_max = np.radians(cov_stats.get('receiver_azimuth_max', 180))
        src_min = np.radians(cov_stats.get('source_azimuth_min', 0))
        src_max = np.radians(cov_stats.get('source_azimuth_max', 180))

        # Plot receiver coverage
        theta_rec = np.linspace(rec_min, rec_max, 50)
        ax.fill_between(theta_rec, 0, 1, alpha=0.3, color='blue', label='Receiver Azimuth')

        # Plot source coverage
        theta_src = np.linspace(src_min, src_max, 50)
        ax.fill_between(theta_src, 0, 1, alpha=0.3, color='red', label='Source Azimuth')

        ax.set_ylim(0, 1)
        ax.set_title('Azimuth Coverage', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

    def plot_summary_statistics(self, filename: str):
        """Plot summary statistics."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Acquisition Summary Statistics', fontsize=16, fontweight='bold')

        geom_stats = self.statistics.get('geometry_stats', {})
        fold_stats = self.statistics.get('fold_stats', {})
        offset_stats = self.statistics.get('offset_stats', {})

        # Trace count
        ax = axes[0, 0]
        ax.text(0.5, 0.7, f"{geom_stats.get('total_traces', 0):,}",
               ha='center', va='center', fontsize=24, fontweight='bold')
        ax.text(0.5, 0.3, 'Total Traces', ha='center', va='center', fontsize=12)
        ax.axis('off')
        ax.set_title('Trace Count', fontweight='bold')

        # CDP count
        ax = axes[0, 1]
        ax.text(0.5, 0.7, f"{fold_stats.get('total_cdps', 0):,}",
               ha='center', va='center', fontsize=24, fontweight='bold')
        ax.text(0.5, 0.3, 'Total CDPs', ha='center', va='center', fontsize=12)
        ax.axis('off')
        ax.set_title('CDP Count', fontweight='bold')

        # Fold efficiency
        ax = axes[1, 0]
        efficiency = fold_stats.get('fold_efficiency', 0) * 100
        ax.text(0.5, 0.7, f"{efficiency:.1f}%",
               ha='center', va='center', fontsize=24, fontweight='bold')
        ax.text(0.5, 0.3, 'Fold Efficiency', ha='center', va='center', fontsize=12)
        ax.axis('off')
        ax.set_title('Fold Efficiency', fontweight='bold')

        # Max offset
        ax = axes[1, 1]
        max_offset = offset_stats.get('max_offset', 0)
        ax.text(0.5, 0.7, f"{max_offset:.0f}m",
               ha='center', va='center', fontsize=24, fontweight='bold')
        ax.text(0.5, 0.3, 'Maximum Offset', ha='center', va='center', fontsize=12)
        ax.axis('off')
        ax.set_title('Offset Coverage', fontweight='bold')

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()
