# AI_based_chatbot_and_youtube_analytics
## Installation

Before running the app, you need to install the required packages. You can do this by running the following command:

```bash
pip install -r requirements.txt
```
This command reads the requirements.txt file and installs all the packages listed in it.

## Running the App
After installing the required packages, you can run the Flask app with the following command:

```bash
python app.py
```
## Hugging Face Read-Only Access Key

1. Go to the [Hugging Face website](https://huggingface.co/).
2. Sign in or create a new account.
3. Navigate to your account settings or dashboard.
4. Look for API access or API keys section.
5. Generate a new read-only API key.
6. Copy the generated access key.

## Google Cloud Console API Key (YouTube API)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Sign in or create a new Google Cloud account.
3. Create a new project or select an existing one.
4. In the sidebar, navigate to "APIs & Services" > "Dashboard."
5. Click on "+ ENABLE APIS AND SERVICES" at the top.
6. Search for "YouTube Data API v3" and enable it for your project.
7. Once enabled, go to "Credentials" in the left sidebar.
8. Create a new API Key.
9. Copy the generated API key.

## Configuring the Application

Now that you have obtained both keys, configure the application with these keys.

1. Open the `config.py` file in the project.
2. Replace the `HUGGING_FACE_ACCESS_KEY` variable with your Hugging Face read-only access key.
3. Replace the `GOOGLE_API_KEY` variable with your Google Cloud Console API key.

```python
# config.py

# Hugging Face API Key
HUGGING_FACE_ACCESS_KEY = 'your_hugging_face_access_key'

# Google Cloud Console API Key
GOOGLE_API_KEY = 'your_google_api_key'
