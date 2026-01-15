#!/bin/bash
#$ -P scc-chat       # Project name
#$ -N ollama-server  # Job name
#$ -l h_rt=02:00:00  # 2-hour runtime
#$ -l gpus=1         # Request 1 GPU
#$ -l gpu_c=6.0      # CC needed for ollama
#$ -l gpu_memory=60G # 60gb vram
#$ -m ea             # Email on end or abort
#$ -j y              # Combine output and error files
#$ -pe omp 8         # Request 8 cores


# Set working directory
cd /projectnb/scc-chat/ollama/bin

# Set environment variables
export OLLAMA_MODELS=/projectnb/scc-chat/ollama/models
export OLLAMA_HOST="0.0.0.0:11434"
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_CONTEXT_LENGTH=16384

# Create log directory if it doesn't exist
mkdir -p /projectnb/scc-chat/ollama/logs

# Start Ollama server with logging
./ollama serve > /projectnb/scc-chat/ollama/logs/ollama_server_$(date +"%Y%m%d_%H%M%S").log 2>&1 &

# Keep the job running and allow interaction
wait