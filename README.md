# 🛠️ sregpt – AI CLI Assistant for SRE & Sysadmin Teams

`sregpt` is a command-line tool that uses OpenAI models to help SREs and sysadmins generate shell commands, explain infrastructure actions, and analyze inputs. It's lightweight, fast, and tailored for terminal use.

---

## 🚀 Features

- Generate complex shell commands with explanation
- Built-in safety warnings for dangerous operations
- One-time API key prompt and secure storage
- Clean CLI output with optional formats (`--json`, `--cmd-only`)
- Supports stdin input (e.g. `cat log.txt | sregpt -s "analyze this"`)

---

## 📦 Installation

You need Python 3.9+ and `pip` installed.

```bash
pip install git+https://github.com/wquinones/sregpt.git
```

> ✅ Works on macOS, Linux, and WSL  
> ✅ Also works with [pipx](https://github.com/pypa/pipx):  
> `pipx install git+https://github.com/wquinones/sregpt.git`

---

## 🔑 First Time Setup

On the first run, you’ll be prompted for your OpenAI API key:

```bash
sregpt -s "list all docker containers"
```

🔐 Your key is securely stored at:
```
~/.config/sre_gpt/config.yaml
```
with permissions `0600`.

To reset it, delete that file.

---

## 🧪 Usage Examples

```bash
sregpt -s "how do I check disk space on linux"
```

```
cmd: df -h
explanation: Shows disk usage in human-readable format
dangerous: false
```

```bash
cat nginx.log | sregpt -s "analyze the errors"
```

```bash
sregpt -s "generate terraform to make an S3 bucket" --json
```

---

## ⚙️ CLI Options

| Flag          | Description                                   |
|---------------|-----------------------------------------------|
| `-s`          | Your question or shell prompt (required)      |
| `--cmd-only`  | Output only the shell command                 |
| `--json`      | Output full structured JSON                   |
| `--model`     | OpenAI model to use (default: `gpt-4o-mini`)  |

---

## 🔒 Security Notes

- Your API key is never exposed in logs or output
- Dangerous commands (e.g., `rm -rf`) are flagged in red
- `sregpt` does **not** execute anything — it just suggests

---

## 📄 License

MIT © 2025 [William Quinones](https://github.com/wquinones)

---

## 🤝 Contributing

Want to extend the command library or output format?

1. Fork the repo
2. Run `pip install -e .`
3. Edit `sre_gpt/cli.py`
4. Submit a PR!
