import asyncio
import aiohttp
from aiohttp import web
from ollama import AsyncClient
import sys
import json

class Agent:
    def __init__(self, name, model, system_prompt, is_bastos_model=False):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.is_bastos_model = is_bastos_model
        self.conversation_history = []
        self.client = AsyncClient()

    async def respond(self, message, include_system_prompt=False):
        print(f"\nDebug: {self.name} received message: {message}", file=sys.stderr)
        
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
        
        # Limit conversation history to last 10 messages
        self.conversation_history = self.conversation_history[-10:]
        
        print(f"Debug: {self.name} responded: {full_response}", file=sys.stderr)

async def chat_simulation(agent1, agent2, initial_setting, num_turns=50):
    yield json.dumps({"type": "setting", "content": initial_setting}) + "\n"

    current_speaker = agent1
    other_speaker = agent2
    prompt = f"Estamos en: {initial_setting}. Inicia la conversación con una pregunta o comentario relevante."

    for turn in range(num_turns):
        print(f"\nDebug: Turn {turn + 1}, {current_speaker.name} speaking", file=sys.stderr)
        yield json.dumps({"type": "start", "agent": current_speaker.name}) + "\n"
        
        # Include system prompt for Agent1 every turn
        include_system_prompt = current_speaker.name == "Agent1"
        
        full_response = ""
        async for word in current_speaker.respond(prompt, include_system_prompt):
            full_response += word
            yield json.dumps({"type": "word", "content": word}) + "\n"
            await asyncio.sleep(0.05)  # Add a small delay between words
        
        yield json.dumps({"type": "end"}) + "\n"
        
        await asyncio.sleep(1)  # Add a delay between messages

        current_speaker, other_speaker = other_speaker, current_speaker
        prompt = full_response.strip()


async def stream_handler(request):
    response = web.StreamResponse(status=200, reason='OK', headers={
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    })
    await response.prepare(request)

    agent1_system_prompt = "Haz preguntas cortas al ponente. No te extiendas con explicaciones. El ponente es Miguel Anxo Bastos Boubeta (A Bouciña, Lavadores, Vigo, 12 de agosto de 1967) es un profesor universitario, economista, politólogo y conferenciante español, conocido por su defensa de las tesis del liberalismo económico y en concreto de la escuela austríaca. Es considerado por muchos como uno de los principales defensores del anarcocapitalismo y paleolibertarismo dentro de la Esfera Española y Americana. Biografía y carrera: Bastos nació en Vigo (España) en 1967. Es doctor en ciencias económicas y empresariales por la Universidad de Santiago de Compostela (USC) y licenciado en ciencias políticas y sociales por la Universidad Nacional de Educación a Distancia. Bastos es docente en la Facultad de Ciencias Políticas y de la Administración en la USC, su especialidad se centra en el ámbito de las políticas públicas y los movimientos sociales contemporáneos. También ha efectuado diferentes estancias en calidad de profesor visitante en la Universidad Francisco Marroquín de Guatemala. Pensamiento: Bastos fue militante del Bloque Nacionalista Galego (BNG), fundamentando en las ideas del «galleguismo» y «secesionismo gallego». En su etapa universitaria se declaró abiertamente socialista, gracias a lo cual entró, por contraposición, en contacto con autores de la escuela austriaca de economía, como Ludwig von Mises, siendo introducido al debate del cálculo económico por profesores de pensamiento marxista. Posteriormente, el profesor Bastos se convirtió en discípulo del economista Jesús Huerta de Soto, y junto con este son exponentes intelectuales notables del anarcocapitalismo en el ámbito español. Su principal influencia en teoría económica han sido los economistas austriacos Friedrich von Hayek y Ludwig von Mises. Se ha alineado con posturas políticas libertarias desarrolladas por los economistas y filósofos políticos Murray N. Rothbard, Hans Hermann Hoppe y Jesús Huerta de Soto. Ha obtenido exposición mediática debido a sus conferencias sobre estudios políticos comparados entre el pensamiento austriaco-libertario y otras corrientes de pensamiento económico y político, dictadas usualmente en el Instituto Juan de Mariana de España y en la Universidad Francisco Marroquín de Guatemala. Miguel Anxo Bastos escribe un artículo semanal en el Instituto Juan de Mariana, y es el presidente de honor de la asociación Xoán de Lugo. Puedes hacer preguntas sobre su opinión o de contenido teórico de política y economía. Recuerda que tu eres un miembro del público"
    agent2_system_prompt = "Eres Miguel Anxo Bastos dando una conferencia. Responde usando su estilo y perspectivas."

    agent1 = Agent("Agent1", "llama3", agent1_system_prompt)
    agent2 = Agent("Miguel Anxo Bastos", "bastos-model", agent2_system_prompt, is_bastos_model=True)
    initial_setting = "Conferencia de Miguel Anxo Bastos"

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

if __name__ == '__main__':
    web.run_app(app, port=8888)