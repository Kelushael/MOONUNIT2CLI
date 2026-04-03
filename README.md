# MOONUNIT2 — Sovereign AI Agent

One alias. Everything starts. You're in.

- Local model server auto-starts on launch
- Persistent memory across sessions
- Self-extending toolkit — creates tools on the fly
- SSH to remote servers conversationally
- DNS self-maintenance
- Release pipeline: test here → publish to release hub

---

## Install

### Linux (Debian/Ubuntu)

```bash
sudo apt update && sudo apt install -y python3 python3-pip git
git clone https://github.com/Kelushael/MOONUNIT2CLI.git
cd MOONUNIT2CLI
pip3 install -r requirements.txt
sudo ln -s $(pwd)/moonunit2cli.py /usr/local/bin/moonunit2
sudo chmod +x moonunit2cli.py
```

### macOS

```bash
brew install python3 git
git clone https://github.com/Kelushael/MOONUNIT2CLI.git
cd MOONUNIT2CLI
pip3 install -r requirements.txt
sudo ln -s $(pwd)/moonunit2cli.py /usr/local/bin/moonunit2
sudo chmod +x moonunit2cli.py
```

### Windows (WSL)

```bash
# Run inside WSL (Ubuntu)
sudo apt update && sudo apt install -y python3 python3-pip git
git clone https://github.com/Kelushael/MOONUNIT2CLI.git
cd MOONUNIT2CLI
pip3 install -r requirements.txt
sudo ln -s $(pwd)/moonunit2cli.py /usr/local/bin/moonunit2
sudo chmod +x moonunit2cli.py
```

### Termux (Android)

```bash
pkg update && pkg install -y python git
git clone https://github.com/Kelushael/MOONUNIT2CLI.git
cd MOONUNIT2CLI
pip install -r requirements.txt
mkdir -p ~/.local/bin
ln -s $(pwd)/moonunit2cli.py ~/.local/bin/moonunit2
chmod +x moonunit2cli.py
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

### Arch Linux

```bash
sudo pacman -Sy python python-pip git
git clone https://github.com/Kelushael/MOONUNIT2CLI.git
cd MOONUNIT2CLI
pip install -r requirements.txt
sudo ln -s $(pwd)/moonunit2cli.py /usr/local/bin/moonunit2
sudo chmod +x moonunit2cli.py
```

---

## Run

```bash
moonunit2
```

That's it.
