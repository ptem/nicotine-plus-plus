# Nicotine++

<img src="pynicotine/gtkgui/icons/hicolor/scalable/apps/org.nicotine_plus.Nicotine.svg" align="right" width="128" height="128" style="margin: 0 10px">

Nicotine++ is a vitaminized version of the popular [Soulseek](https://www.slsknet.org/) client [Nicotine+](https://nicotine-plus.org/).

Its main purpose is to run headlessly in a docker container and to expose an API so that any client is able to search and download your favorite files using the Soulseek peer-to-peer network.

## Install

The installation steps are:

1. Checkout the repository in your machine.
2. Create a file called the file `npp_credentials.txt` and write the credentials you want to use in order to be able to connect to the network. In line 1 type your user and in line 2 type your password. You can use just some random credentials since you do not need to register or anything like that. Taking this into account, the file should look like this:
   ```
   chair
   table
   ```
    The user will be `chair` and the password will be `table`. Once done, you can save and close the file
3. The next step is optional. If you want to define your own folder structure where the files are downloaded you have to edit the `docker-compose.yaml` file. You only have to change the path that is before the colon `:`.
    ```
    volumes:
      - ./nicotine_data/transfers/downloads:/data/nicotine/downloads
      - ./nicotine_data/transfers/incomplete:/data/nicotine/incomplete
      - ./nicotine_data/transfers/received:/data/nicotine/received
      - ./nicotine_data/config:/config/nicotine
    
    ```
4. Run the following command to build the docker and create the container: ```docker compose up -d --build```

And that's it! Nicotine++ should now be running on your machine.

## API

```
Under construction
```

## Nicotine+
In case you want further information about Nicotine+ and its source code, please check the original repository [here](https://github.com/nicotine-plus/nicotine-plus).
