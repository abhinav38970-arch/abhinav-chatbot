"""
Performance Monitoring Dashboard

This system tracks and analyzes performance metrics for:
- Retrieval speed and quality
- Validation performance
- System health
- User satisfaction

Features:
- Real-time performance tracking
- Quality metrics dashboard
- Anomaly detection
- Historical trends
- Alert system
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import statistics
from datetime import datetime, timedelta

logger = logging.getLogger("performance_monitor")

@dataclass
class PerformanceMetric:
    """Structured performance metric"""
    operation: str
    duration_ms: float
    timestamp: str
    quality_score: Optional[float] = None
    success: bool = True
    metadata: Optional[Dict] = None

class PerformanceMonitor:
    """Comprehensive performance monitoring system"""
    
    def __init__(self):
        # Performance thresholds
        self.thresholds = {
            'retrieval_speed': {'max': 500, 'warning': 300},  # ms
            'validation_speed': {'max': 200, 'warning': 100},  # ms
            'quality_score': {'min': 0.75, 'warning': 0.85},
            'success_rate': {'min': 0.95, 'warning': 0.98}
        }
        
        # Performance tracking
        self.metrics = deque(maxlen=1000)  # Recent metrics
        self.historical_metrics = []  # All metrics
        self.quality_trends = deque(maxlen=100)  # Quality scores
        
        # Statistics
        self.stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'average_speed': 0.0,
            'average_quality': 0.0,
            'current_success_rate': 1.0,
            'last_updated': None
        }
        
        # Alert system
        self.alerts = []
        self.alert_thresholds = {
            'consecutive_failures': 3,
            'speed_degradation': 2.0,  # 2x slower than average
            'quality_drop': 0.2  # 20% quality drop
        }
        
        logger.info("✅ Performance monitor initialized")
        
    def track_performance(self, operation: str, start_time: float, 
                         quality_score: Optional[float] = None, 
                         success: bool = True, 
                         metadata: Optional[Dict] = None) -> None:
        """Track performance metrics"""
        duration_ms = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        metric = PerformanceMetric(
            operation=operation,
            duration_ms=duration_ms,
            timestamp=datetime.now().isoformat(),
            quality_score=quality_score,
            success=success,
            metadata=metadata
        )
        
        # Add to tracking
        self.metrics.append(metric)
        self.historical_metrics.append(metric)
        
        if quality_score is not None:
            self.quality_trends.append(quality_score)
        
        # Update statistics
        self._update_statistics()
        
        # Check for alerts
        self._check_for_alerts(metric)
        
        quality_text = f"{quality_score:.2f}" if quality_score is not None else 'N/A'
        logger.debug(f"📊 Tracked {operation}: {duration_ms:.1f}ms, quality: {quality_text}")
        
    def _update_statistics(self) -> None:
        """Update performance statistics"""
        if not self.metrics:
            return
        
        # Count operations
        self.stats['total_operations'] = len(self.metrics)
        successful = sum(1 for m in self.metrics if m.success)
        failed = sum(1 for m in self.metrics if not m.success)
        
        self.stats['successful_operations'] = successful
        self.stats['failed_operations'] = failed
        
        # Calculate success rate
        if self.stats['total_operations'] > 0:
            self.stats['current_success_rate'] = successful / self.stats['total_operations']
        
        # Calculate average speed
        durations = [m.duration_ms for m in self.metrics]
        if durations:
            self.stats['average_speed'] = statistics.mean(durations)
        
        # Calculate average quality
        qualities = [m.quality_score for m in self.metrics if m.quality_score is not None]
        if qualities:
            self.stats['average_quality'] = statistics.mean(qualities)
        
        self.stats['last_updated'] = datetime.now().isoformat()
        
    def _check_for_alerts(self, metric: PerformanceMetric) -> None:
        """Check for performance issues and generate alerts"""
        # Check for consecutive failures
        if not metric.success:
            recent_failures = sum(1 for m in list(self.metrics)[-5:] if not m.success)
            if recent_failures >= self.alert_thresholds['consecutive_failures']:
                self._generate_alert(
                    'consecutive_failures',
                    f"{recent_failures} consecutive failures detected",
                    severity='high'
                )
        
        # Check for speed degradation
        if self.stats['average_speed'] > 0:
            speed_ratio = metric.duration_ms / self.stats['average_speed']
            if speed_ratio > self.alert_thresholds['speed_degradation']:
                self._generate_alert(
                    'speed_degradation',
                    f"Operation {metric.operation} is {speed_ratio:.1f}x slower than average " + 
                    f"({metric.duration_ms:.1f}ms vs {self.stats['average_speed']:.1f}ms avg)",
                    severity='medium',
                    metadata={'operation': metric.operation, 'duration': metric.duration_ms}
                )
        
        # Check for quality drop
        if metric.quality_score is not None and self.stats['average_quality'] > 0:
            quality_drop = self.stats['average_quality'] - metric.quality_score
            if quality_drop > self.alert_thresholds['quality_drop']:
                self._generate_alert(
                    'quality_drop',
                    f"Quality drop detected: {quality_drop:.2f} below average " + 
                    f"({metric.quality_score:.2f} vs {self.stats['average_quality']:.2f} avg)",
                    severity='medium',
                    metadata={'quality_score': metric.quality_score}
                )
        
        # Check threshold violations
        if metric.operation == 'retrieval' and metric.duration_ms > self.thresholds['retrieval_speed']['max']:
            self._generate_alert(
                'slow_retrieval',
                f"Slow retrieval: {metric.duration_ms:.1f}ms (max {self.thresholds['retrieval_speed']['max']}ms)",
                severity='high'
            )
        
        elif metric.operation == 'validation' and metric.duration_ms > self.thresholds['validation_speed']['max']:
            self._generate_alert(
                'slow_validation',
                f"Slow validation: {metric.duration_ms:.1f}ms (max {self.thresholds['validation_speed']['max']}ms)",
                severity='high'
            )
        
        elif metric.quality_score is not None and metric.quality_score < self.thresholds['quality_score']['min']:
            self._generate_alert(
                'low_quality',
                f"Low quality score: {metric.quality_score:.2f} (min {self.thresholds['quality_score']['min']})",
                severity='high'
            )
        
    def _generate_alert(self, alert_type: str, message: str, 
                       severity: str = 'medium', 
                       metadata: Optional[Dict] = None) -> None:
        """Generate performance alert"""
        alert = {
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.alerts.append(alert)
        
        # Log alert
        log_method = logger.error if severity == 'high' else logger.warning
        log_method(f"🚨 ALERT: {alert_type} - {message}")
        
        # Limit alerts to last 100
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
    def get_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        if not self.metrics:
            return {'error': 'No performance data available'}
        
        # Calculate time-based statistics
        now = datetime.now()
        time_ranges = {
            '1h': now - timedelta(hours=1),
            '6h': now - timedelta(hours=6),
            '24h': now - timedelta(days=1),
            '7d': now - timedelta(days=7)
        }
        
        time_range_stats = {}
        for range_name, cutoff_time in time_ranges.items():
            range_metrics = [m for m in self.metrics 
                           if datetime.fromisoformat(m.timestamp) >= cutoff_time]
            
            if range_metrics:
                avg_speed = statistics.mean([m.duration_ms for m in range_metrics])
                avg_quality = statistics.mean([m.quality_score for m in range_metrics 
                                             if m.quality_score is not None] or [0])
                success_rate = sum(1 for m in range_metrics if m.success) / len(range_metrics)
                
                time_range_stats[range_name] = {
                    'operations': len(range_metrics),
                    'average_speed_ms': avg_speed,
                    'average_quality': avg_quality,
                    'success_rate': success_rate
                }
        
        # Calculate operation breakdown
        operation_breakdown = defaultdict(int)
        for metric in self.metrics:
            operation_breakdown[metric.operation] += 1
        
        # Calculate quality distribution
        quality_bins = [0.0, 0.6, 0.7, 0.8, 0.9, 1.0]
        quality_distribution = {f"{quality_bins[i]:.1f}-{quality_bins[i+1]:.1f}": 0 
                              for i in range(len(quality_bins)-1)}
        
        for metric in self.metrics:
            if metric.quality_score is not None:
                for i in range(len(quality_bins)-1):
                    if quality_bins[i] <= metric.quality_score < quality_bins[i+1]:
                        quality_distribution[f"{quality_bins[i]:.1f}-{quality_bins[i+1]:.1f}"] += 1
                        break
        
        # Calculate speed distribution
        speed_bins = [0, 50, 100, 200, 500, 1000]
        speed_distribution = {f"{speed_bins[i]}-{speed_bins[i+1]}": 0 
                            for i in range(len(speed_bins)-1)}
        
        for metric in self.metrics:
            for i in range(len(speed_bins)-1):
                if speed_bins[i] <= metric.duration_ms < speed_bins[i+1]:
                    speed_distribution[f"{speed_bins[i]}-{speed_bins[i+1]}"] += 1
                    break
        
        return {
            'overall_stats': self.stats.copy(),
            'time_range_stats': time_range_stats,
            'operation_breakdown': dict(operation_breakdown),
            'quality_distribution': quality_distribution,
            'speed_distribution': speed_distribution,
            'recent_alerts': self.alerts[-10:] if self.alerts else [],
            'total_alerts': len(self.alerts),
            'thresholds': self.thresholds.copy(),
            'generated_at': datetime.now().isoformat()
        }
        
    def get_recent_performance(self, limit: int = 20) -> List[Dict]:
        """Get recent performance metrics"""
        recent = list(self.metrics)[-limit:] if self.metrics else []
        
        return [{
            'operation': m.operation,
            'duration_ms': m.duration_ms,
            'timestamp': m.timestamp,
            'quality_score': m.quality_score,
            'success': m.success,
            'metadata': m.metadata
        } for m in recent]
        
    def get_quality_trends(self) -> Dict:
        """Get quality score trends"""
        if not self.quality_trends:
            return {'error': 'No quality data available'}
        
        # Calculate moving averages
        window_sizes = [5, 10, 20]
        moving_averages = {}
        
        for window in window_sizes:
            if len(self.quality_trends) >= window:
                averages = []
                for i in range(len(self.quality_trends) - window + 1):
                    window_data = list(self.quality_trends)[i:i+window]
                    averages.append(statistics.mean(window_data))
                moving_averages[f'moving_avg_{window}'] = averages
        
        # Calculate overall trend
        if len(self.quality_trends) >= 2:
            trend = self.quality_trends[-1] - self.quality_trends[0]
            trend_percentage = (trend / self.quality_trends[0]) * 100 if self.quality_trends[0] > 0 else 0
        else:
            trend = 0
            trend_percentage = 0
        
        return {
            'current_quality': self.quality_trends[-1] if self.quality_trends else None,
            'average_quality': statistics.mean(self.quality_trends),
            'min_quality': min(self.quality_trends),
            'max_quality': max(self.quality_trends),
            'trend': trend,
            'trend_percentage': trend_percentage,
            'moving_averages': moving_averages,
            'recent_qualities': list(self.quality_trends)[-20:]
        }
        
    def get_alert_history(self, limit: int = 20) -> List[Dict]:
        """Get recent alerts"""
        return list(self.alerts)[-limit:] if self.alerts else []
        
    def clear_alerts(self) -> None:
        """Clear all alerts"""
        self.alerts = []
        logger.info("🔄 All alerts cleared")
        
    def reset_monitor(self) -> None:
        """Reset performance monitoring"""
        self.metrics.clear()
        self.quality_trends.clear()
        self.alerts = []
        self.stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'average_speed': 0.0,
            'average_quality': 0.0,
            'current_success_rate': 1.0,
            'last_updated': None
        }
        logger.info("🔄 Performance monitor reset")
        
    def get_system_health(self) -> Dict:
        """Get overall system health assessment"""
        if not self.metrics:
            return {'status': 'unknown', 'score': 0.0, 'message': 'No performance data'}
        
        # Calculate health score (0-1)
        health_score = 0.0
        
        # Speed factor (0-0.4)
        avg_speed = self.stats.get('average_speed', 0)
        if avg_speed > 0:
            speed_factor = min(1.0, max(0.0, 1.0 - (avg_speed / 1000)))  # Normalize to 0-1
            health_score += speed_factor * 0.4
        
        # Quality factor (0-0.3)
        avg_quality = self.stats.get('average_quality', 0)
        quality_factor = min(1.0, avg_quality / 1.0)  # Normalize to 0-1
        health_score += quality_factor * 0.3
        
        # Success rate factor (0-0.3)
        success_rate = self.stats.get('current_success_rate', 1.0)
        success_factor = success_rate  # Already 0-1
        health_score += success_factor * 0.3
        
        # Determine health status
        if health_score >= 0.9:
            status = 'excellent'
            message = 'System performing optimally'
        elif health_score >= 0.8:
            status = 'good'
            message = 'System performing well'
        elif health_score >= 0.7:
            status = 'fair'
            message = 'System performing adequately'
        elif health_score >= 0.6:
            status = 'poor'
            message = 'System needs attention'
        else:
            status = 'critical'
            message = 'System requires immediate attention'
        
        # Check for recent alerts
        recent_alerts = len([a for a in self.alerts 
                           if datetime.fromisoformat(a['timestamp']) > 
                           datetime.now() - timedelta(hours=1)])
        
        if recent_alerts > 0:
            message += f' ({recent_alerts} recent alert(s))'
        
        return {
            'status': status,
            'score': health_score,
            'message': message,
            'factors': {
                'speed': {'score': speed_factor, 'value': avg_speed},
                'quality': {'score': quality_factor, 'value': avg_quality},
                'success_rate': {'score': success_factor, 'value': success_rate}
            },
            'recent_alerts': recent_alerts,
            'timestamp': datetime.now().isoformat()
        }
        
    def export_performance_data(self) -> Dict:
        """Export performance data for visualization"""
        return {
            'metrics': [{
                'operation': m.operation,
                'duration_ms': m.duration_ms,
                'timestamp': m.timestamp,
                'quality_score': m.quality_score,
                'success': m.success
            } for m in self.historical_metrics],
            'quality_trends': list(self.quality_trends),
            'alerts': self.alerts,
            'stats': self.stats.copy()
        }

# Example usage
if __name__ == "__main__":
    # Initialize performance monitor
    monitor = PerformanceMonitor()
    
    # Simulate operations
    start_time = time.time()
    time.sleep(0.05)  # Simulate retrieval
    monitor.track_performance('retrieval', start_time, quality_score=0.85, success=True)
    
    start_time = time.time()
    time.sleep(0.02)  # Simulate validation
    monitor.track_performance('validation', start_time, quality_score=0.90, success=True)
    
    # Get performance report
    report = monitor.get_performance_report()
    print(f"Performance Report:")
    print(f"  Operations: {report['overall_stats']['total_operations']}")
    print(f"  Average Speed: {report['overall_stats']['average_speed']:.1f}ms")
    print(f"  Average Quality: {report['overall_stats']['average_quality']:.2f}")
    print(f"  Success Rate: {report['overall_stats']['current_success_rate']:.1%}")
    
    # Get system health
    health = monitor.get_system_health()
    print(f"\nSystem Health: {health['status']} ({health['score']:.1%})")
    print(f"  Message: {health['message']}")
