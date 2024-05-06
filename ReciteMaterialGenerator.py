"""
This file contains a class that represents a sentence generator:
2023.Dec.6:
In order not to complicate things, so far I will make a generator, that takes a pandas df of two columns:
[HebrewWord, EnglishTranslation, ...], and returns a list of dictionaries with the following fields:
{
"Hebrew":".....",
"Translation":"....",
"ExampleSentence":"......",
"SentenceTranslation": "......",
}
I will generate sentences using Chatgpt API, for now we will use gpt3.5-turbo.
This design is open to extension, So in the future we can expand to any language. In the future we can also add more
methods for generating languages, such as using other language models.
#todo For now I will not write an abstract class: class ContextSentenceGenerator
"""

import openai
import json
from itertools import chain


class ReciteMaterialGenerator:
    """
    This recite material generator depends on the Hebrew 10000 word list.
    The input must be a pandas df with columns ['Rank', 'Transliteration', 'Hebrew', 'English']
    Later it might be able to expand to all language pairs
    """
    def __init__(self):
        self.language_models = "gpt-3.5-turbo"

    def get_context_sentence_from_ChatGPT(self, new_materials_df, API_KEY):
        """
        get_context_sentence_from_ChatGPT
        :param new_materials_df: a pandas df with columns ['Rank', 'Transliteration', 'Hebrew', 'English']
        :return:
        """
        english_hebrew_tuples = list(zip(new_materials_df["Hebrew"], new_materials_df["English"]))
        english_hebrew_strings = []
        for english_hebrew_tuple in english_hebrew_tuples:
            english_hebrew_string = english_hebrew_tuple[0] + " (" + english_hebrew_tuple[1] + ")"
            english_hebrew_strings.append(english_hebrew_string)
        results_temp = []
        for english_hebrew_string in english_hebrew_strings:
            result = self._request_ChatGTP(english_hebrew_string, API_KEY)
            results_temp.append(result)
        return results_temp

    def _request_ChatGTP(self, hebrew_word, API_KEY):
        """
        each time we send 5 words to chat gpt
        might go wrong, if chat gpt went wrong. If it went wrong, we can try refresh
        :param hebrew_words_list:
        :return:
        """
        with open("HebrewContextSentenceGeneratorFirstPrompt", 'r') as file:
            # todo there might be a bug here: the file path is relative to the running script. might not be this script
            first_prompt = file.read()
        # todo remember hide this in the environment when push to git
        client = openai.OpenAI(api_key=API_KEY)
        response = client.chat.completions.create(
            model=self.language_models,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": first_prompt},
                {"role": "assistant", "content": "Yes"},
                {"role": "user", "content": hebrew_word}
            ]
        )
        # Check if response is finished normally
        if not response.choices[0].finish_reason == "stop":
            raise Exception("The response didn't end properly")
        # Check if response is in "list of dictionary" format
        try:
            context_sentences = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            raise Exception("Chatgpt response is not in jason format")
        # todo what is the max length for hebrew_words_list? Need to check, so far I pick 5.
        return context_sentences

# test
# myClass = HebrewContextSentenceGenerator()
# sents = myClass.get_context_sentence_from_ChatGPT(["כאשר", "אין", "אמר", "באופן", "הברית"])
# print(1)
