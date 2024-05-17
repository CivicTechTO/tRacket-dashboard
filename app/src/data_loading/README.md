# [Dev Notes] Data Loading

The `data_loading` module is responsible for pulling raw data from a backend database (DB), currently hosted on WebCommand - see `config.ini` for the URL.

- `noise_api.py`: defines the `NoiseAPI` class for sending parametrized requests to the backend DB.
- `models.py`: data models to define the expected API reply and data validation using the `pydantic` library.
- `main.py`: collects high level functions for creating the API connections and issueing data requests.
