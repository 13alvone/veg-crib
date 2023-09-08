#!/bin/sh

sudo docker build -t veg-crib .
sudo docker run -p 80:80 -d veg-crib
