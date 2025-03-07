from llama_cpp import Llama


class LLM:
    def __init__(self, model_path: str) -> None:
        '''
        Initialise the model given by the model_path string.
        '''
        self.llm = Llama(
            model_path=model_path,
            n_threads=6,
            n_batch=512,
            n_ctx=2048,
            verbose=False,
        )
        self.custom_instruction = None

    def set_custom_instruction(self, instruction: str | None) -> None:
        '''
        Set custom instruction which is prepended to each prompt.
        '''
        self.custom_instruction = instruction

    def generate_response(self, prompt: str) -> str:
        '''
        Generate a response for a given prompt.
        '''
        if self.custom_instruction:
            prompt = f'{self.custom_instruction}\n\n{prompt}'

        output = self.llm(
            prompt,
            max_tokens=50,
        )

        return output['choices'][0]['text']