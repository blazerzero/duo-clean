#!/bin/bash

docker image build -t duoclean-front .
docker container run -p 8000:8000 -d duoclean-front
