import json
from src.fastapi_app.main import app

# Save directly to the Sphinx _static folder
with open("docs/source/_static/swagger-ui/openapi.json", "w") as f:
    json.dump(app.openapi(), f)
