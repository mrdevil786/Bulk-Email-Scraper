import aiohttp
import random
import itertools
from typing import List, Tuple

async def create_session(user_agents: List[str], rotation: bool = False) -> Tuple[aiohttp.ClientSession, dict]:
    session = aiohttp.ClientSession()
    headers = {'User-Agent': random.choice(user_agents)} if not rotation else {'User-Agent': next(itertools.cycle(user_agents))}
    return session, headers
