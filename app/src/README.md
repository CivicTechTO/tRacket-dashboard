# [DEV NOTES] App Source Code

Most dashboard back-and front-end functionality is contained here.

- `data_loading/`: data models and data loading functionality from the API.
- `app_components.py`: functions and classes for creating the individual front-end components and callbacks for interactive functionality.
- `config.ini`: configuration for plots and dashboard styling, including colors.
- `assets/styles.css`: CSS styling.
- `plotting.py`: functionalities for creating individual `plotly` charts.
- `pages/`: the individual pages defined.
    - `pages/locations.py`: the main page of the dashboard that defines the system map and location dashboards.
    - `pages/admin.py`: a bare-bones admin page for the dashboard.
    - `pages/not_found_404.py`: basic 404 page.
- `utils.py`: general utility functions and classes.