import asyncio
import aiohttp
from aiohttp import web
from ollama import AsyncClient
import sys
import json
import random

class Agent:
    def __init__(self, name, model, system_prompt, is_bastos_model=False):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.is_bastos_model = is_bastos_model
        self.conversation_history = []
        self.client = AsyncClient()

    async def respond(self, message, include_system_prompt=True):
        if include_system_prompt:
            prompt = f"{self.system_prompt}\n\nConversation history:\n"
        else:
            prompt = "Conversation history:\n"
        
        prompt += "\n".join([f"{m['role']}: {m['content']}" for m in self.conversation_history]) + f"\n\nHuman: {message}\nAI:"
        
        full_response = ""
        if self.is_bastos_model:
            async for response in await self.client.generate(model=self.model, prompt=prompt, stream=True):
                content = response['response']
                full_response += content
                yield content
        else:
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history,
                {"role": "user", "content": message}
            ]
            
            async for chunk in await self.client.chat(
                model=self.model,
                messages=messages,
                stream=True
            ):
                if chunk:
                    content = chunk['message']['content']
                    full_response += content
                    yield content

        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": full_response})
        
        self.conversation_history = self.conversation_history[-10:]

def load_user_prompts(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

async def chat_simulation(agent1, agent2, initial_setting, num_turns=10):
    yield json.dumps({"type": "setting", "content": initial_setting}) + "\n"

    user_prompts = load_user_prompts('user_prompts.txt')

    current_speaker = agent1
    other_speaker = agent2
    prompt = f"Estamos en: {initial_setting}. Inicia la conversación con una pregunta relevante en español."

    for turn in range(num_turns):
        print(f"\nDebug: Turn {turn + 1}, {current_speaker.name} speaking", file=sys.stderr)
        yield json.dumps({"type": "start", "agent": current_speaker.name}) + "\n"
        
        if current_speaker.name == "Agent1":
            new_topic = random.choice(user_prompts)
            current_speaker.system_prompt = f"Eres un miembro del público en una conferencia de Miguel Anxo Bastos. Mantén tus intervenciones breves y neutrales, con poca personalidad. Hazle preguntas breves y abiertas sobre sus ideas en diversos temas interesantes, especialmente sobre: {new_topic}. El ponente es Miguel Anxo Bastos Boubeta (A Bouciña, Lavadores, Vigo, 12 de agosto de 1967) es un profesor universitario, economista, politólogo y conferenciante español, conocido por su defensa de las tesis del liberalismo económico y en concreto de la escuela austríaca. Nunca ha escrito un libro. Es considerado por muchos como uno de los principales defensores del anarcocapitalismo y paleolibertarismo dentro de la Esfera Española y Americana. Las preguntas deben ser originales y complejas. Mantén tus intervenciones cortas y directas, no más de un párrafo, profundizando en el tema. No halagues al profesor si interactues demasiado con su argumento, simplemente propón nuevas preguntas."
        
        #include_system_prompt = current_speaker.name == "Agent1"
        
        full_response = ""
        async for word in current_speaker.respond(prompt, True): # include_system_prompt
            full_response += word
            yield json.dumps({"type": "word", "content": word}) + "\n"
            await asyncio.sleep(0.05)
        
        yield json.dumps({"type": "end"}) + "\n"
        
        await asyncio.sleep(1)

        current_speaker, other_speaker = other_speaker, current_speaker
        prompt = full_response.strip()

async def stream_handler(request):
    response = web.StreamResponse(status=200, reason='OK', headers={
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    })
    await response.prepare(request)

    agent1_system_prompt = "Eres un miembro del público en una conferencia de Miguel Anxo Bastos. Hazle preguntas originales, cortas y abiertas sobre sus ideas en diversos temas interesantes. El ponente es Miguel Anxo Bastos Boubeta (A Bouciña, Lavadores, Vigo, 12 de agosto de 1967) es un profesor universitario, economista, politólogo y conferenciante español, conocido por su defensa de las tesis del liberalismo económico y en concreto de la escuela austríaca. Es considerado por muchos como uno de los principales defensores del anarcocapitalismo y paleolibertarismo dentro de la Esfera Española y Americana. Las preguntas deben ser originales y complejas. Mantén tus intervenciones cortas y directas, no más de un párrafo, profundizando en el tema."
    agent2_system_prompt = "Eres Miguel Anxo Bastos. Responde usando su estilo, perspectivas y manerismos a las preguntas efectuadas por el público. Extiendete en tu respuesta e hila diferentes temáticas relevantes. Utiliza puntos suspensivos entre frases de vez en cuando."

    agent1 = Agent("Agent1", "llama3", agent1_system_prompt)
    agent2 = Agent("Miguel Anxo Bastos", "bastos-model2", agent2_system_prompt, is_bastos_model=True)
    initial_setting = "Conferencia infinita de Miguel Anxo Bastos"

    try:
        async for message in chat_simulation(agent1, agent2, initial_setting):
            await response.write(f"data: {message}\n\n".encode('utf-8'))
    except Exception as e:
        print(f"Debug: Error occurred: {str(e)}", file=sys.stderr)
    finally:
        await response.write(b"data: [DONE]\n\n")

    return response

async def index_handler(request):
    with open('index.html', 'r') as f:
        content = f.read()
    return web.Response(text=content, content_type='text/html')

app = web.Application()
app.router.add_get('/', index_handler)  
app.router.add_get('/stream', stream_handler)
app.router.add_static('/static/', path='./static/', name='static')


if __name__ == '__main__':
    web.run_app(app, port=8888)