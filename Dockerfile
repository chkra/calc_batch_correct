# you can use any base image you like
# for example python:3.4 or the smaller version python:3.6.1-alpine
FROM python:3.6
#RUN apk add --update --no-cache git
RUN apt-get install git
# These values provide you the data you need. See the readme.md file for details
VOLUME /fastgenomics/data/
VOLUME /fastgenomics/output/
VOLUME /fastgenomics/summary/
VOLUME /fastgenomics/config/

# Install fastgenomics python bindings
RUN pip install git+https://github.com/fastgenomics/fastgenomics-py.git@v0.3.0

# Install any dependencies your app has
COPY ./requirements.txt /requirements/
RUN pip install -r /requirements/requirements.txt

# Copy your app manifest to /app - must be located here for usage of default parameters
COPY manifest.json /app/

# Copy your code into the app
COPY hello_genomics /app/hello_genomics/
COPY templates /app/templates/

# Run the app when the container starts.
WORKDIR /app/
ENV PYTHONPATH /app/
CMD ["python", "/app/hello_genomics/main.py"]
