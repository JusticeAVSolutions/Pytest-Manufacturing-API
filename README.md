# Pytest-Manufacturing-API

A pytest plugin to integrate with a Manufacturing Database API for serial numbering, MAC addressing, and logging test results.

## Description

Pytest-Manufacturing-API is a pytest plugin that allows you to interact with a Manufacturing Database API during your test runs. It provides fixtures and options to:

- Retrieve or assign serial numbers to units under test.
- Retrieve or assign MAC addresses to units under test.
- Log test results back to the Manufacturing Database.
- Integrate seamlessly with existing test workflows.

This plugin is particularly useful in manufacturing environments where each unit tested needs to be tracked, and test results need to be logged against specific units in a database.

## Features

- **Assign Serial Numbers**: Automatically get the next available serial number or use existing ones.
- **Assign MAC Addresses**: Automatically get the next available MAC address or use existing ones.
- **Log Test Results**: After test execution, results are uploaded to the Manufacturing API.
- **Customizable API URL**: Specify the Manufacturing API endpoint via command-line options.
- **Integration with Pytest Fixtures**: Provides fixtures for interacting with the Manufacturing API within your tests.

## Installation

You can install the plugin directly from GitHub using `pip`:

```bash
pip install git+https://github.com/justiceavsolutions/pytest-manufacturing-api.git
```

## Requirements

- Python 3.x
- `pytest`
- `requests`
- `pytest-json-report`

## Usage

### Command-Line Options

The plugin adds the following command-line options to pytest:

- `--manufacturing-api-url`: Specify the base URL of the Manufacturing API. Defaults to `http://192.168.114.187:8000/`.
- `--use-manufacturing-api`: Enable the plugin to interact with the Manufacturing API. If not set, the plugin will not be used.

### Fixtures

- `manufacturing_api_client`: Provides an API client for interacting with the Manufacturing API within your tests.
- `unit_id`: Tracks the `unit_id` throughout the test session for result logging.

### Running Tests with the Plugin

To use the plugin, include the `--use-manufacturing-api` flag and specify the API URL if different from the default:

```bash
pytest -s --use-manufacturing-api --manufacturing-api-url http://localhost:8000/
```

### Example Test

Here's an example of how to use the plugin within a test:

```python
import pytest

MIC_DEFAULT_SN = "0000000000000000"

def test_get_or_make_unit(request, record_property, manufacturing_api_client):
    product_name = "Boundary Mic"
    product_id = None
    unit_id = None
    serial_number_str = None

    # Determine product ID based on product name
    products = manufacturing_api_client.get_products(product_name)
    for product in products:
        if product["name"] == product_name:
            product_id = product["id"]
            break
    
    # Read the initial serial number from the device under test
    mic_initial_sn = "JP1369999998"  # Replace with actual SN read from device

    if mic_initial_sn == MIC_DEFAULT_SN:
        # Get the next available serial number from the API
        unit_id, serial_number_str = manufacturing_api_client.get_next_serial(product_id)
    else:
        # Check if the serial number exists in the database
        unit_id = manufacturing_api_client.get_unit_by_serial(mic_initial_sn)
        if unit_id is None:
            # Create a new unit with the existing serial number
            unit_id = manufacturing_api_client.create_unit(product_id, mic_initial_sn)
            serial_number_str = mic_initial_sn
        else:
            serial_number_str = mic_initial_sn

    # Store the unit ID for logging test results
    request.session.unit_id = unit_id

    # Record the serial number for reporting
    record_property("serial number", serial_number_str)

    # ... continue with other test steps ...
```

### Logging Test Results

After the test session finishes, the plugin will automatically:

1. Collect test results in JSON format.
2. Upload the test results to the Manufacturing API associated with the `unit_id`.

### Notes

- Ensure the Manufacturing API is accessible from the test environment.
- The plugin uses `pytest-json-report` to generate the test report in JSON format.

## Plugin Details

### Command-Line Options

- **`--manufacturing-api-url`**: Sets the base URL for the Manufacturing API. The default is `http://192.168.114.187:8000/`.
- **`--use-manufacturing-api`**: Enables the plugin. If not specified, the plugin will not interact with the Manufacturing API.

### Fixtures and API Client

#### `manufacturing_api_client`

An instance of `APIClient` is provided as a fixture. This client includes methods to interact with the Manufacturing API:

- `create_unit(product_id, serial_number_id=None, mac_address_id=None)`: Creates a new unit in the database.
- `get_products(name)`: Retrieves products from the database.
- `get_next_serial(product_id)`: Retrieves the next available serial number for a product.
- `get_unit_by_serial(serial_number)`: Retrieves a unit by its serial number.

#### `unit_id`

A fixture that stores the `unit_id` for the current test session, used for logging test results.

#### Example Usage of Fixtures

```python
def test_example(request, record_property, manufacturing_api_client):
    # Use the manufacturing_api_client to interact with the API
    products = manufacturing_api_client.get_products("Product Name")
    product_id = products[0]["id"]

    # Get or create a unit
    unit_id, serial_number = manufacturing_api_client.get_next_serial(product_id)

    # Store unit_id for result logging
    request.session.unit_id = unit_id

    # Record properties for reporting
    record_property("serial number", serial_number)

    # Proceed with test steps...
```

### Uploading Test Results

At the end of the test session, the plugin automatically handles:

1. Collecting test results into a JSON report.
2. Uploading the JSON report to the Manufacturing API endpoint `/units/{unit_id}/test_results/add_json`.

Ensure that the API endpoint expects the JSON format provided by `pytest-json-report`.
