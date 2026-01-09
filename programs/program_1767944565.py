import jarvis_runtime
import random

__PROGRAM__ = {
    "name": "抽選ツール",
    "version": "1.0",
    "description": "候補者リストから重複なしで当選者を選ぶツール",
    "params": [
        {"key": "candidates", "label": "候補者リスト", "type": "list[str]", "required": True, "placeholder": "例: ['Alice', 'Bob', 'Charlie']"},
        {"key": "winners", "label": "当選者数", "type": "int", "required": True, "placeholder": "例: 2"},
        {"key": "seed", "label": "シード値", "type": "int", "required": False, "default": None}
    ],
    "kind": "module"
}

def run(params: dict):
    candidates = params['candidates']
    winners_count = params['winners']
    seed_value = params.get('seed')

    if seed_value is not None:
        random.seed(seed_value)

    if winners_count > len(candidates):
        return "当選者数は候補者数以下でなければなりません。"

    winners = random.sample(candidates, winners_count)
    return winners