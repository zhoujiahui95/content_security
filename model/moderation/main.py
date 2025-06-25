import datetime
import os
from filter import DFAFilter  # 假设你在 filter.py 中定义了 DFAFilter 类
from content import get_openai_response
DEBUG_LOG = "C:/Users/29742/Desktop/contentsecurity/log/debug_log.txt"
# 创建 DFAFilter 实例
f = DFAFilter()
def ensure_log_dir_exists(log_path):
    log_dir = os.path.dirname(log_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
# 加载已经训练的敏感词模型
model_filename = 'dfa_model.pkl'
def write_debug(message: str):
    ensure_log_dir_exists(DEBUG_LOG)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp} DEBUG] {message}\n\n")
try:
    # 尝试加载已保存的模型
    f.load(model_filename)
    print("模型加载成功！")
except FileNotFoundError:
    print("未找到已保存的模型，开始训练...")
    file_path = './keywords'  # 你的敏感词文件路径

    # 读取文件并将敏感词添加到 DFAFilter 中
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            sensitive_word = line.strip()
            f.add(sensitive_word)

    # 保存训练好的模型
    f.save(model_filename)
    print("模型已训练并保存！")


# 函数：检测字符串是否包含敏感内容
def filter_message(message):
    filtered_message = f.filter(message)  # 使用DFAFilter过滤敏感词
    if filtered_message != message:
        # 过滤包含敏感词的消息，输出过滤后的消息
        write_debug(f"用户问题包含敏感内容:")
        write_debug(f"过滤后的消息：{filtered_message}")
        return None
    return message


# 主程序
def main():
    while True:
        message = input("请输入消息:")
        #这里修改消息

        # 检查并过滤消息内容
        filtered_message = filter_message(message)

        if filtered_message:  # 如果没有敏感词，发送到 OpenAI API
            response = get_openai_response(filtered_message)  # 调用 openai.py 中的函数

            print("OpenAI 回复:", response)
        # 如果过滤器返回 None，表示消息含有敏感词，因此不再进行 OpenAI 调用
        # 不需要额外的输出或操作，直接跳过并等待用户输入下一条消息


if __name__ == '__main__':
    main()
