# Base Image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /opt/stage0/runner

# Copy the Pipfile and Pipfile.lock to the container
COPY Pipfile Pipfile.lock ./

# Install pipenv
RUN pip install pipenv

# Install dependencies using pipenv
RUN pipenv install --deploy --system

# Copy the source code into the container
COPY src/ /opt/stage0/runner/

# Install runbook wrapper script to /usr/local/bin
COPY src/runbook /usr/local/bin/runbook
RUN chmod +x /usr/local/bin/runbook

# Set Environment Variables
ENV PYTHONPATH=/opt/stage0/runner