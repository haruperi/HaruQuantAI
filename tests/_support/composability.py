"""Business-neutral capabilities used by foundation tests."""

from app.kernel.capability import CapabilityKey

ROOT_CAPABILITY = CapabilityKey[object](name="test.root", major=1)
PROVIDER_CAPABILITY = CapabilityKey[object](name="test.provider", major=1)
CONSUMER_CAPABILITY = CapabilityKey[object](name="test.consumer", major=1)
OPTIONAL_CAPABILITY = CapabilityKey[object](name="test.optional", major=1)
UNDECLARED_CAPABILITY = CapabilityKey[object](name="test.undeclared", major=1)
