#!/usr/bin/env python3
"""
Example usage of the LLM Benchmarking Suite.
"""

import json
from pathlib import Path

import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from utils.evaluator import BenchmarkEvaluator
from config import ModelConfig, BenchmarkConfigClassInstance


def example_single_benchmark():
    """Example: Run a single benchmark on one model."""
    print("🔬 Example: Single Benchmark")
    print("=" * 40)
    
    evaluator = BenchmarkEvaluator()
    
    try:
        # Run text generation benchmark on GPT-2
        result = evaluator.run_benchmark(
            model_name="gpt2",
            benchmark_name="text-generation",
            num_samples=10  # Small sample for demo
        )
        
        print(f"✅ Benchmark completed!")
        print(f"Model: {result['model_name']}")
        print(f"Benchmark: {result['benchmark_name']}")
        print(f"Samples: {result['num_samples']}")
        
        # Display metrics
        metrics = result.get('metrics', {})
        if metrics:
            print("\n📊 Metrics:")
            for metric_name, value in metrics.items():
                if isinstance(value, float):
                    print(f"  {metric_name}: {value:.4f}")
                else:
                    print(f"  {metric_name}: {value}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        evaluator.cleanup()


def example_model_comparison():
    """Example: Compare multiple models on the same benchmark."""
    print("\n🔬 Example: Model Comparison")
    print("=" * 40)
    
    evaluator = BenchmarkEvaluator()
    
    try:
        # Compare multiple models
        models = ["gpt2", "gpt2-medium"]
        results = evaluator.compare_models(
            model_names=models,
            benchmark_name="text-generation",
            num_samples=5  # Small sample for demo
        )
        
        print(f"✅ Comparison completed!")
        
        # Display results
        for model_name, result in results.items():
            if "error" in result:
                print(f"❌ {model_name}: {result['error']}")
            else:
                metrics = result.get('metrics', {})
                print(f"✅ {model_name}:")
                for metric_name, value in metrics.items():
                    if isinstance(value, float):
                        print(f"    {metric_name}: {value:.4f}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        evaluator.cleanup()


def example_multiple_benchmarks():
    """Example: Run multiple benchmarks on one model."""
    print("\n🔬 Example: Multiple Benchmarks")
    print("=" * 40)
    
    evaluator = BenchmarkEvaluator()
    
    try:
        # Run multiple benchmarks
        benchmarks = ["text-generation", "summarization"]
        results = evaluator.run_multiple_benchmarks(
            model_name="gpt2",
            benchmark_names=benchmarks,
            num_samples=5  # Small sample for demo
        )
        
        print(f"✅ Multiple benchmarks completed!")
        
        # Display results
        for benchmark_name, result in results.items():
            if "error" in result:
                print(f"❌ {benchmark_name}: {result['error']}")
            else:
                metrics = result.get('metrics', {})
                print(f"✅ {benchmark_name}:")
                for metric_name, value in metrics.items():
                    if isinstance(value, float):
                        print(f"    {metric_name}: {value:.4f}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        evaluator.cleanup()


def example_leaderboard():
    """Example: View leaderboard."""
    print("\n🏆 Example: Leaderboard")
    print("=" * 40)
    
    evaluator = BenchmarkEvaluator()
    
    try:
        # Get leaderboard for text generation
        leaderboard = evaluator.get_leaderboard("text-generation", limit=5)
        
        if leaderboard:
            print("📊 Text Generation Leaderboard:")
            print(f"{'Rank':<4} {'Model':<20} {'Metric':<15} {'Score':<10}")
            print("-" * 50)
            
            for entry in leaderboard:
                print(f"{entry['rank']:<4} {entry['model_name']:<20} "
                      f"{entry['metric_name']:<15} {entry['metric_value']:<10.4f}")
        else:
            print("No leaderboard data available yet.")
        
        return leaderboard
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def example_model_info():
    """Example: Get model information."""
    print("\n📋 Example: Model Information")
    print("=" * 40)
    
    evaluator = BenchmarkEvaluator()
    
    try:
        # Get info for a model
        model_name = "gpt2"
        info = evaluator.model_loader.get_model_info(model_name)
        
        print(f"📋 Model Information for {model_name}:")
        print(json.dumps(info, indent=2))
        
        return info
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def example_available_models_and_benchmarks():
    """Example: List available models and benchmarks."""
    print("\n📋 Example: Available Models and Benchmarks")
    print("=" * 50)
    
    # List models
    print("🤖 Available Models:")
    for model_key in ModelConfig.list_models()[:5]:  # Show first 5
        full_name = ModelConfig.get_model_name(model_key)
        print(f"  {model_key:<20} -> {full_name}")
    print(f"  ... and {len(ModelConfig.list_models()) - 5} more")
    
    # List benchmarks
    print("\n🔬 Available Benchmarks:")
    for benchmark_key in BenchmarkConfigClassInstance.list_benchmarks():
        info = BenchmarkConfigClassInstance.get_benchmark_info(benchmark_key)
        print(f"  {benchmark_key:<20} - {info.get('name', 'Unknown')}")
        print(f"    {info.get('description', 'No description')}")


def main():
    """Run all examples."""
    print("🤖 LLM Benchmarking Suite - Examples")
    print("=" * 50)
    
    # Show available models and benchmarks
    example_available_models_and_benchmarks()
    
    # Run examples
    print("\n" + "=" * 50)
    print("Running Examples...")
    print("=" * 50)
    
    # Single benchmark
    example_single_benchmark()
    
    # Model comparison
    example_model_comparison()
    
    # Multiple benchmarks
    example_multiple_benchmarks()
    
    # Leaderboard
    example_leaderboard()
    
    # Model info
    example_model_info()
    
    print("\n" + "=" * 50)
    print("🎉 Examples completed!")
    print("=" * 50)
    
    print("\n💡 Tips:")
    print("- Use the web interface: streamlit run web_interface/app.py")
    print("- Use the CLI: python main.py --help")
    print("- Check the README.md for more information")
    print("- Modify config.py to customize settings")


if __name__ == "__main__":
    main()
