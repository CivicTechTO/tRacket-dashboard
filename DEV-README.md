# [Dev Notes] High-level Technical Notes

The application is implemented in Python, using [Plotly Dash](https://dash.plotly.com/), and packaged into a [Docker container](https://www.docker.com/) for ease of portability and deployement. The noise meters are sending data at regular intervals to a database hosted on [WebCommand](https://live.noisemeter.webcomand.com/open-data/) which exposes a REST API that is used to pull data for the maps and dashboard.

Process overview:
1. The app sends a API requests to Webcommand for the unique Device IDs and locations to create the system map.
2. The user selects a location and clicks on the map, a new page opens with the location dashboard.
3. Multiple requests are sent to WebCommand to get the data required to construct each chart.
4. The data is cached on the client side.
5. After formatting and processing, we use `plotly` to generate the interactive visuals.

## Design Principles

 We aim to pull the minimum amount of data required to save network usage and improve performance even if it requires multiple requests. We expect much more data being stored in the future.

## Starting the Application Locally

**Prerequisites**: 

1. Docker Engine and `make` installed. 
2. Create a `config.env` file at the same level as the `makefile` and add a line `API_TOKEN=...` with your WebCommand token. The public token can be accessed [here](https://live.noisemeter.webcomand.com/open-data/) with some more info about the data base. 

Run the following commands to start the application locally:

1. Build the production container: `make prod_build`
2. Run the production container: `make prod_container`
3. The Dash app is accessible on `http://localhost:8501` in your browser.
4. To stop the app, run `make docker_clean`.

## Developement Setup

For starting the development container:

1. Build the dev container: `make dev_build`
2. Run dev container: `make dev_container`
3. There are two ways to run the app:
    - Run `make debug` in the container to start the app in debug mode.
    - Run `make app` in the container to start the app in regular deploy mode.
4. Hitting `Control+C` will stop the app and typing `exit` will exit and shut down the container.
4. To remove the stopped container, run `make docker_clean`.

## Deploying the Application

Currently, we have GitHub Actions setup so that each push to `main` triggers a deployment.

### Manual Deployment Process

**Prerequisites**: registered Heroku account and Heroku CLI authenticated; Heroku App set up on Heroku Dashboard with the app name appropriately matching in the `makefile`. 

The app is set up for deployement on [Heroku](https://www.heroku.com/).

1. Build the production container: `make prod_build`
2. Push the container to the Heroku Container Registry: `make heroku_push`
3. Release the app publicly: `make heroku_release`

## Testing

For unit testing, run `make test`.
