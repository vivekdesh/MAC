## docker server start command

docker run -it --rm \
  -e LOG_ALL_EVENTS=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /Users/vivek/icici_direct:/workspace/project/code \
  -v /Users/vivek/icici_direct/Google:/workspace/project/logs \
  -v ~/.openhands:/.openhands \
  -p 3000:3000 \
  --add-host host.docker.internal:host-gateway \
  --name openhands-app \
  docker.openhands.dev/openhands/openhands:latest

