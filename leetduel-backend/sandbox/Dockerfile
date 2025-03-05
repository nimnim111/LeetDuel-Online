# Use an official lightweight Python image
FROM python:3.11-slim

# Set a working directory inside the container
WORKDIR /sandbox

# Copy any necessary files (if applicable)
COPY script.py /sandbox/

# Ensure the container runs as a non-root user for security
RUN useradd -m runner && chown -R runner:runner /sandbox
USER runner

# Default command: Open a shell (can be overridden when running the container)
CMD ["/bin/sh"]