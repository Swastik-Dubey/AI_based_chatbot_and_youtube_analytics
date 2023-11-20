from flask import Flask, render_template, request, jsonify, url_for, redirect
import requests
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
nltk.download('vader_lexicon')
app = Flask(__name__)

# Define the headers variable
headers = {"Authorization": "Bearer hugging_face_access_keys"}
api_key = 'API_keys_here'

# Question and Answer models
qa_models = [
    {"api_url": "https://api-inference.huggingface.co/models/distilbert-base-uncased-distilled-squad", "name": "DistilBERT"},
    {"api_url": "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2", "name": "RoBERTa"},
    {"api_url": "https://api-inference.huggingface.co/models/deepset/bert-large-uncased-whole-word-masking-squad2", "name": "BERT"},
]
# Initialize the Sentiment Intensity Analyzer
sia = SentimentIntensityAnalyzer()

# Variables to store the pending commands and chat conversation
pending_summarize_command = False
pending_translation_command = False
pending_qa_context = False
context_text = ""
chat_history = []

def query_api(model_url, payload):
    try:
        response = requests.post(model_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying model {model_url}: {str(e)}")
        return None

def summarize_with_models(input_text):
    model_urls = [
        "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
        "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6",
        "https://api-inference.huggingface.co/models/philschmid/bart-large-cnn-samsum",
    ]

    for model_url in model_urls:
        output = query_api(model_url, {"inputs": input_text})

        if output and 'summary_text' in output[0]:
            return output[0]['summary_text']

    return "Unable to generate summarization with any model."



def query_question_answering(payload):
    for model in qa_models:
        response = requests.post(model["api_url"], headers=headers, json=payload)
        try:
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            output = response.json()
            if 'answer' in output:
                return output['answer']
        except requests.exceptions.RequestException as e:
            print(f"Error querying model {model['name']}: {str(e)}")
    return "Unable to generate an answer with any model."

def translate_text(input_text):
    translation_url = "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-en-hi"
    translation_payload = {"inputs": input_text}
    translation_output = query_api(translation_url, translation_payload)

    if translation_output:
        return translation_output[0]['translation_text']
    else:
        return "Translation failed."
    
def get_video_details(api_key, video_id):
    # Function to retrieve video details
    def get_video_info(video_id):
        youtube = build('youtube', 'v3', developerKey=api_key)
        video_response = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        ).execute()
        return video_response['items'][0] if 'items' in video_response else None

    # Function to extract transcript in English
    def get_transcript(video_id):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            full_transcript = ' '.join(entry['text'] for entry in transcript)
            return full_transcript.replace('[Music]', '')
        except Exception as e:
            print(f"Error getting transcript: {e}")
            return ""

    # Function to load top comments with most likes
    def get_top_comments(video_id):
        try:
            comments_response = requests.get(
                f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={api_key}&order=relevance&maxResults=100"
            ).json()
            top_comments = []

            for item in comments_response.get('items', []):
                comment_data = item['snippet']['topLevelComment']['snippet']
                top_comments.append({
                    'author': comment_data['authorDisplayName'],
                    'textDisplay': comment_data['textDisplay'],
                    'likeCount': comment_data['likeCount']
                })

            return top_comments

        except HttpError as e:
            print(f"Error getting top comments: {e}")
            return []

    # Main function to get video details, transcript, and top comments
    try:
        video_info = get_video_info(video_id)
        if video_info:
            # Video details
            title = video_info['snippet']['title']
            thumbnail_url = video_info['snippet']['thumbnails']['default']['url']
            description = video_info['snippet']['description']
            likes = video_info['statistics']['likeCount']
            views = video_info['statistics']['viewCount']
            uploaded_date = video_info['snippet']['publishedAt']

            # Transcript
            transcript = get_transcript(video_id)

            # Top comments
            top_comments = get_top_comments(video_id)

            # Return a dictionary with all information
            result = {
                'title': title,
                'thumbnail_url': thumbnail_url,
                'description': description,
                'likes': likes,
                'views': views,
                'uploaded_date': uploaded_date,
                'transcript': transcript,
                'top_comments': top_comments
            }

        else:
            result = {"error": "Video not found."}

    except HttpError as e:
        result = {"error": f"An error occurred: {e}"}


    
  
    return result
    


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_response', methods=['POST'])
def get_response():
    global pending_summarize_command
    global pending_qa_context
    global context_text
    global chat_history
    global pending_translation_command

    user_message = request.form['user_message']

    if user_message.lower() == '/help':
        bot_response = "Available commands:\n" \
                       "/help - Display this help message\n" \
                       "/summarize - Begin summarizing text (type your text after the command)\n" \
                       "/clear - Clear the chat conversation\n" \
                       "/youtube_analytics - Analyze YouTube analytics\n" \
                       "/translation - Translate text\n" \
                       "/questionandanswer - Answer questions"
                       
                      
    elif user_message.lower() == '/clear':
        # Clear the chat history and reset context_text
        chat_history = []
        context_text = ""
        bot_response = "Chat conversation cleared."
    elif user_message.lower().startswith('/summarize'):
        # Set the pending command to /summarize, expecting the next input as text
        pending_summarize_command = True
        bot_response = "Please provide the text you want to summarize."
    elif pending_summarize_command:
        # User has entered /summarize, use this input as the text for summarization
        input_text = user_message.strip()

        if input_text:
            bot_response = summarize_with_models(input_text)
        else:
            bot_response = "Please provide text for summarization."

        # Reset the pending command
        pending_summarize_command = False
    elif user_message.lower().startswith('/translation'):
        # Set the pending command to /translation, expecting the next input as text
        pending_translation_command =True
        bot_response = "Please provide the text you want to translate to Hindi."
    elif pending_translation_command:
        # User has entered /summarize, use this input as the text for summarization
        input_text = user_message.strip()

        if input_text:
            bot_response = translate_text(input_text)
        else:
            bot_response = "Please provide the text you want to translate to Hindi."

        # Reset the pending command
        pending_translation_command = False
          
       
    elif user_message.lower() == '/questionandanswer':
        # Set the pending command to /questionandanswer, expecting the next input as context
        pending_qa_context = True
        bot_response = "Please provide the context for question and answer."
    elif pending_qa_context:
        # User has entered context for question and answer, use this input as the context
        context_text = user_message.strip()
        pending_qa_context = False
        bot_response = "Please provide the question for question and answer."
    elif user_message.lower().startswith('/questionandanswer'):
        # Set the pending command to /questionandanswer, expecting the next input as context
        pending_qa_context = True
        bot_response = "Please provide the context for question and answer."
    elif pending_qa_context:
        # User has entered context for question and answer, use this input as the context
        context_text = user_message.strip()
        pending_qa_context = False
        bot_response = "Please provide the question for question and answer."
     
    else:
        # User has entered a question for question and answer, use this input as the question
        question_text = user_message.strip()

        if question_text:
            # Call the query_question_answering function
            bot_response = query_question_answering({
                "inputs": {
                    "question": question_text,
                    "context": context_text
                },
            })
        else:
            bot_response = "Please provide a question for question and answer."
    return jsonify({'bot_response': bot_response, 'chat_history': chat_history})



def analyze_sentiment(comment):
    # Analyze the sentiment of a given comment
    sentiment_score = sia.polarity_scores(comment)['compound']

    if sentiment_score >= 0.05:
        return 'positive'
    elif sentiment_score > -0.05 and sentiment_score < 0.05:
        return 'neutral'
    else:
        return 'negative'




def parse_video_id(video_url):
    # Add your logic to extract the video_id from the video_url
    # Example: Extracting video_id from a YouTube URL
    parsed_url = urlparse(video_url)
    if parsed_url.hostname == 'www.youtube.com' and parsed_url.path == '/watch':
        video_id = parse_qs(parsed_url.query)['v'][0]
        print(video_id)
        return video_id
    else:
        return None
    

@app.route('/input_url', methods=['GET', 'POST'])
def input_url():
    if request.method == 'POST':
        video_url = request.form.get('video_url')
        # Parse the video URL to get the video ID
        url_data = urlparse(video_url)
        query = parse_qs(url_data.query)
        video_id = query["v"][0]

        # Call your function to get video details
        video_details = get_video_details(api_key, video_id)

        # Apply sentiment analysis on the comments
        for comment in video_details['top_comments']:
            sentiment = sia.polarity_scores(comment['textDisplay'])
            if sentiment['compound'] > 0.05:
                comment['sentiment'] = 'positive'
            elif sentiment['compound'] < -0.05:
                comment['sentiment'] = 'negative'
            else:
                comment['sentiment'] = 'neutral'

        # Summarize the transcript
        video_details['transcript_summary'] = summarize_with_models(video_details['transcript'])

        # Redirect to the YouTube analytics page with the video details
        return render_template('youtube_analytics.html', video_details=video_details)

    # If the request method is GET, just render the page
    return render_template('input_url.html')

@app.route('/youtube_analytics', methods=['GET'])
def youtube_analytics():
    video_details = request.args.get('video_details', {})
    return render_template('youtube_analytics.html', video_details=video_details)
  
if __name__ == '__main__':
    app.run(debug=True)
