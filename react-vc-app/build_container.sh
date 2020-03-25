#!/bin/bash

docker build -t duoclean .
docker run -it -d duoclean -p 8000:3000 --name duoclean
