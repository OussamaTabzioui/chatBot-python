import json
from difflib import get_close_matches
import re
from transformers import pipeline

# Load the paraphrasing model
paraphraser = pipeline("text2text-generation", model="Vamsi/T5_Paraphrase_Paws")

def load_knowledge_base(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        data: dict = json.load(file)
    return data

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def correct_question(user_question: str) -> str:
    # Basic typo correction using regular expressions
    corrections = {
        r'\bwath\b': 'what',
        r'\bwht\b': 'what',
        r'\bisnt\b': 'isn\'t',
        r'\bdont\b': 'don\'t',
        r'\bcant\b': 'can\'t',
        r'\bwont\b': 'won\'t',
        r'\brecieve\b': 'receive',
        r'\bteh\b': 'the',
        r'\bdefinately\b': 'definitely',
        r'\bseperate\b': 'separate',
        r'\boccured\b': 'occurred',
        r'\buntill\b': 'until',
        r'\btruely\b': 'truly',
        r'\balot\b': 'a lot',
        r'\bwich\b': 'which',
        r'\bthier\b': 'their',
        r'\byour\b': 'you\'re',
        r'\btheyre\b': 'they\'re',
        r'\bwerent\b': 'weren\'t',
        r'\byourselfs\b': 'yourselves',
        r'\bshouldnt\b': 'shouldn\'t',
        r'\bhis\b': 'he\'s',
        r'\bwhos\b': 'who\'s',
        r'\bwhould\b': 'would',
        r'\bbeleive\b': 'believe',
        r'\bacheive\b': 'achieve',
        r'\bgrammer\b': 'grammar',
        r'\bmispell\b': 'misspell',
        r'\bneccessary\b': 'necessary',
        r'\bbegining\b': 'beginning',
        r'\bfoward\b': 'forward',
        r'\bknowlege\b': 'knowledge',
        r'\blabled\b': 'labeled',
    }

    for typo, correct in corrections.items():
        user_question = re.sub(typo, correct, user_question, flags=re.IGNORECASE)
    return user_question

def find_best_match(user_question: str, questions: list[str]) -> str | None:
    user_question = correct_question(user_question)
    matches: list = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

def generate_contextual_answer(question: str, original_answer: str) -> str:
    # Use the paraphrasing model to generate a more contextually appropriate answer
    paraphrased_answer = paraphraser(f"Paraphrase this: {original_answer}", max_length=100)[0]['generated_text']
    return paraphrased_answer if paraphrased_answer.strip() else original_answer

def get_answer_for_question(question: str, knowledge_base: dict) -> str | None:
    for q in knowledge_base["questions"]:
        if q["question"].lower() == question.lower():
            return generate_contextual_answer(question, q["answer"])
    return None

def chatbot():
    knowledge_base: dict = load_knowledge_base("knowledge_base.json")
    print("Welcome to the chatbot, I can answer your questions about the following topics:")

    while True:
        user_input: str = input("You: ")
        if user_input.lower() == "quit":
            break

        best_match: str | None = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])

        if best_match:
            answer: str = get_answer_for_question(best_match, knowledge_base)
            print(f'Bot: {answer}')
        else:
            print("Bot: Sorry, I did not understand your question. Can you teach me?")
            new_answer: str = input("Type your answer or type 'skip' to skip: ")
            if new_answer.lower() != 'skip':
                knowledge_base["questions"].append({"question": user_input, "answer": new_answer})
                save_knowledge_base('knowledge_base.json', knowledge_base)
                print("Bot: Thank you very much. I learned this response.")

if __name__ == "__main__":
    chatbot()
