# Nicotine++

<img src="pynicotine/gtkgui/icons/hicolor/scalable/apps/org.nicotine_plus.Nicotinepp.svg" align="right">

Nicotine++ is a vitaminized version of the popular [Soulseek](https://www.slsknet.org/) client [Nicotine+](https://nicotine-plus.org/).

Its main purpose is to run headlessly in a docker container and to expose an API so that any client is able to search and download your favorite files using the Soulseek peer-to-peer network.

## Prerequisites

- Docker v20 or higher.
- docker-compose v2.
  
  This is normally installed by default in Windows but if you are using a Raspberry Pi it might not be installed. If that's the case, [this](https://medium.com/@vinothsubramanian/how-to-install-docker-compose-in-raspberry-pi-4a11e6314bbb) may help you.

## Install

The installation steps are:

1. Checkout the repository in your machine.
2. Create a file called the file `npp_credentials.txt` and write the credentials you want to use in order to be able to connect to the network. In line 1 type your user and in line 2 type your password. You can use just some random credentials since you do not need to register or anything like that. Taking this into account, the file should look like this:
   ```
   chair
   table
   ```
    The user will be `chair` and the password will be `table`. Once done, you can save and close the file.
3. The next step is optional. If you want to define your own folder structure where the files are downloaded you have to edit the `docker-compose.yaml` file. You only have to change the path that is before the colon `:`.
    ```
    volumes:
      - ./nicotine_data/transfers/downloads:/data/nicotine/downloads
      - ./nicotine_data/transfers/incomplete:/data/nicotine/incomplete
      - ./nicotine_data/transfers/received:/data/nicotine/received
      - ./nicotine_data/config:/config/nicotine
    
    ```
4. Open a command prompt, navigate to the repository root folder and run the following command: ```docker compose up -d --build```.

And that's it! Nicotine++ should be now running on your machine. 

*If you want, you can now delete the file `credentials.txt` that you created previously.*

## API

```
Documentation under construction
```

## Nicotine+
In case you want further information about Nicotine+ and its source code, please check the original repository [here](https://github.com/nicotine-plus/nicotine-plus).
