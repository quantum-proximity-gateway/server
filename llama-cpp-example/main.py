from llm import LLM

if __name__ == '__main__':
    model_path = 'models/ibm-granite_granite-3.2-8b-instruct-Q6_K_L.gguf'
    granite_3_2 = LLM(model_path=model_path)

    system_prompt = 'You are an assistant that only replies in JSON format with the key "message".'
    granite_3_2.set_system_prompt(system_prompt)

    user_prompt = 'Hello, how are you doing?'
    response = granite_3_2.generate_response(user_prompt)
    print(f'Prompt: {user_prompt}\n\nResponse: {response}')