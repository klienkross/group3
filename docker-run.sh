#!/bin/bash
docker run -it --rm \
  --name npm-vuln-box \
  -v $(pwd):/workspace \
  -w /workspace \
  node:18-bullseye bash -c "npm install && node poc.js"