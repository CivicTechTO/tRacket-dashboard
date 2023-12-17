# Urban Noise Meter

Environmental noise, especially in urban settings, is a [known public health concern](https://www.toronto.ca/wp-content/uploads/2017/11/8f98-tph-How-Loud-is-Too-Loud-Health-Impacts-Environmental-Noise.pdf):

> The growing body of evidence indicates that exposure to excessive environmental
noise does not only impact quality of life and cause hearing loss but also has other health impacts, such as cardiovascular effects, cognitive impacts, sleep disturbance and mental health effects.


Our application presents a real-time, interactive visual interface to a system of IoT sound meters deployed in the city of Toronto, Ontario, to better understand the ambient sound levels as well as extreme noise events local communities experience day to day.

The app is currently under active development but can be accessed [by following this link.](https://noise-dashboard-651f4e432386.herokuapp.com/) It might take a few seconds to load.

The project has been started and is maintained by volunteers from the [CivicTech Toronto](http://www.civictech.ca) community.

## Privacy

We followed Privacy by Design principles in setting up the data collection. 

1. The sound meter devices are deployed on private properties in residential areas at different locations in the city. We are **not publishing exact device locations**. 
2. The devices **do not record sound** only sound levels in A-weighted decibel levels (dBA)(https://en.wikipedia.org/wiki/Decibel). 
3. We calculate minimum and maximum sound levels at 5 minute intervals on the device and **only broadcast these aggregate values** (along wiht the device ID) to a database.

## Technical Notes

The application is implemented in Python, using [Plotly Dash](https://dash.plotly.com/), and packaged into a [Docker container](https://www.docker.com/) for ease of portability and deployement. The noise meters are sending data at regular intervals to a SQL database hosted on [WebCommand]().

Process overview:
1. The dashboard sends a web requests to Webcommand for the unique Device IDs available.
2. The user selects a device based on the IDs to be presented.
3. Multiple requests are sent to WebCommand to get the data required to construct each chart.
4. The data is cached on the client side.
5. After formatting and processing, we use `plotly` to generate the interactive visuals.

### Design Principles

 We aim to pull the minimum amount of data required to save network usage and improve performance even if it requires multiple requests. We expect much more data being stored in the future.

### Starting the Application Locally

**Prerequisites**: 

1. Docker Engine and `make` installed. 
2. Create a `config.env` file at the same level as the `makefile` and add a line `API_TOKEN=...` with your WebCommand token.

Run the following commands to start the application locally:

1. Build the production container: `make prod_build`
2. Run the production container: `make prod_container`
3. The Dash app is accessible on `http://localhost:8501` in your browser.
4. To stop the app, run `make docker_clean`.

### Developement Setup

For starting the development container:

1. Build the dev container: `make dev_build`
2. Run dev container: `make dev_container`
3. There are two ways to run the app:
    - Run `make debug` in the container to start the app in debug mode.
    - Run `make app` in the container to start the app in regular deploy mode.
4. Hitting `Control+C` will stop the app and typing `exit` will exit and shut down the container.
4. To remove the stopped container, run `make docker_clean`.

### Deploying the Application

**Prerequisites**: registered Heroku account and Heroku CLI authenticated; Heroku App set up on Heroku Dashboard with the app name appropriately matching in the `makefile`. 

The app is set up for deployement on [Heroku](https://www.heroku.com/).

1. Build the production container: `make prod_build`
2. Push the container to the Heroku Container Registry: `make heroku_push`
3. Release the app publicly: `make heroku_release`

### Testing

For unit testing, run `make test`.