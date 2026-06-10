# Number Grid Puzzle Bot: Project Whitepaper

> Canonical bilingual overview and operating manual.  
> Trang giới thiệu và hướng dẫn vận hành song ngữ chính thức.

## 1. Purpose / Mục tiêu

### English

This repository implements an AI bot for the Number Grid Puzzle. The bot separates
real-time inference from offline heuristic training:

- **Inference** chooses a move under a time budget with dynamic-depth Expectimax.
- **Training** evolves heuristic weights offline with a genetic algorithm (GA).
- **Evaluation** uses reproducible datasets so changes can be compared fairly.

Use this page as the first operational reference. Detailed feature specs remain under
`specs/`, and the original algorithm design remains in
`thiet_ke_thuat_toan_bot_puzzle.md`.

### Tiếng Việt

Repository này triển khai bot AI cho trò chơi Number Grid Puzzle. Bot tách riêng suy
luận thời gian thực và huấn luyện heuristic offline:

- **Inference** chọn nước đi trong giới hạn thời gian bằng Expectimax có độ sâu động.
- **Training** tiến hóa trọng số heuristic offline bằng giải thuật di truyền (GA).
- **Evaluation** dùng bộ dữ liệu tái lập được để so sánh thay đổi một cách công bằng.

Hãy dùng trang này làm tài liệu vận hành đầu tiên. Các đặc tả chi tiết vẫn nằm trong
`specs/`, còn thiết kế thuật toán gốc nằm trong `thiet_ke_thuat_toan_bot_puzzle.md`.

## 2. Puzzle Rules / Luật chơi

### English

- The grid is `9 x 9`, with coordinates `(0, 0)` through `(8, 8)`.
- A game has exactly `27` turns.
- Each turn places one fixed-orientation vertical `3 x 1` block.
- Every cell value is randomly drawn from `{7, 8, 9, 10}`.
- A score is created by a continuous horizontal, vertical, or diagonal line of at least
  three identical numbers.
- Scored cells remain on the board and can score again later.
- Valid placements are aligned slots: `x in 0..8`, `y in {0, 3, 6}`.
- The effective action space is exactly `9 x 3 = 27` slots.

Because `27 blocks x 3 cells = 81 cells`, aligned placement guarantees perfect packing
of the board. The bot must not search arbitrary cell positions.

### Tiếng Việt

- Bàn chơi có kích thước `9 x 9`, tọa độ từ `(0, 0)` đến `(8, 8)`.
- Mỗi ván có đúng `27` lượt.
- Mỗi lượt đặt một block dọc cố định `3 x 1`.
- Giá trị từng ô được sinh ngẫu nhiên từ `{7, 8, 9, 10}`.
- Điểm được tạo bởi chuỗi ngang, dọc hoặc chéo liên tục có ít nhất ba số giống nhau.
- Ô đã ghi điểm vẫn nằm trên bàn và có thể tiếp tục tham gia ghi điểm.
- Vị trí hợp lệ là slot thẳng hàng: `x in 0..8`, `y in {0, 3, 6}`.
- Không gian hành động thực tế có đúng `9 x 3 = 27` slot.

Do `27 block x 3 ô = 81 ô`, cách đặt thẳng hàng bảo đảm lấp đầy toàn bộ bàn chơi. Bot
không được tìm kiếm trên các vị trí ô tùy ý.

## 3. Architecture / Kiến trúc

| Area / Khu vực | Main files / File chính | Responsibility / Trách nhiệm |
|---|---|---|
| Game state | `bot/game_state.py` | 1D row-major board, aligned slots, local placement score / Bàn 1D row-major, slot hợp lệ, tính điểm cục bộ |
| Inference | `bot/expectimax.py` | Real-time dynamic-depth Expectimax and transposition table / Expectimax độ sâu động và cache trạng thái |
| Features | `bot/features.py` | Heuristic feature extraction / Trích xuất feature heuristic |
| Training | `bot/genetics.py`, `bot/training_runner.py` | GA evolution, deterministic simulation, multiprocessing, run records / Tiến hóa GA, mô phỏng tái lập, đa tiến trình, log |
| Training data | `bot/training_data.py` | Reusable Common Random Numbers datasets / Bộ dữ liệu CRN dùng lại |
| Active weights | `bot/training_weights.py` | Promote and load a trained chromosome / Chọn và tải chromosome đã train |
| Display | `utils/display.py` | Final board rendering / Hiển thị bàn chơi |
| CLI | `run_bot.py`, `bot/cli.py` | Play, train, and replay entry points / Điểm vào play, train và replay |
| Offline comparison | `bot/foresight.py`, `scripts/compare_known_future.py` | Approximate beam-search baseline with known future blocks / Baseline beam search biết trước block |

## 4. Algorithms / Thuật toán

### English

**Inference:** The real-time engine uses dynamic-depth Expectimax:

- Opening, turns `1-10`: depth `2`.
- Middlegame, turns `11-20`: depth `3`.
- Endgame, turns `21-27`: depth `4-5` where feasible.

It uses a transposition table and local ray-casting score updates from newly placed
cells. Runtime inference loads precomputed weights; it does not learn online.

**Training:** The offline GA evolves phase-specific chromosomes:

```text
H(state) = sum(mask_i * weight_i * feature_i(state))
```

The optimizer uses feature masks, Common Random Numbers (CRN), elite preservation,
tournament selection, injected candidates, variance penalties, and adaptive mutation
pulses after plateaus.

### Tiếng Việt

**Inference:** Engine thời gian thực dùng Expectimax với độ sâu động:

- Đầu game, lượt `1-10`: depth `2`.
- Giữa game, lượt `11-20`: depth `3`.
- Cuối game, lượt `21-27`: depth `4-5` khi phù hợp.

Engine dùng transposition table và ray-casting cục bộ từ các ô vừa đặt. Inference chỉ
tải trọng số đã train; không học online khi đang chơi.

**Training:** GA offline tiến hóa chromosome riêng theo từng giai đoạn:

```text
H(state) = sum(mask_i * weight_i * feature_i(state))
```

Optimizer dùng mask feature, Common Random Numbers (CRN), giữ elite, tournament
selection, candidate bổ sung, variance penalty và mutation pulse khi plateau.

## 5. Glossary / Thuật ngữ

Các thuật ngữ tiếng Anh dưới đây được giữ lại trong log, command và phần phân tích để
khớp với tên kỹ thuật trong code. Bảng này giải thích nghĩa của chúng trong phạm vi
project.

### Core Concepts / Khái niệm cốt lõi

| Term / Thuật ngữ | Meaning in this project / Ý nghĩa trong project |
|---|---|
| **Inference** | Quá trình bot dùng model hiện có để chọn nước đi khi đang chơi. Inference không tự học thêm. |
| **Training** | Quá trình tối ưu offline trước khi chơi để tìm bộ trọng số heuristic tốt hơn. |
| **Model** | Cách bot chấm điểm và chọn nước đi; trong project này model chủ yếu được xác định bởi chromosome heuristic. |
| **Heuristic** | Hàm ước lượng chất lượng của một trạng thái bàn cờ khi search chưa thể mô phỏng hết tương lai. |
| **Feature** | Một tín hiệu số mô tả trạng thái, ví dụ điểm hiện tại, số slot trống hoặc tiềm năng tạo line. |
| **Weight** | Hệ số thể hiện mức ảnh hưởng của một feature lên điểm heuristic. |
| **Mask** | Cờ bật hoặc tắt một feature. `mask = 1` nghĩa là feature được dùng; `mask = 0` nghĩa là bỏ qua. |
| **Expectimax** | Thuật toán search xét cả lựa chọn của bot và các block ngẫu nhiên có thể xuất hiện. |
| **Phase** | Một giai đoạn của ván chơi: đầu game, giữa game hoặc cuối game. Mỗi phase có thể dùng weight khác nhau. |
| **Baseline** | Mốc tham chiếu hiện tại để so sánh experiment mới. Baseline không mặc nhiên là nghiệm tối ưu. |
| **Experiment** | Một lần thử có kiểm soát để đo tác động của thay đổi. Nên chỉ đổi một biến có ý nghĩa mỗi experiment. |

### Genetic Algorithm / Giải thuật di truyền

| Term / Thuật ngữ | Meaning in this project / Ý nghĩa trong project |
|---|---|
| **Genetic Algorithm (GA)** | Phương pháp tối ưu mô phỏng tiến hóa: tạo nhiều candidate, đánh giá, chọn candidate tốt và biến đổi chúng qua nhiều vòng. |
| **Gene** | Một thành phần nhỏ của chromosome; ở đây thường là cặp `mask` và `weight` của một feature trong một phase. |
| **Chromosome** hoặc **genome** | Toàn bộ bộ gene mô tả một candidate model. Project dùng chromosome theo phase đầu, giữa và cuối game. |
| **Candidate** | Một chromosome đang được đánh giá hoặc cân nhắc sử dụng. |
| **Population** | Tập hợp candidate được đánh giá trong cùng một generation. |
| **Generation** | Một vòng tiến hóa: đánh giá population hiện tại rồi tạo population kế tiếp. |
| **Fitness** | Điểm dùng để xếp hạng candidate trong GA. Training fitness là kết quả trên training dataset, không phải bảo đảm candidate sẽ tốt trên dữ liệu mới. |
| **Best fitness** | Fitness training cao nhất đã tìm được trong run hoặc generation đang nói tới. |
| **Global best** | Candidate tốt nhất tính trên toàn bộ các generation đã chạy, không chỉ generation hiện tại. |
| **Elite** | Nhóm candidate tốt được giữ nguyên sang generation kế tiếp. |
| **Mutation** | Thay đổi ngẫu nhiên gene để tạo biến thể mới và mở rộng vùng tìm kiếm. |
| **Mutation rate** | Xác suất mutation cơ sở. |
| **Adaptive mutation surge** hoặc **mutation pulse** | Đợt tạm thời tăng mutation khi nhiều generation liên tiếp không cải thiện best fitness. |
| **Active gene** | Gene có `mask = 1`, tức feature tương ứng đang tham gia tính heuristic. |

### Evaluation And Diagnostics / Đánh giá và chẩn đoán

| Term / Thuật ngữ | Meaning in this project / Ý nghĩa trong project |
|---|---|
| **Run** | Một lần chạy training với config, dataset và seed cụ thể. |
| **Summary** | File JSON ghi lại config, tiến trình và kết quả của một run. |
| **Status** | Trạng thái run, ví dụ `running`, `completed`, `interrupted` hoặc `failed`. |
| **Config** | Toàn bộ tham số cấu hình của một run, ví dụ population size, số generation và mutation rate. |
| **Dataset** | Tập scenario dùng lại được để đánh giá candidate một cách tái lập. |
| **Training dataset** | Tập scenario dùng để tối ưu chromosome. |
| **Validation dataset** hoặc **holdout dataset** | Tập scenario tách biệt, không dùng để tối ưu trực tiếp; dùng để kiểm tra candidate có tổng quát hóa tốt hay không. |
| **Validation fitness** | Fitness đo trên validation dataset. Đây là bằng chứng quan trọng trước khi promote weights. |
| **Validation gap** | Chênh lệch `validation fitness - training fitness`. Gap âm lớn là tín hiệu candidate có thể chưa tổng quát hóa tốt. |
| **Scenario** | Một chuỗi block tái lập được dùng để đánh giá bot trong một ván. |
| **Seed** | Số đầu vào giúp tái tạo lại dữ liệu hoặc hành vi ngẫu nhiên của GA. |
| **Common Random Numbers (CRN)** | Cách so sánh công bằng: các candidate được đánh giá trên cùng scenario ngẫu nhiên. |
| **Worker** | Process cục bộ thực hiện việc đánh giá candidate. Tăng worker có thể tận dụng thêm CPU. |
| **Overlap** | Scenario xuất hiện ở cả training dataset và validation dataset. Nên tránh overlap để validation có ý nghĩa. |
| **Replay** | Chạy đánh giá lại một chromosome đã lưu trên dataset được chọn. |
| **Convergence** | Xu hướng thuật toán tiến dần tới vùng kết quả ổn định, nơi cải thiện mới ngày càng nhỏ hoặc hiếm. |
| **Plateau** | Giai đoạn best fitness gần như đứng yên qua nhiều generation. Plateau là tín hiệu cần phân tích, không tự động chứng minh đã đạt tối ưu. |
| **Diversity** hoặc **chromosome diversity ratio** | Tỷ lệ chromosome khác nhau trong population. Diversity cao cho thấy candidate khác nhau, nhưng không chứng minh chúng đang khám phá vùng hữu ích. |
| **No-improvement streak** | Số generation liên tiếp chưa tạo global best mới. |
| **Active weights** | Bộ chromosome đã được chọn để inference cục bộ sử dụng. |
| **Promote weights** | Đưa chromosome đã kiểm chứng vào `training_runs/active_chromosome.json` để trở thành active weights. |

## 6. Heuristic Features / Feature heuristic

### English

The feature pool includes current score, horizontal and diagonal potential pairs,
column bumpiness, center bias, isolated slots, dead ends, maximum height, per-number
density, vertical match interfaces, empty-slot count, diagonal cross points, and
generalized three-cell line-window signals:

- Open one-match windows.
- Open two-match windows.
- Blocked windows.
- Empty cells that can complete multiple lines.

The GA decides which features are active through binary masks. New features should be
added with mathematical rationale and focused performance checks.

### Tiếng Việt

Feature pool gồm điểm hiện tại, cặp tiềm năng ngang và chéo, độ gồ ghề cột, ưu tiên
trung tâm, slot cô lập, dead end, chiều cao tối đa, mật độ theo từng số, giao diện match
dọc, số slot trống, giao điểm chéo và tín hiệu cửa sổ ba ô tổng quát:

- Cửa sổ mở có một số khớp.
- Cửa sổ mở có hai số khớp.
- Cửa sổ bị chặn.
- Ô trống có thể hoàn tất nhiều line.

GA tự quyết định feature nào được bật qua binary mask. Feature mới cần có lập luận toán
học và kiểm tra hiệu năng tập trung.

## 7. Quick Start / Chạy nhanh

### English

Run one game:

```sh
python3 run_bot.py
```

Generate reusable training and validation datasets:

```sh
python3 scripts/generate_training_seeds.py \
  --dataset-id train-10m \
  --purpose training \
  --master-seed 20260530 \
  --scenarios 100 \
  --output training_data/train-10m.json

python3 scripts/generate_training_seeds.py \
  --dataset-id validation-10m \
  --purpose validation \
  --master-seed 20260531 \
  --scenarios 100 \
  --output training_data/validation-10m.json
```

Start interactive training:

```sh
python3 run_bot.py train
```

### Tiếng Việt

Chạy một ván:

```sh
python3 run_bot.py
```

Sinh dataset training và validation có thể dùng lại:

```sh
python3 scripts/generate_training_seeds.py \
  --dataset-id train-10m \
  --purpose training \
  --master-seed 20260530 \
  --scenarios 100 \
  --output training_data/train-10m.json

python3 scripts/generate_training_seeds.py \
  --dataset-id validation-10m \
  --purpose validation \
  --master-seed 20260531 \
  --scenarios 100 \
  --output training_data/validation-10m.json
```

Bắt đầu training tương tác:

```sh
python3 run_bot.py train
```

## 8. Command Catalog / Danh mục command

### Play / Chơi game

```sh
python3 run_bot.py
python3 run_bot.py play
```

### Scripted training / Training bằng command đầy đủ

```sh
python3 run_bot.py train \
  --non-interactive \
  --population-size 40 \
  --generations 40 \
  --games-per-genome 20 \
  --mutation-rate 0.05 \
  --elite-ratio 0.10 \
  --tournament-size 5 \
  --inject-ratio 0.10 \
  --variance-penalty 0.15 \
  --workers 8 \
  --seed 20260530 \
  --watchdog-patience 12 \
  --watchdog-min-generations 10 \
  --watchdog-min-delta 0.0 \
  --watchdog-average-recovery 0.0 \
  --training-dataset training_data/train-10m.json \
  --validation-dataset training_data/validation-10m.json
```

The example above is a practical continuation profile. CLI defaults may differ.  
Ví dụ trên là cấu hình tiếp tục tối ưu thực dụng. Giá trị mặc định của CLI có thể khác.

Use `--disable-watchdog` when an experiment must run for the exact `--generations`
budget regardless of plateau evidence.  
Dùng `--disable-watchdog` khi thí nghiệm bắt buộc chạy đủ số vòng `--generations` dù
log đã có tín hiệu plateau.

### Run training agent skill / Skill agent chạy training

For short prompts such as "run training" or "run trainning", Codex should use
`.codex/skills/matrix-run-training/` to avoid broad repository exploration before
launching the standard non-interactive training profile above. The skill verifies the
standard CRN datasets, starts the run, monitors progress, and leaves weight promotion
to a later explicit request.

Với prompt ngắn như "run training" hoặc "run trainning", Codex nên dùng
`.codex/skills/matrix-run-training/` để tránh đọc rộng toàn repo trước khi chạy cấu
hình non-interactive chuẩn ở trên. Skill kiểm tra dataset CRN chuẩn, khởi động run,
theo dõi tiến trình, và chỉ promote weight khi có yêu cầu rõ ràng sau đó.

### Replay a trained candidate / Đánh giá lại candidate đã train

Replay against the recorded training subset / Replay trên tập training đã ghi nhận:

```sh
python3 run_bot.py replay training_runs/<summary-file>.json
```

Replay against the full recorded validation dataset / Replay trên toàn bộ tập validation:

```sh
python3 run_bot.py replay training_runs/<summary-file>.json --dataset validation
```

### Plot training progress / Vẽ tiến trình training

```sh
python3 scripts/plot_training_log.py training_runs/<summary-file>.json

python3 scripts/plot_training_log.py \
  training_runs/<summary-file>.json \
  --output training_runs/training-progress.png \
  --no-ui
```

Use `--no-ui` in headless environments.  
Dùng `--no-ui` trong môi trường không có giao diện đồ họa.

### Analyze latest training run / Phân tích run training mới nhất

Human-readable report / Report cho người đọc:

```sh
python3 .codex/skills/matrix-analyze-latest-training-run/scripts/analyze_latest_training_run.py
```

Versioned JSON handoff for another agent / JSON có version để truyền cho agent khác:

```sh
python3 .codex/skills/matrix-analyze-latest-training-run/scripts/analyze_latest_training_run.py \
  --json
```

The JSON payload uses `schema_version = 1`, separates measured fields from
`assessment` inferences and caveats, and provides one structured
`recommended_next_action`. Every invocation persists the JSON handoff beside the
selected summary as `training_runs/analysis-<train-summary-stem>.json`, including when
stdout is rendered as Markdown. If that artifact already exists, the analyzer warns
and stops instead of overwriting or re-analyzing an old log. The analyzer is read-only
with respect to training summaries and active weights.

JSON dùng `schema_version = 1`, tách field đo được khỏi diễn giải và cảnh báo trong
`assessment`, đồng thời cung cấp một `recommended_next_action` có cấu trúc. Analyzer
luôn lưu JSON handoff cạnh summary đã chọn theo mẫu
`training_runs/analysis-<train-summary-stem>.json`, kể cả khi stdout hiển thị Markdown.
Nếu artifact đó đã tồn tại, analyzer cảnh báo và dừng thay vì ghi đè hoặc phân tích lại
log cũ. Analyzer không sửa summary training, không promote weight hoặc tự khởi động
training.

### Recommend weight adjustments / Đề xuất chỉnh trọng số

Human-readable report / Report cho người đọc:

```sh
python3 .codex/skills/matrix-recommend-weight-adjustments/scripts/recommend_weight_adjustments.py
```

Versioned JSON handoff for another agent / JSON có version để truyền cho agent khác:

```sh
python3 .codex/skills/matrix-recommend-weight-adjustments/scripts/recommend_weight_adjustments.py \
  --json
```

The recommender reads saved `training_runs/train-*.json` summaries, analyzes population
telemetry when available, falls back to generation-best chromosome weight and mask
movement for older logs, correlates those directional changes with training and
validation outcomes, and persists a read-only recommendation under
`training_runs/weight-adjustment-recommendation-<timestamp>.json`. Recommendations are
directional and should be validated with controlled follow-up runs. Before building
the recommendation, the script verifies that the newest selected training summary has
`training_runs/analysis-<train-summary-stem>.json`; if missing, it runs the latest-run
analyzer first and records the status in `latest_training_analysis`. When an active
chromosome is available, the report also creates a ready-to-run candidate active model
under `training_runs/experiment-adjusted-high-confidence-<timestamp>/active_chromosome.json`
and prints the full training command for that isolated output directory.
High-confidence weight deltas are applied to the candidate; mask changes remain
advisory until a separate controlled experiment validates them.

Recommender đọc các summary `training_runs/train-*.json`, phân tích telemetry toàn
population khi có, fallback về biến động weight và mask của best chromosome theo
generation với log cũ, đối chiếu hướng thay đổi với kết quả training và validation, rồi
lưu recommendation read-only theo mẫu
`training_runs/weight-adjustment-recommendation-<timestamp>.json`. Khuyến nghị là định
hướng và cần được kiểm chứng bằng run có kiểm soát. Trước khi tạo recommendation, script
kiểm tra summary training mới nhất đã có
`training_runs/analysis-<train-summary-stem>.json` chưa; nếu thiếu, nó chạy latest-run
analyzer trước và ghi trạng thái vào `latest_training_analysis`. Khi có active
chromosome, report cũng tạo candidate active model có thể chạy ngay tại
`training_runs/experiment-adjusted-high-confidence-<timestamp>/active_chromosome.json`
và in đầy đủ command training cho output directory tách biệt đó. Candidate chỉ áp dụng
delta trọng số confidence cao; thay đổi mask vẫn là khuyến nghị tham khảo cho experiment
riêng.

### Promote active weights / Chọn weight đang hoạt động

```sh
python3 scripts/sync_latest_weights.py
```

The newest run summary containing a best chromosome is promoted into
`training_runs/active_chromosome.json`. Validate promising candidates before trusting
them in production-like comparisons.

Summary mới nhất có best chromosome sẽ được đưa vào
`training_runs/active_chromosome.json`. Hãy validation candidate tốt trước khi tin cậy
trong các so sánh quan trọng.

### Known-future comparison / So sánh với baseline biết trước block

Use an existing scenario:

```sh
python3 scripts/compare_known_future.py \
  --dataset training_data/train-10m.json \
  --scenario-id scenario-0001 \
  --beam-width 500 \
  --json-output training_runs/known-future-scenario-0001.json \
  --no-ui
```

Generate one new scenario and compare immediately:

```sh
python3 scripts/compare_known_future.py \
  --generate-dataset training_data/known-future-demo.json \
  --master-seed 20260530 \
  --beam-width 500 \
  --overwrite \
  --no-ui
```

This is an approximate beam-search baseline, not a proof of the absolute optimum.  
Đây là baseline beam search xấp xỉ, không phải chứng minh nghiệm tối ưu tuyệt đối.

### Discover available flags / Xem flag hiện có

```sh
python3 run_bot.py --help
python3 run_bot.py train --help
python3 run_bot.py replay --help
python3 scripts/generate_training_seeds.py --help
python3 scripts/plot_training_log.py --help
python3 scripts/sync_latest_weights.py --help
python3 scripts/compare_known_future.py --help
```

## 9. Training Parameters / Tham số training

| Flag | Valid values / Giá trị hợp lệ | Meaning and tuning effect / Ý nghĩa và ảnh hưởng |
|---|---|---|
| `--population-size` | Positive integer / Số nguyên dương | Genomes per generation. Larger values explore more candidates but cost more time. / Số genome mỗi generation. Tăng để khám phá rộng hơn nhưng chạy lâu hơn. |
| `--generations` | Positive integer / Số nguyên dương | Maximum evolution rounds. Stop early when evidence shows a stable plateau. / Số vòng tối đa. Có thể dừng sớm khi plateau ổn định. |
| `--games-per-genome` | Positive integer within dataset size / Không vượt số scenario | CRN scenarios used for each candidate. Increase for more stable fitness at higher cost. / Số scenario CRN cho mỗi candidate. Tăng để fitness ổn định hơn nhưng tốn thời gian. |
| `--mutation-rate` | `0..1` | Base mutation probability. Start near `0.05`; mutation pulses multiply it during plateaus. / Xác suất mutation cơ sở. Nên bắt đầu gần `0.05`; pulse sẽ nhân lên khi plateau. |
| `--elite-ratio` | `0..1` | Fraction copied unchanged into the next generation. Too high can reduce exploration. / Tỷ lệ elite giữ nguyên. Quá cao làm giảm khám phá. |
| `--tournament-size` | Positive integer, at most population size / Không vượt population | Parent-selection pressure. Larger values favor strong candidates more aggressively. / Áp lực chọn parent. Tăng để ưu tiên candidate mạnh hơn. |
| `--inject-ratio` | `0..1` | Fraction of additional mutated candidates derived from the current best. / Tỷ lệ candidate bổ sung được mutate từ best hiện tại. |
| `--variance-penalty` | Non-negative number / Số không âm | Penalizes unstable scores across scenarios. / Phạt candidate có score dao động mạnh giữa scenario. |
| `--workers` | Positive integer / Số nguyên dương | Local process workers for candidate evaluation. Tune to available CPU capacity. / Số process cục bộ. Điều chỉnh theo CPU. |
| `--seed` | Integer / Số nguyên | Reproducibility seed for GA population behavior. / Seed tái lập cho hành vi quần thể GA. |
| `--training-dataset` | Existing JSON path / Đường dẫn JSON tồn tại | Required CRN training dataset. / Dataset CRN training bắt buộc. |
| `--validation-dataset` | Existing JSON path / Đường dẫn JSON tồn tại | Optional holdout dataset; use it before promotion decisions. / Dataset holdout tùy chọn; nên dùng trước khi chọn model. |
| `--output-directory` | Directory path / Đường dẫn thư mục | Location for incremental run summaries and active weights. / Nơi lưu summary tăng dần và active weights. |
| `--disable-watchdog` | Flag / Cờ bật tắt | Disables automatic plateau stopping for fixed-length experiments. / Tắt dừng sớm do plateau cho thí nghiệm cần chạy đủ vòng. |
| `--watchdog-patience` | Positive integer / Số nguyên dương | No-improvement generations required before early-stop eligibility. / Số generation không cải thiện cần có trước khi được dừng sớm. |
| `--watchdog-min-delta` | Non-negative number / Số không âm | Minimum best-fitness improvement treated as meaningful. / Mức cải thiện best fitness tối thiểu được xem là có ý nghĩa. |
| `--watchdog-min-generations` | Positive integer / Số nguyên dương | Minimum completed generations before watchdog can stop. / Số generation tối thiểu phải hoàn tất trước khi watchdog được dừng. |
| `--watchdog-average-recovery` | Non-negative number / Số không âm | Required recent average-fitness recovery to keep training after plateau; `0` disables this recovery gate. / Mức hồi phục average fitness gần đây để tiếp tục training sau plateau; `0` tắt gate hồi phục này. |

## 10. Logs And Diagnostics / Log và chẩn đoán

### English

Training writes incremental JSON summaries under:

```text
training_runs/train-<timestamp>.json
```

Important top-level fields:

| Field | Meaning |
|---|---|
| `status` | `running`, `completed`, `interrupted`, or `failed` |
| `config` | Exact GA parameters and dataset paths |
| `training_dataset`, `validation_dataset` | Dataset identity and checksum |
| `best_fitness` | Best training fitness found so far |
| `validation_fitness` | Holdout fitness, normally written after a completed run |
| `best_chromosome` | Best phase-based masks and weights |
| `stop_reason` | `max_generations`, `watchdog_plateau`, `keyboard_interrupt`, or failure text |
| `watchdog_decision` | Details for an automatic watchdog stop, when present |

Important generation fields:

| Field | Meaning |
|---|---|
| `best_fitness` | Best fitness in this generation |
| `average_fitness` | Population average |
| `minimum_fitness` | Population minimum |
| `elapsed_seconds` | Generation evaluation time |
| `plateau_diagnostics.chromosome_diversity_ratio` | Exact unique chromosome ratio |
| `plateau_diagnostics.no_improvement_generations` | Consecutive generations without a global best |
| `plateau_diagnostics.adaptive_mutation_surge` | Whether the next evolution uses a mutation pulse |
| `plateau_diagnostics.active_gene_count_*` | Distribution of active masked genes |

### Tiếng Việt

Training ghi summary JSON tăng dần tại:

```text
training_runs/train-<timestamp>.json
```

Các field top-level quan trọng:

| Field | Ý nghĩa |
|---|---|
| `status` | `running`, `completed`, `interrupted` hoặc `failed` |
| `config` | Tham số GA và đường dẫn dataset chính xác |
| `training_dataset`, `validation_dataset` | Danh tính dataset và checksum |
| `best_fitness` | Fitness training tốt nhất hiện có |
| `validation_fitness` | Fitness holdout, thường được ghi khi run hoàn tất |
| `best_chromosome` | Mask và weight theo phase của candidate tốt nhất |
| `stop_reason` | `max_generations`, `watchdog_plateau`, `keyboard_interrupt` hoặc mô tả lỗi |
| `watchdog_decision` | Chi tiết khi training tự dừng do watchdog, nếu có |

Field theo generation quan trọng:

| Field | Ý nghĩa |
|---|---|
| `best_fitness` | Fitness tốt nhất trong generation |
| `average_fitness` | Trung bình quần thể |
| `minimum_fitness` | Fitness thấp nhất |
| `elapsed_seconds` | Thời gian đánh giá generation |
| `plateau_diagnostics.chromosome_diversity_ratio` | Tỷ lệ chromosome khác nhau hoàn toàn |
| `plateau_diagnostics.no_improvement_generations` | Số generation liên tiếp không tạo global best |
| `plateau_diagnostics.adaptive_mutation_surge` | Evolution kế tiếp có dùng mutation pulse không |
| `plateau_diagnostics.active_gene_count_*` | Phân bố số gene đang bật |

## 11. Optimization Loop / Quy trình tối ưu

### English

1. Generate distinct training and validation CRN datasets.
2. Run a bounded baseline and preserve its summary.
3. Change one meaningful variable at a time: features, mutation policy, or GA controls.
4. Reuse the same CRN datasets and seed for fair comparisons.
5. Let the watchdog inspect every completed generation, or manually inspect logs every
   `10-15` generations when watchdog is disabled.
6. Stop early when best fitness stays flat through the configured patience window after
   mutation-pulse evidence and the population average does not recover.
7. Replay the best candidate against validation data.
8. Promote only candidates that improve validation fitness or provide a justified
   tradeoff.
9. Run inference performance gates after heuristic changes.

The previous plateau analysis is documented in
`specs/005-training-plateau-features/quickstart.md`.

### Tiếng Việt

1. Sinh dataset CRN training và validation tách biệt.
2. Chạy baseline giới hạn và lưu summary.
3. Mỗi lần chỉ đổi một biến có ý nghĩa: feature, chính sách mutation hoặc tham số GA.
4. Dùng lại cùng dataset CRN và seed để so sánh công bằng.
5. Để watchdog kiểm tra từng generation đã hoàn tất, hoặc tự kiểm tra log mỗi `10-15`
   generation khi watchdog bị tắt.
6. Dừng sớm khi best đứng yên qua cửa sổ patience đã cấu hình sau khi có bằng chứng
   mutation pulse và average không hồi phục.
7. Replay candidate tốt nhất trên validation data.
8. Chỉ promote candidate cải thiện validation fitness hoặc có tradeoff được giải thích.
9. Chạy performance gate inference sau khi thay đổi heuristic.

Phân tích plateau trước đây nằm tại
`specs/005-training-plateau-features/quickstart.md`.

## 12. Tests / Kiểm thử

Run focused checks for changed areas. Useful commands:

Regression checks live under `tests/`. Performance gates and timing reports live under
`tests/benchmarks/` because they are slower and more sensitive to host load.

Các kiểm tra regression nằm trong `tests/`. Performance gate và báo cáo timing nằm
trong `tests/benchmarks/` vì chạy chậm hơn và nhạy với tải của máy host.

```sh
python3 tests/test_bot.py
python3 tests/test_display.py
python3 tests/test_foresight.py
python3 tests/benchmarks/test_performance.py
python3 tests/test_training_config.py
python3 tests/test_training_data.py
python3 tests/test_training_overlap.py
python3 tests/test_training_runner.py
python3 tests/test_training_parallel.py
python3 tests/test_training_ui.py
python3 tests/test_training_cli.py
python3 tests/test_training_records.py
python3 tests/test_training_replay.py
python3 tests/test_training_weights.py
python3 tests/test_training_mutation.py
python3 tests/test_training_features.py
python3 tests/benchmarks/test_training_feature_performance.py
python3 tests/benchmarks/test_training_performance.py
python3 tests/test_analyze_latest_training_run_skill.py
python3 tests/test_recommend_weight_adjustments_skill.py
```

`tests/test_training_parallel.py` and `tests/benchmarks/test_training_performance.py` use multiprocessing and
may require a normal host environment rather than a restricted sandbox.

`tests/test_training_parallel.py` và `tests/benchmarks/test_training_performance.py` dùng multiprocessing và có
thể cần môi trường host thông thường thay vì sandbox giới hạn.

Manual diagnostics that do not assert application behavior live under
`scripts/diagnostics/`, for example `python3 scripts/diagnostics/class_vars.py`.

Các script chẩn đoán thủ công không assert hành vi ứng dụng nằm trong
`scripts/diagnostics/`, ví dụ `python3 scripts/diagnostics/class_vars.py`.

## 13. Generated Artifacts / Artifact được sinh ra

| Path | Purpose / Mục đích |
|---|---|
| `training_data/*.json` | Reusable CRN datasets / Dataset CRN dùng lại |
| `training_runs/train-*.json` | Incremental training summaries / Summary training tăng dần |
| `training_runs/analysis-train-*.json` | Persisted analyzer handoffs / Handoff analyzer đã lưu |
| `training_runs/weight-adjustment-recommendation-*.json` | Persisted weight-adjustment recommendations / Khuyến nghị chỉnh trọng số đã lưu |
| `training_runs/experiment-adjusted-high-confidence-*/active_chromosome.json` | Ready-to-run candidate active model from weight recommender / Candidate active model chạy thử từ recommender |
| `training_runs/active_chromosome.json` | Promoted local weights / Weight cục bộ đang dùng |
| `training_runs/*.png` | Optional charts / Biểu đồ tùy chọn |
| `training_runs/known-future-*.json` | Optional comparison reports / Report so sánh tùy chọn |

Generated artifacts are ignored by Git unless explicitly preserved for analysis.  
Artifact sinh ra được Git bỏ qua trừ khi chủ động lưu để phân tích.

## 14. Living Documentation Rule / Quy tắc tài liệu sống

### English

`WHITEPAPER.md` is the canonical project overview and operating manual. Every feature,
fix, or refactor must review whitepaper impact. Update this page when a change affects
user-facing behavior, architecture, commands, parameters, generated artifacts, log
fields, optimization guidance, or operational workflows. If no update is required,
record that decision in the feature tasks or review notes.

### Tiếng Việt

`WHITEPAPER.md` là trang giới thiệu và hướng dẫn vận hành chính thức. Mọi feature, bugfix
hoặc refactor đều phải kiểm tra ảnh hưởng lên whitepaper. Cập nhật trang này khi thay đổi
ảnh hưởng hành vi người dùng, kiến trúc, command, tham số, artifact sinh ra, field log,
hướng dẫn tối ưu hoặc quy trình vận hành. Nếu không cần cập nhật, ghi nhận quyết định đó
trong task hoặc review note của feature.

## 15. Deeper References / Tài liệu chi tiết hơn

- `README.md`: short repository entry point / trang vào ngắn gọn.
- `thiet_ke_thuat_toan_bot_puzzle.md`: original algorithm design / thiết kế thuật toán gốc.
- `.specify/memory/constitution.md`: mandatory project principles / nguyên tắc bắt buộc.
- `specs/`: feature specifications, plans, and quickstarts / đặc tả, kế hoạch và quickstart.
- `AGENTS.md`, `CLAUDE.md`: agent development guidance / hướng dẫn agent phát triển.
