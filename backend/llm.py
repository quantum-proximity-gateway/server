from llama_cpp import Llama
from threading import Lock


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
        self.system_prompt = None
        self.lock = Lock()

    def set_system_prompt(self, system_prompt: str | None) -> None:
        '''
        Set system_prompt used in each prompt.
        '''
        self.system_prompt = system_prompt

    def generate_response(self, user_prompt: str) -> str:
        '''
        Generate a response for a given prompt.
        '''
        prompt = f'''
<|start_of_role|>system<|end_of_role|>{self.system_prompt}<|end_of_text|>
<|start_of_role|>user<|end_of_role|>{user_prompt}<|end_of_text|>
<|start_of_role|>assistant<|end_of_role|>
'''

        with self.lock:
            output = self.llm(
                prompt,
                max_tokens=128,
            )

        return output['choices'][0]['text']