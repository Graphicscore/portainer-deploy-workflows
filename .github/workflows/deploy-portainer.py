import os
import sys

import requests
import json

PORTAINER_URL = os.environ["PORTAINER_URL"]
PORTAINER_TOKEN = os.environ["PORTAINER_TOKEN"]
CONTAINER_NAME = os.environ["CONTAINER_NAME"]
IMAGE_TAG = "ghcr.io/graphicscore/discord-voice-message-transcriber:latest"


def pretty_print_response(response):
    print(json.dumps(response.json(), sort_keys=True, indent=5))


headers = {"X-API-Key": PORTAINER_TOKEN}


def do_request(method="GET", docker_request_path="/"):
    response = requests.request(method, "{0}/api/endpoints/1/docker{1}".format(PORTAINER_URL, docker_request_path),
                                headers=headers)
    return response


def do_request_post(docker_request_path="/", data=None):
    response = requests.request("POST", "{0}/api/endpoints/1/docker{1}".format(PORTAINER_URL, docker_request_path),
                                headers=headers, json=data)
    return response


def inspect_container(container_name):
    return do_request(docker_request_path="/containers/{id}/json".format(id=container_name))


def create_image():
    s = requests.Session()
    url = "{0}/api/endpoints/1/docker/images/create?fromImage={1}".format(PORTAINER_URL, IMAGE_TAG)
    with s.post(url, headers=headers, stream=True) as resp:
        status = None
        id = None
        for line in resp.iter_lines():
            if line:
                print(line)

    s.close()


def print_httpcheck(response, code):
    if response.status_code == code:
        print("success")
    else:
        print("error")


if len(sys.argv) <= 2:
    print("no create config specified")
    sys.exit(1)

create_config = None

with open(sys.argv[1]) as fd:
    create_config = json.load(fd)

if len(sys.argv) > 2:
    for i in range(2, len(sys.argv)):
        create_config["Env"].append(sys.argv[i])

current_container_status = inspect_container(container_name=CONTAINER_NAME)

old_container_id = None
if current_container_status.status_code == 404:
    # container does not exist we can deploy right away
    print("container does not exists, please create a template container manually")
elif current_container_status.status_code == 200:
    # container already exists, we have to replace the currently running one
    print("container already exists ... disecting config")
    old_container_id = current_container_status.json()["Id"]

print("pulling image ...")
create_image()

if old_container_id is not None:
    print("stopping old container")
    print_httpcheck(do_request_post(docker_request_path="/containers/{0}/stop".format(old_container_id)), 204)
    print_httpcheck(do_request_post(docker_request_path="/containers/{0}/wait".format(old_container_id)), 200)
    print("rename old docker container")
    print_httpcheck(do_request_post(
        docker_request_path="/containers/{0}/rename?name={1}".format(old_container_id, CONTAINER_NAME + "-old")), 204)

print("get image meta data...")
image_status = do_request(docker_request_path="/images/{0}/json".format(IMAGE_TAG))
create_config["Labels"] = image_status.json()["Config"]["Labels"]

print("setting new image for container")
create_config["Image"] = IMAGE_TAG

create_status = do_request_post(docker_request_path="/containers/create?name={0}".format(CONTAINER_NAME),
                                      data=create_config).json()
print(create_status)
new_container_id = create_status["Id"]

print("starting container ...")
print_httpcheck(do_request_post(docker_request_path="/containers/{0}/start".format(new_container_id)), 204)

print("delete old container")
print_httpcheck(do_request(method="DELETE", docker_request_path="/containers/{0}".format(old_container_id)), 204)


#2bd1362615db89fcf8fe787fc06cfda480ac0f17fbb55066b734812c30dd89a2


#new_config = old_config["Config"]
#new_config["HostConfig"] = old_config["HostConfig"]
#new_config["Image"] = CONTAINER_IMAGE
#new_config["MacAddress"] = old_config["NetworkSettings"]["MacAddress"]
#new_config["HostConfig"] = old_config["HostConfig"]
