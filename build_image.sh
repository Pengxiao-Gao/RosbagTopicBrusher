#!/bin/bash

branch=`git branch | grep \* | cut -d ' ' -f2 | sed 's/\//-/g'`
commit_id=`git rev-parse --short HEAD`
date=`date +%Y%m%d%H%M%S`
docker_tag=${branch}-${commit_id}-${date}

docker build . -f Dockerfile.base -t memory_cruise_brush:base
docker build . -f Dockerfile -t memory_cruise_brush:${docker_tag}
docker tag memory_cruise_brush:${docker_tag} artifactory.XXXXXXX/memory_cruise_brush/memory_cruise_brush:${docker_tag}
docker push artifactory.XXXXXXX/memory_cruise_brush/memory_cruise_brush:${docker_tag}
echo "artifactory.XXXXXXX/memory_cruise_brush/memory_cruise_brush:${docker_tag}"