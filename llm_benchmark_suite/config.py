"""
Configuration management for the LLM Benchmarking Suite.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class BenchmarkConfig(BaseSettings):
    """Configuration for benchmark settings."""
    
    # Database settings
    database_url: str = Field(default="sqlite:///benchmark_results.db", env="DATABASE_URL")
    
    # HuggingFace settings
    hf_token: Optional[str] = Field(default=None, env="HF_TOKEN")
    hf_cache_dir: str = Field(default="~/.cache/huggingface", env="HF_CACHE_DIR")
    
    # Model settings
    default_device: str = Field(default="auto", env="DEVICE")  # auto, cpu, cuda, mps
    max_length: int = Field(default=512, env="MAX_LENGTH")
    batch_size: int = Field(default=1, env="BATCH_SIZE")
    
    # Benchmark settings
    num_samples: int = Field(default=100, env="NUM_SAMPLES")
    timeout_seconds: int = Field(default=300, env="TIMEOUT_SECONDS")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    
    # Metrics settings
    enable_rouge: bool = Field(default=True, env="ENABLE_ROUGE")
    enable_bleu: bool = Field(default=True, env="ENABLE_BLEU")
    enable_bleurt: bool = Field(default=True, env="ENABLE_BLEURT")
    enable_latency: bool = Field(default=True, env="ENABLE_LATENCY")
    
    # Web interface settings
    web_port: int = Field(default=8501, env="WEB_PORT")
    web_host: str = Field(default="localhost", env="WEB_HOST")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Output settings
    results_dir: str = Field(default="./results", env="RESULTS_DIR")
    save_predictions: bool = Field(default=True, env="SAVE_PREDICTIONS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class ModelConfig:
    """Configuration for specific models."""
    
    # Popular models for quick access
    POPULAR_MODELS = {
        "gpt2": "gpt2",
        "gpt2-medium": "gpt2-medium",
        "gpt2-large": "gpt2-large",
        "gpt2-xl": "gpt2-xl",
        "bert-base-uncased": "bert-base-uncased",
        "bert-large-uncased": "bert-large-uncased",
        "t5-small": "t5-small",
        "t5-base": "t5-base",
        "t5-large": "t5-large",
        "gpt-neo-125m": "EleutherAI/gpt-neo-125M",
        "gpt-neo-1.3b": "EleutherAI/gpt-neo-1.3B",
        "gpt-neo-2.7b": "EleutherAI/gpt-neo-2.7B",
        "llama-7b": "meta-llama/Llama-2-7b-hf",
        "llama-13b": "meta-llama/Llama-2-13b-hf",
        "llama-70b": "meta-llama/Llama-2-70b-hf",
        "falcon-7b": "tiiuae/falcon-7b",
        "falcon-40b": "tiiuae/falcon-40b",
        "mpt-7b": "mosaicml/mpt-7b",
        "mpt-30b": "mosaicml/mpt-30b",
    }
    
    @classmethod
    def get_model_name(cls, model_key: str) -> str:
        """Get the full model name from a key."""
        return cls.POPULAR_MODELS.get(model_key, model_key)
    
    @classmethod
    def list_models(cls) -> List[str]:
        """List all available model keys."""
        return list(cls.POPULAR_MODELS.keys())


class BenchmarkConfigClass:
    """Configuration for available benchmarks."""
    
    AVAILABLE_BENCHMARKS = {
        "text-generation": {
            "name": "Text Generation",
            "description": "Generate text continuations",
            "metrics": ["perplexity", "latency", "throughput"],
            "datasets": ["wikitext-2-raw-v1", "ptb_text_only"]
        },
        "text-classification": {
            "name": "Text Classification",
            "description": "Classify text into categories",
            "metrics": ["accuracy", "f1", "precision", "recall"],
            "datasets": ["glue", "sst2", "ag_news"]
        },
        "summarization": {
            "name": "Text Summarization",
            "description": "Generate summaries of documents",
            "metrics": ["rouge1", "rouge2", "rougeL", "bleu"],
            "datasets": ["cnn_dailymail", "xsum", "samsum"]
        },
        "translation": {
            "name": "Machine Translation",
            "description": "Translate text between languages",
            "metrics": ["bleu", "sacrebleu"],
            "datasets": ["wmt14", "wmt16", "opus_books"]
        },
        "question-answering": {
            "name": "Question Answering",
            "description": "Answer questions based on context",
            "metrics": ["exact_match", "f1"],
            "datasets": ["squad", "squad_v2", "hotpot_qa"]
        },
        "code-generation": {
            "name": "Code Generation",
            "description": "Generate code from natural language",
            "metrics": ["pass@k", "bleu", "exact_match"],
            "datasets": ["code_search_net", "conala", "mbpp"]
        }
    }
    
    @classmethod
    def get_benchmark_info(cls, benchmark_name: str) -> Dict:
        """Get information about a specific benchmark."""
        return cls.AVAILABLE_BENCHMARKS.get(benchmark_name, {})
    
    @classmethod
    def list_benchmarks(cls) -> List[str]:
        """List all available benchmarks."""
        return list(cls.AVAILABLE_BENCHMARKS.keys())


# Create instance for backward compatibility
BenchmarkConfigClassInstance = BenchmarkConfigClass()


# Global configuration instance
config = BenchmarkConfig()

# Ensure results directory exists
Path(config.results_dir).mkdir(parents=True, exist_ok=True)

# Export for use in other modules
__all__ = ['config', 'BenchmarkConfigClassInstance', 'ModelConfig', 'BenchmarkConfig']
