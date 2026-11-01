"""
Verified Question Bank Service for SkillProof AI (Module 4).
Contains curated, verified coding challenges with reference solutions and test cases.
Never exposes reference solutions or hidden test cases to candidate responses.
"""

from __future__ import annotations

import re
import io
import sys
import inspect
import logging
from typing import List, Optional, Dict, Any
from app.models import Question, QuestionPublic, TestCase, QuestionResult

logger = logging.getLogger("skillproof.question_bank")

# Curated, pre-verified repository of 24 software engineering & DSA challenges
SEED_QUESTIONS: List[Question] = [
    # -------------------------------------------------------------------------
    # NOVICE (EASY) — 8 Questions
    # -------------------------------------------------------------------------
    Question(
        id="two-sum",
        title="Two Sum",
        difficulty="easy",
        domain="Algorithms & DSA",
        topic="Arrays & Hash Tables",
        language="python",
        problem_statement="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target. You may assume that each input would have exactly one solution, and you may not use the same element twice.",
        constraints="2 <= nums.length <= 10^4, -10^9 <= nums[i] <= 10^9, -10^9 <= target <= 10^9",
        starter_code="def two_sum(nums: list[int], target: int) -> list[int]:\n    # Implement your solution here\n    pass\n",
        sample_input="nums = [2, 7, 11, 15], target = 9",
        sample_output="[0, 1]",
        reference_solution="def two_sum(nums, target):\n    lookup = {}\n    for i, n in enumerate(nums):\n        diff = target - n\n        if diff in lookup:\n            return [lookup[diff], i]\n        lookup[n] = i\n    return []\n",
        test_cases=[
            TestCase(input_data="[2, 7, 11, 15], 9", expected_output="[0, 1]", is_hidden=False),
            TestCase(input_data="[3, 2, 4], 6", expected_output="[1, 2]", is_hidden=False),
            TestCase(input_data="[3, 3], 6", expected_output="[0, 1]", is_hidden=True),
        ],
    ),
    Question(
        id="valid-palindrome",
        title="Valid Palindrome",
        difficulty="easy",
        domain="Algorithms & DSA",
        topic="Strings & Two Pointers",
        language="python",
        problem_statement="A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward. Return True if phrase s is a palindrome, or False otherwise.",
        constraints="1 <= s.length <= 2 * 10^5",
        starter_code="def is_palindrome(s: str) -> bool:\n    # Implement your solution here\n    pass\n",
        sample_input='s = "A man, a plan, a canal: Panama"',
        sample_output="True",
        reference_solution="def is_palindrome(s):\n    cleaned = ''.join(ch.lower() for ch in s if ch.isalnum())\n    return cleaned == cleaned[::-1]\n",
        test_cases=[
            TestCase(input_data='"A man, a plan, a canal: Panama"', expected_output="True", is_hidden=False),
            TestCase(input_data='"race a car"', expected_output="False", is_hidden=False),
            TestCase(input_data='" "', expected_output="True", is_hidden=True),
        ],
    ),
    Question(
        id="reverse-words",
        title="Reverse Words in String",
        difficulty="easy",
        domain="Web Development",
        topic="Strings",
        language="python",
        problem_statement="Given an input string s, reverse the order of the words. A word is defined as a sequence of non-space characters. The words in s will be separated by at least one space. Return a string of the words in reverse order concatenated by a single space.",
        constraints="1 <= s.length <= 10^4",
        starter_code="def reverse_words(s: str) -> str:\n    # Implement your solution here\n    pass\n",
        sample_input='s = "the sky is blue"',
        sample_output='"blue is sky the"',
        reference_solution="def reverse_words(s):\n    return ' '.join(s.strip().split()[::-1])\n",
        test_cases=[
            TestCase(input_data='"the sky is blue"', expected_output='"blue is sky the"', is_hidden=False),
            TestCase(input_data='"  hello world  "', expected_output='"world hello"', is_hidden=False),
            TestCase(input_data='"a good   example"', expected_output='"example good a"', is_hidden=True),
        ],
    ),
    Question(
        id="count-vowels",
        title="Count Vowels and Consonants",
        difficulty="easy",
        domain="Web Development",
        topic="Strings",
        language="python",
        problem_statement="Given a string s, return a dictionary with counts of vowels and consonants: {'vowels': int, 'consonants': int}. Ignore punctuation, spaces, and numbers.",
        constraints="0 <= len(s) <= 10^4",
        starter_code="def count_characters(s: str) -> dict:\n    # Implement your solution here\n    pass\n",
        sample_input='s = "Hello World!"',
        sample_output="{'vowels': 3, 'consonants': 7}",
        reference_solution="def count_characters(s):\n    vowels = set('aeiouAEIOU')\n    v_count = 0\n    c_count = 0\n    for ch in s:\n        if ch.isalpha():\n            if ch in vowels:\n                v_count += 1\n            else:\n                c_count += 1\n    return {'vowels': v_count, 'consonants': c_count}\n",
        test_cases=[
            TestCase(input_data='"Hello World!"', expected_output="{'vowels': 3, 'consonants': 7}", is_hidden=False),
            TestCase(input_data='"SkillProof AI"', expected_output="{'vowels': 5, 'consonants': 7}", is_hidden=False),
            TestCase(input_data='"12345"', expected_output="{'vowels': 0, 'consonants': 0}", is_hidden=True),
        ],
    ),
    Question(
        id="fizzbuzz-api",
        title="API Range Formatter (FizzBuzz)",
        difficulty="easy",
        domain="Backend Development",
        topic="Logic & Formatting",
        language="python",
        problem_statement="Given an integer n, return a string array answer (1-indexed) where: answer[i] == 'FizzBuzz' if i is divisible by 3 and 5, answer[i] == 'Fizz' if i is divisible by 3, answer[i] == 'Buzz' if i is divisible by 5, and answer[i] == str(i) otherwise.",
        constraints="1 <= n <= 10^4",
        starter_code="def fizz_buzz(n: int) -> list[str]:\n    # Implement your solution here\n    pass\n",
        sample_input="n = 5",
        sample_output="['1', '2', 'Fizz', '4', 'Buzz']",
        reference_solution="def fizz_buzz(n):\n    res = []\n    for i in range(1, n + 1):\n        if i % 15 == 0:\n            res.append('FizzBuzz')\n        elif i % 3 == 0:\n            res.append('Fizz')\n        elif i % 5 == 0:\n            res.append('Buzz')\n        else:\n            res.append(str(i))\n    return res\n",
        test_cases=[
            TestCase(input_data="3", expected_output="['1', '2', 'Fizz']", is_hidden=False),
            TestCase(input_data="5", expected_output="['1', '2', 'Fizz', '4', 'Buzz']", is_hidden=False),
            TestCase(input_data="15", expected_output="['1', '2', 'Fizz', '4', 'Buzz', 'Fizz', '7', '8', 'Fizz', 'Buzz', '11', 'Fizz', '13', '14', 'FizzBuzz']", is_hidden=True),
        ],
    ),
    Question(
        id="factorial-memo",
        title="Factorial with Caching",
        difficulty="easy",
        domain="Backend Development",
        topic="Recursion & Caching",
        language="python",
        problem_statement="Compute the factorial of a non-negative integer n. For n = 0, factorial is 1. If n is negative, raise a ValueError with 'Input must be non-negative'.",
        constraints="0 <= n <= 20",
        starter_code="def factorial(n: int) -> int:\n    # Implement your solution here\n    pass\n",
        sample_input="n = 5",
        sample_output="120",
        reference_solution="def factorial(n):\n    if n < 0:\n        raise ValueError('Input must be non-negative')\n    res = 1\n    for i in range(2, n + 1):\n        res *= i\n    return res\n",
        test_cases=[
            TestCase(input_data="0", expected_output="1", is_hidden=False),
            TestCase(input_data="5", expected_output="120", is_hidden=False),
            TestCase(input_data="7", expected_output="5040", is_hidden=True),
        ],
    ),
    Question(
        id="filter-active-users",
        title="Filter and Transform Records",
        difficulty="easy",
        domain="Backend Development",
        topic="Data Filtering",
        language="python",
        problem_statement="Given a list of user dictionaries each containing 'name', 'status', and 'role', return a list of names for all users who have status == 'active' and role == 'student', sorted alphabetically.",
        constraints="0 <= len(users) <= 1000",
        starter_code="def filter_students(users: list[dict]) -> list[str]:\n    # Implement your solution here\n    pass\n",
        sample_input="users = [{'name': 'Bob', 'status': 'active', 'role': 'student'}, {'name': 'Alice', 'status': 'active', 'role': 'student'}, {'name': 'Eve', 'status': 'pending', 'role': 'student'}]",
        sample_output="['Alice', 'Bob']",
        reference_solution="def filter_students(users):\n    return sorted([u['name'] for u in users if u.get('status') == 'active' and u.get('role') == 'student'])\n",
        test_cases=[
            TestCase(input_data="[{'name': 'Bob', 'status': 'active', 'role': 'student'}, {'name': 'Alice', 'status': 'active', 'role': 'student'}, {'name': 'Eve', 'status': 'pending', 'role': 'student'}]", expected_output="['Alice', 'Bob']", is_hidden=False),
            TestCase(input_data="[]", expected_output="[]", is_hidden=True),
        ],
    ),
    Question(
        id="merge-sorted-arrays",
        title="Merge Two Sorted Arrays",
        difficulty="easy",
        domain="Algorithms & DSA",
        topic="Arrays & Two Pointers",
        language="python",
        problem_statement="Given two sorted integer arrays nums1 and nums2, return a new sorted array combining all elements from both arrays in non-decreasing order.",
        constraints="0 <= nums1.length, nums2.length <= 1000",
        starter_code="def merge_sorted(nums1: list[int], nums2: list[int]) -> list[int]:\n    # Implement your solution here\n    pass\n",
        sample_input="nums1 = [1, 2, 4], nums2 = [1, 3, 4]",
        sample_output="[1, 1, 2, 3, 4, 4]",
        reference_solution="def merge_sorted(nums1, nums2):\n    res = []\n    i = j = 0\n    while i < len(nums1) and j < len(nums2):\n        if nums1[i] <= nums2[j]:\n            res.append(nums1[i])\n            i += 1\n        else:\n            res.append(nums2[j])\n            j += 1\n    res.extend(nums1[i:])\n    res.extend(nums2[j:])\n    return res\n",
        test_cases=[
            TestCase(input_data="[1, 2, 4], [1, 3, 4]", expected_output="[1, 1, 2, 3, 4, 4]", is_hidden=False),
            TestCase(input_data="[], [1]", expected_output="[1]", is_hidden=False),
            TestCase(input_data="[2, 5], [1, 3, 6, 8]", expected_output="[1, 2, 3, 5, 6, 8]", is_hidden=True),
        ],
    ),

    # -------------------------------------------------------------------------
    # ADEPT (MEDIUM) — 8 Questions
    # -------------------------------------------------------------------------
    Question(
        id="group-anagrams",
        title="Group Anagrams",
        difficulty="medium",
        domain="Algorithms & DSA",
        topic="Hash Tables & Sorting",
        language="python",
        problem_statement="Given an array of strings strs, group the anagrams together. You can return the answer in any order, but each sub-group should have its words sorted.",
        constraints="1 <= strs.length <= 10^4, 0 <= strs[i].length <= 100",
        starter_code="def group_anagrams(strs: list[str]) -> list[list[str]]:\n    # Implement your solution here\n    pass\n",
        sample_input='strs = ["eat", "tea", "tan", "ate", "nat", "bat"]',
        sample_output='[["bat"], ["nat", "tan"], ["ate", "eat", "tea"]]',
        reference_solution="def group_anagrams(strs):\n    import collections\n    ans = collections.defaultdict(list)\n    for s in strs:\n        ans[''.join(sorted(s))].append(s)\n    return sorted([sorted(group) for group in ans.values()])\n",
        test_cases=[
            TestCase(input_data='["eat", "tea", "tan", "ate", "nat", "bat"]', expected_output='[["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]', is_hidden=False),
            TestCase(input_data='[""]', expected_output='[[""]]', is_hidden=False),
            TestCase(input_data='["a"]', expected_output='[["a"]]', is_hidden=True),
        ],
    ),
    Question(
        id="longest-substring-no-repeat",
        title="Longest Substring Without Repeating Characters",
        difficulty="medium",
        domain="Algorithms & DSA",
        topic="Sliding Window",
        language="python",
        problem_statement="Given a string s, find the length of the longest substring without duplicate characters.",
        constraints="0 <= s.length <= 5 * 10^4",
        starter_code="def length_of_longest_substring(s: str) -> int:\n    # Implement your solution here\n    pass\n",
        sample_input='s = "abcabcbb"',
        sample_output="3",
        reference_solution="def length_of_longest_substring(s):\n    char_index = {}\n    max_len = 0\n    start = 0\n    for i, ch in enumerate(s):\n        if ch in char_index and char_index[ch] >= start:\n            start = char_index[ch] + 1\n        char_index[ch] = i\n        max_len = max(max_len, i - start + 1)\n    return max_len\n",
        test_cases=[
            TestCase(input_data='"abcabcbb"', expected_output="3", is_hidden=False),
            TestCase(input_data='"bbbbb"', expected_output="1", is_hidden=False),
            TestCase(input_data='"pwwkew"', expected_output="3", is_hidden=True),
        ],
    ),
    Question(
        id="subarray-sum-k",
        title="Subarray Sum Equals K",
        difficulty="medium",
        domain="Algorithms & DSA",
        topic="Prefix Sum & Hash Tables",
        language="python",
        problem_statement="Given an array of integers nums and an integer k, return the total number of continuous subarrays whose sum equals to k.",
        constraints="1 <= nums.length <= 2 * 10^4, -1000 <= nums[i] <= 1000, -10^7 <= k <= 10^7",
        starter_code="def subarray_sum(nums: list[int], k: int) -> int:\n    # Implement your solution here\n    pass\n",
        sample_input="nums = [1, 1, 1], k = 2",
        sample_output="2",
        reference_solution="def subarray_sum(nums, k):\n    count = 0\n    curr_sum = 0\n    prefix_sums = {0: 1}\n    for n in nums:\n        curr_sum += n\n        if (curr_sum - k) in prefix_sums:\n            count += prefix_sums[curr_sum - k]\n        prefix_sums[curr_sum] = prefix_sums.get(curr_sum, 0) + 1\n    return count\n",
        test_cases=[
            TestCase(input_data="[1, 1, 1], 2", expected_output="2", is_hidden=False),
            TestCase(input_data="[1, 2, 3], 3", expected_output="2", is_hidden=False),
            TestCase(input_data="[1, -1, 0], 0", expected_output="3", is_hidden=True),
        ],
    ),
    Question(
        id="lru-cache-mechanism",
        title="LRU Cache Mechanism",
        difficulty="medium",
        domain="Backend Development",
        topic="Caching & Data Structures",
        language="python",
        problem_statement=(
            "Implement an LRUCache class with a fixed capacity. "
            "Implement get(key) -> int (returns -1 if absent) and put(key, value) -> None "
            "(evicts the least-recently-used key when over capacity). "
            "Then implement lru_cache_runner(capacity, ops) -> list which instantiates "
            "LRUCache(capacity) and runs each op tuple: ('put', key, value) or ('get', key), "
            "returning a list of results (None for put, int for get)."
        ),
        constraints="capacity >= 1; 1 <= len(ops) <= 1000",
        starter_code=(
            "class LRUCache:\n"
            "    def __init__(self, capacity: int):\n"
            "        pass\n"
            "    def get(self, key: int) -> int:\n"
            "        pass\n"
            "    def put(self, key: int, value: int) -> None:\n"
            "        pass\n"
            "\n"
            "def lru_cache_runner(capacity: int, ops: list) -> list:\n"
            "    \"\"\"Run ops on LRUCache(capacity). ops: [('put',k,v)|('get',k)]\"\"\"\n"
            "    pass\n"
        ),
        sample_input="capacity=2, ops=[('put',1,1),('put',2,2),('get',1),('put',3,3),('get',2)]",
        sample_output="[None, None, 1, None, -1]",
        reference_solution=(
            "from collections import OrderedDict\n"
            "class LRUCache:\n"
            "    def __init__(self, capacity):\n"
            "        self.capacity = capacity\n"
            "        self.cache = OrderedDict()\n"
            "    def get(self, key):\n"
            "        if key not in self.cache:\n"
            "            return -1\n"
            "        self.cache.move_to_end(key)\n"
            "        return self.cache[key]\n"
            "    def put(self, key, value):\n"
            "        if key in self.cache:\n"
            "            self.cache.move_to_end(key)\n"
            "        self.cache[key] = value\n"
            "        if len(self.cache) > self.capacity:\n"
            "            self.cache.popitem(last=False)\n"
            "\n"
            "def lru_cache_runner(capacity, ops):\n"
            "    cache = LRUCache(capacity)\n"
            "    results = []\n"
            "    for op in ops:\n"
            "        if op[0] == 'put':\n"
            "            results.append(cache.put(op[1], op[2]))\n"
            "        else:\n"
            "            results.append(cache.get(op[1]))\n"
            "    return results\n"
        ),
        test_cases=[
            TestCase(
                input_data="2, [('put', 1, 1), ('put', 2, 2), ('get', 1), ('put', 3, 3), ('get', 2)]",
                expected_output="[None, None, 1, None, -1]",
                is_hidden=False,
            ),
            TestCase(
                input_data="1, [('put', 1, 10), ('get', 1), ('put', 2, 20), ('get', 1), ('get', 2)]",
                expected_output="[None, 10, None, -1, 20]",
                is_hidden=True,
            ),
        ],
    ),
    Question(
        id="rate-limiter-token-bucket",
        title="Token Bucket Rate Limiter",
        difficulty="medium",
        domain="Backend Development",
        topic="Rate Limiting",
        language="python",
        problem_statement="Implement a token bucket rate limiter function simulate_rate_limiter(capacity: int, refill_rate: float, requests: list[float]) -> list[bool]. Each request arrives at time t. The bucket refills at refill_rate tokens/sec up to capacity. Consuming 1 request uses 1 token. Return True for allowed, False for throttled.",
        constraints="capacity >= 1, refill_rate > 0",
        starter_code="def simulate_rate_limiter(capacity: int, refill_rate: float, requests: list[float]) -> list[bool]:\n    # Implement your solution here\n    pass\n",
        sample_input="capacity = 3, refill_rate = 1.0, requests = [0.0, 0.2, 0.4, 0.6, 2.0]",
        sample_output="[True, True, True, False, True]",
        reference_solution="def simulate_rate_limiter(capacity, refill_rate, requests):\n    tokens = float(capacity)\n    last_time = 0.0\n    results = []\n    for t in requests:\n        tokens = min(float(capacity), tokens + (t - last_time) * refill_rate)\n        last_time = t\n        if tokens >= 1.0:\n            tokens -= 1.0\n            results.append(True)\n        else:\n            results.append(False)\n    return results\n",
        test_cases=[
            TestCase(input_data="3, 1.0, [0.0, 0.2, 0.4, 0.6, 2.0]", expected_output="[True, True, True, False, True]", is_hidden=False),
            TestCase(input_data="1, 0.5, [0.0, 1.0, 1.5, 3.0]", expected_output="[True, False, False, True]", is_hidden=True),
        ],
    ),
    Question(
        id="invert-binary-tree",
        title="Invert Binary Tree",
        difficulty="medium",
        domain="Algorithms & DSA",
        topic="Trees & Recursion",
        language="python",
        problem_statement="Given a nested dictionary representing a binary tree node {'val': int, 'left': dict | None, 'right': dict | None}, invert the tree (swap left and right subtrees recursively) and return the inverted root.",
        constraints="0 <= Node count <= 1000",
        starter_code="def invert_tree(root: dict | None) -> dict | None:\n    # Implement your solution here\n    pass\n",
        sample_input="root = {'val': 4, 'left': {'val': 2, 'left': None, 'right': None}, 'right': {'val': 7, 'left': None, 'right': None}}",
        sample_output="{'val': 4, 'left': {'val': 7, 'left': None, 'right': None}, 'right': {'val': 2, 'left': None, 'right': None}}",
        reference_solution="def invert_tree(root):\n    if not root:\n        return None\n    left = invert_tree(root.get('left'))\n    right = invert_tree(root.get('right'))\n    root['left'] = right\n    root['right'] = left\n    return root\n",
        test_cases=[
            TestCase(input_data="{'val': 4, 'left': {'val': 2, 'left': None, 'right': None}, 'right': {'val': 7, 'left': None, 'right': None}}", expected_output="{'val': 4, 'left': {'val': 7, 'left': None, 'right': None}, 'right': {'val': 2, 'left': None, 'right': None}}", is_hidden=False),
            TestCase(input_data="None", expected_output="None", is_hidden=True),
        ],
    ),
    Question(
        id="binary-tree-level-order",
        title="Binary Tree Level Order Traversal",
        difficulty="medium",
        domain="Algorithms & DSA",
        topic="Trees & Queues",
        language="python",
        problem_statement="Given the root of a binary tree as a dictionary node {'val': int, 'left': dict, 'right': dict}, return the level order traversal of its nodes' values (i.e., from left to right, level by level as list[list[int]]).",
        constraints="0 <= Node count <= 2000",
        starter_code="def level_order(root: dict | None) -> list[list[int]]:\n    # Implement your solution here\n    pass\n",
        sample_input="root = {'val': 3, 'left': {'val': 9, 'left': None, 'right': None}, 'right': {'val': 20, 'left': {'val': 15, 'left': None, 'right': None}, 'right': {'val': 7, 'left': None, 'right': None}}}",
        sample_output="[[3], [9, 20], [15, 7]]",
        reference_solution="def level_order(root):\n    if not root:\n        return []\n    res = []\n    queue = [root]\n    while queue:\n        level = []\n        next_q = []\n        for node in queue:\n            level.append(node['val'])\n            if node.get('left'): next_q.append(node['left'])\n            if node.get('right'): next_q.append(node['right'])\n        res.append(level)\n        queue = next_q\n    return res\n",
        test_cases=[
            TestCase(input_data="{'val': 3, 'left': {'val': 9, 'left': None, 'right': None}, 'right': {'val': 20, 'left': {'val': 15, 'left': None, 'right': None}, 'right': {'val': 7, 'left': None, 'right': None}}}", expected_output="[[3], [9, 20], [15, 7]]", is_hidden=False),
            TestCase(input_data="None", expected_output="[]", is_hidden=True),
        ],
    ),
    Question(
        id="async-task-pipeline",
        title="Dependency Task Pipeline Order",
        difficulty="medium",
        domain="Backend Development",
        topic="Topological Sort & Queues",
        language="python",
        problem_statement="Given num_tasks and a list of prerequisites [[task_a, task_b]] indicating task_b must be completed before task_a, return a valid task execution order as a list. If a circular deadlock is detected, return an empty list.",
        constraints="1 <= num_tasks <= 2000",
        starter_code="def task_order(num_tasks: int, prerequisites: list[list[int]]) -> list[int]:\n    # Implement your solution here\n    pass\n",
        sample_input="num_tasks = 2, prerequisites = [[1, 0]]",
        sample_output="[0, 1]",
        reference_solution="from collections import deque, defaultdict\ndef task_order(num_tasks, prerequisites):\n    graph = defaultdict(list)\n    in_degree = [0] * num_tasks\n    for dest, src in prerequisites:\n        graph[src].append(dest)\n        in_degree[dest] += 1\n    queue = deque([i for i in range(num_tasks) if in_degree[i] == 0])\n    order = []\n    while queue:\n        u = queue.popleft()\n        order.append(u)\n        for v in graph[u]:\n            in_degree[v] -= 1\n            if in_degree[v] == 0:\n                queue.append(v)\n    return order if len(order) == num_tasks else []\n",
        test_cases=[
            TestCase(input_data="2, [[1, 0]]", expected_output="[0, 1]", is_hidden=False),
            TestCase(input_data="4, [[1, 0], [2, 0], [3, 1], [3, 2]]", expected_output="[0, 1, 2, 3]", is_hidden=False),
            TestCase(input_data="2, [[1, 0], [0, 1]]", expected_output="[]", is_hidden=True),
        ],
    ),

    # -------------------------------------------------------------------------
    # MASTER (HARD) — 8 Questions
    # -------------------------------------------------------------------------
    Question(
        id="trapping-rain-water",
        title="Trapping Rain Water",
        difficulty="hard",
        domain="Algorithms & DSA",
        topic="Two Pointers & Monotonic Stack",
        language="python",
        problem_statement="Given n non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.",
        constraints="n == height.length, 1 <= n <= 2 * 10^4, 0 <= height[i] <= 10^5",
        starter_code="def trap(height: list[int]) -> int:\n    # Implement your solution here\n    pass\n",
        sample_input="height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]",
        sample_output="6",
        reference_solution="def trap(height):\n    if not height: return 0\n    l, r = 0, len(height) - 1\n    left_max, right_max = height[l], height[r]\n    water = 0\n    while l < r:\n        if left_max < right_max:\n            l += 1\n            left_max = max(left_max, height[l])\n            water += left_max - height[l]\n        else:\n            r -= 1\n            right_max = max(right_max, height[r])\n            water += right_max - height[r]\n    return water\n",
        test_cases=[
            TestCase(input_data="[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]", expected_output="6", is_hidden=False),
            TestCase(input_data="[4, 2, 0, 3, 2, 5]", expected_output="9", is_hidden=False),
            TestCase(input_data="[1, 1, 1]", expected_output="0", is_hidden=True),
        ],
    ),
    Question(
        id="merge-k-sorted-lists",
        title="Merge K Sorted Lists",
        difficulty="hard",
        domain="Algorithms & DSA",
        topic="Heaps & Priority Queues",
        language="python",
        problem_statement="You are given an array of k sorted integer lists. Merge all the lists into one sorted list and return it in non-decreasing order with O(N log k) time complexity.",
        constraints="k == lists.length, 0 <= k <= 10^4, 0 <= total nodes <= 10^4",
        starter_code="def merge_k_lists(lists: list[list[int]]) -> list[int]:\n    # Implement your solution here\n    pass\n",
        sample_input="lists = [[1, 4, 5], [1, 3, 4], [2, 6]]",
        sample_output="[1, 1, 2, 3, 4, 4, 5, 6]",
        reference_solution="import heapq\ndef merge_k_lists(lists):\n    min_heap = []\n    for i, lst in enumerate(lists):\n        if lst:\n            heapq.heappush(min_heap, (lst[0], i, 0))\n    res = []\n    while min_heap:\n        val, list_idx, elem_idx = heapq.heappop(min_heap)\n        res.append(val)\n        if elem_idx + 1 < len(lists[list_idx]):\n            next_val = lists[list_idx][elem_idx + 1]\n            heapq.heappush(min_heap, (next_val, list_idx, elem_idx + 1))\n    return res\n",
        test_cases=[
            TestCase(input_data="[[1, 4, 5], [1, 3, 4], [2, 6]]", expected_output="[1, 1, 2, 3, 4, 4, 5, 6]", is_hidden=False),
            TestCase(input_data="[]", expected_output="[]", is_hidden=False),
            TestCase(input_data="[[], [1]]", expected_output="[1]", is_hidden=True),
        ],
    ),
    Question(
        id="longest-valid-parentheses",
        title="Longest Valid Parentheses",
        difficulty="hard",
        domain="Algorithms & DSA",
        topic="Dynamic Programming & Stacks",
        language="python",
        problem_statement="Given a string containing just the characters '(' and ')', return the length of the longest valid (well-formed) parentheses substring.",
        constraints="0 <= s.length <= 3 * 10^4",
        starter_code="def longest_valid_parentheses(s: str) -> int:\n    # Implement your solution here\n    pass\n",
        sample_input='s = ")()())"',
        sample_output="4",
        reference_solution="def longest_valid_parentheses(s):\n    stack = [-1]\n    max_len = 0\n    for i, ch in enumerate(s):\n        if ch == '(':\n            stack.append(i)\n        else:\n            stack.pop()\n            if not stack:\n                stack.append(i)\n            else:\n                max_len = max(max_len, i - stack[-1])\n    return max_len\n",
        test_cases=[
            TestCase(input_data='")()())"', expected_output="4", is_hidden=False),
            TestCase(input_data='"(()"', expected_output="2", is_hidden=False),
            TestCase(input_data='""', expected_output="0", is_hidden=True),
        ],
    ),
    Question(
        id="median-two-sorted-arrays",
        title="Median of Two Sorted Arrays",
        difficulty="hard",
        domain="Algorithms & DSA",
        topic="Binary Search & Divide and Conquer",
        language="python",
        problem_statement="Given two sorted arrays nums1 and nums2 of size m and n respectively, return the median of the two sorted arrays. The overall run time complexity should be O(log (m+n)).",
        constraints="0 <= m, n <= 1000, 1 <= m + n <= 2000",
        starter_code="def find_median_sorted_arrays(nums1: list[int], nums2: list[int]) -> float:\n    # Implement your solution here\n    pass\n",
        sample_input="nums1 = [1, 3], nums2 = [2]",
        sample_output="2.0",
        reference_solution="def find_median_sorted_arrays(nums1, nums2):\n    A, B = nums1, nums2\n    total = len(A) + len(B)\n    half = total // 2\n    if len(B) < len(A):\n        A, B = B, A\n    l, r = 0, len(A) - 1\n    while True:\n        i = (l + r) // 2\n        j = half - i - 2\n        Aleft = A[i] if i >= 0 else float('-infinity')\n        Aright = A[i + 1] if (i + 1) < len(A) else float('infinity')\n        Bleft = B[j] if j >= 0 else float('-infinity')\n        Bright = B[j + 1] if (j + 1) < len(B) else float('infinity')\n        if Aleft <= Bright and Bleft <= Aright:\n            if total % 2:\n                return float(min(Aright, Bright))\n            return (max(Aleft, Bleft) + min(Aright, Bright)) / 2.0\n        elif Aleft > Bright:\n            r = i - 1\n        else:\n            l = i + 1\n",
        test_cases=[
            TestCase(input_data="[1, 3], [2]", expected_output="2.0", is_hidden=False),
            TestCase(input_data="[1, 2], [3, 4]", expected_output="2.5", is_hidden=False),
            TestCase(input_data="[0, 0], [0, 0]", expected_output="0.0", is_hidden=True),
        ],
    ),
    Question(
        id="word-ladder",
        title="Word Ladder BFS",
        difficulty="hard",
        domain="Algorithms & DSA",
        topic="Graphs & BFS",
        language="python",
        problem_statement="Given two words, begin_word and end_word, and a dictionary word_list, return the number of words in the shortest transformation sequence from begin_word to end_word, or 0 if no sequence exists.",
        constraints="1 <= begin_word.length <= 10, word_list.length <= 5000",
        starter_code="def ladder_length(begin_word: str, end_word: str, word_list: list[str]) -> int:\n    # Implement your solution here\n    pass\n",
        sample_input='begin_word = "hit", end_word = "cog", word_list = ["hot","dot","dog","lot","log","cog"]',
        sample_output="5",
        reference_solution="from collections import deque\ndef ladder_length(begin_word, end_word, word_list):\n    words = set(word_list)\n    if end_word not in words:\n        return 0\n    queue = deque([(begin_word, 1)])\n    visited = {begin_word}\n    while queue:\n        word, steps = queue.popleft()\n        if word == end_word:\n            return steps\n        for i in range(len(word)):\n            for c in 'abcdefghijklmnopqrstuvwxyz':\n                next_w = word[:i] + c + word[i+1:]\n                if next_w in words and next_w not in visited:\n                    visited.add(next_w)\n                    queue.append((next_w, steps + 1))\n    return 0\n",
        test_cases=[
            TestCase(input_data='"hit", "cog", ["hot","dot","dog","lot","log","cog"]', expected_output="5", is_hidden=False),
            TestCase(input_data='"hit", "cog", ["hot","dot","dog","lot","log"]', expected_output="0", is_hidden=False),
        ],
    ),
    Question(
        id="distributed-quorum-checker",
        title="Distributed Quorum Consensus",
        difficulty="hard",
        domain="Backend Development",
        topic="Distributed Systems",
        language="python",
        problem_statement="In a distributed cluster of n nodes, calculate if a write operation achieves majority quorum. Given n nodes, write_quorum W, and a list of node responses with timestamps [{'node_id': int, 'status': str, 'timestamp': float}], determine if at least W active nodes successfully acknowledged within timeout_ms. Return a dict with {'consensus_reached': bool, 'ack_count': int}.",
        constraints="1 <= n <= 100",
        starter_code="def check_quorum(total_nodes: int, write_quorum: int, responses: list[dict], timeout_ms: float) -> dict:\n    # Implement your solution here\n    pass\n",
        sample_input="total_nodes = 5, write_quorum = 3, responses = [{'node_id': 1, 'status': 'ok', 'timestamp': 10.0}, {'node_id': 2, 'status': 'ok', 'timestamp': 15.0}, {'node_id': 3, 'status': 'ok', 'timestamp': 45.0}], timeout_ms = 50.0",
        sample_output="{'consensus_reached': True, 'ack_count': 3}",
        reference_solution="def check_quorum(total_nodes, write_quorum, responses, timeout_ms):\n    acks = sum(1 for r in responses if r.get('status') == 'ok' and r.get('timestamp', 0) <= timeout_ms)\n    return {'consensus_reached': acks >= write_quorum, 'ack_count': acks}\n",
        test_cases=[
            TestCase(input_data="5, 3, [{'node_id': 1, 'status': 'ok', 'timestamp': 10.0}, {'node_id': 2, 'status': 'ok', 'timestamp': 15.0}, {'node_id': 3, 'status': 'ok', 'timestamp': 45.0}], 50.0", expected_output="{'consensus_reached': True, 'ack_count': 3}", is_hidden=False),
            TestCase(input_data="5, 3, [{'node_id': 1, 'status': 'ok', 'timestamp': 10.0}, {'node_id': 2, 'status': 'err', 'timestamp': 15.0}], 50.0", expected_output="{'consensus_reached': False, 'ack_count': 1}", is_hidden=True),
        ],
    ),
    Question(
        id="concurrent-resource-pool",
        title="Resource Pool Leaser",
        difficulty="hard",
        domain="Backend Development",
        topic="Concurrency & Resource Management",
        language="python",
        problem_statement="Simulate a resource pool leaser: manage pool_size resources. Given a sequence of events [('acquire', req_id, duration), ('release', req_id)], track resource allocations and return the number of requests successfully served without waiting more than max_wait time.",
        constraints="pool_size >= 1",
        starter_code="def simulate_pool(pool_size: int, events: list[tuple]) -> int:\n    # Implement your solution here\n    pass\n",
        sample_input="pool_size = 2, events = [('acquire', 1), ('acquire', 2), ('acquire', 3)]",
        sample_output="2",
        reference_solution="def simulate_pool(pool_size, events):\n    active = 0\n    served = 0\n    for ev in events:\n        op = ev[0]\n        if op == 'acquire':\n            if active < pool_size:\n                active += 1\n                served += 1\n        elif op == 'release':\n            if active > 0:\n                active -= 1\n    return served\n",
        test_cases=[
            TestCase(input_data="2, [('acquire', 1), ('acquire', 2), ('acquire', 3)]", expected_output="2", is_hidden=False),
            TestCase(input_data="2, [('acquire', 1), ('release', 1), ('acquire', 2), ('acquire', 3)]", expected_output="3", is_hidden=True),
        ],
    ),
    Question(
        id="alien-dictionary",
        title="Alien Dictionary Topological Sort",
        difficulty="hard",
        domain="Algorithms & DSA",
        topic="Graphs & Topological Sort",
        language="python",
        problem_statement="There is a new alien language that uses the English alphabet. Given a list of words from the alien language dictionary sorted lexicographically by their rules, derive the order of letters in this language as a string. If no valid order exists, return ''.",
        constraints="1 <= words.length <= 100",
        starter_code="def alien_order(words: list[str]) -> str:\n    # Implement your solution here\n    pass\n",
        sample_input='words = ["wrt","wrf","er","ett","rftt"]',
        sample_output='"wertf"',
        reference_solution="def alien_order(words):\n    adj = {c: set() for w in words for c in w}\n    for i in range(len(words) - 1):\n        w1, w2 = words[i], words[i + 1]\n        min_len = min(len(w1), len(w2))\n        if len(w1) > len(w2) and w1[:min_len] == w2[:min_len]:\n            return ''\n        for j in range(min_len):\n            if w1[j] != w2[j]:\n                adj[w1[j]].add(w2[j])\n                break\n    visited = {}\n    res = []\n    def dfs(c):\n        if c in visited:\n            return visited[c]\n        visited[c] = True\n        for neighbor in adj[c]:\n            if dfs(neighbor):\n                return True\n        visited[c] = False\n        res.append(c)\n        return False\n    for c in adj:\n        if dfs(c):\n            return ''\n    return ''.join(res[::-1])\n",
        test_cases=[
            TestCase(input_data='["wrt","wrf","er","ett","rftt"]', expected_output='"wertf"', is_hidden=False),
            TestCase(input_data='["z","x"]', expected_output='"zx"', is_hidden=False),
            TestCase(input_data='["z","x","z"]', expected_output='""', is_hidden=True),
        ],
    ),
]


def get_all_questions() -> List[Question]:
    """Returns all curated questions."""
    return list(SEED_QUESTIONS)


def get_question_by_id(question_id: str) -> Optional[Question]:
    """Retrieves a single question by id slug."""
    for q in SEED_QUESTIONS:
        if q.id == question_id:
            return q
    return None


def to_public_question(q: Question) -> QuestionPublic:
    """
    Transforms internal Question into QuestionPublic:
    Conceals reference solution and hidden evaluation test cases.
    """
    public_tests = [t for t in q.test_cases if not t.is_hidden]
    return QuestionPublic(
        id=q.id,
        title=q.title,
        difficulty=q.difficulty,
        domain=q.domain,
        topic=q.topic,
        language=q.language,
        problem_statement=q.problem_statement,
        constraints=q.constraints,
        starter_code=q.starter_code,
        sample_input=q.sample_input,
        sample_output=q.sample_output,
        public_test_cases=public_tests,
    )


def filter_questions(
    difficulty: Optional[str] = None,
    domain: Optional[str] = None,
    topic: Optional[str] = None,
) -> List[Question]:
    """Filters questions by difficulty, domain, or topic."""
    res = SEED_QUESTIONS
    if difficulty:
        d_lower = difficulty.lower()
        # map tier names if passed
        if d_lower == "novice": d_lower = "easy"
        elif d_lower == "adept": d_lower = "medium"
        elif d_lower == "master": d_lower = "hard"
        res = [q for q in res if q.difficulty == d_lower]
    if domain:
        dom_lower = domain.lower()
        res = [q for q in res if dom_lower in q.domain.lower()]
    if topic:
        t_lower = topic.lower()
        res = [q for q in res if t_lower in q.topic.lower()]
    return res


def evaluate_submission(question: Question, submitted_code: str) -> QuestionResult:
    """
    Evaluates a candidate's submission deterministically against all test cases.
    Rules:
      - 100% deterministic assertion execution.
      - Never uses an LLM to grade.
      - Tests against both public and hidden test cases.
    """
    clean_code = submitted_code.strip()
    if not clean_code or clean_code == question.starter_code.strip():
        return QuestionResult(
            question_id=question.id,
            title=question.title,
            difficulty=question.difficulty,
            domain=question.domain,
            passed_tests=0,
            total_tests=len(question.test_cases),
            all_passed=False,
            feedback="No implementation provided or starter code unmodified.",
        )

    # -----------------------------------------------------------------------
    # Extract the primary entry-point name from starter_code.
    # Prefer the first `def` (function) so class + runner patterns work
    # correctly; fall back to the first `class` for pure class questions.
    # -----------------------------------------------------------------------
    _def_match = re.search(r'^def\s+(\w+)', question.starter_code, re.MULTILINE)
    _cls_match = re.search(r'^class\s+(\w+)', question.starter_code, re.MULTILINE)
    _entry_match = _def_match or _cls_match
    entry_name = _entry_match.group(1) if _entry_match else None

    # Syntax check
    try:
        compiled = compile(clean_code, f"<candidate_{question.id}>", "exec")
    except SyntaxError as syn_err:
        return QuestionResult(
            question_id=question.id,
            title=question.title,
            difficulty=question.difficulty,
            domain=question.domain,
            passed_tests=0,
            total_tests=len(question.test_cases),
            all_passed=False,
            feedback=f"Syntax Error: {syn_err.msg} (Line {syn_err.lineno})",
        )

    passed_count = 0
    total_count = len(question.test_cases)
    first_failure = None

    # -----------------------------------------------------------------------
    # Execute the submission using local_env as BOTH globals and locals.
    # This ensures:
    #   1. Module-level imports (e.g. `import heapq`, `from collections import deque`)
    #      are stored in the same dict that function bodies use as globals, so
    #      they are accessible when the function is actually called.
    #   2. Recursive functions can resolve their own name in globals.
    # -----------------------------------------------------------------------
    local_env: Dict[str, Any] = {}
    try:
        exec(compiled, local_env)
    except Exception as exc:
        return QuestionResult(
            question_id=question.id,
            title=question.title,
            difficulty=question.difficulty,
            domain=question.domain,
            passed_tests=0,
            total_tests=total_count,
            all_passed=False,
            feedback=f"Runtime Error during definition: {str(exc)}",
        )

    # -----------------------------------------------------------------------
    # Locate the entry-point callable.
    # Priority 1: name derived from starter_code via regex.
    # Priority 2: first user-defined function found in local_env.
    # Priority 3: first user-defined class found in local_env.
    # -----------------------------------------------------------------------
    fn = None
    if entry_name:
        candidate = local_env.get(entry_name)
        if callable(candidate):
            fn = candidate

    if fn is None:
        for k, v in local_env.items():
            if inspect.isfunction(v) and not k.startswith("__"):
                fn = v
                break

    if fn is None:
        return QuestionResult(
            question_id=question.id,
            title=question.title,
            difficulty=question.difficulty,
            domain=question.domain,
            passed_tests=0,
            total_tests=total_count,
            all_passed=False,
            feedback="No callable function found in submission.",
        )

    # -----------------------------------------------------------------------
    # Run each test case.
    # eval uses local_env as the global namespace so that any helper
    # functions or imported names defined at module level are visible.
    # -----------------------------------------------------------------------
    for idx, test in enumerate(question.test_cases):
        try:
            eval_globals = dict(local_env)
            eval_globals["_entry_fn"] = fn
            actual_res = eval(f"_entry_fn({test.input_data})", eval_globals)
            expected_res = eval(test.expected_output, eval_globals)

            if actual_res == expected_res or str(actual_res) == str(expected_res):
                passed_count += 1
            else:
                if not first_failure:
                    first_failure = (
                        f"Test {idx + 1} failed: expected {test.expected_output}, "
                        f"got {actual_res!r}"
                    )
        except Exception as exc:
            if not first_failure:
                first_failure = f"Test {idx + 1} raised an exception: {str(exc)}"

    all_passed = passed_count == total_count
    feedback = (
        "All test cases passed successfully!"
        if all_passed
        else (first_failure or f"Passed {passed_count}/{total_count} tests.")
    )

    return QuestionResult(
        question_id=question.id,
        title=question.title,
        difficulty=question.difficulty,
        domain=question.domain,
        passed_tests=passed_count,
        total_tests=total_count,
        all_passed=all_passed,
        feedback=feedback,
    )
