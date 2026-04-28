# Claude Task: Fix `opsRun` argument passthrough

## Context

TRINITY has access to the S25 terminal/infra operations through `opsRun`, but
the current GPT/plugin schema only exposes the top-level `op` reliably.

Operations such as `git_status`, `git_log`, `service_status`, `disk_usage`,
`ram_status`, and `gpu_status` work.

Dynamic operations that require arguments are currently blocked from the GPT
side because the argument payload is not passed through reliably.

## Working examples

These work from TRINITY:

```json
{"op":"git_status"}
{"op":"git_log"}
{"op":"service_status"}
{"op":"disk_usage"}
{"op":"ram_status"}
{"op":"gpu_status"}
```

## Broken examples

These should work but currently do not pass usable arguments:

```json
{
  "op": "shell_safe",
  "args": {
    "cmd": "python tools/strategy_inventory.py --root /home/alienstef/S25-COMMAND-CENTER"
  }
}
```

```json
{
  "op": "log_tail",
  "args": {
    "file": "auto_signal_scanner",
    "n": 80
  }
}
```

```json
{
  "op": "process_check",
  "args": {
    "pattern": "mission_worker"
  }
}
```

## Desired schema

`opsRun` should accept:

```json
{
  "op": "shell_safe",
  "args": {
    "cmd": "ls /home/alienstef/S25-COMMAND-CENTER/tools"
  }
}
```

and preserve existing whitelist controls server-side.

## Security requirements

Do not make `shell_safe` unrestricted.

Keep command whitelist limited to safe read-only/system diagnostic commands:

- `ls`
- `cat`
- `tail`
- `head`
- `grep`
- `find`
- `pwd`
- `whoami`
- `date`
- `uname`
- `uptime`
- `systemctl`
- `git`
- `ps`
- `pgrep`
- `df`
