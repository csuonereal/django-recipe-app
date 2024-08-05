FROM python:3.9-alpine3.13
LABEL maintainer="londonappdeveloper.com"

# Set an environment variable to ensure Python output is sent straight to the terminal (without buffering).
# This means that all print statements and log messages will be immediately visible in the container logs,
# which is useful for debugging and monitoring because it provides real-time feedback.
ENV PYTHONUNBUFFERED 1


COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app

# Set the working directory to /app so all subsequent commands are run from this directory
WORKDIR /app

# Expose port 8000 on the container to allow access to the application
EXPOSE 8000

# Default value for the DEV build argument, we are overriding this value in the docker-compose.yml file
ARG DEV=false

# Run multiple commands to set up the Python environment and install dependencies:
# 1. Create a virtual environment in the /py directory
# 2. Upgrade pip to the latest version
# 3. Install the required Python packages from requirements.txt
# 4. Remove the /tmp directory to clean up unnecessary files
# 5. Add a new user named 'django-user' without password and home directory for running the application
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user

# Set the PATH environment variable to include the virtual environment's bin directory
ENV PATH="/py/bin:$PATH"

# Switch to the 'django-user' user to run the application with non-root privileges
USER django-user
