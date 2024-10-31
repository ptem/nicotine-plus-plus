# Nicotine++

<img src="pynicotine/gtkgui/icons/hicolor/scalable/apps/org.nicotine_plus.Nicotinepp.svg" align="right">

Nicotine++ is a vitaminized version of the popular [Soulseek](https://www.slsknet.org/) client [Nicotine+](https://nicotine-plus.org/).

Its main purpose is to run headlessly in a docker container and to expose an API so that any client is able to search and download your favorite files using the Soulseek peer-to-peer network.

## Prerequisites

- Docker v20 or higher.
- Docker compose v2: this is normally installed by default in Windows when you perform the Docker installation but if you are using a Raspberry Pi it might not be installed. If that's the case, [this](https://medium.com/@vinothsubramanian/how-to-install-docker-compose-in-raspberry-pi-4a11e6314bbb) may help you.

## Install

The installation steps are:

1. Checkout the repository in your machine.
2. The next step is optional. If you want to define your own folder structure where the files are downloaded you have to edit the `docker-compose.yaml` file. You only have to change the path that is before the colon `:`.
    ```
    volumes:
      - ./npp_data/transfers/downloads:/data/nicotine/downloads
      - ./npp_data/transfers/incomplete:/data/nicotine/incomplete
      - ./npp_data/transfers/received:/data/nicotine/received
      - ./npp_data/config:/config/nicotine
    
    ```
3. Open a command prompt, navigate to the repository root folder and run the following command: ```docker compose up -d --build```.

And that's it! Nicotine++ should be now running on your machine. 

When you create the docker container for the first time, by default, Nicotine++ will generate random user and password so that you can connect to the network. In case you want to use your own credentials you can stop the container and change them in the config file. Once you save the changes on the configuration file, the container will read and use the new credentials.

## API

```
Documentation under construction
```

## Nicotine+
In case you want further information about Nicotine+ and its source code, please check the original repository [here](https://github.com/nicotine-plus/nicotine-plus).
