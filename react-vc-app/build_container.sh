#!/bin/bash

docker image build -t duoclean-front .
docker container run -p 3000:3000 -d duoclean-front
