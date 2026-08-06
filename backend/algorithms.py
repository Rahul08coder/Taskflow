"""
Hand-rolled sorting and search algorithms powering the /tasks?sort=... and
/tasks/search?... endpoints. No built-in sorted()/list.sort() used anywhere.

Convention: "not found" is represented as -1 (documented here and in the README).
"""


def insertion_sort(records, key):
    """
    Sorts `records` (a list of dicts) in place by record[key], using the
    standard insertion-sort structure: starting from the second element,
    compare backwards and shift larger elements right until the correct
    slot for the current element is found.

    Mutates `records` directly. Returns None (no return value needed).
    """
    for i in range(1, len(records)):
        current = records[i]
        j = i - 1
        while j >= 0 and records[j][key] > current[key]:
            records[j + 1] = records[j]
            j -= 1
        records[j + 1] = current


def binary_search(sorted_records, target_value, key):
    """
    Searches `sorted_records` (already sorted ascending by key, e.g. via
    insertion_sort) for a record where record[key] == target_value.

    Returns the index of a matching record, or -1 if no match exists.
    """
    low = 0
    high = len(sorted_records) - 1

    while low <= high:
        mid = (low + high) // 2
        mid_value = sorted_records[mid][key]

        if mid_value == target_value:
            return mid
        elif mid_value < target_value:
            low = mid + 1
        else:
            high = mid - 1

    return -1


def linear_search(records, target_value, key):
    """
    Baseline search: scans `records` in order and returns the index of the
    first record where record[key] == target_value, or -1 if absent.
    """
    for i, record in enumerate(records):
        if record[key] == target_value:
            return i
    return -1


# =========================================================
# Counting wrappers — same logic/contract as above, but each
# also counts and reports the number of comparisons made.
# =========================================================
 
def insertion_sort_count(records, key):
    """
    Sorts `records` in place exactly as insertion_sort does, but also
    counts every comparison made (records[j][key] > current[key]).
 
    Returns a single int: the comparison count.
    """
    comparisons = 0
    for i in range(1, len(records)):
        current = records[i]
        j = i - 1
        while j >= 0:
            comparisons += 1
            if records[j][key] > current[key]:
                records[j + 1] = records[j]
                j -= 1
            else:
                break
        records[j + 1] = current
    return comparisons
 
 
def binary_search_count(sorted_records, target_value, key):
    """
    Same logic as binary_search, but counts comparisons made against
    sorted_records[mid][key].
 
    Returns {"index": <int>, "comparison_count": <int>}.
    """
    low = 0
    high = len(sorted_records) - 1
    comparisons = 0
 
    while low <= high:
        mid = (low + high) // 2
        mid_value = sorted_records[mid][key]
        comparisons += 1
 
        if mid_value == target_value:
            return {"index": mid, "comparison_count": comparisons}
        elif mid_value < target_value:
            low = mid + 1
        else:
            high = mid - 1
 
    return {"index": -1, "comparison_count": comparisons}
 
 
def linear_search_count(records, target_value, key):
    """
    Same logic as linear_search, but counts comparisons made against
    record[key].
 
    Returns {"index": <int>, "comparison_count": <int>}.
    """
    comparisons = 0
    for i, record in enumerate(records):
        comparisons += 1
        if record[key] == target_value:
            return {"index": i, "comparison_count": comparisons}
    return {"index": -1, "comparison_count": comparisons}
 