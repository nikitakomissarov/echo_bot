from google.cloud import dialogflow
import json
from dotenv import dotenv_values
import logging
from logger import TelegramLogsHandler, bot_logger
from logging.handlers import TimedRotatingFileHandler
from logger import TelegramLogsHandler, bot_logger


config = dotenv_values('.env')
TRAINING_PHRASES = config['TRAINING_PHRASES']
GOOGLE_APPLICATION_CREDENTIALS = config['GOOGLE_APPLICATION_CREDENTIALS']

logger_info = logging.getLogger('loggerinfo')
logger_error = logging.getLogger("loggererror")


def create_intent(project_id, training_phrases_parts):
    for section in training_phrases_parts:
        display_name = section
        training_phrases_part = training_phrases_parts[display_name]['questions']

        message_texts = [training_phrases_parts[display_name]['answer']]

        intents_client = dialogflow.IntentsClient()

        parent = dialogflow.AgentsClient.agent_path(project_id)

        training_phrases = []
        for a in training_phrases_part:
            part = dialogflow.Intent.TrainingPhrase.Part(text=a)

            training_phrase = dialogflow.Intent.TrainingPhrase(parts=[part])
            training_phrases.append(training_phrase)

        text = dialogflow.Intent.Message.Text(text=message_texts)
        message = dialogflow.Intent.Message(text=text)

        intent = dialogflow.Intent(
            display_name=display_name, training_phrases=training_phrases, messages=[message]
        )
        language_code = 'ru'

        response = intents_client.create_intent(
            request={"parent": parent, "intent": intent, "language_code": language_code}
        )

        logger_info.info("Intent created: {}".format(response))


def main():
    try:
        handler = TimedRotatingFileHandler("app.log", when='D', interval=30, backupCount=1)
        handler_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(handler_format)
        logger_info.setLevel(logging.INFO)
        logger_info.addHandler(handler)
        logger_error.setLevel(logging.ERROR)
        logger_error.addHandler(handler)
        telegram_notification_handler = TelegramLogsHandler(bot_logger)
        telegram_notification_handler.setFormatter(handler_format)
        logger_error.addHandler(telegram_notification_handler)

        with open(GOOGLE_APPLICATION_CREDENTIALS, "r") as my_file:
            credentials = my_file.read()
            credentials = json.loads(credentials)

        with open(TRAINING_PHRASES, "r", encoding='utf-8') as phrases_file:
            training_phrases_parts = phrases_file.read()
            training_phrases_parts = json.loads(training_phrases_parts)

        create_intent(credentials['quota_project_id'], training_phrases_parts)

    except Exception as err:
        logger_error.error(err, exc_info=True)


if __name__ == '__main__':
    main()
