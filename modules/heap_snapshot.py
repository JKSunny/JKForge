
import json
from pathlib import Path

class HeapSnapshot:
    def __init__(self, path):
        self.path = Path(path)

        with open(self.path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.blocks = self.data.get("blocks", [])
        self.blocks.sort(key=lambda b: b["addr"])

    def metrics(self):
        largest_gap = 0
        total_gap = 0

        total_requested = 0
        total_usable = 0

        for b in self.blocks:
            total_requested += b.get("requested", b.get("size", 0))
            total_usable += b.get("usable", b.get("size", 0))

        for i in range(len(self.blocks) - 1):
            cur = self.blocks[i]
            nxt = self.blocks[i + 1]

            cur_end = cur["addr"] + cur.get("usable", cur.get("size", 0))
            gap = max(0, nxt["addr"] - cur_end)

            total_gap += gap

            if gap > largest_gap:
                largest_gap = gap

        fragmentation = 0.0

        if total_gap > 0:
            fragmentation = 1.0 - (largest_gap / total_gap)

        return {
            "blocks": len(self.blocks),
            "largest_gap": largest_gap,
            "total_gap": total_gap,
            "fragmentation": fragmentation,
            "total_requested": total_requested,
            "total_usable": total_usable,
            "internal_fragmentation": total_usable - total_requested
        }


def load_snapshot_directory(path):
    path = Path(path)

    snapshots = []

    for file in sorted(path.glob("*.json")):
        snapshots.append({
            "name": file.name,
            "path": str(file)
        })

    return snapshots
