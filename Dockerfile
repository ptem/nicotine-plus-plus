FROM python:3.12-slim
ENV TZ="Europe/Madrid"

WORKDIR /usr/nicotine/app

ENV XDG_CONFIG_HOME /usr/nicotine/config
ENV XDG_DATA_HOME /usr/nicotine/data

#Copy the python code
COPY pynicotine /usr/nicotine/app/pynicotine
COPY nicotine /usr/nicotine/app/nicotine
COPY requirements.txt /usr/nicotine/app/requirements.txt

RUN pip3 install -r requirements.txt

#Entrypoint
ENTRYPOINT [ "python3", "./nicotine", "--headless"]