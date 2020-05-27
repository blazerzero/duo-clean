#!/bin/bash

docker image build -t duoclean-back .
docker container run -p 5000:5000 -d duoclean-back
