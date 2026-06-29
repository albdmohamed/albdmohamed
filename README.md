# Seismic Feasibility Model - MESA Standard Validator

A Python module for validating seismic acquisition geometry against MESA (Model for Extended Seismic Acquisition) standards. Generates comprehensive validation reports, statistics, and visualization plots.

## Features

- **MESA Standard Validation**: Validates acquisition geometry against industry best practices
- **Statistical Analysis**: Calculates comprehensive acquisition statistics
- **Multiple Report Formats**: Text, HTML, and JSON reports
- **Visualization Plots**: 
  - Acquisition layout diagram
  - Fold distribution analysis
  - Offset vector distribution
  - Azimuth coverage polar plot
  - Summary statistics visualization

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from seismic_feasibility_model import (
    AcquisitionGeometry,
    MESAValidator,
    StatisticsCalculator,
    ReportGenerator,
    PlotGenerator
)

# Define acquisition geometry
geometry = AcquisitionGeometry(
    num_rec_lines=20,
    rec_line_azimuth_min=30,
    rec_line_azimuth_max=210,
    rec_line_spacing=360,
    rec_line_length=12210,
    rec_channels_per_line=408,
    rec_channel_interval=30,
    
    num_src_lines=20,
    src_line_azimuth_min=120,
    src_line_azimuth_max=300,
    src_line_spacing=360,
    src_line_length=3570,
    src_points_per_line=120,
    src_point_interval=30,
    
    nominal_fold=170,
    max_offset=8022,
    max_in_line_offset=6105,
    max_x_line_offset=5175,
    bin_size=(15, 15),
)

# Run validation
validator = MESAValidator(geometry)
results = validator.validate_all()

# Calculate statistics
calculator = StatisticsCalculator(geometry)
stats = calculator.calculate_all()

# Generate reports
generator = ReportGenerator(geometry, validator, calculator)
generator.generate_text_report('report.txt')
generator.generate_html_report('report.html')

# Generate plots
plotter = PlotGenerator(geometry, stats)
plotter.generate_all_plots('.')
```

## Running the Tests

The project ships with a `pytest` suite covering geometry totals, every MESA
validation check (pass / warn / fail and zero-guard edge cases), the statistics
calculator, report rendering, and plot generation.

```bash
pip install pytest
python -m pytest -q
```

## Running the Example

```bash
python example_mesa_validation.py
```

This will generate:
- `MESA_VALIDATION_REPORT.txt` - Text report with validation results
- `MESA_VALIDATION_REPORT.html` - HTML report (viewable in browser)
- `mesa_statistics.json` - Statistical data in JSON format
- `mesa_validation_results.json` - Validation results in JSON format
- `acquisition_layout.png` - Acquisition geometry visualization
- `fold_distribution.png` - Fold statistics chart
- `offset_distribution.png` - Offset vector diagram
- `azimuth_coverage.png` - Azimuth coverage polar plot
- `summary_statistics.png` - Summary statistics dashboard

## Module Components

### AcquisitionGeometry
Dataclass representing seismic acquisition parameters:
- **Receiver parameters**: Lines, azimuth, spacing, channels
- **Source parameters**: Lines, azimuth, spacing, points
- **Fold parameters**: Nominal fold, offset limits, bin size

### MESAValidator
Validates geometry against MESA standards:
- **Fold Uniformity**: Checks if fold distribution meets minimum thresholds
- **Offset Distribution**: Validates offset coverage ratios
- **Azimuth Coverage**: Ensures adequate azimuth range
- **CDP Spacing**: Validates bin grid parameters
- **Line Parameters**: Checks receiver and source configuration
- **Offset Balance**: Verifies inline/crossline offset balance

### StatisticsCalculator
Computes acquisition statistics:
- **Geometry Statistics**: Receiver/source counts, lengths, intervals
- **Fold Statistics**: Nominal, average, and efficiency metrics
- **Offset Statistics**: Maximum offsets, ratios, and distances
- **Coverage Statistics**: Azimuth ranges and distributions

### ReportGenerator
Creates validation reports in multiple formats:
- **Text Report**: Plain text format with detailed results
- **HTML Report**: Interactive HTML document for browsers

### PlotGenerator
Creates visualization plots:
- Acquisition layout with receiver/source line grids
- Fold distribution bar chart
- Offset vector visualization
- Polar azimuth coverage plot
- Summary statistics dashboard

## MESA Validation Standards

The validator checks against the following MESA standards:

| Standard | Threshold | Description |
|----------|-----------|-------------|
| Fold Uniformity | ≥ 85% | Minimum acceptable fold ratio |
| Offset Distribution | ≥ 90% | Required offset coverage ratio |
| Azimuth Coverage | ≥ 75% | Minimum azimuth range requirement |
| Inline Offset Tolerance | ±15% | Acceptable inline offset variation |
| Crossline Offset Tolerance | ±15% | Acceptable crossline offset variation |

## Output Files

### Text Report (MESA_VALIDATION_REPORT.txt)
Contains:
- Validation summary with pass/fail status
- Detailed results for each validation test
- Error and warning messages
- Complete acquisition statistics

### HTML Report (MESA_VALIDATION_REPORT.html)
Interactive HTML document with:
- Color-coded validation status
- Tabular results display
- Summary and detailed sections
- Can be opened in any web browser

### JSON Files
- `mesa_statistics.json`: All calculated statistics
- `mesa_validation_results.json`: All validation test results

### Plot Files (PNG format)
- `acquisition_layout.png`: Receiver and source line layout
- `fold_distribution.png`: Nominal vs. average fold
- `offset_distribution.png`: Offset vector distribution
- `azimuth_coverage.png`: Receiver and source azimuth coverage
- `summary_statistics.png`: Key metrics dashboard

## Customization

### Modifying MESA Standards

Edit the thresholds in `MESAValidator` class:

```python
FOLD_UNIFORMITY_THRESHOLD = 0.85
OFFSET_DISTRIBUTION_RATIO = 0.90
AZIMUTH_COVERAGE_MIN = 0.75
```

### Adding Custom Validations

Extend `MESAValidator` with new validation methods:

```python
class CustomValidator(MESAValidator):
    def validate_custom_metric(self):
        # Your validation logic
        return {
            'passed': True,
            'result': 'value',
            'status': 'PASS'
        }
```

## Dependencies

- **numpy**: Numerical computations
- **matplotlib**: Data visualization and plotting

## License

MIT License - See LICENSE file for details

## References

- MESA (Model for Extended Seismic Acquisition) Standards
- SEG (Society of Exploration Geophysicists) Guidelines
- Industry best practices for seismic survey design

## Support

For issues, questions, or contributions, please submit through the project repository.
