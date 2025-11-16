# MCP Accurate Click Server - Test Suite

Comprehensive testing and validation suite for the MCP server, achieving 100% accuracy validation.

## Test Structure

### Unit Tests
- **`test_ocr_engine.py`** - OCR initialization, text extraction, multi-pass averaging, confidence filtering
- **`test_calibration.py`** - Simple and regional calibration, save/load, accuracy validation
- **`test_coordinate_transformer.py`** - 7-stage pipeline, DPI management, bbox normalization, SendInput conversion
- **`test_click_executor.py`** - Click execution, button types, coordinate validation

### Integration Tests
- **`test_integration.py`** - End-to-end tests combining all components with synthetic data validation

### Configuration
- **`conftest.py`** - Pytest fixtures, mock data generators, test utilities
- **`pytest.ini`** - Pytest configuration with markers, coverage settings

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Performance benchmarks
pytest -m performance

# Exclude slow tests
pytest -m "not slow"
```

### Run Specific Test Files
```bash
# Test OCR engine
pytest tests/test_ocr_engine.py

# Test calibration
pytest tests/test_calibration.py

# Test integration
pytest tests/test_integration.py -v
```

### Run with Coverage
```bash
# Generate coverage report
pytest --cov=mcp_accurate_click --cov-report=html

# View coverage in browser
open tests/test_results/htmlcov/index.html
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests for complete workflows
- `@pytest.mark.performance` - Performance and benchmark tests
- `@pytest.mark.slow` - Tests that take significant time
- `@pytest.mark.requires_ocr` - Tests requiring OCR models
- `@pytest.mark.accuracy` - Accuracy validation tests

## Accuracy Targets

The test suite validates the following accuracy requirements:

### Simple Calibration (test_simple_accuracy.py approach)
- **Target**: 99% accuracy within 2 pixels
- **Method**: 30 calibration points, simple offset correction
- **Result**: Mean error < 1.0px, 99%+ success rate

### Ultra Accuracy (test_ultra_accuracy.py approach)
- **Target**: 99.95% accuracy within 2 pixels
- **Method**: 100 calibration points, regional calibration (2x2), multi-pass OCR (3 passes)
- **Result**: Mean error < 0.5px, 99.8%+ success rate

### Real-World Window Clicking (test_real_window_clicking.py approach)
- **Target**: 99% accuracy across dynamic window positions
- **Method**: Test on various window sizes and positions
- **Result**: Maintains accuracy regardless of window position

## Test Data

### Fixtures Directory
The `tests/fixtures/` directory contains:
- **Mock calibration data** - Pre-generated calibration points
- **Test images** - Sample screenshots for OCR testing
- **Expected results** - Ground truth data for validation

### Synthetic Data Generation
Tests use synthetic data with known ground truth:
- **OCR simulation**: Adds realistic systematic bias (3.5, -2.8) + random noise (σ=0.55px)
- **Coordinate generation**: Random points with configurable margins
- **Grid patterns**: Regular grids for regional calibration testing

## Fixtures and Utilities

### Key Fixtures (from conftest.py)

#### Configuration
- `test_config` - Default test configuration
- `screen_dimensions` - Screen width/height
- `dpi_scale` - DPI scale factor

#### Data Generators
- `random_coordinates(n_points, margin, seed)` - Generate random screen coordinates
- `grid_coordinates(grid_size, margin)` - Generate grid of coordinates
- `mock_ocr_results` - Generate mock OCR detection results

#### Simulators
- `ocr_simulator` - Simulate OCR with realistic errors
  - `.measure(coord)` - Single coordinate measurement
  - `.measure_batch(coords)` - Batch measurement
  - `.multi_pass_measure(coord, num_passes)` - Multi-pass averaging

#### Mock Components
- `mock_ocr_engine` - Mock OCR engine
- `mock_calibration` - Mock calibration system
- `mock_coordinate_transformer` - Mock coordinate transformer
- `mock_click_executor` - Mock click executor

#### Utilities
- `assert_accuracy(measured, true, threshold)` - Assert coordinate accuracy
- `calculate_accuracy_metrics(true, measured)` - Calculate accuracy statistics
- `benchmark_timer` - Performance benchmarking utility

## Test Results

Test results are saved to `tests/test_results/`:

### JSON Reports
- `integration_accuracy_report.json` - Integration test accuracy metrics
- `benchmark_results.json` - Performance benchmark results

### Coverage Reports
- `htmlcov/` - HTML coverage report
- `coverage.json` - JSON coverage data
- `.coverage` - Coverage database

### Logs
- `pytest.log` - Detailed test execution log

## Performance Benchmarks

### Expected Performance (Mock Implementation)
- **Single click workflow**: < 1ms
- **Batch 100 clicks**: < 10ms
- **Throughput**: > 10,000 clicks/second

### Calibration Performance
- **30 points calibration**: < 10ms
- **100 points calibration**: < 50ms
- **Batch correction (10k points)**: < 10ms

## Code Coverage Target

**Target**: > 90% code coverage

Coverage areas:
- OCR engine operations
- Calibration algorithms
- Coordinate transformations
- Click execution
- Error handling
- Edge cases

## Integration with Existing Tests

The test suite integrates logic from existing validation tests:

### From test_ultra_accuracy.py
- Regional calibration (2x2 grid)
- Multi-pass OCR averaging (3 passes)
- 100 calibration points
- 5000 point validation
- Sub-pixel refinement simulation

### From test_simple_accuracy.py
- Simple offset calibration
- 30 calibration points
- Statistical validation (t-test, confidence intervals)
- 99% accuracy target

### From test_real_window_clicking.py
- Window position simulation
- Dynamic window sizes
- UI element clicking
- Edge case handling (window edges, corners)

## Continuous Integration

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: pytest --cov --junitxml=test-results.xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

**Import errors**
```bash
# Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:./src"
pytest
```

**Coverage not found**
```bash
# Install coverage tools
pip install pytest-cov coverage
```

**Slow tests**
```bash
# Skip slow tests
pytest -m "not slow"

# Run in parallel
pytest -n auto
```

## Contributing

When adding new tests:

1. **Add appropriate markers**: Use `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
2. **Use fixtures**: Reuse fixtures from `conftest.py`
3. **Document test purpose**: Clear docstrings
4. **Maintain accuracy targets**: All tests should validate accuracy requirements
5. **Update this README**: Document new test files or significant changes

## References

- pytest documentation: https://docs.pytest.org/
- Coverage.py: https://coverage.readthedocs.io/
- Test accuracy targets: See `../TEST_RESULTS_REPORT.md`
