"""
Inference engine for the LLM Benchmarking Suite.
"""

import time
import torch
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from transformers import GenerationConfig
import psutil

from .model_loader import ModelLoader
from config import config


class InferenceEngine:
    """Inference engine for running benchmarks on models."""
    
    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader
        self.generation_config = GenerationConfig(
            max_length=config.max_length,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=50256,  # GPT-2 pad token
        )
    
    def generate_text(self, model_name: str, prompt: str, max_length: int = None,
                     temperature: float = 0.7, top_p: float = 0.9) -> Dict[str, Any]:
        """Generate text using a loaded model."""
        try:
            # Check if model is already loaded
            from config import ModelConfig
            full_model_name = ModelConfig.get_model_name(model_name)
            if full_model_name not in self.model_loader.loaded_models:
                model, tokenizer = self.model_loader.load_model(model_name, "text-generation")
            else:
                model = self.model_loader.loaded_models[full_model_name]
                tokenizer = self.model_loader.loaded_tokenizers[full_model_name]
            
            # Update generation config
            generation_config = GenerationConfig(
                max_length=max_length or config.max_length,
                do_sample=True,
                temperature=temperature,
                top_p=top_p,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
            
            # Tokenize input
            inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            # Measure inference time
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    generation_config=generation_config,
                    return_dict_in_generate=True,
                    output_scores=False,
                )
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            # Decode output
            generated_text = tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
            
            # Calculate metrics
            latency_ms = (end_time - start_time) * 1000
            input_tokens = inputs['input_ids'].shape[1]
            output_tokens = outputs.sequences.shape[1] - input_tokens
            throughput_tps = output_tokens / (end_time - start_time) if end_time > start_time else 0
            memory_usage_mb = (end_memory - start_memory) / (1024 * 1024)
            
            return {
                "generated_text": generated_text,
                "input_text": prompt,
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "throughput_tps": throughput_tps,
                "memory_usage_mb": memory_usage_mb,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
                "latency_ms": 0,
                "throughput_tps": 0,
                "memory_usage_mb": 0
            }
    
    def classify_text(self, model_name: str, text: str, labels: List[str] = None) -> Dict[str, Any]:
        """Classify text using a loaded model."""
        try:
            model, tokenizer = self.model_loader.load_model(model_name, "text-classification")
            
            # Tokenize input
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            # Measure inference time
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            with torch.no_grad():
                outputs = model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][predicted_class].item()
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            # Get label if available
            if hasattr(model.config, 'id2label') and model.config.id2label:
                predicted_label = model.config.id2label[predicted_class]
            elif labels and predicted_class < len(labels):
                predicted_label = labels[predicted_class]
            else:
                predicted_label = f"class_{predicted_class}"
            
            # Calculate metrics
            latency_ms = (end_time - start_time) * 1000
            memory_usage_mb = (end_memory - start_memory) / (1024 * 1024)
            
            return {
                "input_text": text,
                "predicted_label": predicted_label,
                "predicted_class": predicted_class,
                "confidence": confidence,
                "probabilities": probabilities[0].tolist(),
                "latency_ms": latency_ms,
                "memory_usage_mb": memory_usage_mb,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
                "latency_ms": 0,
                "memory_usage_mb": 0
            }
    
    def summarize_text(self, model_name: str, text: str, max_length: int = 150) -> Dict[str, Any]:
        """Summarize text using a loaded model."""
        try:
            model, tokenizer = self.model_loader.load_model(model_name, "summarization")
            
            # Tokenize input
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=1024)
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            # Measure inference time
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_length=max_length,
                    min_length=30,
                    do_sample=False,
                    num_beams=4,
                    early_stopping=True,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                )
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            # Decode output
            summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Calculate metrics
            latency_ms = (end_time - start_time) * 1000
            input_tokens = inputs['input_ids'].shape[1]
            output_tokens = outputs.shape[1]
            throughput_tps = output_tokens / (end_time - start_time) if end_time > start_time else 0
            memory_usage_mb = (end_memory - start_memory) / (1024 * 1024)
            
            return {
                "input_text": text,
                "summary": summary,
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "compression_ratio": input_tokens / output_tokens if output_tokens > 0 else 0,
                "throughput_tps": throughput_tps,
                "memory_usage_mb": memory_usage_mb,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
                "latency_ms": 0,
                "throughput_tps": 0,
                "memory_usage_mb": 0
            }
    
    def translate_text(self, model_name: str, text: str, source_lang: str = "en", 
                      target_lang: str = "fr") -> Dict[str, Any]:
        """Translate text using a loaded model."""
        try:
            model, tokenizer = self.model_loader.load_model(model_name, "translation")
            
            # Add language prefix if needed
            if hasattr(tokenizer, 'src_lang'):
                tokenizer.src_lang = source_lang
            if hasattr(tokenizer, 'tgt_lang'):
                tokenizer.tgt_lang = target_lang
            
            # Tokenize input
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            # Measure inference time
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_length=512,
                    do_sample=False,
                    num_beams=5,
                    early_stopping=True,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                )
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            # Decode output
            translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Calculate metrics
            latency_ms = (end_time - start_time) * 1000
            input_tokens = inputs['input_ids'].shape[1]
            output_tokens = outputs.shape[1]
            throughput_tps = output_tokens / (end_time - start_time) if end_time > start_time else 0
            memory_usage_mb = (end_memory - start_memory) / (1024 * 1024)
            
            return {
                "input_text": text,
                "translation": translation,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "throughput_tps": throughput_tps,
                "memory_usage_mb": memory_usage_mb,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
                "latency_ms": 0,
                "throughput_tps": 0,
                "memory_usage_mb": 0
            }
    
    def answer_question(self, model_name: str, question: str, context: str) -> Dict[str, Any]:
        """Answer questions using a loaded model."""
        try:
            model, tokenizer = self.model_loader.load_model(model_name, "question-answering")
            
            # Format input for question answering
            inputs = tokenizer(
                question,
                context,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            # Measure inference time
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            with torch.no_grad():
                outputs = model(**inputs)
                answer_start = torch.argmax(outputs.start_logits)
                answer_end = torch.argmax(outputs.end_logits) + 1
                answer = tokenizer.convert_tokens_to_string(
                    tokenizer.convert_ids_to_tokens(inputs["input_ids"][0][answer_start:answer_end])
                )
                confidence = (outputs.start_logits[0][answer_start] + outputs.end_logits[0][answer_end - 1]).item()
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            # Calculate metrics
            latency_ms = (end_time - start_time) * 1000
            memory_usage_mb = (end_memory - start_memory) / (1024 * 1024)
            
            return {
                "question": question,
                "context": context,
                "answer": answer,
                "confidence": confidence,
                "answer_start": answer_start.item(),
                "answer_end": answer_end.item(),
                "latency_ms": latency_ms,
                "memory_usage_mb": memory_usage_mb,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
                "latency_ms": 0,
                "memory_usage_mb": 0
            }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in bytes."""
        process = psutil.Process()
        return process.memory_info().rss
    
    def batch_inference(self, model_name: str, task: str, inputs: List[str], 
                       batch_size: int = None) -> List[Dict[str, Any]]:
        """Run batch inference on multiple inputs."""
        batch_size = batch_size or config.batch_size
        results = []
        
        for i in range(0, len(inputs), batch_size):
            batch_inputs = inputs[i:i + batch_size]
            batch_results = []
            
            for input_text in batch_inputs:
                if task == "text-generation":
                    result = self.generate_text(model_name, input_text)
                elif task == "text-classification":
                    result = self.classify_text(model_name, input_text)
                elif task == "summarization":
                    result = self.summarize_text(model_name, input_text)
                elif task == "translation":
                    result = self.translate_text(model_name, input_text)
                elif task == "question-answering":
                    # For QA, we need question and context
                    if isinstance(input_text, dict):
                        result = self.answer_question(
                            model_name, 
                            input_text.get("question", ""), 
                            input_text.get("context", "")
                        )
                    else:
                        result = {"error": "Invalid input format for QA", "success": False}
                else:
                    result = {"error": f"Unknown task: {task}", "success": False}
                
                batch_results.append(result)
            
            results.extend(batch_results)
        
        return results
