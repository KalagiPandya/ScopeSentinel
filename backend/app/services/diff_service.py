"""
Myers-style word-level diff between two requirement texts.
No external dependencies — pure Python.
Used by the Change Detector to show exactly which words changed.
"""
from typing import List, Dict


def compute_word_diff(old_text: str, new_text: str) -> List[Dict]:
    """
    Returns a list of tokens, each with a 'word' and 'type'.
    type is one of: 'unchanged', 'added', 'removed'

    Example:
      old: "Users can login with email"
      new: "Users can login with email and OTP"
      result: [..., {"word": "and", "type": "added"}, {"word": "OTP", "type": "added"}]
    """
    old_words = old_text.split()
    new_words = new_text.split()
    m, n = len(old_words), len(new_words)

    # Build LCS (Longest Common Subsequence) table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if old_words[i - 1].lower() == new_words[j - 1].lower():
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    # Backtrack to produce diff
    diff, i, j = [], m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and old_words[i-1].lower() == new_words[j-1].lower():
            diff.append({"word": old_words[i - 1], "type": "unchanged"})
            i -= 1; j -= 1
        elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):
            diff.append({"word": new_words[j - 1], "type": "added"})
            j -= 1
        else:
            diff.append({"word": old_words[i - 1], "type": "removed"})
            i -= 1

    diff.reverse()
    return diff


def get_change_summary(old_text: str, new_text: str) -> dict:
    """Full diff analysis — tokens + added/removed word lists + formatted string."""
    diff = compute_word_diff(old_text, new_text)
    added   = [t["word"] for t in diff if t["type"] == "added"]
    removed = [t["word"] for t in diff if t["type"] == "removed"]

    parts = []
    for t in diff:
        if t["type"] == "added":
            parts.append(f"[+{t['word']}]")
        elif t["type"] == "removed":
            parts.append(f"[-{t['word']}]")
        else:
            parts.append(t["word"])

    return {
        "diff_tokens": diff,
        "added_words": added,
        "removed_words": removed,
        "formatted": " ".join(parts),
        "words_added": len(added),
        "words_removed": len(removed),
    }
