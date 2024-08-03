# tRacket: Community-Driven Urban Noise Monitoring

Environmental noise, especially in urban settings, is a [known public health concern](https://www.toronto.ca/wp-content/uploads/2017/11/8f98-tph-How-Loud-is-Too-Loud-Health-Impacts-Environmental-Noise.pdf):

> The growing body of evidence indicates that exposure to excessive environmental
noise does not only impact quality of life and cause hearing loss but also has other health impacts, such as cardiovascular effects, cognitive impacts, sleep disturbance and mental health effects.


Our application presents a real-time, interactive visual interface to a system of IoT sound meters deployed in the city of Toronto, Ontario, to better understand the ambient sound levels as well as extreme noise events local communities experience day to day.

The app is currently under active development but can be accessed [by following this link](https://dashboard.tracket.info/locations) which gives you the system level map view. Individual devices can be reached by appending `/<location-id>` to the previous URL [like this](https://dashboard.tracket.info/locations/572234). The app might take a few seconds to load.

The project has been started and is maintained by volunteers from the [CivicTech Toronto](http://www.civictech.ca) community.

## Privacy

We followed Privacy by Design principles in setting up the data collection. 

1. The sound meter devices are deployed on private properties in residential areas at different locations in the city. We are **not publishing exact device locations**. 
2. The devices **do not record sound** only sound levels in A-weighted decibel levels (dBA)(https://en.wikipedia.org/wiki/Decibel). 
3. We calculate minimum and maximum sound levels at 5 minute intervals on the device and **only broadcast these aggregate values** (along wiht the device ID) to a database.

## For Developers

If you'd like to contribute or dig deeper into the technical details, please see our [DEV-README](DEV-README.md) and check out the open Issues on GitHub.
