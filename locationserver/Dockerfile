##########################
## Create runtime image ##
##########################
FROM python:3-slim AS RUNTIME_IMAGE

# Set our working directory to /app
WORKDIR /app

# Install the one requirement
RUN pip install websockets

# Copy the source file
COPY location_server.py /app/

# Run the app
CMD ["python", "./location_server.py"]
