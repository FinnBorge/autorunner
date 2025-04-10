# AutoRunner

A tool for automating button clicks in applications based on image recognition.

## Installation

```bash
# Install with Poetry
poetry install
```

## Usage

```bash
# Run the auto clicker
poetry run autorunner

# Debug mode
poetry run autorunner --debug

# Test a single click
poetry run autorunner --test-click

# Check screen dimensions
poetry run autorunner --check-screen
```

## Configuration

Place your button images in the `images` directory:
- `start_button.png` - Image of the start button
- `end_button.png` - Image of the end button
- `end_button_alt.png` - Alternative image of the end button (optional)

## Requirements

- Python 3.12+
- PyAutoGUI
- Pillow
