"""
Metrics calculation for the LLM Benchmarking Suite.
"""

import re
import numpy as np
from typing import Dict, List, Optional, Any, Union
from collections import Counter
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.tokenize import word_tokenize, sent_tokenize

try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    ROUGE_AVAILABLE = False
    print("Warning: rouge-score not available. Install with: pip install rouge-score")

try:
    from sacrebleu import BLEU
    SACREBLEU_AVAILABLE = True
except ImportError:
    SACREBLEU_AVAILABLE = False
    print("Warning: sacrebleu not available. Install with: pip install sacrebleu")

try:
    from bleurt import score
    BLEURT_AVAILABLE = True
except ImportError:
    BLEURT_AVAILABLE = False
    print("Warning: BLEURT not available. Install with: pip install bleurt")

from config import config


class MetricsCalculator:
    """Comprehensive metrics calculator for LLM evaluation."""
    
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        # Initialize ROUGE scorer if available
        if ROUGE_AVAILABLE:
            self.rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        
        # Initialize BLEU scorer
        self.bleu_scorer = BLEU() if SACREBLEU_AVAILABLE else None
        self.smoothing = SmoothingFunction().method1
    
    def calculate_rouge_scores(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """Calculate ROUGE scores for text generation tasks."""
        if not ROUGE_AVAILABLE:
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
        
        rouge1_scores = []
        rouge2_scores = []
        rougeL_scores = []
        
        for pred, ref in zip(predictions, references):
            scores = self.rouge_scorer.score(ref, pred)
            rouge1_scores.append(scores['rouge1'].fmeasure)
            rouge2_scores.append(scores['rouge2'].fmeasure)
            rougeL_scores.append(scores['rougeL'].fmeasure)
        
        return {
            "rouge1": np.mean(rouge1_scores),
            "rouge2": np.mean(rouge2_scores),
            "rougeL": np.mean(rougeL_scores)
        }
    
    def calculate_bleu_score(self, predictions: List[str], references: List[str]) -> float:
        """Calculate BLEU score for text generation tasks."""
        if SACREBLEU_AVAILABLE:
            # Use sacrebleu for more robust BLEU calculation
            return self.bleu_scorer.corpus_score(predictions, [references]).score / 100.0
        else:
            # Fallback to NLTK BLEU
            bleu_scores = []
            for pred, ref in zip(predictions, references):
                pred_tokens = word_tokenize(pred.lower())
                ref_tokens = word_tokenize(ref.lower())
                bleu_scores.append(sentence_bleu([ref_tokens], pred_tokens, smoothing_function=self.smoothing))
            return np.mean(bleu_scores)
    
    def calculate_bleurt_score(self, predictions: List[str], references: List[str]) -> float:
        """Calculate BLEURT score for text generation tasks."""
        if not BLEURT_AVAILABLE:
            return 0.0
        
        try:
            # Note: This requires a BLEURT checkpoint
            # You would need to specify the checkpoint path
            scores = score(candidates=predictions, references=references)
            return np.mean(scores)
        except Exception as e:
            print(f"BLEURT calculation failed: {e}")
            return 0.0
    
    def calculate_accuracy(self, predictions: List[Any], references: List[Any]) -> float:
        """Calculate accuracy for classification tasks."""
        correct = sum(1 for pred, ref in zip(predictions, references) if pred == ref)
        return correct / len(predictions) if predictions else 0.0
    
    def calculate_f1_score(self, predictions: List[Any], references: List[Any], 
                          labels: Optional[List[str]] = None) -> Dict[str, float]:
        """Calculate F1 score for classification tasks."""
        from sklearn.metrics import f1_score, precision_score, recall_score
        
        if labels:
            # Multi-class classification
            f1_macro = f1_score(references, predictions, average='macro', zero_division=0)
            f1_micro = f1_score(references, predictions, average='micro', zero_division=0)
            f1_weighted = f1_score(references, predictions, average='weighted', zero_division=0)
            
            precision_macro = precision_score(references, predictions, average='macro', zero_division=0)
            recall_macro = recall_score(references, predictions, average='macro', zero_division=0)
            
            return {
                "f1_macro": f1_macro,
                "f1_micro": f1_micro,
                "f1_weighted": f1_weighted,
                "precision_macro": precision_macro,
                "recall_macro": recall_macro
            }
        else:
            # Binary classification
            f1 = f1_score(references, predictions, zero_division=0)
            precision = precision_score(references, predictions, zero_division=0)
            recall = recall_score(references, predictions, zero_division=0)
            
            return {
                "f1": f1,
                "precision": precision,
                "recall": recall
            }
    
    def calculate_exact_match(self, predictions: List[str], references: List[str]) -> float:
        """Calculate exact match accuracy for question answering tasks."""
        exact_matches = 0
        for pred, ref in zip(predictions, references):
            if self._normalize_answer(pred) == self._normalize_answer(ref):
                exact_matches += 1
        return exact_matches / len(predictions) if predictions else 0.0
    
    def calculate_f1_qa(self, predictions: List[str], references: List[str]) -> float:
        """Calculate F1 score for question answering tasks."""
        f1_scores = []
        for pred, ref in zip(predictions, references):
            pred_tokens = self._normalize_answer(pred).split()
            ref_tokens = self._normalize_answer(ref).split()
            
            common = Counter(pred_tokens) & Counter(ref_tokens)
            num_same = sum(common.values())
            
            if len(pred_tokens) == 0 or len(ref_tokens) == 0:
                f1_scores.append(0.0)
                continue
            
            precision = num_same / len(pred_tokens)
            recall = num_same / len(ref_tokens)
            
            if precision + recall == 0:
                f1_scores.append(0.0)
            else:
                f1_scores.append(2 * precision * recall / (precision + recall))
        
        return np.mean(f1_scores)
    
    def calculate_perplexity(self, model_outputs: List[Dict[str, Any]]) -> float:
        """Calculate perplexity for language modeling tasks."""
        total_loss = 0.0
        total_tokens = 0
        
        for output in model_outputs:
            if 'loss' in output and 'num_tokens' in output:
                total_loss += output['loss'] * output['num_tokens']
                total_tokens += output['num_tokens']
        
        if total_tokens == 0:
            return float('inf')
        
        avg_loss = total_loss / total_tokens
        return np.exp(avg_loss)
    
    def calculate_latency_metrics(self, latencies: List[float]) -> Dict[str, float]:
        """Calculate latency statistics."""
        if not latencies:
            return {"mean_latency": 0.0, "median_latency": 0.0, "p95_latency": 0.0, "p99_latency": 0.0}
        
        latencies = np.array(latencies)
        return {
            "mean_latency": np.mean(latencies),
            "median_latency": np.median(latencies),
            "p95_latency": np.percentile(latencies, 95),
            "p99_latency": np.percentile(latencies, 99),
            "min_latency": np.min(latencies),
            "max_latency": np.max(latencies),
            "std_latency": np.std(latencies)
        }
    
    def calculate_throughput_metrics(self, throughputs: List[float]) -> Dict[str, float]:
        """Calculate throughput statistics."""
        if not throughputs:
            return {"mean_throughput": 0.0, "median_throughput": 0.0, "total_tokens": 0.0}
        
        throughputs = np.array(throughputs)
        return {
            "mean_throughput": np.mean(throughputs),
            "median_throughput": np.median(throughputs),
            "min_throughput": np.min(throughputs),
            "max_throughput": np.max(throughputs),
            "std_throughput": np.std(throughputs)
        }
    
    def calculate_memory_metrics(self, memory_usage: List[float]) -> Dict[str, float]:
        """Calculate memory usage statistics."""
        if not memory_usage:
            return {"mean_memory": 0.0, "peak_memory": 0.0, "total_memory": 0.0}
        
        memory_usage = np.array(memory_usage)
        return {
            "mean_memory_mb": np.mean(memory_usage),
            "peak_memory_mb": np.max(memory_usage),
            "min_memory_mb": np.min(memory_usage),
            "std_memory_mb": np.std(memory_usage)
        }
    
    def calculate_compression_ratio(self, input_lengths: List[int], output_lengths: List[int]) -> float:
        """Calculate compression ratio for summarization tasks."""
        if not input_lengths or not output_lengths:
            return 0.0
        
        total_input = sum(input_lengths)
        total_output = sum(output_lengths)
        
        return total_output / total_input if total_input > 0 else 0.0
    
    def calculate_pass_at_k(self, predictions: List[str], references: List[str], k: int = 1) -> float:
        """Calculate pass@k for code generation tasks."""
        if k > len(predictions):
            return 0.0
        
        # This is a simplified version - in practice, you'd need to actually run the code
        # For now, we'll use exact match as a proxy
        exact_matches = sum(1 for pred, ref in zip(predictions, references) if pred.strip() == ref.strip())
        return exact_matches / len(predictions) if predictions else 0.0
    
    def _normalize_answer(self, answer: str) -> str:
        """Normalize answer for comparison."""
        # Remove articles, punctuation, and convert to lowercase
        answer = re.sub(r'\b(a|an|the)\b', ' ', answer.lower())
        answer = re.sub(r'[^\w\s]', ' ', answer)
        answer = ' '.join(answer.split())
        return answer
    
    def calculate_all_metrics(self, task: str, predictions: List[Any], references: List[Any],
                            latencies: Optional[List[float]] = None,
                            throughputs: Optional[List[float]] = None,
                            memory_usage: Optional[List[float]] = None,
                            **kwargs) -> Dict[str, float]:
        """Calculate all relevant metrics for a given task."""
        metrics = {}
        
        # Check if we have valid predictions and references
        if not predictions or not references:
            return {"error": "No predictions or references available"}
        
        # Task-specific metrics
        if task == "text-generation":
            if len(predictions) > 0 and len(references) > 0 and isinstance(predictions[0], str) and isinstance(references[0], str):
                metrics.update(self.calculate_rouge_scores(predictions, references))
                metrics["bleu"] = self.calculate_bleu_score(predictions, references)
                if config.enable_bleurt:
                    metrics["bleurt"] = self.calculate_bleurt_score(predictions, references)
        
        elif task == "text-classification":
            metrics["accuracy"] = self.calculate_accuracy(predictions, references)
            metrics.update(self.calculate_f1_score(predictions, references, kwargs.get('labels')))
        
        elif task == "summarization":
            if len(predictions) > 0 and len(references) > 0 and isinstance(predictions[0], str) and isinstance(references[0], str):
                metrics.update(self.calculate_rouge_scores(predictions, references))
                metrics["bleu"] = self.calculate_bleu_score(predictions, references)
                if 'input_lengths' in kwargs and 'output_lengths' in kwargs:
                    metrics["compression_ratio"] = self.calculate_compression_ratio(
                        kwargs['input_lengths'], kwargs['output_lengths']
                    )
        
        elif task == "translation":
            if len(predictions) > 0 and len(references) > 0 and isinstance(predictions[0], str) and isinstance(references[0], str):
                metrics["bleu"] = self.calculate_bleu_score(predictions, references)
        
        elif task == "question-answering":
            if len(predictions) > 0 and len(references) > 0 and isinstance(predictions[0], str) and isinstance(references[0], str):
                metrics["exact_match"] = self.calculate_exact_match(predictions, references)
                metrics["f1"] = self.calculate_f1_qa(predictions, references)
        
        elif task == "code-generation":
            if len(predictions) > 0 and len(references) > 0 and isinstance(predictions[0], str) and isinstance(references[0], str):
                metrics["pass@1"] = self.calculate_pass_at_k(predictions, references, k=1)
                metrics["exact_match"] = self.calculate_exact_match(predictions, references)
        
        # Performance metrics
        if latencies and config.enable_latency:
            metrics.update(self.calculate_latency_metrics(latencies))
        
        if throughputs:
            metrics.update(self.calculate_throughput_metrics(throughputs))
        
        if memory_usage:
            metrics.update(self.calculate_memory_metrics(memory_usage))
        
        return metrics
