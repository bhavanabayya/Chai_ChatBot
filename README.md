Follow the steps below to set up and run the project on your local machine.

**1. Create a Virtual Environment**
From the root directory of the project, run the following command to create a virtual environment named `.venv`:

    python3 -m venv .venv

**2. Activate the Virtual Environment**
Before you can install dependencies or run the project, you must activate the environment.

On macOS / Linux (bash/zsh):

    source .venv/bin/activate

On Windows (Command Prompt):

    .venv\Scripts\activate.bat

On Windows (PowerShell):

    .venv\Scripts\Activate.ps1

Note: If you get an error in PowerShell about script execution being disabled, you may need to set the execution policy for your session by running:

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

**3. Install Dependencies**
With the virtual environment active, install the required Python packages using the requirements.txt file. pip will automatically find and install the specific versions listed in the file.

    pip install -r requirements.txt

**4. Running the Streamlit Frontend**
To launch the chatbot frontend interface:

    streamlit run frontend/app.py

**5. Running the FastAPI Backend**
To start the backend API server:

    uvicorn backend.main:app --reload --port 8000

**6. Deactivating the Environment**
When you are finished working on the project, you can deactivate the environment and return to your global Python context by simply running:

    deactivate
