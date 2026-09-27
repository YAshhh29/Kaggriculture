# Local RL Data

Store replay-derived JSONL datasets here. Everything except this guide is
ignored by Git because files can contain Kaggle Competition Data.

Each JSONL begins with a metadata header containing its source episode, seed,
team, optional submission and score snapshot, replay SHA-256, collection and
replay dates, terminal rewards/result, simulator version, schema versions, and
train/validation/test assignment.

Do not publish or redistribute these files to non-participants during the
competition.