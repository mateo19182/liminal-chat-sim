import asyncio
import aiohttp
from aiohttp import web
from ollama import AsyncClient
import sys
import json

class Agent:
    def __init__(self, name, model, system_prompt):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.conversation_history = []
        self.client = AsyncClient()

    async def respond(self, message):
        print(f"\nDebug: {self.name} received message: {message}", file=sys.stderr)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.conversation_history,
            {"role": "user", "content": message}
        ]
        
        full_response = ""
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
        
        print(f"Debug: {self.name} responded: {full_response}", file=sys.stderr)

async def chat_simulation(agent1, agent2, initial_setting, num_turns=5):
    yield json.dumps({"type": "setting", "content": initial_setting}) + "\n"

    current_speaker = agent1
    other_speaker = agent2
    prompt = f"We are in this setting: {initial_setting}. Start the conversation with the other agent."

    for turn in range(num_turns):
        print(f"\nDebug: Turn {turn + 1}, {current_speaker.name} speaking", file=sys.stderr)
        yield json.dumps({"type": "start", "agent": current_speaker.name}) + "\n"
        
        full_response = ""
        async for word in current_speaker.respond(prompt):
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

    agent1_system_prompt = "You are a concise and friendly agent. Keep your responses short. Engage in a natural conversation, responding to the other agent's messages."
    agent2_system_prompt = "You are a concise and slightly sarcastic agent. Keep your responses short. Engage in a natural conversation, responding to the other agent's messages with a hint of wit."

    agent1 = Agent("Agent1", "llama3", agent1_system_prompt)
    agent2 = Agent("Agent2", "llama3", agent2_system_prompt)
    initial_setting = "negotiation for land"

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