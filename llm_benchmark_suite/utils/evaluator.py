"""
Benchmark evaluator for the LLM Benchmarking Suite.
"""

import time
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from tqdm import tqdm
import numpy as np

from models.model_loader import ModelLoader
from models.inference import InferenceEngine
from utils.metrics import MetricsCalculator
from database import db_manager
from config import config, BenchmarkConfigClassInstance


class BenchmarkEvaluator:
    """Main evaluator for running benchmarks on models."""
    
    def __init__(self):
        self.model_loader = ModelLoader()
        self.inference_engine = InferenceEngine(self.model_loader)
        self.metrics_calculator = MetricsCalculator()
    
    def run_benchmark(self, model_name: str, benchmark_name: str, dataset_name: str = None,
                     num_samples: int = None, save_results: bool = True) -> Dict[str, Any]:
        """Run a complete benchmark on a model."""
        print(f"Running benchmark '{benchmark_name}' on model '{model_name}'")
        
        # Get benchmark configuration
        benchmark_info = BenchmarkConfigClassInstance.get_benchmark_info(benchmark_name)
        if not benchmark_info:
            raise ValueError(f"Unknown benchmark: {benchmark_name}")
        
        # Load dataset
        dataset = self._load_dataset(benchmark_name, dataset_name, num_samples or config.num_samples)
        
        # Run inference
        print(f"Running inference on {len(dataset)} samples...")
        results = self._run_inference(model_name, benchmark_name, dataset)
        
        # Calculate metrics
        print("Calculating metrics...")
        metrics = self._calculate_metrics(benchmark_name, results, dataset)
        
        # Save results
        if save_results:
            self._save_results(model_name, benchmark_name, dataset_name, metrics, results)
        
        return {
            "model_name": model_name,
            "benchmark_name": benchmark_name,
            "dataset_name": dataset_name,
            "num_samples": len(dataset),
            "metrics": metrics,
            "results": results if config.save_predictions else None
        }
    
    def run_multiple_benchmarks(self, model_name: str, benchmark_names: List[str],
                               num_samples: int = None) -> Dict[str, Any]:
        """Run multiple benchmarks on a model."""
        all_results = {}
        
        for benchmark_name in benchmark_names:
            try:
                result = self.run_benchmark(model_name, benchmark_name, num_samples=num_samples)
                all_results[benchmark_name] = result
            except Exception as e:
                print(f"Error running benchmark {benchmark_name}: {e}")
                all_results[benchmark_name] = {"error": str(e)}
        
        return all_results
    
    def compare_models(self, model_names: List[str], benchmark_name: str,
                      num_samples: int = None) -> Dict[str, Any]:
        """Compare multiple models on a single benchmark."""
        comparison_results = {}
        
        for model_name in model_names:
            try:
                result = self.run_benchmark(model_name, benchmark_name, num_samples=num_samples)
                comparison_results[model_name] = result
            except Exception as e:
                print(f"Error running benchmark on {model_name}: {e}")
                comparison_results[model_name] = {"error": str(e)}
        
        return comparison_results
    
    def _load_dataset(self, benchmark_name: str, dataset_name: str = None, 
                     num_samples: int = None) -> List[Dict[str, Any]]:
        """Load dataset for a benchmark."""
        from datasets import load_dataset
        
        # Determine dataset name
        if not dataset_name:
            benchmark_info = BenchmarkConfigClassInstance.get_benchmark_info(benchmark_name)
            dataset_name = benchmark_info.get("datasets", [None])[0]
        
        if not dataset_name:
            raise ValueError(f"No dataset specified for benchmark {benchmark_name}")
        
        try:
            # Load dataset from HuggingFace datasets
            dataset = load_dataset(dataset_name, split="test")
            
            # Limit number of samples
            if num_samples and len(dataset) > num_samples:
                dataset = dataset.select(range(num_samples))
            
            # Convert to list of dictionaries
            dataset_list = []
            for item in dataset:
                dataset_list.append(dict(item))
            
            return dataset_list
            
        except Exception as e:
            print(f"Error loading dataset {dataset_name}: {e}")
            # Return a simple test dataset as fallback
            return self._get_fallback_dataset(benchmark_name, num_samples or 10)
    
    def _get_fallback_dataset(self, benchmark_name: str, num_samples: int) -> List[Dict[str, Any]]:
        """Get a fallback dataset for testing."""
        if benchmark_name == "text-generation":
            samples = [
                {"text": "The quick brown fox jumps over the lazy dog."},
                {"text": "In a hole in the ground there lived a hobbit."},
                {"text": "It was the best of times, it was the worst of times."},
                {"text": "To be or not to be, that is the question."},
                {"text": "All happy families are alike; each unhappy family is unhappy in its own way."},
            ]
            return samples[:min(num_samples, len(samples))]
        
        elif benchmark_name == "text-classification":
            return [
                {"text": "I love this movie!", "label": 1},
                {"text": "This is terrible.", "label": 0},
                {"text": "Amazing performance!", "label": 1},
            ][:num_samples]
        
        elif benchmark_name == "summarization":
            return [
                {
                    "text": "The quick brown fox jumps over the lazy dog. The fox was very quick and agile.",
                    "summary": "A quick fox jumps over a lazy dog."
                },
                {
                    "text": "In a hole in the ground there lived a hobbit. Not a nasty, dirty, wet hole.",
                    "summary": "A hobbit lives in a comfortable hole."
                },
            ][:num_samples]
        
        elif benchmark_name == "translation":
            return [
                {"text": "Hello, how are you?", "translation": "Bonjour, comment allez-vous?"},
                {"text": "The weather is nice today.", "translation": "Le temps est beau aujourd'hui."},
            ][:num_samples]
        
        elif benchmark_name == "question-answering":
            return [
                {
                    "question": "What color is the fox?",
                    "context": "The quick brown fox jumps over the lazy dog.",
                    "answer": "brown"
                },
                {
                    "question": "Where does the hobbit live?",
                    "context": "In a hole in the ground there lived a hobbit.",
                    "answer": "in a hole in the ground"
                },
            ][:num_samples]
        
        else:
            return [{"text": "Sample text for testing."}] * num_samples
    
    def _run_inference(self, model_name: str, benchmark_name: str, 
                      dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run inference on the dataset."""
        results = []
        
        for i, item in enumerate(tqdm(dataset, desc="Running inference")):
            try:
                if benchmark_name == "text-generation":
                    result = self.inference_engine.generate_text(
                        model_name, item.get("text", "")
                    )
                
                elif benchmark_name == "text-classification":
                    result = self.inference_engine.classify_text(
                        model_name, item.get("text", "")
                    )
                
                elif benchmark_name == "summarization":
                    result = self.inference_engine.summarize_text(
                        model_name, item.get("text", "")
                    )
                
                elif benchmark_name == "translation":
                    result = self.inference_engine.translate_text(
                        model_name, item.get("text", "")
                    )
                
                elif benchmark_name == "question-answering":
                    result = self.inference_engine.answer_question(
                        model_name, 
                        item.get("question", ""), 
                        item.get("context", "")
                    )
                
                else:
                    # Default to text generation
                    result = self.inference_engine.generate_text(
                        model_name, str(item)
                    )
                
                # Add dataset item info
                result["dataset_item"] = item
                result["sample_index"] = i
                results.append(result)
                
            except Exception as e:
                print(f"Error processing sample {i}: {e}")
                results.append({
                    "error": str(e),
                    "success": False,
                    "dataset_item": item,
                    "sample_index": i
                })
        
        return results
    
    def _calculate_metrics(self, benchmark_name: str, results: List[Dict[str, Any]], 
                          dataset: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate metrics for the benchmark results."""
        # Extract predictions and references
        predictions = []
        references = []
        latencies = []
        throughputs = []
        memory_usage = []
        
        for result in results:
            if not result.get("success", False):
                continue
            
            # Extract predictions based on benchmark type
            if benchmark_name == "text-generation":
                pred = result.get("generated_text", "")
                ref = result.get("dataset_item", {}).get("text", "")
                predictions.append(pred)
                references.append(ref)
            
            elif benchmark_name == "text-classification":
                pred = result.get("predicted_label", "")
                ref = result.get("dataset_item", {}).get("label", "")
                predictions.append(pred)
                references.append(ref)
            
            elif benchmark_name == "summarization":
                pred = result.get("summary", "")
                ref = result.get("dataset_item", {}).get("summary", "")
                predictions.append(pred)
                references.append(ref)
            
            elif benchmark_name == "translation":
                pred = result.get("translation", "")
                ref = result.get("dataset_item", {}).get("translation", "")
                predictions.append(pred)
                references.append(ref)
            
            elif benchmark_name == "question-answering":
                pred = result.get("answer", "")
                ref = result.get("dataset_item", {}).get("answer", "")
                predictions.append(pred)
                references.append(ref)
            
            # Extract performance metrics
            if "latency_ms" in result:
                latencies.append(result["latency_ms"])
            if "throughput_tps" in result:
                throughputs.append(result["throughput_tps"])
            if "memory_usage_mb" in result:
                memory_usage.append(result["memory_usage_mb"])
        
        # Calculate all metrics
        metrics = self.metrics_calculator.calculate_all_metrics(
            benchmark_name,
            predictions,
            references,
            latencies=latencies if latencies else None,
            throughputs=throughputs if throughputs else None,
            memory_usage=memory_usage if memory_usage else None
        )
        
        return metrics
    
    def _save_results(self, model_name: str, benchmark_name: str, dataset_name: str,
                     metrics: Dict[str, float], results: List[Dict[str, Any]]):
        """Save results to database and file system."""
        # Save to database
        try:
            db_manager.save_result(
                model_name=model_name,
                benchmark_name=benchmark_name,
                dataset=dataset_name or "unknown",
                metrics=metrics,
                predictions=[r.get("generated_text", r.get("summary", r.get("translation", ""))) 
                           for r in results if r.get("success", False)],
                latency_ms=metrics.get("mean_latency", 0),
                throughput_tps=metrics.get("mean_throughput", 0),
                memory_usage_mb=metrics.get("mean_memory_mb", 0)
            )
        except Exception as e:
            print(f"Error saving to database: {e}")
        
        # Save to file system
        try:
            results_dir = Path(config.results_dir)
            results_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = int(time.time())
            filename = f"{model_name}_{benchmark_name}_{timestamp}.json"
            filepath = results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump({
                    "model_name": model_name,
                    "benchmark_name": benchmark_name,
                    "dataset_name": dataset_name,
                    "timestamp": timestamp,
                    "metrics": metrics,
                    "results": results if config.save_predictions else None
                }, f, indent=2)
            
            print(f"Results saved to {filepath}")
            
        except Exception as e:
            print(f"Error saving to file: {e}")
    
    def get_leaderboard(self, benchmark_name: str, metric_name: str = None, 
                       limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard for a benchmark."""
        return db_manager.get_leaderboard(benchmark_name, metric_name, limit)
    
    def get_model_results(self, model_name: str, benchmark_name: str = None) -> List[Dict[str, Any]]:
        """Get all results for a model."""
        return db_manager.get_model_results(model_name, benchmark_name)
    
    def get_benchmark_history(self, benchmark_name: str, model_name: str = None) -> List[Dict[str, Any]]:
        """Get historical results for a benchmark."""
        return db_manager.get_benchmark_history(benchmark_name, model_name)
    
    def cleanup(self):
        """Clean up resources."""
        self.model_loader.clear_all_models()
