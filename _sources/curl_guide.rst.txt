TEsting guide with `curl`
==================================================================

This guide provides step-by-step instructions for configuring Google Cloud Identity-Aware Proxy (IAP) to secure a Cloud Run service, generating an access token, and submitting a request to the service using `curl`.

Prerequisites
-------------
1. **Google Cloud Project** with a deployed Cloud Run service.
2. **Permissions**:
   - **IAP-secured Web App User** role for users who need access to the IAP-protected service.
   - **Viewer** or higher permission on the project to configure IAP and OAuth credentials.
3. **Tools**:
   - `Google Cloud SDK (gcloud)` - See installation instructions: https://cloud.google.com/sdk/docs/install
   - `curl` installed on your machine.

Step 1: Install Google Cloud SDK and Authenticate
-------------------------------------------------
1. **Install the Google Cloud SDK**:
   Follow the installation guide for your OS: `https://cloud.google.com/sdk/docs/install`

2. **Initialize and Authenticate**:
   After installation, run the following commands to initialize `gcloud` and authenticate:

   .. code-block:: bash

      gcloud init
      gcloud auth login

Step 2: Set Up OAuth Credentials for IAP
----------------------------------------
1. Go to the **Google Cloud Console**.
2. Navigate to **APIs & Services > Credentials**.
3. Click **Create Credentials** > **OAuth 2.0 Client ID**.
4. Choose **Desktop App** as the Application type.
5. Note the **Client ID** and **Client Secret**. You’ll need these to authenticate users for IAP.

Step 3: Grant IAP-secured Web App User Role
-------------------------------------------
1. In **Google Cloud Console**, go to **IAM & Admin > IAM**.
2. Locate the user who needs access to the Cloud Run service.
3. Assign the **IAP-secured Web App User** role to the user for your Cloud Run service.

Step 4: Enable IAP on the Cloud Run Service
-------------------------------------------
1. Go to **Security > Identity-Aware Proxy** in the Google Cloud Console.
2. Find your Cloud Run service and **Enable IAP** for it.

Step 5: Generate an Identity Token
----------------------------------
To access the IAP-protected service, generate an identity token using `gcloud`:

.. code-block:: bash

   ACCESS_TOKEN=$(gcloud auth print-identity-token)

This command retrieves a JWT identity token that can be used to access IAP-protected services.

Step 6: Submit a Request with `curl`
------------------------------------
Use `curl` to send a request to the IAP-protected Cloud Run service. Replace `<YOUR_CLOUD_RUN_URL>` with the URL of your Cloud Run service.

.. code-block:: bash

   curl -X POST <YOUR_CLOUD_RUN_URL>/data/ \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
              "time_stamp": "2019-05-01T06:00:00-04:00",
              "data": [0.379, 1.589, 2.188]
            }'

**Example Command**:

.. code-block:: bash

   curl -X POST https://fastapi-service-1093935530204.europe-west3.run.app/data/ \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
              "time_stamp": "2019-05-01T06:00:00-04:00",
              "data": [0.379, 1.589, 2.188]
            }'

Troubleshooting
---------------
- **401 Unauthorized**: Ensure the identity token is generated using `gcloud auth print-identity-token` and that IAP is enabled on the Cloud Run service.
- **403 Forbidden**: Check that the user has the `IAP-secured Web App User` role for the Cloud Run service.

