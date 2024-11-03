from diagrams import Diagram
from diagrams.gcp.compute import Run
from diagrams.gcp.database import SQL
from diagrams.gcp.compute import Functions
from diagrams.gcp.analytics import Pubsub

with Diagram("GCP Diagram", show=False):
    Run("Container with FastAPI") >> Pubsub("Message Queue") >> Functions(
        "Python Consumer Function") >> SQL("Postgres")
