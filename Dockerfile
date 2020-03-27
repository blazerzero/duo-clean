FROM ubuntu:latest
RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev build-essential
COPY . /app
WORKDIR /app
RUN pip3 install -r vc-server/requirements.txt && \
    mkdir vc-server/store
ENTRYPOINT ["python3"]
CMD ["vc-server/api.py"]
