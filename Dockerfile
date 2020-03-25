FROM ubuntu:latest
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential
COPY . /app
WORKDIR /app
RUN pip3 install -r vc-server/pip_reqs.txt
ENTRYPOINT ["python3"]
CMD ["vc-server/api.py"]
