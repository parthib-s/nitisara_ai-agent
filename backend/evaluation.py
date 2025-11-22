"""
NITISARA AI Evaluation Framework
Implements AI Evals, LLM-as-Judge, and A/B Testing for Captain Agent
"""

import json
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from gemini_chain import get_llm_response

@dataclass
class EvaluationResult:
    """Structure for evaluation results"""
    test_id: str
    timestamp: float
    user_input: str
    agent_response: str
    metrics: Dict[str, float]
    llm_judge_score: float
    human_feedback: str = ""

class NitisaraEvaluator:
    """NITISARA AI Evaluation Framework"""
    
    def __init__(self):
        self.evaluation_history = []
        self.performance_metrics = {
            'response_time': [],
            'accuracy': [],
            'user_satisfaction': [],
            'compliance_accuracy': [],
            'rate_accuracy': []
        }
    
    def evaluate_conversation(self, user_input: str, agent_response: str, context: Dict = None) -> EvaluationResult:
        """Evaluate a single conversation turn"""
        start_time = time.time()
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Run LLM-as-Judge evaluation
        llm_score = self._llm_judge_evaluation(user_input, agent_response, context)
        
        # Calculate accuracy metrics
        accuracy_metrics = self._calculate_accuracy_metrics(user_input, agent_response, context)
        
        # Create evaluation result
        result = EvaluationResult(
            test_id=f"eval_{int(time.time())}",
            timestamp=time.time(),
            user_input=user_input,
            agent_response=agent_response,
            metrics={
                'response_time': response_time,
                'llm_judge_score': llm_score,
                **accuracy_metrics
            },
            llm_judge_score=llm_score
        )
        
        self.evaluation_history.append(result)
        self._update_performance_metrics(result)
        
        return result
    
    def _llm_judge_evaluation(self, user_input: str, agent_response: str, context: Dict = None) -> float:
        """Use LLM as judge to evaluate response quality"""
        
        evaluation_prompt = f"""
        You are an expert evaluator for NITISARA's logistics AI assistant. 
        Rate the agent's response on a scale of 1-10 for each criterion:
        
        USER INPUT: {user_input}
        AGENT RESPONSE: {agent_response}
        CONTEXT: {context or 'No additional context'}
        
        Evaluation Criteria:
        1. Relevance (1-10): Does the response address the user's question/request?
        2. Accuracy (1-10): Is the information provided correct and factual?
        3. Completeness (1-10): Does the response provide sufficient information?
        4. Professionalism (1-10): Is the tone appropriate for business logistics?
        5. Actionability (1-10): Does the response provide clear next steps?
        6. NITISARA Brand Alignment (1-10): Does it reflect NITISARA's values and capabilities?
        
        Provide scores as: Relevance: X, Accuracy: Y, Completeness: Z, Professionalism: A, Actionability: B, Brand Alignment: C
        Then provide an overall score (1-10) and brief reasoning.
        """
        
        try:
            judge_response = get_llm_response(evaluation_prompt)
            # Extract overall score from response
            overall_score = self._extract_score_from_judge_response(judge_response)
            return overall_score
        except Exception as e:
            print(f"LLM Judge evaluation failed: {e}")
            return 5.0  # Default neutral score
    
    def _extract_score_from_judge_response(self, judge_response: str) -> float:
        """Extract numerical score from LLM judge response"""
        import re
        # Look for overall score pattern
        score_match = re.search(r'overall score[:\s]*(\d+(?:\.\d+)?)', judge_response.lower())
        if score_match:
            return float(score_match.group(1))
        
        # Fallback: look for any number between 1-10
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', judge_response)
        for num in numbers:
            score = float(num)
            if 1 <= score <= 10:
                return score
        
        return 5.0  # Default neutral score
    
    def _calculate_accuracy_metrics(self, user_input: str, agent_response: str, context: Dict = None) -> Dict[str, float]:
        """Calculate accuracy metrics for the response"""
        metrics = {}
        
        # Check for compliance accuracy
        if 'compliance' in user_input.lower() or 'document' in user_input.lower():
            metrics['compliance_accuracy'] = self._check_compliance_accuracy(agent_response)
        
        # Check for rate estimation accuracy
        if 'rate' in user_input.lower() or 'price' in user_input.lower() or 'cost' in user_input.lower():
            metrics['rate_accuracy'] = self._check_rate_accuracy(agent_response)
        
        # Check for general accuracy indicators
        metrics['response_completeness'] = self._check_response_completeness(agent_response)
        metrics['professional_tone'] = self._check_professional_tone(agent_response)
        
        return metrics
    
    def _check_compliance_accuracy(self, response: str) -> float:
        """Check if compliance response contains accurate information"""
        score = 0.0
        
        # Check for compliance keywords
        compliance_keywords = ['compliance', 'document', 'certificate', 'hs code', 'trade']
        for keyword in compliance_keywords:
            if keyword in response.lower():
                score += 1.0
        
        # Check for specific compliance elements
        if '✅' in response or '⚠️' in response:
            score += 1.0
        
        if 'hs code' in response.lower():
            score += 1.0
        
        return min(score / 3.0, 1.0)  # Normalize to 0-1
    
    def _check_rate_accuracy(self, response: str) -> float:
        """Check if rate response contains accurate pricing information"""
        score = 0.0
        
        # Check for rate-related keywords
        rate_keywords = ['rate', 'price', 'cost', '₹', 'inr', 'usd']
        for keyword in rate_keywords:
            if keyword in response.lower():
                score += 1.0
        
        # Check for multiple shipping options
        if 'sea' in response.lower() and 'air' in response.lower():
            score += 1.0
        
        # Check for CO2e information
        if 'co₂e' in response.lower() or 'carbon' in response.lower():
            score += 1.0
        
        return min(score / 3.0, 1.0)  # Normalize to 0-1
    
    def _check_response_completeness(self, response: str) -> float:
        """Check if response is complete and informative"""
        # Basic completeness checks
        if len(response) < 50:
            return 0.3
        elif len(response) < 100:
            return 0.6
        else:
            return 1.0
    
    def _check_professional_tone(self, response: str) -> float:
        """Check if response maintains professional tone"""
        score = 1.0
        
        # Check for unprofessional language
        unprofessional_words = ['damn', 'crap', 'stupid', 'idiot']
        for word in unprofessional_words:
            if word in response.lower():
                score -= 0.3
        
        # Check for professional elements
        professional_elements = ['thank you', 'please', 'recommend', 'suggest']
        for element in professional_elements:
            if element in response.lower():
                score += 0.1
        
        return max(0.0, min(score, 1.0))
    
    def _update_performance_metrics(self, result: EvaluationResult):
        """Update running performance metrics"""
        self.performance_metrics['response_time'].append(result.metrics.get('response_time', 0))
        self.performance_metrics['accuracy'].append(result.llm_judge_score)
        
        if 'compliance_accuracy' in result.metrics:
            self.performance_metrics['compliance_accuracy'].append(result.metrics['compliance_accuracy'])
        
        if 'rate_accuracy' in result.metrics:
            self.performance_metrics['rate_accuracy'].append(result.metrics['rate_accuracy'])
    
    def run_ab_test(self, test_scenarios: List[Dict], iterations: int = 10) -> Dict[str, Any]:
        """Run A/B test comparing different agent configurations"""
        results = {
            'scenario_a': [],
            'scenario_b': [],
            'comparison': {}
        }
        
        for i in range(iterations):
            for scenario in test_scenarios:
                # Simulate conversation with different configurations
                user_input = scenario['user_input']
                agent_response = scenario['agent_response']
                
                # Evaluate response
                result = self.evaluate_conversation(user_input, agent_response, scenario.get('context'))
                
                if scenario['scenario'] == 'A':
                    results['scenario_a'].append(result)
                else:
                    results['scenario_b'].append(result)
        
        # Compare scenarios
        results['comparison'] = self._compare_scenarios(results['scenario_a'], results['scenario_b'])
        
        return results
    
    def _compare_scenarios(self, scenario_a: List[EvaluationResult], scenario_b: List[EvaluationResult]) -> Dict[str, Any]:
        """Compare two scenarios and return statistical analysis"""
        if not scenario_a or not scenario_b:
            return {'error': 'Insufficient data for comparison'}
        
        # Calculate average scores
        avg_score_a = sum(r.llm_judge_score for r in scenario_a) / len(scenario_a)
        avg_score_b = sum(r.llm_judge_score for r in scenario_b) / len(scenario_b)
        
        # Calculate average response time
        avg_time_a = sum(r.metrics.get('response_time', 0) for r in scenario_a) / len(scenario_a)
        avg_time_b = sum(r.metrics.get('response_time', 0) for r in scenario_b) / len(scenario_b)
        
        return {
            'scenario_a_avg_score': avg_score_a,
            'scenario_b_avg_score': avg_score_b,
            'score_difference': avg_score_b - avg_score_a,
            'scenario_a_avg_time': avg_time_a,
            'scenario_b_avg_time': avg_time_b,
            'time_difference': avg_time_b - avg_time_a,
            'winner': 'B' if avg_score_b > avg_score_a else 'A'
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        if not self.evaluation_history:
            return {'error': 'No evaluation data available'}
        
        summary = {
            'total_evaluations': len(self.evaluation_history),
            'average_llm_score': sum(r.llm_judge_score for r in self.evaluation_history) / len(self.evaluation_history),
            'average_response_time': sum(r.metrics.get('response_time', 0) for r in self.evaluation_history) / len(self.evaluation_history)
        }
        
        # Add metric-specific averages
        for metric, values in self.performance_metrics.items():
            if values:
                summary[f'average_{metric}'] = sum(values) / len(values)
        
        return summary

# Global evaluator instance
evaluator = NitisaraEvaluator()

def evaluate_agent_response(user_input: str, agent_response: str, context: Dict = None) -> EvaluationResult:
    """Convenience function to evaluate agent response"""
    return evaluator.evaluate_conversation(user_input, agent_response, context)

