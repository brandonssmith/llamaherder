# Llama Herder

A comprehensive GUI application for managing Ollama models on your local system. This tool allows you to list installed models, remove them, and install new models from a curated list with detailed descriptions.

## Features

- **List Installed Models**: View all locally installed Ollama models with detailed information including size, modification date, and technical details
- **Remove Models**: Safely remove unwanted models to free up disk space
- **Install New Models**: Browse and install from a curated list of popular models with descriptions
- **Model Information**: View detailed information about each model including size, family, and capabilities
- **Search Functionality**: Search through available models by name, family, or description
- **Real-time Status**: Get real-time feedback on operations with a status bar

## Requirements

- Python 3.7 or higher
- Ollama installed and running on your system
- Internet connection for installing new models

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Make sure Ollama is running on your system (usually on `http://localhost:11434`)
2. Run the application:
   ```bash
   python llama_herder.py
   ```

## How to Use

### Viewing Installed Models
- The left panel shows all currently installed models
- Click on a model to view detailed information
- Use the "Refresh" button to update the list

### Removing Models
1. Select a model from the installed models list
2. Click "Remove Selected Model"
3. Confirm the deletion in the dialog

### Installing New Models
1. Use the search box to find models by name, family, or description
2. Select a model from the available models list
3. Read the description to understand the model's capabilities
4. Click "Install Selected Model"
5. Wait for the installation to complete

## Available Models

The application includes a curated list of popular models:

### General Purpose Models
- **Llama 3.2/3.1**: Meta's latest models with excellent performance
- **Mistral**: Efficient models with good performance-to-size ratio
- **Mixtral**: Advanced mixture of experts models
- **Gemma**: Google's open-source models
- **Phi-3**: Microsoft's compact but capable models
- **Qwen2.5**: Alibaba's multilingual models

### Specialized Models
- **Code Llama**: Specialized for code generation and programming tasks
- **Neural Chat**: Optimized for conversational AI
- **Dolphin**: Uncensored models for creative tasks
- **OpenChat**: Open-source conversational models

## Technical Details

- **API Integration**: Uses Ollama's REST API for all operations
- **Threading**: Operations run in background threads to keep the UI responsive
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Cross-platform**: Works on Windows, macOS, and Linux

## Troubleshooting

### "Could not connect to Ollama" Error
- Make sure Ollama is installed and running
- Check that Ollama is accessible at `http://localhost:11434`
- Try restarting the Ollama service

### Installation Fails
- Check your internet connection
- Ensure you have enough disk space
- Some models are large and may take time to download

### Model Removal Fails
- Make sure the model is not currently in use
- Try refreshing the model list first
- Check that you have sufficient permissions

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this application.

## License

This project is open source and available under the MIT License.
