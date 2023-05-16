import os
import redis
import random

from pathlib import Path


def is_system_file(filename):
    system_files_extentions = [".DS_Store"]
    return any(extention in filename for extention in system_files_extentions)


def get_question_with_answer(path_to_quiz_questions):
    quiz_questions_path = Path(path_to_quiz_questions).resolve()
    filepaths = []
    for root, _, filenames in os.walk(quiz_questions_path):
        for filename in filenames:
            if not is_system_file(filename):
                filepath = os.path.join(root, filename)
                filepaths.append(filepath)
    questions_with_answers = {}
    random_filepath = random.choice(filepaths)
    with open(random_filepath, encoding="KOI8-R") as file:
        text = file.read()
    paragraphs = [text_part.strip() for text_part in text.split("\n\n")]
    question = None
    while paragraphs:
        paragraph = paragraphs.pop(0)
        if paragraph.startswith("Вопрос"):
            question = paragraph.split(":\n")[-1]
        elif paragraph.startswith("Ответ"):
            questions_with_answers[question] = paragraph.split(":\n")[-1]
    next_question = random.choice(list(questions_with_answers.keys()))
    return next_question, questions_with_answers[next_question]


def get_questions_with_answers(path_to_quiz_questions):
    quiz_questions_path = Path(path_to_quiz_questions).resolve()
    filepaths = []
    for root, _, filenames in os.walk(quiz_questions_path):
        for filename in filenames:
            if not is_system_file(filename):
                filepath = os.path.join(root, filename)
                filepaths.append(filepath)
    questions_with_answers = {}
    num_paths = 5
    random_filepaths = random.sample(filepaths, num_paths)
    for filepath in random_filepaths:
        with open(filepath, encoding="KOI8-R") as file:
            text = file.read()
        paragraphs = [text_part.strip() for text_part in text.split("\n\n")]
        question = None
        while paragraphs:
            paragraph = paragraphs.pop(0)
            if paragraph.startswith("Вопрос"):
                question = paragraph.split(":\n")[-1]
            elif paragraph.startswith("Ответ"):
                questions_with_answers[question] = paragraph.split(":\n")[-1]
    return questions_with_answers


def set_db_result(result_status, player_id, r):
    score_key = f"{result_status} {player_id}"
    score = r.get(score_key)
    new_score = int(score) + 1 if score else 1
    r.set(score_key, str(new_score))
