from llm import LLM

if __name__ == '__main__':
    model_path = 'models/ibm-granite_granite-3.2-8b-instruct-Q6_K_L.gguf'
    granite_3_2 = LLM(model_path=model_path)

    instruction = 'You are an assistant that only replies in JSON format with the "message".'
    granite_3_2.set_custom_instruction(instruction)

    prompt = 'Hello, how are you doing?'
    response = granite_3_2.generate_response(prompt)
    print(response)