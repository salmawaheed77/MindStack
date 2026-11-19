# Linux Operations — MindStack

## Architecture

MindStack handles Linux and computer operations through the `executor/` package.

There is no separate `linux_ops/` package.

## Supported Modules

The Executor consists of:

- `app_manager.py`: Application management.
- `browser_manager.py`: Browser and website operations.
- `device_manager.py`: Volume, brightness, and Wi-Fi controls.
- `file_manager.py`: File and folder operations.
- `system_manager.py`: System information and system controls.
- `security.py`: Payload validation and workspace protection.
- `executor.py`: Main action dispatcher.

## Workspace

All file operations are restricted to:

`~/MindStack_Workspace`

Use relative paths whenever possible.

## Integration

Other project components must send structured action dictionaries to the Executor.

Example:

```python
from executor.executor import execute_command

action = {
    "action": "get_cpu_usage"
}

result = execute_command(action)
print(result["message"])
```

The Executor does not accept arbitrary shell commands.

## Security

The Executor validates structured actions before execution.

Destructive operations require explicit confirmation.

The separate `security/` package provides Linux shell-command validation through `security_gate.py`.

It is not automatically invoked by the structured Executor.

Do not bypass the Executor's validation when executing structured actions.

## Testing

Run Executor tests:

```bash
python3 -m unittest executor.test_executor -v
```

Run Linux operation tests:

```bash
python3 -m unittest tests.test_linux_ops -v
```

Run Security tests:

```bash
python3 -m unittest tests.test_security -v
```

Hardware-dependent operations must also be tested on the target Ubuntu machine.
