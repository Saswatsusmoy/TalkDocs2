"""
Model loader for the LLM Benchmarking Suite with HuggingFace MCP integration.
"""

import os
import time
import psutil
import torch
from typing import Dict, List, Optional, Tuple, Any
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification, AutoModelForQuestionAnswering,
    AutoModelForTokenClassification, pipeline
)
from huggingface_hub import snapshot_download, hf_hub_download
import gc

from config import config, ModelConfig


class ModelLoader:
    """Model loader with HuggingFace MCP integration."""
    
    def __init__(self, device: Optional[str] = None):
        self.device = device or self._get_device()
        self.loaded_models: Dict[str, Any] = {}
        self.loaded_tokenizers: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict] = {}
        
    def _get_device(self) -> str:
        """Determine the best available device."""
        if config.default_device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return config.default_device
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get model information from HuggingFace Hub."""
        try:
            # Get the full model name
            full_model_name = ModelConfig.get_model_name(model_name)
            
            # Download model info
            model_info = snapshot_download(
                repo_id=full_model_name,
                cache_dir=config.hf_cache_dir,
                token=config.hf_token,
                local_files_only=False
            )
            
            # Try to get model card info
            try:
                from huggingface_hub import model_info as get_model_info
                info = get_model_info(full_model_name, token=config.hf_token)
                return {
                    "name": full_model_name,
                    "architecture": info.model_type if hasattr(info, 'model_type') else None,
                    "parameters": info.safetensors.get('total') if hasattr(info, 'safetensors') else None,
                    "tags": info.tags if hasattr(info, 'tags') else [],
                    "downloads": info.downloads if hasattr(info, 'downloads') else 0,
                    "likes": info.likes if hasattr(info, 'likes') else 0,
                }
            except Exception:
                return {
                    "name": full_model_name,
                    "architecture": None,
                    "parameters": None,
                    "tags": [],
                    "downloads": 0,
                    "likes": 0,
                }
                
        except Exception as e:
            print(f"Error getting model info for {model_name}: {e}")
            return {"name": model_name, "error": str(e)}
    
    def load_model(self, model_name: str, task: str = "text-generation") -> Tuple[Any, Any]:
        """Load a model and tokenizer for a specific task."""
        full_model_name = ModelConfig.get_model_name(model_name)
        
        # Check if already loaded
        if full_model_name in self.loaded_models:
            return self.loaded_models[full_model_name], self.loaded_tokenizers[full_model_name]
        
        print(f"Loading model: {full_model_name}")
        start_time = time.time()
        
        try:
            # Load tokenizer with better error handling
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    full_model_name,
                    cache_dir=config.hf_cache_dir,
                    token=config.hf_token,
                    trust_remote_code=True
                )
            except Exception as e:
                print(f"Error loading tokenizer with cache, trying without cache: {e}")
                # Try without cache if there are cache issues
                tokenizer = AutoTokenizer.from_pretrained(
                    full_model_name,
                    token=config.hf_token,
                    trust_remote_code=True
                )
            
            # Add padding token if not present
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model based on task
            if task == "text-generation":
                try:
                    model = AutoModelForCausalLM.from_pretrained(
                        full_model_name,
                        cache_dir=config.hf_cache_dir,
                        token=config.hf_token,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        device_map="auto" if self.device == "cuda" else None,
                        trust_remote_code=True
                    )
                except Exception as e:
                    print(f"Error loading model with cache, trying without cache: {e}")
                    # Try without cache if there are cache issues
                    model = AutoModelForCausalLM.from_pretrained(
                        full_model_name,
                        token=config.hf_token,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        device_map="auto" if self.device == "cuda" else None,
                        trust_remote_code=True
                    )
            elif task == "text-classification":
                model = AutoModelForSequenceClassification.from_pretrained(
                    full_model_name,
                    cache_dir=config.hf_cache_dir,
                    token=config.hf_token,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map="auto" if self.device == "cuda" else None,
                    trust_remote_code=True
                )
            elif task == "summarization":
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    full_model_name,
                    cache_dir=config.hf_cache_dir,
                    token=config.hf_token,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map="auto" if self.device == "cuda" else None,
                    trust_remote_code=True
                )
            elif task == "translation":
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    full_model_name,
                    cache_dir=config.hf_cache_dir,
                    token=config.hf_token,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map="auto" if self.device == "cuda" else None,
                    trust_remote_code=True
                )
            elif task == "question-answering":
                model = AutoModelForQuestionAnswering.from_pretrained(
                    full_model_name,
                    cache_dir=config.hf_cache_dir,
                    token=config.hf_token,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map="auto" if self.device == "cuda" else None,
                    trust_remote_code=True
                )
            else:
                # Default to causal LM
                model = AutoModelForCausalLM.from_pretrained(
                    full_model_name,
                    cache_dir=config.hf_cache_dir,
                    token=config.hf_token,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map="auto" if self.device == "cuda" else None,
                    trust_remote_code=True
                )
            
            # Move to device if not using device_map
            if self.device != "cuda" or model.device_map is None:
                model = model.to(self.device)
            
            # Set to evaluation mode
            model.eval()
            
            # Store loaded model and tokenizer
            self.loaded_models[full_model_name] = model
            self.loaded_tokenizers[full_model_name] = tokenizer
            
            # Store metadata
            self.model_metadata[full_model_name] = {
                "task": task,
                "device": self.device,
                "load_time": time.time() - start_time,
                "parameters": sum(p.numel() for p in model.parameters()),
                "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
            }
            
            print(f"Model loaded successfully in {time.time() - start_time:.2f}s")
            return model, tokenizer
            
        except Exception as e:
            print(f"Error loading model {full_model_name}: {e}")
            raise
    
    def load_pipeline(self, model_name: str, task: str) -> Any:
        """Load a HuggingFace pipeline for a specific task."""
        full_model_name = ModelConfig.get_model_name(model_name)
        
        try:
            pipe = pipeline(
                task,
                model=full_model_name,
                tokenizer=full_model_name,
                device=self.device,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                token=config.hf_token,
                trust_remote_code=True
            )
            return pipe
        except Exception as e:
            print(f"Error loading pipeline for {full_model_name}: {e}")
            raise
    
    def unload_model(self, model_name: str):
        """Unload a model to free memory."""
        full_model_name = ModelConfig.get_model_name(model_name)
        
        if full_model_name in self.loaded_models:
            del self.loaded_models[full_model_name]
            del self.loaded_tokenizers[full_model_name]
            if full_model_name in self.model_metadata:
                del self.model_metadata[full_model_name]
            
            # Force garbage collection
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            print(f"Model {full_model_name} unloaded")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage."""
        memory_info = {}
        
        # System memory
        system_memory = psutil.virtual_memory()
        memory_info["system_total_gb"] = system_memory.total / (1024**3)
        memory_info["system_available_gb"] = system_memory.available / (1024**3)
        memory_info["system_used_gb"] = system_memory.used / (1024**3)
        memory_info["system_percent"] = system_memory.percent
        
        # GPU memory if available
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory
            gpu_memory_allocated = torch.cuda.memory_allocated(0)
            gpu_memory_reserved = torch.cuda.memory_reserved(0)
            
            memory_info["gpu_total_gb"] = gpu_memory / (1024**3)
            memory_info["gpu_allocated_gb"] = gpu_memory_allocated / (1024**3)
            memory_info["gpu_reserved_gb"] = gpu_memory_reserved / (1024**3)
            memory_info["gpu_percent"] = (gpu_memory_allocated / gpu_memory) * 100
        
        return memory_info
    
    def list_loaded_models(self) -> List[str]:
        """List currently loaded models."""
        return list(self.loaded_models.keys())
    
    def get_model_metadata(self, model_name: str) -> Dict[str, Any]:
        """Get metadata for a loaded model."""
        full_model_name = ModelConfig.get_model_name(model_name)
        return self.model_metadata.get(full_model_name, {})
    
    def clear_all_models(self):
        """Clear all loaded models."""
        for model_name in list(self.loaded_models.keys()):
            self.unload_model(model_name)
