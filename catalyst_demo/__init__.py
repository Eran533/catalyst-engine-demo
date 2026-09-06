"""Catalyst engine demo: re-engage dormant brokerage clients with a reason to look
at the market again.

Every trading day the engine finds clients who have not traded for a while,
works out which symbols each of them cares about, checks those symbols for a
market catalyst (a large daily move, a 52-week high or low), and sends at most
one personalised notification per client per day.

The package is split so each part can be swapped or tested alone:

    universe     who is dormant, and what do they care about
    catalysts    is anything happening in those symbols today
    state        have we already told this client (idempotency)
    templates    what the message says, in the client's language
    notifier     how the message is delivered
    engine       the daily run that wires the above together
    report       did the notification lead to a trade
"""

__version__ = "1.0.0"
