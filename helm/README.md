# Moshi TTS Helm Chart

This Helm chart deploys the Moshi TTS server on Kubernetes with configurable settings.

## Configuration

The TTS server configuration is externalized and can be customized via the `values.yaml` file.

### Configuration Structure

The configuration has three levels:

1. **Server-level settings**: Basic server configuration
   - `static_dir`: Directory for static files
   - `log_dir`: Directory for logs
   - `instance_name`: Server instance name
   - `authorized_ids`: List of authorized API keys

2. **Module-level settings**: TTS module configuration
   - `type`: Module type (must be "Py")
   - `path`: API endpoint path
   - `text_tokenizer_file`: Path to tokenizer model
   - `batch_size`: Number of concurrent connections
   - `text_bos_token`: Beginning of sequence token

3. **Python TTS-specific settings**: Passed to the Python TTS script
   - `log_folder`: Python logs directory
   - `voice_folder`: Voice embeddings location
   - `default_voice`: Default voice to use
   - `cfg_coef`: Classifier-free guidance coefficient
   - `cfg_is_no_text`: Whether CFG is no-text based
   - `padding_between`: Padding tokens between words
   - `n_q`: Number of quantization levels
   - `temp`: Sampling temperature
   - `debug`: Enable debug logging

### Customizing Configuration

Edit `values.yaml` to customize the TTS configuration:

```yaml
ttsConfig:
  static_dir: "./static/"
  log_dir: "$HOME/tmp/tts-logs"
  instance_name: "tts"
  authorized_ids:
    - "public_token"

  modules:
    tts_py:
      type: "Py"
      path: "/api/tts_streaming"
      text_tokenizer_file: "hf://kyutai/tts-1.6b-en_fr/tokenizer_spm_8k_en_fr_audio.model"
      batch_size: 8
      text_bos_token: 1

      py:
        voice_folder: "hf-snapshot://kyutai/tts-voices/**/*.safetensors"
        default_voice: "unmute-prod-website/default_voice.wav"
        cfg_coef: 2.0
        # ... more settings
```

### Installation

```bash
# Install the chart
helm install moshi-tts ./helm

# Upgrade with new configuration
helm upgrade moshi-tts ./helm

# Uninstall
helm uninstall moshi-tts
```

### Local Development (Docker Compose)

For local development outside Kubernetes, use docker-compose which mounts the config from your local filesystem:

```bash
# Edit rust/tts.toml with your local settings
vim rust/tts.toml

# Start the server
docker-compose up moshi-rust
```

The docker-compose setup mounts `rust/tts.toml` into the container at `/workspace/tts.toml`.

## Architecture

- **ConfigMap**: Stores the `tts.toml` configuration file
- **Deployment**: Runs the moshi-server container with the ConfigMap mounted at `/config/tts.toml`
- **Service**: Exposes the TTS API on port 50020

The container uses the `TTS_CONFIG_PATH` environment variable to locate the config file:
- In Kubernetes: Set to `/config/tts.toml` (from ConfigMap)
- In local Docker: Defaults to `./tts.toml` (from build-time COPY)
