FROM python:3.12-slim
ENV TZ="America/New_York"

WORKDIR /usr/nicotine/app

ENV XDG_CONFIG_HOME /config
ENV XDG_DATA_HOME /data

# Timezone
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

# Install curl
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the python code
COPY pynicotine /usr/nicotine/app/pynicotine
COPY nicotine /usr/nicotine/app/nicotine
COPY requirements.txt /usr/nicotine/app/requirements.txt

# Install Python dependencies
RUN pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Entrypoint
ENTRYPOINT ["python3", "./nicotine", "--headless"]