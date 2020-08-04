#!/bin/bash

docker image build -t duoclean-api .
docker container run -p 5000:5000 -d duoclean-api
