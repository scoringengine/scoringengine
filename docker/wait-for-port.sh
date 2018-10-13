#!/bin/bash

set -e

host="$1"
port="$2"
shift
shift
cmd="$@"

until (echo > /dev/tcp/$host/$port) >/dev/null 2>&1
do
  >&2 echo "$host:$port is still not ready yet...sleeping 15 seconds"
  sleep 15
done

>&2 echo "$host:$port is ready...starting container"
exec $cmd
