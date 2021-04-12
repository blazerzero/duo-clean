FROM ubuntu:latest
RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev build-essential
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
RUN rm -rdf store && mkdir store
RUN rm -rdf study-utils && mkdir study-utils
ENTRYPOINT ["python3"]
CMD ["api.py"]
