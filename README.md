
# Server Check Status

Server Check Status is a lightweight Python desktop tool for checking whether a
single server accepts TCP connections on a selected port.

The tool is designed for simple availability checks: enter a server IP address
or domain name, choose a port, set the number of attempts, and click `Start`.

## Features

- Single-server status checks
- Preset port selections for common services
- Custom port input from `1` to `65535`
- Multiple attempts for the same server and port
- Per-attempt status, latency, and error details
- Windows launcher for direct desktop use

## Open the Desktop Tool

On Windows, double-click:

```text
Open Server Check Status.cmd
```

You can also launch the Python GUI directly:

```text
server_check_status_gui.pyw
```

## Desktop Usage

1. Enter a server IP address or domain name.
2. Select a preset port, or choose `Custom` and enter a specific port number.
3. Enter the number of attempts.
4. Click `Start`.

Use [It should be available](It_should_be_available.txt) 

Each attempt is shown in the results table with one of these statuses:

- `available`: the TCP connection succeeded.
- `unavailable`: the connection failed, timed out, or the server could not be
  resolved.

The tool is intentionally limited to one server per check.

## Default Ports

The desktop tool includes common preset ports such as:

```text
80, 443, 22, 21, 25, 53, 110, 143, 993, 995, 3306, 5432, 6379, 8080, 8443
```

Select `Custom` if you need to test another port.

## Command-line Usage

The same single-server check can be run from a terminal:

```powershell
python .\server_check_status.py example.com --port 443 --attempts 3
```

Arguments:

- `server`: server IP address or domain name
- `--port`: TCP port number to check
- `--attempts`: number of times to run the check

## Notes

This tool checks TCP reachability only. A successful result means the target
accepted a TCP connection on the selected port. It does not validate any
higher-level application behavior or service-specific response.

## License

This project is licensed under the [MIT License](LICENSE).
