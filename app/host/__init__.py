"""Host composition, transport, and lifecycle services.

Import concrete modules explicitly; this package performs no startup or
registration. BootstrapCoordinator assembles dependencies, while app.main owns
the listening server. Research algorithms and domain storage are not supplied
by the host package; absent lifecycle providers remain unavailable.
"""
