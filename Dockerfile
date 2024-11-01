# Use the official FastAPI image
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# Set the working directory
WORKDIR /app

# Copy the pyproject.toml and poetry.lock files and install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-root --no-dev

# Copy the application code
COPY ./app /app

# Expose the port
EXPOSE 80

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]