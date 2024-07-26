import os
import re
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from afinn import Afinn
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Path to token and credentials
TOKEN_PATH = 'token.json'
CREDENTIALS_PATH = 'C://Users//HP//OneDrive//Masaüstü//credentials.json'

# Download required NLTK data
nltk.download('stopwords')
nltk.download('wordnet')
english_stopwords = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()
afinn = Afinn()

# Function to clean and lemmatize text
def clean_and_lemmatize_text(text):
    text = BeautifulSoup(text, "html.parser").get_text()
    text = re.sub(r'[^a-zA-ZçÇğĞıİöÖşŞüÜ]', ' ', text)
    text = text.lower()
    words = text.split()
    meaningful_words = [lemmatizer.lemmatize(w) for w in words if not w in english_stopwords]
    return " ".join(meaningful_words)

# Function to calculate sentiment
def calculate_sentiment(text):
    cleaned_text = clean_and_lemmatize_text(text)
    sentiment_score = afinn.score(cleaned_text)
    return sentiment_score

@csrf_exempt
def index(request):
    context = {}
    if request.method == 'POST':
        creds = None
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=8080)
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())

        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', maxResults=1, labelIds=['INBOX'], q='').execute()
        messages = results.get('messages', [])
        if not messages:
            context['error'] = 'No messages found.'
        else:
            message = service.users().messages().get(userId='me', id=messages[0]['id']).execute()
            snippet = message.get('snippet', 'No snippet found.')
            email_text = snippet
            if not email_text.strip() or len(email_text.split()) < 3:
                context['error'] = 'Email text is empty or too short to analyze.'
            else:
                try:
                    email_language = detect(email_text)
                    if email_language == 'tr':
                        translated_text = GoogleTranslator(source='auto', target='en').translate(email_text)
                        email_text = translated_text
                    cleaned_email_text = clean_and_lemmatize_text(email_text)
                    sentiment_score = calculate_sentiment(email_text)
                    if sentiment_score > 0:
                        sentiment = 'Positive'
                    elif sentiment_score < 0:
                        sentiment = 'Negative'
                    else:
                        sentiment = 'Neutral'
                    context['snippet'] = snippet
                    context['cleaned_email_text'] = cleaned_email_text
                    context['sentiment_score'] = sentiment_score
                    context['sentiment'] = sentiment
                except LangDetectException:
                    context['error'] = 'Unable to detect language due to insufficient features in the text.'
    return render(request, 'C://Users//HP//OneDrive//Masaüstü//email//email_sentiment_project//sentiment//templates//index.html', context)

@csrf_exempt
def analyze_email(request):
    context = {}
    if request.method == 'POST':
        # Perform email analysis logic
        context['message'] = 'Email analyzed successfully.'
    return render(request, 'C://Users//HP//OneDrive//Masaüstü//email//email_sentiment_project//sentiment//templates//index.html', context)
