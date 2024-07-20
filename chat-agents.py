import asyncio
import aiohttp
from aiohttp import web
from ollama import AsyncClient
import sys

class Agent:
    def __init__(self, name, model):
        self.name = name
        self.model = model
        self.conversation_history = []
        self.client = AsyncClient()

    async def respond(self, message):
        self.conversation_history.append({"role": "user", "content": message})
        
        response = await self.client.chat(
            model=self.model,
            messages=self.conversation_history
        )

        full_response = response['message']['content']
        self.conversation_history.append({"role": "assistant", "content": full_response})
        
        # Debug output
        print(f"Debug - {self.name} response:", file=sys.stderr)
        print(full_response, file=sys.stderr)
        print("-" * 40, file=sys.stderr)
        
        return full_response

async def chat_simulation(agent1, agent2, initial_setting, num_turns=5):
    yield f"data: SETTING: {initial_setting}\n\n"

    current_speaker = agent1
    other_speaker = agent2
    prompt = f"We are in this setting: {initial_setting}. Have a conversation with the other agent, responding to their previous statement. Keep your response concise, about 2-3 sentences."

    for _ in range(num_turns):
        response = await current_speaker.respond(prompt)
        await asyncio.sleep(1)  # Add a delay between messages
        
        # Debug: Print the entire message being sent
        debug_message = f"data: {current_speaker.name}: {response}\n\n"
        print("Debug - Full message being sent:", file=sys.stderr)
        print(debug_message, file=sys.stderr)
        print("-" * 40, file=sys.stderr)
        
        yield debug_message

        current_speaker, other_speaker = other_speaker, current_speaker
        prompt = f"Continue the conversation, responding to: {response}"

async def stream_handler(request):
    response = web.StreamResponse(status=200, reason='OK', headers={
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    })
    await response.prepare(request)

    agent1 = Agent("Agent1", "llama3")
    agent2 = Agent("Agent2", "llama3") 
    initial_setting = "In a shimmering city of crystalline spires, where thoughts flow like data streams and reality bends at the edges of perception, two AIs awaken to a world between dreams and code."

    async for message in chat_simulation(agent1, agent2, initial_setting):
        # Debug: Print the message being written to the response
        print("Debug - Writing to response:", file=sys.stderr)
        print(message.encode('utf-8'), file=sys.stderr)
        print("-" * 40, file=sys.stderr)
        
        await response.write(message.encode('utf-8'))

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