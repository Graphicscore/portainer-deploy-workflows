import os
import sys

import requests
import json

PORTAINER_URL = os.environ["PORTAINER_URL"]
PORTAINER_TOKEN = os.environ["PORTAINER_TOKEN"]
CONTAINER_NAME = os.environ["CONTAINER_NAME"]


def pretty_print_response(response):
    print(json.dumps(response.json(), sort_keys=True, indent=5))


def do_request(docker_request_path):
    headers = {"X-API-Key": PORTAINER_TOKEN}
    response = requests.get("{0}/api/endpoints/1/docker{1}".format(PORTAINER_URL, docker_request_path), headers=headers)
    return response


def inspect_container(container_name):
    return do_request("/containers/{id}/json".format(id=container_name))


current_container_status = inspect_container(container_name=CONTAINER_NAME)

if current_container_status.status_code == 404:
    # container does not exist we can deploy right away
    print("container does not exists, please create a template container manually")
    sys.exit(1)
elif current_container_status.status_code == 200:
    # container already exists, we have to replace the currently running one

pretty_print_response(current_container_status)