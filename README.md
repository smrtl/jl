# JSON Logs formatter

```
Usage: jl [OPTIONS] [FILE]

Options:
  -t, --timestamp TEXT  Adds a key to detect the log time.
  -l, --level TEXT      Adds a key to detect the log level.
  -m, --message TEXT    Adds a key to detect the log message.
  -a, --add TEXT        Additional value to display if present.
  -i, --ignore          Ignore non JSON logs
  --debug               Turns on debug logs
  --help                Show this message and exit.
```

Example:

```sh
kubectl logs -f deployment/my-deployment --all-pods | jl
```
