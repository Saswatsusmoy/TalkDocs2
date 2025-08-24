"""
Database management for the LLM Benchmarking Suite.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

from config import config

Base = declarative_base()


class Model(Base):
    """Model metadata table."""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(500), nullable=False)
    architecture = Column(String(100))
    parameters = Column(Integer)  # Number of parameters in millions
    tokenizer = Column(String(100))
    max_length = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Benchmark(Base):
    """Benchmark metadata table."""
    __tablename__ = "benchmarks"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    dataset = Column(String(100))
    metrics = Column(JSON)  # List of metrics used
    created_at = Column(DateTime, default=func.now())


class BenchmarkResult(Base):
    """Benchmark results table."""
    __tablename__ = "benchmark_results"
    
    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, nullable=False)
    benchmark_id = Column(Integer, nullable=False)
    dataset = Column(String(100))
    metrics = Column(JSON)  # Dictionary of metric results
    predictions = Column(JSON)  # Model predictions (if saved)
    latency_ms = Column(Float)
    throughput_tps = Column(Float)  # Tokens per second
    memory_usage_mb = Column(Float)
    timestamp = Column(DateTime, default=func.now())
    
    # Foreign key relationships
    model = None  # Will be set up in relationship
    benchmark = None  # Will be set up in relationship


class Leaderboard(Base):
    """Leaderboard table for tracking top performers."""
    __tablename__ = "leaderboard"
    
    id = Column(Integer, primary_key=True)
    benchmark_name = Column(String(100), nullable=False)
    model_name = Column(String(255), nullable=False)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    rank = Column(Integer)
    timestamp = Column(DateTime, default=func.now())


class DatabaseManager:
    """Database manager for the benchmarking suite."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or config.database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def add_model(self, name: str, full_name: str, architecture: str = None, 
                  parameters: int = None, tokenizer: str = None, max_length: int = None) -> Model:
        """Add a new model to the database."""
        with self.get_session() as session:
            model = Model(
                name=name,
                full_name=full_name,
                architecture=architecture,
                parameters=parameters,
                tokenizer=tokenizer,
                max_length=max_length
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return model
    
    def get_model(self, name: str) -> Optional[Model]:
        """Get a model by name."""
        with self.get_session() as session:
            return session.query(Model).filter(Model.name == name).first()
    
    def add_benchmark(self, name: str, description: str = None, dataset: str = None, 
                     metrics: List[str] = None) -> Benchmark:
        """Add a new benchmark to the database."""
        with self.get_session() as session:
            benchmark = Benchmark(
                name=name,
                description=description,
                dataset=dataset,
                metrics=metrics or []
            )
            session.add(benchmark)
            session.commit()
            session.refresh(benchmark)
            return benchmark
    
    def get_benchmark(self, name: str) -> Optional[Benchmark]:
        """Get a benchmark by name."""
        with self.get_session() as session:
            return session.query(Benchmark).filter(Benchmark.name == name).first()
    
    def save_result(self, model_name: str, benchmark_name: str, dataset: str,
                   metrics: Dict[str, float], predictions: List[str] = None,
                   latency_ms: float = None, throughput_tps: float = None,
                   memory_usage_mb: float = None) -> BenchmarkResult:
        """Save benchmark results to the database."""
        with self.get_session() as session:
            # Get or create model
            model = self.get_model(model_name)
            if not model:
                model = self.add_model(model_name, model_name)
            
            # Get or create benchmark
            benchmark = self.get_benchmark(benchmark_name)
            if not benchmark:
                benchmark = self.add_benchmark(benchmark_name)
            
            result = BenchmarkResult(
                model_id=model.id,
                benchmark_id=benchmark.id,
                dataset=dataset,
                metrics=metrics,
                predictions=predictions if config.save_predictions else None,
                latency_ms=latency_ms,
                throughput_tps=throughput_tps,
                memory_usage_mb=memory_usage_mb
            )
            
            session.add(result)
            session.commit()
            session.refresh(result)
            
            # Update leaderboard
            self._update_leaderboard(session, benchmark_name, model_name, metrics)
            
            return result
    
    def _update_leaderboard(self, session: Session, benchmark_name: str, 
                           model_name: str, metrics: Dict[str, float]):
        """Update the leaderboard with new results."""
        for metric_name, metric_value in metrics.items():
            # Skip non-numeric metrics
            if not isinstance(metric_value, (int, float)) or isinstance(metric_value, bool):
                continue
                
            # Get current rank
            existing_entries = session.query(Leaderboard).filter(
                Leaderboard.benchmark_name == benchmark_name,
                Leaderboard.metric_name == metric_name
            ).order_by(Leaderboard.metric_value.desc()).all()
            
            # Find if this model already has an entry
            existing_entry = None
            for entry in existing_entries:
                if entry.model_name == model_name:
                    existing_entry = entry
                    break
            
            if existing_entry:
                # Update existing entry
                existing_entry.metric_value = float(metric_value)
                existing_entry.timestamp = datetime.now()
            else:
                # Create new entry
                entry = Leaderboard(
                    benchmark_name=benchmark_name,
                    model_name=model_name,
                    metric_name=metric_name,
                    metric_value=float(metric_value)
                )
                session.add(entry)
                existing_entries.append(entry)
            
            # Recalculate ranks
            existing_entries.sort(key=lambda x: x.metric_value, reverse=True)
            for i, entry in enumerate(existing_entries):
                entry.rank = i + 1
        
        session.commit()
    
    def get_leaderboard(self, benchmark_name: str, metric_name: str = None, 
                       limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard entries for a benchmark."""
        with self.get_session() as session:
            query = session.query(Leaderboard).filter(
                Leaderboard.benchmark_name == benchmark_name
            )
            
            if metric_name:
                query = query.filter(Leaderboard.metric_name == metric_name)
            
            entries = query.order_by(Leaderboard.rank).limit(limit).all()
            
            return [
                {
                    "rank": entry.rank,
                    "model_name": entry.model_name,
                    "metric_name": entry.metric_name,
                    "metric_value": entry.metric_value,
                    "timestamp": entry.timestamp.isoformat()
                }
                for entry in entries
            ]
    
    def get_model_results(self, model_name: str, benchmark_name: str = None) -> List[Dict[str, Any]]:
        """Get all results for a specific model."""
        with self.get_session() as session:
            query = session.query(BenchmarkResult).join(Model).filter(Model.name == model_name)
            
            if benchmark_name:
                query = query.join(Benchmark).filter(Benchmark.name == benchmark_name)
            
            results = query.order_by(BenchmarkResult.timestamp.desc()).all()
            
            return [
                {
                    "id": result.id,
                    "benchmark_name": result.benchmark.name if result.benchmark else None,
                    "dataset": result.dataset,
                    "metrics": result.metrics,
                    "latency_ms": result.latency_ms,
                    "throughput_tps": result.throughput_tps,
                    "memory_usage_mb": result.memory_usage_mb,
                    "timestamp": result.timestamp.isoformat()
                }
                for result in results
            ]
    
    def get_benchmark_history(self, benchmark_name: str, model_name: str = None) -> List[Dict[str, Any]]:
        """Get historical results for a benchmark."""
        with self.get_session() as session:
            query = session.query(BenchmarkResult).join(Benchmark).filter(
                Benchmark.name == benchmark_name
            )
            
            if model_name:
                query = query.join(Model).filter(Model.name == model_name)
            
            results = query.order_by(BenchmarkResult.timestamp.desc()).all()
            
            return [
                {
                    "model_name": result.model.name if result.model else None,
                    "dataset": result.dataset,
                    "metrics": result.metrics,
                    "timestamp": result.timestamp.isoformat()
                }
                for result in results
            ]


# Global database manager instance
db_manager = DatabaseManager()
