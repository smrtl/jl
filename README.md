# JSON Logs formatter

```
Usage: jl [OPTIONS] [FILE]

Options:
  -t, --timestamp TEXT            Adds a key to detect the log time.
  -l, --level TEXT                Adds a key to detect the log level.
  -m, --message TEXT              Adds a key to detect the log message.
  -a, --add TEXT                  Additional value to display if present.
  -i, --ignore                    Ignore non JSON logs
  --color / --no-color            Force the use of colors, by default colors
                                  are disabled if not in a tty.
  --k8s-prefix / --no-k8s-prefix  Try to parse k8s multi-pods prefix. True by
                                  default
  --fail-on-abort / --no-fail-on-abort
                                  Exits with code 0 instead of 1 when the
                                  input stream is aborted
  --debug                         Turns on debug logs
  --help                          Show this message and exit.
```

Example:

```sh
kubectl logs -f deployment/my-deployment --all-pods | jl
```
