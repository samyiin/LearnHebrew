from RecitePlanner import EbbinghausPlanner
import dbAPI
from ReciteMaterialGenerator import ReciteMaterialGenerator
from datetime import datetime, timedelta

NUM_NEW_WORD_PER_DAY = 20


def generate_today_material(num_new_words_to_learn, API_KEY):
    # decide what to study today
    # begin_rank, end_rank = 90, 100
    begin_rank, end_rank = dbAPI.get_next_new_material(num_new_words_to_learn)
    new_materials_df = dbAPI.get_vocabs(begin_rank, end_rank)

    # generate context sentences: notice that it's seperated by ";"
    recite_material_generator = ReciteMaterialGenerator()
    context_sentence = recite_material_generator.get_context_sentence_from_ChatGPT(new_materials_df, API_KEY)
    new_materials_df['ExampleSentence'] = [d['ExampleSentence'] for d in context_sentence]
    new_materials_df['SentenceTranslation'] = [d['SentenceTranslation'] for d in context_sentence]
    new_materials_df[["ExampleSentence", 'SentenceTranslation']].to_csv(
        f"GeneratedStudyMaterial/CS_{datetime.now().strftime("%Y-%m-%d")}.csv",
        index=False, sep=";")
    # todo: for now I will use this with quizlet, so just need to output to csv and upload to quizlet.

    # output the hebrew+pronounce - english: notice that it's seperated by ";"
    hebrew_pronounce_tuples = list(zip(new_materials_df["Hebrew"], new_materials_df["Transliteration"]))
    hebrew_pronounce_strings = []
    for hebrew_pronounce_tuple in hebrew_pronounce_tuples:
        hebrew_pronounce_string = hebrew_pronounce_tuple[0] + " (" + hebrew_pronounce_tuple[1] + ")"
        hebrew_pronounce_strings.append(hebrew_pronounce_string)
    new_materials_df['Hebrew+Pronounce'] = hebrew_pronounce_strings
    new_materials_df[['Hebrew+Pronounce', "English"]].to_csv(
        f"GeneratedStudyMaterial/HL_{datetime.now().strftime("%Y-%m-%d")}.csv",
        index=False, sep=";")
    # update study progress
    datetime_now_str = dbAPI.format_date_string(datetime.now())
    dbAPI.update_study_progress(date_str=datetime_now_str, new_material=[begin_rank, end_rank])
    print(f"Your study material is being saved under GeneratedStudyMaterial/ folder, files names are today's date: {datetime.now().strftime("%Y-%m-%d")}")


def print_study_progress_table():
    print("Here are the current study progress")
    study_progress_table = dbAPI.get_study_progress_df()
    print(study_progress_table)

def print_date_need_to_recite():
    print("Here are the dates you need to recite materials for.")
    recite_planner = EbbinghausPlanner()
    should_recite_dates = recite_planner.get_recite_datetime()
    for date_str in should_recite_dates:
        print(date_str)

def main():
    print("Please select your action:")
    print(f"1. generate study material for today: {NUM_NEW_WORD_PER_DAY} new words with context sentences")
    print("2. get previous dates that I need to review materials on")
    print("3. view my study progress")
    print("9. Exit program")
    while True:
        user_input = input("Your choice (number 1, 2, 3, or 9):")
        if user_input == '9':
            print("Goodbye!")
            break
        elif user_input == '1':
            print("Running.....")
            API_KEY = input("Please provide your OPENAI API Key:")
            generate_today_material(NUM_NEW_WORD_PER_DAY, API_KEY)
        elif user_input == '2':
            print_date_need_to_recite()
        elif user_input == '3':
            print_study_progress_table()
        else:
            print("Invalid input, please input number 1, 2, 3, or 9.")


    # todo: mark, unmark
    # print("4. Mark today as done")
    # print("5. mark review material as done")

if __name__ == "__main__":
    main()
