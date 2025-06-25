import os
import ast
import sys
import importlib

if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata


def get_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read())

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                imports.add(node.module.split('.')[0])

    return imports


def get_standard_library_modules():
    # 兼容 Python < 3.10
    try:
        return set(sys.stdlib_module_names)
    except AttributeError:
        import sysconfig
        std_lib_dir = sysconfig.get_path("stdlib")
        std_libs = set()
        for root, dirs, files in os.walk(std_lib_dir):
            for file in files:
                if file.endswith(".py"):
                    std_libs.add(os.path.splitext(file)[0])
        return std_libs


def get_package_version(package_name):
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return None


def analyze_dependencies():
    all_imports = set()

    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                all_imports.update(get_imports(file_path))

    std_libs = get_standard_library_modules()
    third_party_imports = all_imports - std_libs

    with open('requirements.txt', 'w') as f:
        for package in sorted(third_party_imports):
            version = get_package_version(package)
            if version:
                f.write(f"{package}=={version}\n")
            else:
                f.write(f"{package}\n")

    print("✅ requirements.txt 文件已生成，包含实际使用的第三方依赖。")


if __name__ == "__main__":
    analyze_dependencies()
