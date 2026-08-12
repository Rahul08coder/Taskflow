# =====================================================
# Algorithm Test Suite - Validation Script
# =====================================================

"""
Automated checks for the algorithms in algorithms.py.
Plain if/else PASS/FAIL output — no assert, pytest, or unittest.

Run with:  python check_algorithms.py
"""

from algorithms import (
    insertion_sort,
    binary_search,
    linear_search,
    insertion_sort_count,
    binary_search_count,
    linear_search_count,
)

# Helper function to compare result with expected value
def check(case_name, result, expected):
    if result == expected:
        print(f"PASS: {case_name}")
    else:
        print(f"FAIL: {case_name} — expected {expected}, got {result}")

# Main test execution function
def run_checks():
    # --- Case 1: insertion_sort on an empty list ---
    empty = []
    try:
        insertion_sort(empty, "v")
        check("insertion_sort empty list", empty, [])
    except Exception as e:
        print(f"FAIL: insertion_sort empty list — raised exception: {e}")

    # --- Case 2: insertion_sort on a single-element list ---
    single = [{"v": 42}]
    insertion_sort(single, "v")
    check("insertion_sort single element", single, [{"v": 42}])

    # --- Case 3: binary_search finds value at first, last, and middle index ---
    sorted_list = [{"v": i} for i in [1, 2, 5, 8, 9]]

    result_first = binary_search(sorted_list, 1, "v")
    check("binary_search finds first index", result_first, 0)

    result_last = binary_search(sorted_list, 9, "v")
    check("binary_search finds last index", result_last, 4)

    result_mid = binary_search(sorted_list, 5, "v")
    check("binary_search finds middle index", result_mid, 2)

    # --- Case 4: binary_search returns not-found (-1) when target is absent ---
    result_absent = binary_search(sorted_list, 100, "v")
    check("binary_search not-found returns -1", result_absent, -1)

    # --- Case 5: insertion_sort_count sorts correctly and returns a plain int > 0 ---
    hand_checkable = [{"v": 3}, {"v": 1}, {"v": 2}]
    count = insertion_sort_count(hand_checkable, "v")

    check("insertion_sort_count sorts correctly", hand_checkable, [{"v": 1}, {"v": 2}, {"v": 3}])

    if isinstance(count, int) and count > 0:
        print(f"PASS: insertion_sort_count returns a plain int > 0 (got {count})")
    else:
        print(f"FAIL: insertion_sort_count returns a plain int > 0 — got {count} (type {type(count)})")

    # --- Case 6: binary_search_count returns correct index + comparison_count > 0 ---
    sorted_list2 = [{"v": i} for i in [1, 2, 5, 8, 9]]
    bsc_result = binary_search_count(sorted_list2, 5, "v")

    if bsc_result.get("index") == 2 and isinstance(bsc_result.get("comparison_count"), int) and bsc_result["comparison_count"] > 0:
        print(f"PASS: binary_search_count correct index + comparison_count > 0 (got {bsc_result})")
    else:
        print(f"FAIL: binary_search_count correct index + comparison_count > 0 — got {bsc_result}, expected index=2")

    # --- Case 7: linear_search_count on an absent value ---
    lsc_result = linear_search_count(sorted_list2, 100, "v")
    expected_lsc = {"index": -1, "comparison_count": len(sorted_list2)}

    if lsc_result.get("index") == expected_lsc["index"] and lsc_result.get("comparison_count") == expected_lsc["comparison_count"]:
        print(f"PASS: linear_search_count absent value (got {lsc_result})")
    else:
        print(f"FAIL: linear_search_count absent value — expected {expected_lsc}, got {lsc_result}")

# Entry point - runs when script is executed directly
if __name__ == "__main__":
    run_checks()