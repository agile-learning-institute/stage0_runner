FROM hello-world:latest

ARG REPO
LABEL org.opencontainers.image.source="https://github.com/agile-crafts-people/${REPO}"

