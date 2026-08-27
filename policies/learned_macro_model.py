"""Frozen macro selector trained on paired counterfactual outcomes."""


MACRO_MODEL = {
    "feature": "price_milk",
    "threshold": 1.396875,
    "left": {
        "feature": "price_milk",
        "threshold": 1.246875,
        "left": {
            "feature": "own_money_k",
            "threshold": 0.0285,
            "left": {"arm": 1, "samples": 11},
            "right": {"arm": 2, "samples": 14},
            "samples": 25,
        },
        "right": {
            "feature": "shops_strawberry",
            "threshold": 2.5,
            "left": {"arm": 0, "samples": 21},
            "right": {"arm": 1, "samples": 4},
            "samples": 25,
        },
        "samples": 50,
    },
    "right": {"arm": 1, "samples": 4},
    "samples": 54,
}
MODEL_METADATA = {
    "training_contexts": 54,
    "training_wins": 46,
    "training_label_accuracy": 0.463,
    "max_depth": 3,
    "min_leaf": 3,
    "selection_day": 9,
    "objective": "wins first, bounded margin second",
    "validation_wins": 26,
    "validation_games": 30,
    "status": "rejected; fixed compact scored 28/30",
    "artifact": "artifacts/models/v1327-d9-macro-tree.json",
}
