# Use an official Python runtime as a parent image
FROM us-docker.pkg.dev/colab-images/public/runtime

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app


# Run the python script
ENTRYPOINT ["sh", "entry.sh"]
