class _TrieNode:
    __slots__ = ("children", "ids")

    def __init__(self) -> None:
        self.children: dict[str, _TrieNode] = {}
        self.ids: set[int] = set()


class Trie:
    """Prefix trie mapping inserted strings to integer ids.

    Every node on a word's path accumulates that word's id, so `search_prefix` is
    a single O(len(prefix)) walk with no subtree scan. Used to search form leads
    by name, phone number and email prefix without a per-request table scan.
    """

    def __init__(self) -> None:
        self._root = _TrieNode()

    def insert(self, word: str, id_: int) -> None:
        node = self._root
        for ch in word:
            node = node.children.setdefault(ch, _TrieNode())
            node.ids.add(id_)

    def search_prefix(self, prefix: str) -> set[int]:
        node = self._root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return set()
        return set(node.ids)
