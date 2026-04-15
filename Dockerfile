# Use the official Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files
# and to ensure output is logged directly to the terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the pyproject.toml first to leverage Docker caching for dependencies
COPY pyproject.toml ./

# Install the dependencies defined in pyproject.toml
RUN pip install --no-cache-dir .

# Copy the rest of the application code
COPY . .

# Initialize the fresh SQLite database inside the image
RUN python db_setup.py

# Expose the standard Streamlit port
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]