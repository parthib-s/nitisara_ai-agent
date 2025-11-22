"""
NITISARA AI Monitoring & Observability System
Implements API integration, observability, safety guardrails, and performance optimization
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
from collections import defaultdict, deque

@dataclass
class APICall:
    """Structure for API call monitoring"""
    timestamp: float
    endpoint: str
    method: str
    status_code: int
    response_time: float
    user_id: str
    request_size: int
    response_size: int
    error_message: Optional[str] = None

@dataclass
class SafetyViolation:
    """Structure for safety violation tracking"""
    timestamp: float
    user_id: str
    violation_type: str
    severity: str
    description: str
    action_taken: str

@dataclass
class PerformanceMetrics:
    """Structure for performance metrics"""
    timestamp: float
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str]

class NitisaraMonitor:
    """NITISARA AI Monitoring and Observability System"""
    
    def __init__(self):
        self.api_calls = deque(maxlen=10000)  # Keep last 10k API calls
        self.safety_violations = deque(maxlen=1000)  # Keep last 1k violations
        self.performance_metrics = deque(maxlen=5000)  # Keep last 5k metrics
        self.rate_limits = defaultdict(lambda: {'count': 0, 'window_start': time.time()})
        self.safety_rules = self._initialize_safety_rules()
        self.performance_thresholds = self._initialize_performance_thresholds()
        
        # Setup logging
        self._setup_logging()
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def _setup_logging(self):
        """Setup structured logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('nitisara_monitoring.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('NitisaraMonitor')
    
    def _initialize_safety_rules(self) -> Dict[str, Dict]:
        """Initialize safety rules and guardrails"""
        return {
            'pii_detection': {
                'enabled': True,
                'patterns': [
                    r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
                    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
                ],
                'action': 'redact'
            },
            'rate_limiting': {
                'enabled': True,
                'max_requests_per_minute': 60,
                'max_requests_per_hour': 1000
            },
            'content_filtering': {
                'enabled': True,
                'blocked_keywords': ['hack', 'exploit', 'bypass', 'unauthorized'],
                'action': 'block'
            },
            'response_validation': {
                'enabled': True,
                'max_response_length': 5000,
                'min_response_length': 10
            }
        }
    
    def _initialize_performance_thresholds(self) -> Dict[str, float]:
        """Initialize performance monitoring thresholds"""
        return {
            'max_response_time': 5.0,  # seconds
            'max_memory_usage': 1024,  # MB
            'max_cpu_usage': 80.0,  # percentage
            'min_accuracy_score': 7.0,  # out of 10
            'max_error_rate': 0.05  # 5%
        }
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, 
                    response_time: float, user_id: str, request_size: int = 0, 
                    response_size: int = 0, error_message: str = None):
        """Log API call for monitoring"""
        api_call = APICall(
            timestamp=time.time(),
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            user_id=user_id,
            request_size=request_size,
            response_size=response_size,
            error_message=error_message
        )
        
        self.api_calls.append(api_call)
        
        # Log to file
        self.logger.info(f"API Call: {method} {endpoint} - {status_code} - {response_time:.3f}s")
        
        # Check for performance issues
        self._check_performance_thresholds(api_call)
    
    def check_safety_violations(self, user_input: str, user_id: str) -> List[SafetyViolation]:
        """Check for safety violations in user input"""
        violations = []
        
        # Check for PII
        pii_violations = self._check_pii_detection(user_input)
        if pii_violations:
            violations.append(SafetyViolation(
                timestamp=time.time(),
                user_id=user_id,
                violation_type='PII_DETECTED',
                severity='HIGH',
                description=f"PII detected: {pii_violations}",
                action_taken='REDACTED'
            ))
        
        # Check for blocked keywords
        content_violations = self._check_content_filtering(user_input)
        if content_violations:
            violations.append(SafetyViolation(
                timestamp=time.time(),
                user_id=user_id,
                violation_type='CONTENT_FILTER',
                severity='MEDIUM',
                description=f"Blocked content detected: {content_violations}",
                action_taken='BLOCKED'
            ))
        
        # Check rate limiting
        rate_limit_violation = self._check_rate_limiting(user_id)
        if rate_limit_violation:
            violations.append(SafetyViolation(
                timestamp=time.time(),
                user_id=user_id,
                violation_type='RATE_LIMIT',
                severity='LOW',
                description="Rate limit exceeded",
                action_taken='THROTTLED'
            ))
        
        # Log violations
        for violation in violations:
            self.safety_violations.append(violation)
            self.logger.warning(f"Safety Violation: {violation.violation_type} - {violation.description}")
        
        return violations
    
    def _check_pii_detection(self, text: str) -> List[str]:
        """Check for PII in text"""
        violations = []
        import re
        
        for pattern in self.safety_rules['pii_detection']['patterns']:
            matches = re.findall(pattern, text)
            if matches:
                violations.extend(matches)
        
        return violations
    
    def _check_content_filtering(self, text: str) -> List[str]:
        """Check for blocked content"""
        violations = []
        text_lower = text.lower()
        
        for keyword in self.safety_rules['content_filtering']['blocked_keywords']:
            if keyword in text_lower:
                violations.append(keyword)
        
        return violations
    
    def _check_rate_limiting(self, user_id: str) -> bool:
        """Check if user has exceeded rate limits"""
        current_time = time.time()
        user_limits = self.rate_limits[user_id]
        
        # Reset window if needed
        if current_time - user_limits['window_start'] > 3600:  # 1 hour
            user_limits['count'] = 0
            user_limits['window_start'] = current_time
        
        # Check limits
        max_per_hour = self.safety_rules['rate_limiting']['max_requests_per_hour']
        if user_limits['count'] >= max_per_hour:
            return True
        
        user_limits['count'] += 1
        return False
    
    def _check_performance_thresholds(self, api_call: APICall):
        """Check if performance thresholds are exceeded"""
        # Check response time
        if api_call.response_time > self.performance_thresholds['max_response_time']:
            self.logger.warning(f"Slow response: {api_call.endpoint} took {api_call.response_time:.3f}s")
        
        # Check error rate
        if api_call.status_code >= 400:
            self.logger.error(f"API Error: {api_call.endpoint} returned {api_call.status_code}")
    
    def record_performance_metric(self, metric_name: str, value: float, unit: str, tags: Dict[str, str] = None):
        """Record performance metric"""
        metric = PerformanceMetrics(
            timestamp=time.time(),
            metric_name=metric_name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        
        self.performance_metrics.append(metric)
        self.logger.info(f"Performance Metric: {metric_name}={value} {unit}")
    
    def get_api_metrics(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get API metrics for specified time window"""
        cutoff_time = time.time() - time_window
        recent_calls = [call for call in self.api_calls if call.timestamp >= cutoff_time]
        
        if not recent_calls:
            return {'error': 'No data in time window'}
        
        # Calculate metrics
        total_calls = len(recent_calls)
        successful_calls = len([call for call in recent_calls if call.status_code < 400])
        error_rate = (total_calls - successful_calls) / total_calls if total_calls > 0 else 0
        
        avg_response_time = sum(call.response_time for call in recent_calls) / total_calls
        max_response_time = max(call.response_time for call in recent_calls)
        
        # Endpoint breakdown
        endpoint_counts = defaultdict(int)
        for call in recent_calls:
            endpoint_counts[call.endpoint] += 1
        
        return {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'error_rate': error_rate,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'endpoint_breakdown': dict(endpoint_counts)
        }
    
    def get_safety_metrics(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get safety metrics for specified time window"""
        cutoff_time = time.time() - time_window
        recent_violations = [v for v in self.safety_violations if v.timestamp >= cutoff_time]
        
        if not recent_violations:
            return {'total_violations': 0, 'violation_types': {}}
        
        # Count violations by type
        violation_types = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for violation in recent_violations:
            violation_types[violation.violation_type] += 1
            severity_counts[violation.severity] += 1
        
        return {
            'total_violations': len(recent_violations),
            'violation_types': dict(violation_types),
            'severity_breakdown': dict(severity_counts)
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        if not self.performance_metrics:
            return {'error': 'No performance data available'}
        
        # Group metrics by name
        metric_groups = defaultdict(list)
        for metric in self.performance_metrics:
            metric_groups[metric.metric_name].append(metric.value)
        
        summary = {}
        for metric_name, values in metric_groups.items():
            summary[metric_name] = {
                'count': len(values),
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values)
            }
        
        return summary
    
    def _start_background_monitoring(self):
        """Start background monitoring tasks"""
        def monitor_loop():
            while True:
                try:
                    # Check for performance issues
                    self._check_system_health()
                    
                    # Clean up old data
                    self._cleanup_old_data()
                    
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    self.logger.error(f"Background monitoring error: {e}")
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def _check_system_health(self):
        """Check overall system health"""
        # Check API call patterns
        recent_calls = list(self.api_calls)[-100:]  # Last 100 calls
        if recent_calls:
            error_rate = len([call for call in recent_calls if call.status_code >= 400]) / len(recent_calls)
            if error_rate > self.performance_thresholds['max_error_rate']:
                self.logger.warning(f"High error rate detected: {error_rate:.2%}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        # This is handled by deque maxlen, but we can add additional cleanup here
        pass
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        return {
            'timestamp': time.time(),
            'api_metrics': self.get_api_metrics(),
            'safety_metrics': self.get_safety_metrics(),
            'performance_summary': self.get_performance_summary(),
            'system_health': 'HEALTHY' if self._is_system_healthy() else 'DEGRADED'
        }
    
    def _is_system_healthy(self) -> bool:
        """Check if system is healthy"""
        # Simple health check based on recent performance
        recent_calls = list(self.api_calls)[-50:]  # Last 50 calls
        if not recent_calls:
            return True
        
        error_rate = len([call for call in recent_calls if call.status_code >= 400]) / len(recent_calls)
        avg_response_time = sum(call.response_time for call in recent_calls) / len(recent_calls)
        
        return (error_rate < self.performance_thresholds['max_error_rate'] and 
                avg_response_time < self.performance_thresholds['max_response_time'])

# Global monitoring instance
monitor = NitisaraMonitor()

def log_api_call(endpoint: str, method: str, status_code: int, response_time: float, 
                user_id: str, **kwargs):
    """Convenience function to log API calls"""
    monitor.log_api_call(endpoint, method, status_code, response_time, user_id, **kwargs)

def check_safety_violations(user_input: str, user_id: str) -> List[SafetyViolation]:
    """Convenience function to check safety violations"""
    return monitor.check_safety_violations(user_input, user_id)

def record_performance_metric(metric_name: str, value: float, unit: str, **kwargs):
    """Convenience function to record performance metrics"""
    monitor.record_performance_metric(metric_name, value, unit, **kwargs)

