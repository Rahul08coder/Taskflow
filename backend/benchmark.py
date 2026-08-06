"""
Benchmark script for the algorithms powering /tasks?sort=priority and
/tasks/search. Uses synthetic in-memory task dicts (same fields the real
endpoints operate on: title, priority, due_date) at three sizes, since
seeding thousands of real rows into Supabase for a single benchmark run
is impractical.

Run with:  python benchmark.py
"""

import random

from algorithms import insertion_sort_count, binary_search_count, linear_search_count

PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}
SIZES = [10, 500, 3000]

random.seed(42)  # reproducible runs


def generate_tasks(n):
    """Synthetic tasks with the same fields the real endpoints use."""
    priorities = ["low", "medium", "high"]
    tasks = []
    for i in range(n):
        tasks.append({
            "title": f"Task-{i:06d}",
            "priority": random.choice(priorities),
            "due_date": f"2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        })
    random.shuffle(tasks)  # unsorted, like real DB rows would arrive
    return tasks


def run_benchmark():
    results = []

    for n in SIZES:
        tasks = generate_tasks(n)

        # --- Sort benchmark (mirrors GET /tasks?sort=priority) ---
        sort_copy = [dict(t) for t in tasks]
        for t in sort_copy:
            t["_sort_key"] = PRIORITY_RANK[t["priority"]]
        sort_comparisons = insertion_sort_count(sort_copy, "_sort_key")

        # --- Search benchmark (mirrors GET /tasks/search) ---
        # Target: a title that exists, picked from the middle of the original list
        target_title = tasks[n // 2]["title"] if n > 0 else None

        # binary_search requires a title-sorted index first (also counted)
        title_sorted = [dict(t) for t in tasks]
        title_sort_comparisons = insertion_sort_count(title_sorted, "title")
        binary_result = binary_search_count(title_sorted, target_title, "title") if n > 0 else {"comparison_count": 0}

        # linear_search runs on the original unsorted list
        linear_result = linear_search_count(tasks, target_title, "title") if n > 0 else {"comparison_count": 0}

        results.append({
            "size": n,
            "insertion_sort_by_priority_comparisons": sort_comparisons,
            "insertion_sort_by_title_comparisons": title_sort_comparisons,
            "binary_search_comparisons": binary_result["comparison_count"],
            "linear_search_comparisons": linear_result["comparison_count"],
        })

    return results


def print_results(results):
    print(f"{'Size':>6} | {'InsSort(priority)':>18} | {'InsSort(title)':>15} | {'BinarySearch':>13} | {'LinearSearch':>13}")
    print("-" * 78)
    for r in results:
        print(f"{r['size']:>6} | {r['insertion_sort_by_priority_comparisons']:>18} | "
              f"{r['insertion_sort_by_title_comparisons']:>15} | "
              f"{r['binary_search_comparisons']:>13} | {r['linear_search_comparisons']:>13}")


if __name__ == "__main__":
    results = run_benchmark()
    print_results(results)

    # Also save raw results to a file for the README
    with open("benchmark_results.txt", "w") as f:
        f.write("Benchmark Results (synthetic in-memory task data, seed=42)\n")
        f.write("=" * 60 + "\n\n")
        for r in results:
            f.write(f"Size: {r['size']}\n")
            f.write(f"  insertion_sort comparisons (sort by priority): {r['insertion_sort_by_priority_comparisons']}\n")
            f.write(f"  insertion_sort comparisons (sort by title, for search index): {r['insertion_sort_by_title_comparisons']}\n")
            f.write(f"  binary_search comparisons: {r['binary_search_comparisons']}\n")
            f.write(f"  linear_search comparisons: {r['linear_search_comparisons']}\n\n")
    print("\nRaw results saved to benchmark_results.txt")