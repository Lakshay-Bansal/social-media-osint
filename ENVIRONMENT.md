# Environment Reference Guide

## Active Conda Environment: `yio`

This project uses a dedicated Conda virtual environment named **`yio`** for all development, dependencies, and testing.

### Creation and Activation

```bash
# Create the environment with Python 3.12
conda create -n yio python=3.12 -y

# Activate the environment
conda activate yio

# Install required dependencies
pip install -r requirements.txt
```

### Running the Application

Always ensure the `yio` environment is active before running CLI or Dashboard tools:

```bash
# Verify active environment
conda info --envs

# Run interactive CLI
python main.py

# Run interactive Web Dashboard
streamlit run dashboard.py
```

### Environment Specs
- **Environment Name**: `yio`
- **Base Python**: 3.12
- **Core Packages**: `google-api-python-client`, `isodate`, `yt-dlp`, `instaloader`, `pandas`, `rich`, `plotly`, `streamlit`, `python-dotenv`, `requests`
