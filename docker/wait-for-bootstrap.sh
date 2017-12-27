#!/bin/bash
# wait-for-bootstrap.sh

set -e

host="$1"
shift
cmd="$@"

while ping $host -c 1 > /dev/null 2>&1;
do
  >&2 echo "Bootstrap container is still running...sleeping"
  sleep 15
done

>&2 echo "Bootstrap container is finished...Starting container"
exec $cmd
