FROM ubuntu:latest
RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev build-essential
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
RUN rm -rdf store && mkdir store
ENTRYPOINT ["python3"]
CMD ["api.py"]
