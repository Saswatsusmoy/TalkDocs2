# 🚀 Quick Start Guide

## Installation

1. **Install dependencies**:
   ```bash
   cd llm_benchmark_suite
   pip install -r requirements.txt
   ```

2. **Run setup script**:
   ```bash
   python setup.py
   ```

3. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Quick Examples

### 1. Run a Single Benchmark
```bash
python main.py --model gpt2 --benchmark text-generation --samples 50
```

### 2. Compare Multiple Models
```bash
python main.py --models gpt2 gpt2-medium --benchmark text-generation
```

### 3. View Leaderboard
```bash
python main.py --leaderboard text-generation
```

### 4. List Available Models
```bash
python main.py --list-models
```

### 5. Run Web Interface
```bash
streamlit run web_interface/app.py
```

## Web Interface Features

- **Dashboard**: Overview of system status and recent activity
- **Leaderboard**: View and filter benchmark results
- **Run Benchmarks**: Interactive benchmark execution
- **Model Comparison**: Compare multiple models side-by-side
- **Settings**: System configuration and monitoring

## Supported Models

- GPT-2 (various sizes)
- BERT (base, large)
- T5 (small, base, large)
- GPT-Neo (125M, 1.3B, 2.7B)
- Llama-2 (7B, 13B, 70B)
- Falcon (7B, 40B)
- MPT (7B, 30B)
- And many more from HuggingFace Hub

## Supported Benchmarks

- **Text Generation**: Story completion, text continuation
- **Text Classification**: Sentiment analysis, topic classification
- **Summarization**: Document summarization
- **Translation**: Multi-language translation
- **Question Answering**: Context-based Q&A
- **Code Generation**: Programming task completion

## Metrics

- **ROUGE**: ROUGE-1, ROUGE-2, ROUGE-L
- **BLEU**: Bilingual Evaluation Understudy
- **BLEURT**: BLEU, ROUGE, and BERT-based evaluation
- **Accuracy**: Task-specific accuracy
- **F1 Score**: Precision and recall balance
- **Latency**: Inference time measurements
- **Throughput**: Tokens per second
- **Memory Usage**: GPU/CPU memory consumption

## Configuration

Key configuration options in `config.py`:

- `default_device`: Device to use (auto, cpu, cuda, mps)
- `max_length`: Maximum sequence length
- `batch_size`: Batch size for inference
- `num_samples`: Default number of samples for benchmarks
- `save_predictions`: Whether to save model predictions

## Database

Results are automatically saved to SQLite database (`benchmark_results.db`) with:
- Model metadata
- Benchmark results
- Performance metrics
- Leaderboard rankings

## Troubleshooting

### Common Issues

1. **CUDA out of memory**: Reduce batch size or use smaller models
2. **Model loading fails**: Check internet connection and HF token
3. **Import errors**: Ensure all dependencies are installed
4. **Slow performance**: Use GPU if available, reduce sample size

### Getting Help

- Check the logs in `logs/` directory
- Run with `--verbose` flag for detailed output
- Use the web interface for easier debugging
- Check the main README.md for detailed documentation

## Next Steps

1. **Custom Benchmarks**: Add your own benchmarks in `benchmarks/`
2. **Custom Metrics**: Extend metrics in `utils/metrics.py`
3. **Custom Models**: Add models to `ModelConfig.POPULAR_MODELS`
4. **API Integration**: Use the evaluator in your own scripts
5. **Deployment**: Deploy the web interface to production

## Example Scripts

Run the example script to see all features in action:
```bash
python example.py
```

This will demonstrate:
- Single benchmark execution
- Model comparison
- Multiple benchmark runs
- Leaderboard viewing
- Model information retrieval
