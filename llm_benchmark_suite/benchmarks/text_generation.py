"""
Text Generation Benchmark for the LLM Benchmarking Suite.
"""

from typing import Dict, List, Any
from datasets import load_dataset
import random

from utils.metrics import MetricsCalculator


class TextGenerationBenchmark:
    """Text generation benchmark implementation."""
    
    def __init__(self):
        self.metrics_calculator = MetricsCalculator()
        self.name = "text-generation"
        self.description = "Generate text continuations"
    
    def load_dataset(self, dataset_name: str = "wikitext-2-raw-v1", split: str = "test", num_samples: int = 100):
        """Load dataset for text generation."""
        try:
            dataset = load_dataset(dataset_name, split=split)
            
            # For text generation, we need to create prompts
            prompts = []
            for i, item in enumerate(dataset):
                if i >= num_samples:
                    break
                
                text = item.get("text", "")
                if len(text) > 50:  # Only use substantial texts
                    # Create a prompt by taking the first part of the text
                    words = text.split()
                    if len(words) > 20:
                        prompt_length = random.randint(10, min(20, len(words) - 5))
                        prompt = " ".join(words[:prompt_length])
                        continuation = " ".join(words[prompt_length:])
                        
                        prompts.append({
                            "prompt": prompt,
                            "continuation": continuation,
                            "full_text": text
                        })
            
            return prompts[:num_samples]
            
        except Exception as e:
            print(f"Error loading dataset {dataset_name}: {e}")
            # Return fallback dataset
            return self._get_fallback_dataset(num_samples)
    
    def _get_fallback_dataset(self, num_samples: int) -> List[Dict[str, str]]:
        """Get fallback dataset for testing."""
        fallback_prompts = [
            {
                "prompt": "The quick brown fox jumps over the lazy dog",
                "continuation": "and continues running through the forest.",
                "full_text": "The quick brown fox jumps over the lazy dog and continues running through the forest."
            },
            {
                "prompt": "In a hole in the ground there lived a hobbit",
                "continuation": "not a nasty, dirty, wet hole.",
                "full_text": "In a hole in the ground there lived a hobbit not a nasty, dirty, wet hole."
            },
            {
                "prompt": "It was the best of times, it was the worst of times",
                "continuation": "it was the age of wisdom, it was the age of foolishness.",
                "full_text": "It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness."
            },
            {
                "prompt": "To be or not to be, that is the question",
                "continuation": "whether tis nobler in the mind to suffer.",
                "full_text": "To be or not to be, that is the question whether tis nobler in the mind to suffer."
            },
            {
                "prompt": "All happy families are alike",
                "continuation": "each unhappy family is unhappy in its own way.",
                "full_text": "All happy families are alike, each unhappy family is unhappy in its own way."
            }
        ]
        
        return fallback_prompts[:num_samples]
    
    def evaluate(self, predictions: List[str], references: List[str], 
                latencies: List[float] = None, throughputs: List[float] = None) -> Dict[str, float]:
        """Evaluate text generation results."""
        return self.metrics_calculator.calculate_all_metrics(
            "text-generation",
            predictions,
            references,
            latencies=latencies,
            throughputs=throughputs
        )
    
    def get_expected_metrics(self) -> List[str]:
        """Get list of expected metrics for this benchmark."""
        return ["rouge1", "rouge2", "rougeL", "bleu", "mean_latency", "mean_throughput"]
