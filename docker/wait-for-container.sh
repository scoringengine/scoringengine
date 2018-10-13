#!/bin/bash

set -e

host="$1"
shift
cmd=("$@")

while ping $host -c 1 > /dev/null 2>&1
do
  >&2 echo "$host container is still running...sleeping 15 seconds"
  sleep 15
done

>&2 echo "$host container is finished...starting container"
exec "${cmd[@]}"