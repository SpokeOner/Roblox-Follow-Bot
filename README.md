# Roblox Follow Bot

A Python automation tool for following users on Roblox using authenticated sessions.

> ⚠️ **Educational Purposes Only** - This tool is provided for educational and research purposes. Use responsibly and in accordance with Roblox's Terms of Service.

## Features

- Multi-threaded following with configurable thread count
- Proxy support for enhanced anonymity
- Automatic retry mechanism with exponential backoff
- Real-time progress tracking and statistics
- Error handling with detailed failure reasons
- Cookie-based authentication

## Requirements

### Python Version
- Python 3.7 or higher

### Dependencies

Install the required packages using pip:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install curl_cffi cryptography colorama
```

**Package Details:**
- `curl_cffi` - HTTP client with browser impersonation capabilities
- `cryptography` - Cryptographic operations for authentication token generation
- `colorama` - Cross-platform colored terminal output

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

### 1. Create Input Directory

Create an `input` folder in the project root directory.

### 2. Add Cookies

Create `input/cookies.txt` and add your `.ROBLOSECURITY` cookies (one per line):

```
cookie1_here
cookie2_here
cookie3_here
```

### 3. Add Proxies

Create `input/proxies.txt` and add your proxies in the following format (one per line):

```
protocol://user:pass@ip:port
http://user:pass@1.2.3.4:8080
socks5://user:pass@5.6.7.8:1080
```

**Important:** Proxies must be from the same country as your cookies for best results.

**Recommended Proxy Providers:**
- [Vault Proxies](https://vaultproxies.com) - Residential per GB plans recommended

## Usage

1. Ensure your `input` folder contains both `cookies.txt` and `proxies.txt`
2. Run the script:
   ```bash
   python follow.py
   ```
3. Enter the number of threads when prompted
4. Enter the target user ID you want to follow

### Example

```
Enter thread count: 5
Enter user id: 123456789

Starting 5 threads with 10 cookies
```

## Output

The script provides real-time feedback:

- **Success**: Green output showing successful follows
- **Failed**: Red output with error details and retry attempts
- **Final Summary**: Statistics including success rate and completion rate

## Project Structure

```
followbot/
├── follow.py              # Main script
├── input/
│   ├── cookies.txt       # Authentication cookies
│   └── proxies.txt       # Proxy list
└── README.md             # This file
```

## How It Works

1. Loads cookies and proxies from input files
2. Distributes cookies across worker threads
3. Each thread processes cookies sequentially
4. For each cookie:
   - Generates authentication tokens
   - Sets up session with cookies
   - Retrieves CSRF token
   - Executes follow request
   - Retries on failure (up to 3 attempts)

## Error Handling

The script handles various error scenarios:

- **Captcha Required** - Detected and reported
- **Rate Limiting** - Automatic retry with backoff
- **Invalid Cookies** - Authentication errors identified
- **Network Issues** - Connection timeouts and proxy failures
- **User Not Found** - Invalid user ID detection

## Disclaimer

This tool is for educational purposes only. Users are responsible for ensuring their use complies with:
- Roblox Terms of Service
- Applicable laws and regulations
- Platform rules and guidelines

The authors and contributors are not responsible for any misuse of this software.

## License

This project is provided as-is for educational purposes.

## Contributing

Contributions, issues, and feature requests are welcome.

## Author

[SpokeOner](https://github.com/SpokeOner)

