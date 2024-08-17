FROM python:3.9-alpine3.13
LABEL maintainer="londonappdeveloper.com"

# 1. Set an environment variable to ensure Python output is sent straight to the terminal (without buffering).
#    This means that all print statements and log messages will be immediately visible in the container logs,
#    which is useful for debugging and monitoring because it provides real-time feedback.
ENV PYTHONUNBUFFERED 1

# 2. Copy the requirements files to the /tmp directory
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app

# 3. Set the working directory to /app so all subsequent commands are run from this directory
WORKDIR /app

# 4. Expose port 8000 on the container to allow access to the application
EXPOSE 8000

# 5. Default value for the DEV build argument, we are overriding this value in the docker-compose.yml file
ARG DEV=false

# 6. Run multiple commands to set up the Python environment and install dependencies:
#    a. Create a virtual environment in the /py directory
#    b. Upgrade pip to the latest version
#    c. Install postgresql-client using apk
#    d. Install build dependencies for PostgreSQL and Python packages
#    e. Install the required Python packages from requirements.txt
#    f. If DEV is true, install the development requirements from requirements.dev.txt
#    g. Remove the /tmp directory to clean up unnecessary files
#    h. Remove build dependencies to reduce image size
#    i. Add a new user named 'django-user' without password and home directory for running the application
# jpeg-dev is required for Pillow to work with JPEG files
# zlib and zlib-dev are required for Pillow to work with PNG files
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --no-cache postgresql-client jpeg-dev && \
    apk add --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev zlib zlib-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user && \
        # 1. Create directories for storing media and static files within the volume '/vol/web'.
        #    This ensures that these directories exist to hold user-uploaded media and static files served by Django.
        mkdir -p /vol/web/media && \
        mkdir -p /vol/web/static && \
        # 2. Change ownership of the '/vol' directory (and all its subdirectories) to the user 'django-user' and group 'django-user'.
        #    This is important for permissions, ensuring that the Django application running under 'django-user' can access these directories to read and write files.
        chown -R django-user:django-user /vol && \
        # 3. Change permissions of the '/vol' directory recursively to 755.
        #    This sets the permission to read, write, and execute for the owner, and read and execute for group and others.
        #    It ensures that the application has the necessary permissions to operate correctly with the volumes while restricting unnecessary write access.
        chmod -R 755 /vol





# 7. Set the PATH environment variable to include the virtual environment's bin directory
ENV PATH="/py/bin:$PATH"

# 8. Switch to the 'django-user' user to run the application with non-root privileges
USER django-user
