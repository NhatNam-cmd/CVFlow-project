import os

SOURCE_FOLDER = "app"  # Thư mục cần quét
OUTPUT_FILE = "all_code_for_ai.txt"  # File kết quả
IGNORE_DIRS = {"static", "migrations", "__pycache__", "env", "venv", ".git"}


def merge_code():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        root_files = ["config.py", "run.py"]
        for rf in root_files:
            if os.path.exists(rf):
                outfile.write(f"{'='*20}\nFILE: {rf}\n{'='*20}\n")
                with open(rf, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read() + "\n\n")

        for root, dirs, files in os.walk(SOURCE_FOLDER):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)

                    try:
                        with open(file_path, "r", encoding="utf-8") as infile:
                            content = infile.read()

                            outfile.write(f"{'='*40}\n")
                            outfile.write(f"FILE PATH: {file_path}\n")
                            outfile.write(f"{'='*40}\n")

                            outfile.write(content + "\n\n")
                            print(f"✅ Đã thêm: {file_path}")

                    except Exception as e:
                        print(f"⚠️ Lỗi đọc file {file_path}: {e}")

    print(f"\n🎉 Xong! Toàn bộ code đã được lưu vào: {OUTPUT_FILE}")


if __name__ == "__main__":
    merge_code()
