# MTL Finder

Welcome to MTL Finder, an intelligent travel assistant for Montreal!

MTL Finder is a chatbot application that combines Mistral AI, OpenTripPlanner, Photon geocoding, and real-time STM data to provide users with personalized travel recommendations in Montreal.

## Live Version

You can access a live version of MTL Finder here: [https://mtl-finder.alexandredewilde.com/](https://mtl-finder.alexandredewilde.com/)

> **Warning**: This live version is hosted on a personal machine and may not always be available.

## Table of Contents

-   **[Installation Guide](docs/INSTALL.md)**
    -   [Prerequisites](docs/INSTALL.md#prerequisites)
    -   [API Keys](docs/INSTALL.md#api-keys)
    -   [Scripted Installation](docs/INSTALL.md#option-1-scripted-installation-recommended)
    -   [Manual Installation](docs/INSTALL.md#option-2-manual-installation)
-   **[Running the Application](docs/RUN.md)**
    -   [Starting the Application](docs/RUN.md#starting-the-application)
    -   [Accessing the Application](docs/RUN.md#accessing-the-application)
    -   [Configuration](docs/RUN.md#configuration)
    -   [OpenTripPlanner Management](docs/RUN.md#opentripplanner-management)
-   **[Architecture Overview](docs/ARCHITECTURE.md)**
    -   [Project Overview](docs/ARCHITECTURE.md#project-overview)
    -   [Project Structure](docs/ARCHITECTURE.md#project-structure)
    -   [Tools Architecture](docs/ARCHITECTURE.md#tools-architecture)
    -   [System Prompt Strategy](docs/ARCHITECTURE.md#system-prompt-strategy)
    -   [Dependencies](docs/ARCHITECTURE.md#dependencies)

## Key Features

-   ✅ **Intelligent Geocoding**: Photon (OSM-based) converts location names to coordinates
-   ✅ **Multi-Modal Routing**: Metro, bus, bike (BIXI), walking, and combinations
-   ✅ **Real-Time Data**: Live STM transit updates and delays
-   ✅ **Weather Integration**: Weather-aware route recommendations
-   ✅ **Natural Language**: Conversational interface powered by Mistral AI

## Future Enhancements

-   [ ] Rideshare integration (Uber, Lyft)
-   [ ] Clothing/shoe recommendations based on weather conditions
