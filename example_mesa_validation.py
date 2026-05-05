"""
Example: MESA Standard Validation for Orthogonal Cross Array Acquisition
Based on the acquisition parameters from the provided design document.
"""

from seismic_feasibility_model import (
    AcquisitionGeometry,
    MESAValidator,
    StatisticsCalculator,
    ReportGenerator,
    PlotGenerator
)
import json
import numpy as np


def main():
    """Run MESA validation example with orthogonal cross array geometry."""

    # Acquisition parameters from the design document
    geometry = AcquisitionGeometry(
        # Receiver parameters
        num_rec_lines=20,
        rec_line_azimuth_min=30,
        rec_line_azimuth_max=210,
        rec_line_spacing=360,
        rec_line_length=12210,
        rec_channels_per_line=408,
        rec_channel_interval=30,

        # Source parameters
        num_src_lines=20,  # Inferred from layout
        src_line_azimuth_min=120,
        src_line_azimuth_max=300,
        src_line_spacing=360,
        src_line_length=3570,
        src_points_per_line=120,  # VPs per line
        src_point_interval=30,

        # Fold and offset parameters
        nominal_fold=170,
        max_offset=8022,
        max_in_line_offset=6105,
        max_x_line_offset=5175,
        bin_size=(15, 15),
    )

    print("=" * 80)
    print("MESA SEISMIC ACQUISITION VALIDATION")
    print("=" * 80)
    print(f"\nGeometry Summary:")
    print(f"  Total Receivers: {geometry.total_receivers:,}")
    print(f"  Total Sources: {geometry.total_sources:,}")
    print(f"  Total Traces: {geometry.total_traces:,}")
    print(f"  Receiver Lines: {geometry.num_rec_lines}")
    print(f"  Source Lines: {geometry.num_src_lines}")
    print()

    # Create validator
    validator = MESAValidator(geometry)
    validation_results = validator.validate_all()

    print("Running MESA Standard Validations...")
    print("-" * 80)

    for test_name, result in validation_results.items():
        status = result.get('status', 'UNKNOWN')
        status_symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        print(f"{status_symbol} {test_name:.<50} {status}")

    print()

    # Display errors and warnings
    if validator.errors:
        print("ERRORS:")
        for error in validator.errors:
            print(f"  ✗ {error}")
        print()

    if validator.warnings:
        print("WARNINGS:")
        for warning in validator.warnings:
            print(f"  ⚠ {warning}")
        print()

    # Calculate statistics
    calculator = StatisticsCalculator(geometry)
    statistics = calculator.calculate_all()

    print("ACQUISITION STATISTICS:")
    print("-" * 80)
    print("\nGeometry Statistics:")
    for key, val in statistics['geometry_stats'].items():
        print(f"  {key:.<40} {val:,}" if isinstance(val, int) else f"  {key:.<40} {val}")

    print("\nFold Statistics:")
    for key, val in statistics['fold_stats'].items():
        print(f"  {key:.<40} {val}")

    print("\nOffset Statistics:")
    for key, val in statistics['offset_stats'].items():
        print(f"  {key:.<40} {val}")

    print("\nCoverage Statistics:")
    for key, val in statistics['coverage_stats'].items():
        print(f"  {key:.<40} {val}")

    print()
    print("=" * 80)

    # Generate reports
    report_generator = ReportGenerator(geometry, validator, calculator)

    print("Generating Reports...")
    # Text report
    text_report = report_generator.generate_text_report('MESA_VALIDATION_REPORT.txt')
    print("  ✓ Text report saved: MESA_VALIDATION_REPORT.txt")

    # HTML report
    html_report = report_generator.generate_html_report('MESA_VALIDATION_REPORT.html')
    print("  ✓ HTML report saved: MESA_VALIDATION_REPORT.html")

    # Generate plots
    plot_generator = PlotGenerator(geometry, statistics)
    print("  Generating plots...")
    plot_generator.generate_all_plots('.')
    print("  ✓ Acquisition layout: acquisition_layout.png")
    print("  ✓ Fold distribution: fold_distribution.png")
    print("  ✓ Offset distribution: offset_distribution.png")
    print("  ✓ Azimuth coverage: azimuth_coverage.png")
    print("  ✓ Summary statistics: summary_statistics.png")

    # Save statistics as JSON
    with open('mesa_statistics.json', 'w') as f:
        json.dump(statistics, f, indent=2)
    print("  ✓ Statistics saved: mesa_statistics.json")

    # Save validation results as JSON
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.bool_, np.integer, np.floating)):
                return obj.item()
            return super().default(obj)

    with open('mesa_validation_results.json', 'w') as f:
        json.dump(validation_results, f, indent=2, cls=NumpyEncoder)
    print("  ✓ Validation results saved: mesa_validation_results.json")

    print("\n" + "=" * 80)
    print("MESA Validation Complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
