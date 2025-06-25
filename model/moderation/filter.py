# -*- coding:utf-8 -*-
import pickle
from collections import defaultdict
import re

class DFAFilter:
    '''Filter Messages from keywords using DFA (Deterministic Finite Automaton)'''

    def __init__(self):
        self.keyword_chains = {}
        self.delimit = '\x00'

    def add(self, keyword):
        '''
        添加敏感词到 DFA
        '''
        if not isinstance(keyword, str):
            keyword = keyword.decode('utf-8')
        keyword = keyword.lower()
        chars = keyword.strip()
        if not chars:
            return
        level = self.keyword_chains
        for i in range(len(chars)):
            if chars[i] in level:
                level = level[chars[i]]
            else:
                if not isinstance(level, dict):
                    break
                for j in range(i, len(chars)):
                    level[chars[j]] = {}
                    last_level, last_char = level, chars[j]
                    level = level[chars[j]]
                last_level[last_char] = {self.delimit: 0}
                break
        if i == len(chars) - 1:
            level[self.delimit] = 0

    def parse(self, path):
        '''
        从文件中加载敏感词
        '''
        with open(path) as f:
            for keyword in f:
                self.add(keyword.strip())

    def filter(self, message, repl="*"):
        '''
        过滤消息，将敏感词替换为指定字符
        '''
        if not isinstance(message, str):
            message = message.decode('utf-8')
        message = message.lower()
        ret = []
        start = 0
        while start < len(message):
            level = self.keyword_chains
            step_ins = 0
            for char in message[start:]:
                if char in level:
                    step_ins += 1
                    if self.delimit not in level[char]:
                        level = level[char]
                    else:
                        ret.append(repl * step_ins)
                        start += step_ins - 1
                        break
                else:
                    ret.append(message[start])
                    break
            else:
                ret.append(message[start])
            start += 1

        return ''.join(ret)

    def save(self, filename):
        '''保存 DFA 模型到文件'''
        with open(filename, 'wb') as f:
            pickle.dump(self.keyword_chains, f)

    def load(self, filename):
        '''从文件加载 DFA 模型'''
        with open(filename, 'rb') as f:
            self.keyword_chains = pickle.load(f)

# 创建 DFAFilter 实例
f = DFAFilter()

# 如果没有已经保存的模型，则加载敏感词文件并保存
model_filename = 'dfa_model.pkl'

try:
    # 尝试加载已保存的模型
    f.load(model_filename)
    print("模型加载成功！")
except FileNotFoundError:
    print("未找到已保存的模型，开始训练...")
    file_path = './keywords'  # 您的敏感词文件路径

    # 读取文件并将敏感词添加到 DFAFilter 中
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            sensitive_word = line.strip()
            f.add(sensitive_word)

    # 保存训练好的模型
    f.save(model_filename)
    print("模型已训练并保存！")
'''
# 示例过滤
message = ""
filtered_message = f.filter(message)

# 输出过滤后的消息
print("过滤后的消息：", filtered_message)  # 这行代码用于输出过滤结果
'''