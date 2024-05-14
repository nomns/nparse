##########################
## Create runtime image ##
##########################
FROM python:3-slim AS RUNTIME_IMAGE

# Set our working directory to /app
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/

# Install the one requirement
RUN pip install -r requirements.txt

# Copy the source file
COPY location_server.py /app/

# Run the app
CMD ["python", "./location_server.py"]
