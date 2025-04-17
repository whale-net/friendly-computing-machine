# friendly-computing-machine
slackbot

## environment
uv
```
uv venv
source .venv/bin/activate
uv sync
```

your environment is now setup

(optional) update your IDE to use `./.venv/bin/python`

## run
run the bot (or whatever this currently is)
```
uv run fcm
```
```
temporal server start-dev
```

## logging / tracing / metrics

Python logging module with otlp handler. Opentelemetry "zero-code" auto-instrumentation for traces

Currently, the opentelemetry python sdk is "experimental" and has no guarantees with breaking changes.
So the implementation may change in the future, but I imagine it'll still support the builtin python logging library.

Traces are auto-magically handled by the instrumentation. The trace SDK is stable, but it's TBD how to manually
add traces with auto-instrumentation. Probably just works, but haven't tried it yet.

This project does not use otel logging auto-instrumentation. For some reason I (alex) could not get it to work with this
project. The logs always seemed to end up in the void. Maybe it was all batch size or something simple like that in the
end, but it doesn't matter because I went with manual logging.

Metrics are out of scope for now

Everything is intended to be collected by an instance of otel collector. See helm chart values for required endpoints.
Python will still log to stdout. TBH should probably disable it, but it doesn't matter.

### other

if you want to run opentelemetry auto instrumentation outside the tilt environment, you will need to run this script.
```
uv run opentelemetry-bootstrap -a requirements | uv pip install --requirement -
```
