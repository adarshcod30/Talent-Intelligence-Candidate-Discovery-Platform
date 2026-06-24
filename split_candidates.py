import os

input_path = os.path.join('India_runs_data_and_ai_challenge', 'candidates.jsonl')
output_dir = '.'

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Count total lines
with open(input_path, 'r', encoding='utf-8') as f:
    total = sum(1 for _ in f)

part_size = total // 3
remainder = total % 3

filenames = ['candidates_part1.jsonl', 'candidates_part2.jsonl', 'candidates_part3.jsonl']

with open(input_path, 'r', encoding='utf-8') as fin:
    for i, fname in enumerate(filenames, start=1):
        count = part_size + (1 if i <= remainder else 0)
        out_path = os.path.join(output_dir, fname)
        with open(out_path, 'w', encoding='utf-8') as fout:
            for _ in range(count):
                line = fin.readline()
                if not line:
                    break
                fout.write(line)
print('Split completed: ', filenames)
