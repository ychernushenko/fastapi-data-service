from diagrams import Diagram
from diagrams.gcp.compute import Run
from diagrams.gcp.database import SQL
from diagrams.gcp.compute import Functions
from diagrams.gcp.analytics import Pubsub
from diagrams.gcp.security import IAP

with Diagram("GCP Diagram", show=False):
    IAP("Authentication") >> Run("Container with FastAPI") >> Pubsub("Message Queue") >> Functions(
        "Python Processing Function") >> SQL("Postgres")
