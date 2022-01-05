from flask import Flask, jsonify, request, make_response
from pprint import pprint
from flask import jsonify
import json
from google_trans import GoogleTranslator
from pons import PonsTranslator
from linguee import LingueeTranslator
from mymemory import MyMemoryTranslator
from yandex import YandexTranslator
from deepl import DeepL
from qcri import QCRI
from langdetect import detect

app = Flask(__name__)
app.config["DEBUG"] = True


@app.route('/translate/<news_type>/<password>', methods=['POST'])
def scrap_news(news_type, password):
    if password != "password":
        return make_response("HTTP/1.1 401 Unauthorized", 401)
    data_to_translate = request.json
    data_to_translate = json.loads(data_to_translate) if type(data_to_translate) is str else data_to_translate
    if news_type == "news":
        titles = [data["title"] for data in data_to_translate]
        batch_titles = get_titles_batch(titles)
        translated_titles = translate_titles(batch_titles)
        descriptions = [data["description"] for data in data_to_translate]
        batch_descriptions = get_description_batch(descriptions)
        translated_descriptions = translate_descriptions(batch_descriptions)
        pprint([{"ar_title": title, "ar_descriptions": description} for title, description in
                zip(translated_titles, translated_descriptions)])
        return jsonify([
            {
                "title": title,
                "ar_title": ar_title,
                "descriptions": description,
                "ar_description": ar_description,
            }
            for title, ar_title, description, ar_description in zip(
                titles, translated_titles, descriptions, translated_descriptions
            )
        ])
    elif news_type == "tweets":
        tweets = [data for data in data_to_translate]
        return jsonify(
            translate_tweets(tweets)
        )


def translate_tweets(tweets):
    translated_tweets = [GoogleTranslator(detect(tweet), 'ar').translate(tweet) for tweet in tweets]
    pprint([
        {
            "tweet": tweet,
            "ar_tweet": ar_tweet
        }
        for tweet, ar_tweet in zip(tweets, translated_tweets)
    ])
    return [
        {
            "tweet": tweet,
            "ar_tweet": ar_tweet
        }
        for tweet, ar_tweet in zip(tweets, translated_tweets)
    ]


def get_titles_batch(titles):
    total_string_length = 0
    batch_titles = []
    tmp = []
    for t in titles:
        if total_string_length + len(t) < 5000:
            total_string_length += len(t)
            tmp.append(t)
        else:
            batch_titles.append(tmp)
            tmp = [t]
            total_string_length = len(t)
    batch_titles.append(tmp) if tmp not in batch_titles else None
    return batch_titles


def translate_titles(batch_titles):
    translated_titles = []
    for titles in batch_titles:
        for title in GoogleTranslator(detect(titles[0]), 'ar').translate_batch(titles):
            translated_titles.append(title)
    return translated_titles


def translate_descriptions(descriptions):
    translated_descriptions = []
    for paragraphs in descriptions:
        if len(paragraphs) > 1:
            translated_paragraphs = [
                GoogleTranslator(detect(p[0]), 'ar').translate(p)
                for p in paragraphs
            ]
        else:
            translated_paragraphs = GoogleTranslator(detect(paragraphs[0]), 'ar').translate(paragraphs[0])
        translated_descriptions.append("".join(translated_paragraphs).strip(".").strip() + ".")
    return translated_descriptions


def split_description(d):
    if len(d) <= 5000:
        return d
    inner_phrases = d.split(".")
    inner_paragraphs = [""]
    while inner_phrases:
        if len(inner_paragraphs[-1] + f"{inner_phrases[0]}.") <= 5000:
            inner_paragraphs[-1] += f"{inner_phrases.pop(0)}."
        else:
            inner_paragraphs.append("")
            tmp = 0
    return inner_paragraphs


def get_description_batch(descriptions):
    batch_descriptions = []
    for d in descriptions:
        inner_paragraphs = split_description(d)
        batch_descriptions.append(inner_paragraphs)
    return batch_descriptions


app.run(port=5002)
