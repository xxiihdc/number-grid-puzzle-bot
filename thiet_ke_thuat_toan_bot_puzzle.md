# BÁO CÁO PHÂN TÍCH VÀ THIẾT KẾ THUẬT TOÁN TỐI ƯU CHO BOT GAME NUMBER GRID PUZZLE

Tài liệu này tổng hợp toàn bộ các phân tích toán học, tư duy thiết kế, chiến lược tối ưu hóa không gian trạng thái, thuật toán tìm kiếm nước đi và phương pháp học máy (Học di truyền mở rộng) để xây dựng một Bot tự động chơi game "Sắp Xếp Số Trên Lưới" đạt điểm tối ưu.

---

## 1. ĐẶC TẢ MÔI TRƯỜNG GAME VÀ PHÂN TÍCH TOÁN HỌC

### A. Tóm tắt Luật chơi Cốt lõi
* **Không gian:** Ma trận phẳng kích thước $9 \times 9$ (tổng cộng 81 ô). Tọa độ được đánh dấu từ $(0,0)$ đến $(8,8)$.
* **Thời lượng:** Cố định chính xác trong 27 lượt (turns). Game kết thúc ngay sau lượt thứ 27.
* **Vật phẩm sinh ra (Spawned Block):** Mỗi lượt xuất hiện duy nhất một khối dọc kích thước $3 \times 1$ (3 hàng $\times$ 1 cột). Mỗi ô trong 3 ô chứa một số nguyên ngẫu nhiên thuộc tập $\{7, 8, 9, 10\}$.
* **Cơ chế ghi điểm:** Khi xuất hiện chuỗi từ 3 số giống nhau trở lên tạo thành một đường thẳng liên tục (ngang, dọc, hoặc chéo). Sau khi ghi điểm, **các ô số giữ nguyên, không biến mất**, cho phép tái sử dụng để tạo combo ở các lượt tiếp theo.

### B. Giảm thiểu Không gian Hành động (Action Space Reduction)
Ràng buộc nghiêm ngặt của game yêu cầu "Lấp đầy hoàn hảo không vết nứt" (Perfect Packing). Vì $27 \text{ lượt} \times 3 \text{ ô} = 81 \text{ ô}$ (vừa khít diện tích lưới), bất kỳ hành động đặt khối nào tạo ra khoảng trống lẻ 1 hoặc 2 ô cô lập trên một cột sẽ dẫn tới trạng thái thất bại toán học (không thể lấp đầy vào cuối game).

Do khối luôn có kích thước cố định là $3 \times 1$ (dọc) và không thể xoay, chúng ta có thể tối ưu hóa tuyệt đối không gian hành động như sau:
* **Tọa độ X (Cột):** Khối có thể đặt tự do ở bất kỳ cột nào trong 9 cột, $X \in \{0, 1, 2, 3, 4, 5, 6, 7, 8\}\$.
* **Tọa độ Y (Hàng):** Để đảm bảo các khối xếp khít nhau mà không tạo khoảng trống đơn lẻ, trên mỗi cột, lưới phải được chia thành đúng 3 phân vùng (slots) cố định. Do đó, tọa độ ô trên cùng của khối (Anchor Y) **bắt buộc** phải thuộc tập $Y \in \{0, 3, 6\}\$.

**Kết luận:** Thay vì tìm kiếm trên toàn bộ lưới 9x9 với hàng chục cách đặt phức tạp, không gian hành động của Bot được thu hẹp lại thành chính xác **27 vị trí hợp lệ (Slots)**. Mỗi lượt đi, Bot chỉ cần chọn 1 trong số các Slots chưa bị chiếm dụng.

---

## 2. THUẬT TOÁN TÌM KIẾM CHO ĐIỂM SỐ TỐI ƯU (INFERENCE ENGINE)

Do game có tính chất ngẫu nhiên cao (mỗi lượt có $4^3 = 64$ khả năng sinh khối), việc sử dụng các thuật toán duyệt cây thông thường như Minimax là không khả thi. Hai lựa chọn tối ưu nhất là **Expectimax Search** và **Monte Carlo Tree Search (MCTS)**.

### A. Lựa chọn Cấu trúc Dữ liệu Hiệu năng Cao
Để Bot đạt tốc độ duyệt hàng vạn trạng thái trên giây, cấu trúc dữ liệu mô phỏng phải loại bỏ hoàn toàn mô hình Đồ thị đa đỉnh (Graph) truyền thống (như danh sách kề/ma trận kề) để tránh overhead bộ nhớ.
* **Biểu diễn Lưới:** Sử dụng mảng 1 chiều (1D Array) có độ dài 81 để tối ưu cache của CPU, thay vì mảng 2 chiều.
* **Thuật toán tính điểm Cục bộ (Local Ray-casting):** Khi đặt một khối xuống, không quét lại toàn bộ bảng. Chỉ xuất phát từ 3 ô mới đặt, "phóng tia" theo 4 vector hướng: Ngang $(1,0)$, Dọc $(0,1)$, Chéo thuận $(1,1)$, Chéo nghịch $(1,-1)$ về cả hai chiều dương/âm để đếm chuỗi liên thông. Độ phức tạp là $O(1)$ cho mỗi slot.

### B. Chiến lược Tìm kiếm theo Độ sâu Động (Dynamic Depth Expectimax)
Nếu cấu hình laptop hiện đại có hiệu năng CPU đa nhân tốt, việc áp dụng chiến lược Độ sâu Động dựa trên cây tìm kiếm Expectimax kết hợp hàm Heuristic sẽ mang lại độ chính xác cực cao mà không làm nghẽn phần cứng:

1.  **Giai đoạn Khởi đầu (Lượt 1 - 10): Chạy Độ sâu 2**
    * *Mô tả:* Tính toán lượt hiện tại và dự đoán trước 1 lượt tương lai.
    * *Khối lượng:* $27 \text{ (slots)} \times 64 \text{ (khối ngẫu nhiên)} \times 26 \text{ (slots tương lai)} \approx 45,000$ trạng thái. CPU xử lý trong vài mili-giây.
    * *Mục đích:* Bảng còn quá trống, tính quá xa sẽ bị nhiễu do yếu tố ngẫu nhiên (RNG).

2.  **Giai đoạn Trung cuộc (Lượt 11 - 20): Chạy Độ sâu 3**
    * *Mô tả:* Tính toán lượt hiện tại và dự đoán trước 2 lượt tương lai.
    * *Khối lượng:* $45,000 \times 64 \times 25 \approx 72$ triệu trạng thái. Khi được tối ưu bằng C++/C# hoặc thư viện Numba (Python), thời gian chạy chỉ mất từ 1 - 3 giây cho mỗi nước đi.
    * *Mục đích:* Đây là giai đoạn các cụm số đã thành hình, cần tính toán sâu để tránh bít đường và chuẩn bị combo.

3.  **Giai đoạn Tàn cuộc (Lượt 21 - 27): Chạy Độ sâu 4 hoặc 5**
    * *Mô tả:* Dự đoán từ 3 đến 4 lượt tiếp theo cho đến khi kết thúc game.
    * *Khối lượng:* Do số slot trống lúc này giảm mạnh (chỉ còn từ 2 đến 7 slots), số lượng trạng thái sụt giảm nghiêm trọng. Ví dụ ở lượt 24 chỉ còn 4 slots trống: $4 \times 64 \times 3 \times 64 \times 2 \approx 98,304$ trạng thái.
    * *Mục đích:* Duyệt toàn bộ các khả năng còn lại để chốt hạ tổng điểm tối đa, ăn các chuỗi combo dồn dập.

---

## 3. HÀM ĐÁNH GIÁ HEURISTIC VÀ THUẬT TOÁN TỐI ƯU THAM SỐ (TRAINING ENGINE)

Hàm Heuristic tổng quát dùng để chấm điểm một trạng thái bảng chưa hoàn chỉnh có dạng đa thức bậc nhất:
$$H(state) = \sum_{i=1}^{M} (W_i \times f_i(state))$$
Trong đó $f_i$ là điểm số của chỉ số thứ $i$, và $W_i$ là trọng số tương ứng.

### A. Khắc phục lỗi hội tụ sớm (Plateau ở thế hệ 20) của Học Di Truyền (GA)
Nếu bạn chạy thuật toán di truyền thông thường và bị đứng chững điểm số sau 20 thế hệ, đó là do hiện tượng **Hội tụ sớm (Premature Convergence)** do nhiễu RNG đánh lừa hệ thống. Hãy áp dụng các kỹ thuật khắc phục sau:

1.  **Đồng bộ hạt giống ngẫu nhiên (Common Random Numbers - CRN):**
    * Tuyệt đối không cho mỗi cá thể chơi trên các kịch bản ngẫu nhiên khác nhau.
    * Tạo cố định một bộ $N$ kịch bản (ví dụ $N=50$ hạt giống seed đại diện cho chuỗi 27 khối). Tất cả cá thể trong cùng thế hệ phải thi đấu trên cùng một bộ seed này. Điểm thích nghi (Fitness) bằng trung bình cộng điểm số của 50 trận.
2.  **Đột biến thích ứng (Adaptive Mutation Surge):**
    * Nếu điểm số cao nhất của quần thể không thay đổi trong 3 thế hệ liên tiếp, tự động đẩy tỷ lệ đột biến (Mutation Rate) từ $5\%$ lên $25\%$ trong 1 thế hệ duy nhất để phá vỡ cục bộ, ép các cá thể tìm kiếm ở các vùng không gian mới.
3.  **Học Trọng số phân rã theo Giai đoạn (Phase-based Genomes):**
    * Chiến thuật đầu game (cần mở rộng không gian) khác hoàn toàn cuối game (cần vét điểm). Thay vì bắt một bộ trọng số dùng cho toàn bộ ván đấu, hãy cấu trúc bộ Gen gồm 3 phân đoạn tương ứng với 3 Phase của game (Lượt 1-10, Lượt 11-20, Lượt 21-27). AI sẽ tự học cách thay đổi chiến thuật theo thời gian.

---

## 4. THUẬT TOÁN TỰ ĐỘNG KHÁM PHÁ VÀ LỰA CHỌN CHỈ SỐ (FEATURE DISCOVERY)

Để tránh việc con người áp đặt tư duy chủ quan (chỉ chọn vài chỉ số cơ bản), chúng ta có thể lập trình để AI tự tìm ra **"Tên chỉ số nào xứng đáng giữ lại và đặt trọng số"**.

### Phương pháp Khuyên dùng: Bể Đặc Trưng + Mặt Nạ Nhị Phân (Feature Pool & Binary Masking)

Phương pháp này tích hợp trực tiếp vào thuật toán Học Di truyền (GA) sẵn có, chạy rất nhẹ và dễ cài đặt hơn nhiều so với Lập trình di truyền (Genetic Programming).

#### Bước 1: Khởi tạo Bể Đặc Trưng (Feature Pool)
Lập trình viên viết sẵn mã nguồn cho một danh sách lớn gồm $M$ chỉ số hình học và logic tiềm năng (ví dụ $M = 15$). Lúc này, ta chưa biết chỉ số nào đúng, chỉ số nào sai.

#### Bước 2: Tái cấu trúc Bộ Gen (Genome)
Mỗi cá thể trong quần thể GA bây giờ sẽ mang một cấu trúc nhiễm sắc thể kép gồm hai thành phần cho mỗi chỉ số:
$$\text{Gen}_i = (\text{Mask}_i, \text{Weight}_i)$$
* $\text{Mask}_i \in \{0, 1\}$: Biến nhị phân đóng vai trò là "Công tắc". Nếu bằng 1 thì chỉ số đó được sử dụng, bằng 0 thì chỉ số đó bị loại bỏ hoàn toàn khỏi hàm đánh giá.
* $\text{Weight}_i \in [-100.0, 100.0]$: Trọng số dạng số thực của chỉ số đó nếu nó được bật.

Khi tính toán hàm Heuristic cho một cá thể:
$$H(state) = \sum_{i=1}^{M} \left( \text{Mask}_i \times \text{Weight}_i \times f_i(state) \right)$$

#### Bước 3: Đào thải tự động qua các Thế hệ
* **Crossover (Lai ghép):** Các cá thể trao đổi chéo cả thanh công tắc (`Mask`) lẫn trọng số (`Weight`).
* **Mutation (Đột biến):** Có tỷ lệ nhỏ công tắc bị đảo mạch ($0 \rightarrow 1$ hoặc $1 \rightarrow 0$), và trọng số bị thay đổi giá trị.
* **Kết quả:** Nếu một chỉ số $f_x$ mang lại tư duy sai lệch khiến Bot bị thấp điểm, các cá thể có $\text{Mask}_x = 1$ sẽ bị chết dần. Qua nhiều thế hệ, các cá thể xuất sắc nhất sống sót sẽ sở hữu chuỗi $\text{Mask}$ ổn định. Bạn chỉ cần in bộ gen của nhà vô địch ra: Những chỉ số nào có $\text{Mask} = 1$ chính là những "Tên chỉ số" tối ưu mà AI đã tự tìm ra.

---

## 5. ĐỀ XUẤT BỂ ĐẶC TRƯNG (FEATURE POOL) 15 CHỈ SỐ CHO GAME

Dưới đây là danh sách 15 chỉ số cụ thể từ thô sơ đến chuyên sâu về mặt không gian để ném vào Bể Đặc Trưng cho AI tự sàng lọc:

1.  `f1_actual_score`: Số điểm ghi được ngay lập tức tại lượt hiện tại (Giá trị dương).
2.  `f2_potential_horizontal_pairs`: Số lượng cặp 2 ô giống nhau nằm ngang kề nhau mà hai đầu còn trống (Tiềm năng tạo chuỗi ngang).
3.  `f3_potential_diagonal_pairs`: Số lượng cặp 2 ô giống nhau nằm chéo kề nhau mà hai đầu còn trống (Tiềm năng tạo chuỗi chéo).
4.  `f4_column_bumpiness`: Độ gồ ghề của lưới, tính bằng tổng chênh lệch chiều cao (số lượng ô đã lấp) giữa các cột kề nhau. (Thường mang giá trị phạt âm để ép các cột bằng nhau, dễ ăn chuỗi ngang).
5.  `f5_center_bias`: Điểm thưởng khi đặt khối vào các cột trung tâm 3, 4, 5 ở giai đoạn đầu game.
6.  `f6_isolated_slots`: Số lượng các slot trống bị bao vây hoàn toàn bởi các slot đã đầy, gây khó khăn cho việc nối chéo.
7.  `f7_dead_ends`: Số lượng vị trí trống bị kẹp giữa các số khác nhau, khiến đường đi của một số bị chặn đứng (Phá cấu trúc).
8.  `f8_max_height`: Chiều cao lớn nhất hiện tại của toàn lưới.
9.  `f9_number_density_7`: Mức độ tập trung cục bộ (clustering) của riêng các số 7 đứng gần nhau.
10. `f10_number_density_8`: Mức độ tập trung cục bộ của riêng các số 8 đứng gần nhau.
11. `f11_number_density_9`: Mức độ tập trung cục bộ của riêng các số 9 đứng gần nhau.
12. `f12_number_density_10`: Mức độ tập trung cục bộ của riêng các số 10 đứng gần nhau.
13. `f13_vertical_match_interfaces`: Số lượng điểm tiếp xúc khớp số giữa đáy của slot tầng trên và đỉnh của slot tầng dưới trên cùng một cột.
14. `f14_empty_slots_count`: Số lượng slot trống còn lại trên bảng (Giúp nhận diện tiến trình game).
15. `f15_diagonal_cross_points`: Số lượng ô trống mang tính chiến lược, nơi giao nhau của nhiều đường chéo tiềm năng nhất.

---
*Báo cáo kết thúc. Cấu trúc thiết kế này đảm bảo tối ưu hóa từ khâu huấn luyện tìm tham số (Offline) cho đến khâu thực thi đưa ra nước đi tức thời (Online).*
