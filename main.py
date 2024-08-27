import json
from difflib import get_close_matches
import re
import wikipedia
from transformers import pipeline

# Load the paraphrasing model and sentiment analysis model
paraphraser = pipeline("text2text-generation", model="Vamsi/T5_Paraphrase_Paws")
# sentiment_analyzer = pipeline("sentiment-analysis")

# Set the user agent for Wikipedia
wikipedia.set_lang("en")
wikipedia.set_user_agent("chatBot/1.0 (contact: your-email@example.com)")

def load_knowledge_base(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        data: dict = json.load(file)
    return data

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def load_user_infos(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as file:
            data: dict = json.load(file)
    except FileNotFoundError:
        data = {}
    return data

def save_user_infos(file_path: str, data: dict):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def correct_question(user_question: str) -> str:
    corrections = {
        # Your typo corrections here
    }
    for typo, correct in corrections.items():
        user_question = re.sub(typo, correct, user_question, flags=re.IGNORECASE)
    return user_question

def find_best_match(user_question: str, questions: list[str]) -> str | None:
    user_question = correct_question(user_question)
    matches: list = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

def generate_contextual_answer(question: str, original_answer: str) -> str:
    paraphrased_answer = paraphraser(f"Paraphrase this: {original_answer}", max_length=100)[0]['generated_text']
    return paraphrased_answer if paraphrased_answer.strip() else original_answer

def get_answer_from_wikipedia(question: str) -> str:
    try:
        content = wikipedia.summary(question, sentences=1)
        return content
    except wikipedia.exceptions.DisambiguationError as e:
        return f"The term '{question}' may refer to: {', '.join(e.options[:5])}. Please provide more details."
    except wikipedia.exceptions.PageError:
        return "Sorry, I couldn't find any information on this topic."

def get_answer_for_question(question: str, knowledge_base: dict) -> str | None:
    for q in knowledge_base["questions"]:
        if q["question"].lower() == question.lower():
            return generate_contextual_answer(question, q["answer"])
    return None

def update_user_info(user_input: str, user_infos: dict):
    if "my name is" in user_input.lower():
        name = user_input.split("is", 1)[1].strip()
        user_infos["name"] = name
        return f"Nice to meet you, {name}!"

    if "i am from" in user_input.lower():
        location = user_input.split("from", 1)[1].strip()
        user_infos["location"] = location
        return f"Wow, {location} is a great place!"

    if re.search(r'\bi am\b', user_input.lower()):
        match = re.search(r'\bi am (\d+)\b', user_input.lower())
        if match:
            age = match.group(1)
            user_infos["age"] = age
            return f"Great, you're {age} years old!"

    # Add more patterns and information types here
    return None

def personalized_greeting(user_infos: dict) -> str:
    greeting = "Hello!"
    if "name" in user_infos:
        greeting = f"Hello, {user_infos['name']}!"
    if "location" in user_infos:
        greeting += f" How are things in {user_infos['location']}?"
    return greeting

# def analyze_sentiment(user_input: str) -> str:
#     result = sentiment_analyzer(user_input)[0]
#     sentiment = result['label']
#     if sentiment == 'POSITIVE':
#         return "It sounds like you're in a good mood!"
#     elif sentiment == 'NEGATIVE':
#         return "I'm sorry you're feeling down."
#     else:
#         return "I see."

def chatbot():
    knowledge_base: dict = load_knowledge_base("knowledge_base.json")
    user_infos: dict = load_user_infos("user_infos.json")
    conversation_history = []
    print(personalized_greeting(user_infos))
    print("I can answer your questions about various topics:")

    while True:
        user_input: str = input("You: ")
        if user_input.lower() == "quit":
            break

        # Store conversation history
        conversation_history.append({"user": user_input})

        # Sentiment analysis
        # sentiment_response = analyze_sentiment(user_input)
        # print(f'Bot: {sentiment_response}')
        # conversation_history.append({"bot": sentiment_response})

        # Update or retrieve user information
        info_response = update_user_info(user_input, user_infos)
        if info_response:
            print(f'Bot: {info_response}')
            save_user_infos('user_infos.json', user_infos)
            conversation_history.append({"bot": info_response})
            continue

        # First check the knowledge base
        best_match: str | None = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])

        if best_match:
            answer: str = get_answer_for_question(best_match, knowledge_base)
            print(f'Bot: {answer}')
            conversation_history.append({"bot": answer})
        else:
                print("Bot: Sorry, I did not understand your question. Let me check Wikipedia.")
                wikipedia_answer: str = get_answer_from_wikipedia(user_input)
                print(f'Bot: {wikipedia_answer}')
                if wikipedia_answer != "Sorry, I couldn't find any information on this topic.":
                    knowledge_base["questions"].append({"question": user_input, "answer": wikipedia_answer})
                    save_knowledge_base('knowledge_base.json', knowledge_base)
                    print("Bot: Thank you! I have learned this response.")
                    conversation_history.append({"bot": wikipedia_answer})
                else:
                    print("Bot: I couldn't find an answer on Wikipedia. Can you teach me?")
                    new_answer: str = input("Type your answer or type 'skip' to skip: ")
                    if new_answer.lower() != 'skip':
                        knowledge_base["questions"].append({"question": user_input, "answer": new_answer})
                        save_knowledge_base('knowledge_base.json', knowledge_base)
                        print("Bot: Thank you very much. I learned this response.")
                        conversation_history.append({"bot": new_answer})

if __name__ == "__main__":
    chatbot()
