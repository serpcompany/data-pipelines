#!/usr/bin/env python3
"""
Estimate time required to scrape BoxRec data based on URL count and API limits.
"""

import json
from datetime import timedelta
from pathlib import Path
import math


class ScrapeTimeEstimator:
    """Estimate scraping time based on various constraints."""
    
    def __init__(self):
        # Zyte API constraints (typical)
        self.requests_per_second = 2  # Conservative estimate
        self.concurrent_requests = 10  # Typical concurrent limit
        self.avg_response_time = 3  # Seconds per request (including network)
        
        # Retry and error assumptions
        self.retry_rate = 0.05  # 5% of requests need retry
        self.failure_rate = 0.01  # 1% permanent failures
        
        # Processing overhead
        self.parse_time_per_page = 0.1  # Seconds to parse HTML
        self.file_io_time = 0.05  # Seconds to save file
        
    def estimate_for_urls(self, url_count: int, include_wiki: bool = True) -> dict:
        """Estimate time for scraping a given number of URLs."""
        
        # Calculate base request count
        profile_pages = url_count
        wiki_pages = url_count if include_wiki else 0
        total_requests = profile_pages + wiki_pages
        
        # Add retry overhead
        retry_requests = int(total_requests * self.retry_rate)
        total_with_retries = total_requests + retry_requests
        
        # Calculate time based on rate limits
        # With concurrent requests, effective throughput increases
        effective_rate = min(self.requests_per_second * self.concurrent_requests, 
                           self.concurrent_requests / self.avg_response_time)
        
        api_time_seconds = total_with_retries / effective_rate
        
        # Add processing overhead
        processing_time = total_requests * (self.parse_time_per_page + self.file_io_time)
        
        # Total time
        total_seconds = api_time_seconds + processing_time
        
        # Calculate costs (Zyte API typical pricing)
        cost_per_1000 = 1.80  # USD per 1000 requests
        estimated_cost = (total_with_retries / 1000) * cost_per_1000
        
        # Break down into time units
        hours = total_seconds / 3600
        days = hours / 24
        
        # If running 24/7
        continuous_time = {
            'hours': round(hours, 1),
            'days': round(days, 1)
        }
        
        # If running only during work hours (8 hours/day)
        work_hours_days = hours / 8
        
        # With breaks and maintenance (6 effective hours/day)
        realistic_days = hours / 6
        
        return {
            'url_count': url_count,
            'total_requests': total_requests,
            'requests_with_retries': total_with_retries,
            'estimated_failures': int(total_requests * self.failure_rate),
            'time_estimates': {
                'continuous_24_7': continuous_time,
                'work_hours_8h_day': round(work_hours_days, 1),
                'realistic_6h_day': round(realistic_days, 1)
            },
            'api_constraints': {
                'requests_per_second': self.requests_per_second,
                'concurrent_limit': self.concurrent_requests,
                'effective_throughput': round(effective_rate, 2)
            },
            'estimated_cost_usd': round(estimated_cost, 2),
            'breakdown': {
                'api_time_hours': round(api_time_seconds / 3600, 1),
                'processing_time_hours': round(processing_time / 3600, 1)
            }
        }
    
    def estimate_batches(self, total_urls: int, batch_size: int = 1000) -> list:
        """Break down into recommended batch sizes."""
        batches = []
        num_batches = math.ceil(total_urls / batch_size)
        
        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, total_urls)
            batch_urls = end_idx - start_idx
            
            estimate = self.estimate_for_urls(batch_urls, include_wiki=True)
            batches.append({
                'batch_number': i + 1,
                'url_range': f"{start_idx + 1}-{end_idx}",
                'url_count': batch_urls,
                'estimated_hours': estimate['time_estimates']['continuous_24_7']['hours'],
                'estimated_cost': estimate['estimated_cost_usd']
            })
        
        return batches


def main():
    """Run time estimates for various scenarios."""
    estimator = ScrapeTimeEstimator()
    
    print("=" * 60)
    print("🕐 BoxRec Scraping Time Estimates")
    print("=" * 60)
    
    # Current dataset
    print("\n📊 Current Dataset (99 URLs):")
    current = estimator.estimate_for_urls(99)
    print(f"  Total requests: {current['total_requests']} (including wiki pages)")
    print(f"  Time (24/7): {current['time_estimates']['continuous_24_7']['hours']} hours")
    print(f"  Time (6h/day): {current['time_estimates']['realistic_6h_day']} days")
    print(f"  Estimated cost: ${current['estimated_cost_usd']}")
    
    # Full 67,000 boxers scenario
    print("\n🌍 Full Dataset (67,000 boxers):")
    full = estimator.estimate_for_urls(67000)
    print(f"  Total requests: {full['total_requests']:,} (including wiki pages)")
    print(f"  Time (24/7): {full['time_estimates']['continuous_24_7']['days']} days")
    print(f"  Time (6h/day): {full['time_estimates']['realistic_6h_day']} days")
    print(f"  Estimated cost: ${full['estimated_cost_usd']:,.2f}")
    
    # Breakdown
    print(f"\n  Time breakdown:")
    print(f"    API calls: {full['breakdown']['api_time_hours']} hours")
    print(f"    Processing: {full['breakdown']['processing_time_hours']} hours")
    
    # Recommended approach
    print("\n📋 Recommended Batch Approach (1,000 URLs per batch):")
    batches = estimator.estimate_batches(67000, batch_size=1000)
    
    print(f"  Total batches: {len(batches)}")
    print(f"\n  First 5 batches:")
    for batch in batches[:5]:
        print(f"    Batch {batch['batch_number']}: {batch['url_range']} - "
              f"{batch['estimated_hours']}h (${batch['estimated_cost']})")
    
    total_batch_cost = sum(b['estimated_cost'] for b in batches)
    print(f"\n  Total estimated cost: ${total_batch_cost:,.2f}")
    
    # Different scenarios
    print("\n🔧 Different Scenarios:")
    scenarios = [
        (1000, "Small test batch"),
        (5000, "Medium batch"),
        (10000, "Large batch"),
        (25000, "Quarter dataset"),
        (67000, "Full dataset")
    ]
    
    print("\n  URL Count | Days (24/7) | Days (6h/day) | Cost")
    print("  " + "-" * 50)
    for count, desc in scenarios:
        est = estimator.estimate_for_urls(count)
        print(f"  {count:>8} | {est['time_estimates']['continuous_24_7']['days']:>10} | "
              f"{est['time_estimates']['realistic_6h_day']:>12} | ${est['estimated_cost_usd']:>8.2f}")
    
    # Save detailed report
    report = {
        'generated_at': str(Path(__file__).stat().st_mtime),
        'assumptions': {
            'requests_per_second': estimator.requests_per_second,
            'concurrent_requests': estimator.concurrent_requests,
            'avg_response_time': estimator.avg_response_time,
            'retry_rate': estimator.retry_rate,
            'failure_rate': estimator.failure_rate,
            'includes_wiki_pages': True
        },
        'current_dataset': current,
        'full_dataset': full,
        'batches': batches[:10],  # First 10 batches
        'scenarios': {str(count): estimator.estimate_for_urls(count) for count, _ in scenarios}
    }
    
    report_file = Path('data/scraping_time_estimate.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    # Optimization suggestions
    print("\n💡 Optimization Tips:")
    print("  1. Use concurrent requests (up to API limit)")
    print("  2. Implement robust retry logic with exponential backoff")
    print("  3. Cache responses to avoid re-scraping unchanged data")
    print("  4. Monitor rate limits and adjust dynamically")
    print("  5. Consider running during off-peak hours for better performance")
    print("  6. Use the inventory system to track progress and resume from failures")


if __name__ == "__main__":
    main()