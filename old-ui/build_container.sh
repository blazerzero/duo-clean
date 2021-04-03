#!/bin/bash

docker image build -t duoclean-ui .
docker container run -p 5000:5000 -d duoclean-ui
