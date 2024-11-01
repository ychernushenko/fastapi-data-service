# Use the official Python FastAPI image
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# Set the working directory to /app
WORKDIR /app

# Copy the dependency files
COPY pyproject.toml poetry.lock ./

# Install Poetry and dependencies
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

# Copy the application code
COPY ./app /app/app

# Expose the correct port
EXPOSE 8080

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
