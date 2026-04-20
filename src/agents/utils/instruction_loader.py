import json
import os
from functools import lru_cache

@lru_cache(maxsize=2)
def _load_instructions(is_cloud: bool) -> dict:
    env = "cloud" if is_cloud else "local"
    # Use '..' to move up from 'utils' to 'agents'
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        '..',
        'instructions',
        f'{env}.json'
    ))

    with open(path, 'r') as f:
        return json.load(f)

def get_instruction(agent_name: str, is_cloud: bool) -> str:
    return _load_instructions(is_cloud)[agent_name]
