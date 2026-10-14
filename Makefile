REGISTRY ?= quay.io/crc-org
IMAGE ?= concurrency
VERSION ?= v0.1

IMG = $(REGISTRY)/$(IMAGE):$(VERSION)

build:
	podman build -t $(IMG) .

push: build
	podman push $(IMG)
