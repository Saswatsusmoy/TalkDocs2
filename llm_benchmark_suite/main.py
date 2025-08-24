#!/usr/bin/env python3
"""
Main CLI entry point for the LLM Benchmarking Suite.
"""

import argparse
import json
import sys
from typing import List, Optional
from pathlib import Path

import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from utils.evaluator import BenchmarkEvaluator
from config import config, ModelConfig, BenchmarkConfigClassInstance


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="LLM Benchmarking Suite - Compare and evaluate language models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a single benchmark
  python main.py --model gpt2 --benchmark text-generation --samples 50

  # Compare multiple models
  python main.py --models gpt2 gpt2-medium --benchmark text-generation

  # Run multiple benchmarks
  python main.py --model gpt2 --benchmarks text-generation summarization

  # Show leaderboard
  python main.py --leaderboard text-generation --metric rouge1

  # List available models and benchmarks
  python main.py --list-models
  python main.py --list-benchmarks
        """
    )
    
    # Model selection
    parser.add_argument("--model", "-m", type=str, help="Model to benchmark")
    parser.add_argument("--models", "-M", nargs="+", help="Multiple models to compare")
    
    # Benchmark selection
    parser.add_argument("--benchmark", "-b", type=str, help="Benchmark to run")
    parser.add_argument("--benchmarks", "-B", nargs="+", help="Multiple benchmarks to run")
    
    # Dataset and sampling
    parser.add_argument("--dataset", "-d", type=str, help="Dataset to use")
    parser.add_argument("--samples", "-s", type=int, default=config.num_samples,
                       help=f"Number of samples (default: {config.num_samples})")
    
    # Output options
    parser.add_argument("--output", "-o", type=str, help="Output file for results")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to database")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Leaderboard options
    parser.add_argument("--leaderboard", "-l", type=str, help="Show leaderboard for benchmark")
    parser.add_argument("--metric", type=str, help="Metric for leaderboard")
    parser.add_argument("--limit", type=int, default=10, help="Number of leaderboard entries")
    
    # Information options
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--list-benchmarks", action="store_true", help="List available benchmarks")
    parser.add_argument("--model-info", type=str, help="Get information about a model")
    
    # Performance options
    parser.add_argument("--device", type=str, help="Device to use (cpu, cuda, mps, auto)")
    parser.add_argument("--batch-size", type=int, help="Batch size for inference")
    
    args = parser.parse_args()
    
    # Handle information requests
    if args.list_models:
        print("Available models:")
        for model_key in ModelConfig.list_models():
            full_name = ModelConfig.get_model_name(model_key)
            print(f"  {model_key:<20} -> {full_name}")
        return
    
    if args.list_benchmarks:
        print("Available benchmarks:")
        for benchmark_key in BenchmarkConfigClassInstance.list_benchmarks():
            info = BenchmarkConfigClassInstance.get_benchmark_info(benchmark_key)
            print(f"  {benchmark_key:<20} - {info.get('name', 'Unknown')}")
            print(f"    {info.get('description', 'No description')}")
        return
    
    if args.model_info:
        evaluator = BenchmarkEvaluator()
        info = evaluator.model_loader.get_model_info(args.model_info)
        print(f"Model information for {args.model_info}:")
        print(json.dumps(info, indent=2))
        return
    
    # Handle leaderboard request
    if args.leaderboard:
        evaluator = BenchmarkEvaluator()
        leaderboard = evaluator.get_leaderboard(args.leaderboard, args.metric, args.limit)
        
        if not leaderboard:
            print(f"No results found for benchmark '{args.leaderboard}'")
            return
        
        print(f"Leaderboard for {args.leaderboard}:")
        print(f"{'Rank':<4} {'Model':<20} {'Metric':<15} {'Value':<10} {'Timestamp':<20}")
        print("-" * 70)
        
        for entry in leaderboard:
            print(f"{entry['rank']:<4} {entry['model_name']:<20} {entry['metric_name']:<15} "
                  f"{entry['metric_value']:<10.4f} {entry['timestamp'][:19]}")
        return
    
    # Validate required arguments
    if not args.model and not args.models:
        parser.error("Either --model or --models is required")
    
    if not args.benchmark and not args.benchmarks and not args.leaderboard:
        parser.error("Either --benchmark, --benchmarks, or --leaderboard is required")
    
    # Initialize evaluator
    evaluator = BenchmarkEvaluator()
    
    try:
        # Run benchmarks
        if args.models and args.benchmark:
            # Compare multiple models on single benchmark
            print(f"Comparing models {args.models} on benchmark '{args.benchmark}'")
            results = evaluator.compare_models(args.models, args.benchmark, args.samples)
            
        elif args.model and args.benchmarks:
            # Run multiple benchmarks on single model
            print(f"Running benchmarks {args.benchmarks} on model '{args.model}'")
            results = evaluator.run_multiple_benchmarks(args.model, args.benchmarks, args.samples)
            
        elif args.model and args.benchmark:
            # Single model, single benchmark
            print(f"Running benchmark '{args.benchmark}' on model '{args.model}'")
            results = evaluator.run_benchmark(
                args.model, 
                args.benchmark, 
                args.dataset, 
                args.samples,
                save_results=not args.no_save
            )
            results = {args.benchmark: results}
        
        else:
            parser.error("Invalid combination of arguments")
        
        # Display results
        if args.verbose:
            print(json.dumps(results, indent=2))
        else:
            _print_summary(results)
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {args.output}")
    
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        evaluator.cleanup()


def _print_summary(results: dict):
    """Print a summary of benchmark results."""
    print("\n" + "="*60)
    print("BENCHMARK RESULTS SUMMARY")
    print("="*60)
    
    for benchmark_name, result in results.items():
        if "error" in result:
            print(f"\n❌ {benchmark_name}: {result['error']}")
            continue
        
        print(f"\n✅ {benchmark_name}")
        print(f"   Model: {result.get('model_name', 'Unknown')}")
        print(f"   Dataset: {result.get('dataset_name', 'Unknown')}")
        print(f"   Samples: {result.get('num_samples', 0)}")
        
        metrics = result.get('metrics', {})
        if metrics:
            print("   Metrics:")
            for metric_name, value in metrics.items():
                if isinstance(value, float):
                    print(f"     {metric_name}: {value:.4f}")
                else:
                    print(f"     {metric_name}: {value}")
        else:
            print("   No metrics available")


if __name__ == "__main__":
    main()
