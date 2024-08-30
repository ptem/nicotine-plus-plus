FROM python:3.12-slim
ENV TZ="Europe/Madrid"

WORKDIR /usr/nicotine/app

ENV XDG_CONFIG_HOME /config
ENV XDG_DATA_HOME /data

#Copy the python code
COPY pynicotine /usr/nicotine/app/pynicotine
COPY nicotine /usr/nicotine/app/nicotine
COPY requirements.txt /usr/nicotine/app/requirements.txt

RUN pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

#Entrypoint
ENTRYPOINT [ "python3", "./nicotine", "--headless"]