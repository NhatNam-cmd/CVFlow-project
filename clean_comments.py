import os


def remove_comments_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()

        # 1. Bỏ qua dòng comment (bắt đầu bằng #)
        if stripped.startswith("#"):
            continue

        # 2. (Tuỳ chọn) Bỏ qua dòng trống thừa (nếu muốn code gọn hơn)
        # if not stripped:
        #     continue

        new_lines.append(line)

    # Ghi đè lại file
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"✅ Đã dọn dẹp: {file_path}")


def clean_project(root_dir):
    print("🧹 Đang dọn dẹp toàn bộ comment trong dự án...")
    for root, dirs, files in os.walk(root_dir):
        # Bỏ qua thư mục venv và .git
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue

        for file in files:
            if file.endswith(".py") and file != "clean_comments.py":
                file_path = os.path.join(root, file)
                remove_comments_from_file(file_path)


if __name__ == "__main__":
    # Lấy thư mục hiện tại
    current_folder = os.getcwd()

    # Hỏi xác nhận cho chắc
    confirm = input("⚠️  Bạn có chắc muốn xóa HẾT comment trong file .py không? (y/n): ")
    if confirm.lower() == "y":
        clean_project(current_folder)
        print("🎉 Hoàn tất dọn dẹp!")
    else:
        print("Đã hủy.")
