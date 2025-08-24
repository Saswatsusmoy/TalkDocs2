# LLM Benchmarking Suite

A comprehensive, HuggingFace MCP-based benchmarking suite for comparing Large Language Models (LLMs) and maintaining a leaderboard of model performance.

## Features

- **Multi-Model Support**: Benchmark any model available on HuggingFace Hub
- **Comprehensive Metrics**: ROUGE, BLEU, BLEURT, accuracy, latency, and custom metrics
- **Leaderboard System**: Track and compare model performance over time
- **Web Interface**: Beautiful dashboard for visualizing results
- **MCP Integration**: Seamless integration with HuggingFace Model Context Protocol
- **Extensible**: Easy to add new benchmarks and metrics
- **Database Storage**: Persistent storage of results and model metadata

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Web Interface**:
   ```bash
   streamlit run web_interface/app.py
   ```

3. **Run Benchmarks**:
   ```bash
   python main.py --model gpt2 --benchmark text-generation
   ```

## Architecture

```
llm_benchmark_suite/
├── benchmarks/          # Benchmark implementations
├── datasets/           # Benchmark datasets
├── models/             # Model loading and inference
├── utils/              # Utility functions
├── web_interface/      # Streamlit web app
├── main.py            # Main CLI entry point
├── config.py          # Configuration management
└── database.py        # Database operations
```

## Supported Benchmarks

- **Text Generation**: Story completion, question answering
- **Text Classification**: Sentiment analysis, topic classification
- **Summarization**: Document summarization
- **Translation**: Multi-language translation
- **Code Generation**: Programming task completion
- **Reasoning**: Mathematical and logical reasoning

## Metrics

- **ROUGE**: Recall-Oriented Understudy for Gisting Evaluation
- **BLEU**: Bilingual Evaluation Understudy
- **BLEURT**: BLEU, ROUGE, and BERT-based evaluation
- **Accuracy**: Task-specific accuracy metrics
- **Latency**: Inference time measurements
- **Throughput**: Tokens per second
- **Memory Usage**: GPU/CPU memory consumption

## Leaderboard

The leaderboard tracks:
- Model performance across different benchmarks
- Historical performance trends
- Model metadata (size, architecture, training data)
- Cost analysis (inference cost per token)

## Contributing

1. Add new benchmarks in `benchmarks/`
2. Add new datasets in `datasets/`
3. Extend metrics in `utils/metrics.py`
4. Update the web interface in `web_interface/`

## License

MIT License - see LICENSE file for details.
