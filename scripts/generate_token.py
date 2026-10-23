import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.brokers.metatrader import Bridge

print(Bridge.generate_auth_token())
