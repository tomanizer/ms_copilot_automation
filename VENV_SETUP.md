# Virtual Environment Setup

## ✅ Installation Complete

The virtual environment has been successfully created and configured with:
- ✓ Virtual environment created at `venv/`
- ✓ All dependencies from `requirements.txt` installed
- ✓ Project installed in editable mode (`pip install -e .`)
- ✓ CLI command `ms-copilot` is available

## 🚀 Auto-Activation Options

### Option 1: direnv (Recommended)

**Best for**: Automatic activation when entering the directory

1. Install direnv:
   ```bash
   brew install direnv
   ```

2. Add to your `~/.zshrc`:
   ```bash
   eval "$(direnv hook zsh)"
   ```

3. Allow direnv for this project:
   ```bash
   cd /Users/thomas/Documents/Projects/ms_copilot_automation
   direnv allow
   ```

4. Restart your terminal or run:
   ```bash
   source ~/.zshrc
   ```

Now, whenever you `cd` into this directory, the virtual environment will automatically activate!

### Option 2: Interactive Setup Script

Run the interactive setup script to configure auto-activation:

```bash
./setup_auto_activate.sh
```

This will guide you through setting up either direnv or a shell function.

### Option 3: Manual Activation

If you prefer manual control, use the convenient activation script:

```bash
source activate_venv.sh
```

Or use the standard Python method:

```bash
source venv/bin/activate
```

## 📋 Quick Commands

Once the virtual environment is activated:

```bash
# Check installation
ms-copilot --help

# Run tests
pytest

# Install Playwright browsers (first time only)
python -m playwright install chromium

# Authenticate with Copilot
ms-copilot --headed auth --manual

# Send a chat message
ms-copilot chat "Hello, Copilot!"
```

## 🔍 Verifying Activation

When the virtual environment is active, you should see:
- `(venv)` prefix in your terminal prompt
- `which python` should point to `venv/bin/python`
- `which ms-copilot` should point to `venv/bin/ms-copilot`

## 🛠️ Deactivation

To deactivate the virtual environment:

```bash
deactivate
```

## 📦 Adding New Dependencies

When you install new packages, make sure the venv is activated:

```bash
source venv/bin/activate
pip install package-name
pip freeze > requirements.txt  # Update requirements
```

## 🔄 Rebuilding the Environment

If you need to recreate the virtual environment:

```bash
# Remove old environment
rm -rf venv

# Create new environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Install Playwright browsers
python -m playwright install chromium
```

## 📝 Files Created

- `venv/` - Virtual environment directory (git-ignored)
- `.envrc` - direnv configuration file
- `activate_venv.sh` - Convenient activation script
- `setup_auto_activate.sh` - Interactive setup script
- `VENV_SETUP.md` - This guide

## ⚙️ Environment Variables

Create a `.env` file for configuration (already git-ignored):

```bash
M365_USERNAME=your-email@example.com
M365_COPILOT_URL=https://copilot.microsoft.com
BROWSER_HEADLESS=true
OUTPUT_DIRECTORY=./output
```

Store sensitive values in the system keyring:

```bash
python -c "import keyring; keyring.set_password('ms-copilot-automation', 'M365_PASSWORD', 'your-password')"
```

## 🎯 Next Steps

1. Choose an auto-activation method (direnv recommended)
2. Set up your credentials (see README.md)
3. Authenticate with Copilot: `ms-copilot --headed auth --manual`
4. Start automating!

For more information, see the main [README.md](README.md).
