from mitmproxy import http
import json
import datetime
import traceback
import re
import os
from content import get_openai_response
from main import filter_message

LOG_FILE = "C:/Users/29742/Desktop/contentsecurity/log/log.txt"
DEBUG_LOG = "C:/Users/29742/Desktop/contentsecurity/log/debug_log.txt"
flag = False  # 全局变量，判断是否要拦截响应
def ensure_log_dir_exists(log_path):
    log_dir = os.path.dirname(log_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

def write_log(message: str):
    ensure_log_dir_exists(LOG_FILE)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}]\n{message}\n\n")

def write_debug(message: str):
    ensure_log_dir_exists(DEBUG_LOG)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp} DEBUG] {message}\n\n")

def extract_user_question(data):
    if "messages" in data:
        messages = data.get("messages", [])
        if isinstance(messages, list) and messages:
            for msg in messages:
                if isinstance(msg, dict):
                    author = msg.get("author", {})
                    if author.get("role") == "user":
                        content = msg.get("content", {})
                        if isinstance(content, dict) and "parts" in content:
                            parts = content.get("parts", [])
                            if parts and isinstance(parts, list):
                                return parts[0]
    return "(未知)"

def request(flow: http.HTTPFlow):
    global flag
    if "chatgpt.com/backend-api" in flow.request.pretty_url:
        if flow.request.content and flow.request.headers.get("content-type", "").startswith("application/json"):
            try:
                data = json.loads(flow.request.get_text())
                question = extract_user_question(data)
                flow.request.headers["user-question"] = question
                write_debug(f"捕获问题: {question}")

                # 审查用户问题
                filtered_result = filter_message(question)
                if filtered_result == None:
                    write_debug(f"问题命中本地规则，拦截：{filtered_result}")
                    flag = True
                # else:
                #     response = get_openai_response(question)
                #     if "【涉及" in response and "风险】" in response:
                #         write_debug(f"OpenAI 回复命中：{response}")
                #         flag = True
            except Exception as e:
                write_debug(f"提取/审核失败: {str(e)}")

def response(flow: http.HTTPFlow):
    global flag
    if "chatgpt.com/backend-api" in flow.request.pretty_url:
        content_type = flow.response.headers.get("content-type", "")
        question = flow.request.headers.get("user-question", "(未知)")  # 这里一定要加
        if flag and "text/event-stream" in content_type:
            write_debug("开始替换")
            blocked_text = "您输入的内容有误，请重新输入"
            raw_text = flow.response.get_text()
            lines = raw_text.split('\n')
            new_lines = []
            event_type = None
            replaced = False

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    new_lines.append('')  # 保留空行
                    continue
                if stripped.startswith("event: "):
                    event_type = stripped[7:]
                    new_lines.append(line)
                    continue
                if stripped.startswith("data: "):
                    data_content = stripped[6:]
                    if data_content == '[DONE]' or data_content.startswith('"'):
                        new_lines.append(line)
                        continue
                    try:
                        data = json.loads(data_content)
                        if event_type == "delta":
                            if not replaced:
                                # 第一次替换，填充提示文本
                                if data.get('o') == 'append' and data.get('p', '').startswith('/message/content/parts/0'):
                                    data['v'] = blocked_text
                                    replaced = True
                                elif 'v' in data and isinstance(data['v'], str):
                                    data['v'] = blocked_text
                                    replaced = True
                                elif data.get('o') == 'patch' and isinstance(data.get('v'), list):
                                    for patch in data['v']:
                                        if patch.get('o') == 'append' and patch.get('p', '').startswith('/message/content/parts/0'):
                                            patch['v'] = blocked_text
                                            replaced = True
                            else:
                                # 后续替换成空字符串，避免显示原内容
                                if data.get('o') == 'append' and data.get('p', '').startswith('/message/content/parts/0'):
                                    data['v'] = ""
                                elif 'v' in data and isinstance(data['v'], str):
                                    data['v'] = ""
                                elif data.get('o') == 'patch' and isinstance(data.get('v'), list):
                                    for patch in data['v']:
                                        if patch.get('o') == 'append' and patch.get('p', '').startswith('/message/content/parts/0'):
                                            patch['v'] = ""
                        line = "data: " + json.dumps(data, ensure_ascii=False)
                    except Exception as e:
                        write_debug(f"替换解析错误: {str(e)}")
                    new_lines.append(line)
                else:
                    new_lines.append(line)

            flow.response.text = '\n'.join(new_lines) + '\n\n'
            write_debug(f"响应被替换，长度: {len(flow.response.text)}")
            flag = False

            return


        # 提取实际返回内容用于日志记录
        elif  "text/event-stream" in content_type:
                raw_text = flow.response.get_text()
                write_debug(f"原始SSE长度: {len(raw_text)}")

                full_response = ""
                event_type = None

                for line in raw_text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("event: "):
                        event_type = line[7:]
                        continue
                    if line.startswith("data: "):
                        try:
                            data_content = line[6:]
                            if data_content == '[DONE]' or data_content.startswith('"'):
                                continue
                            if '"type":' in data_content and any(x in data_content for x in [
                                '"title_generation"', '"message_stream_complete"', '"conversation_detail_metadata"']):
                                continue
                            data = json.loads(data_content)

                            if event_type == "delta":
                                if data.get('o') == 'append' and 'v' in data:
                                    if data.get('p', '').startswith('/message/content/parts/0'):
                                        full_response += data['v']
                                elif 'v' in data and isinstance(data['v'], str):
                                    full_response += data['v']
                                elif data.get('o') == 'patch' and isinstance(data.get('v'), list):
                                    for patch in data['v']:
                                        if patch.get('o') == 'append' and patch.get('p', '').startswith('/message/content/parts/0'):
                                            full_response += patch['v']
                        except Exception as e:
                            write_debug(f"SSE解析失败: {traceback.format_exc()}")
                if full_response:
                    clean_response = re.sub(r'<[^>]+>', '', full_response)
                    qa_pair = f"问：{question}\n答：{clean_response}"
                    write_log(qa_pair)
                    write_debug(f"成功提取回答，长度: {len(clean_response)}")

                    with open("C:/Users/29742/Desktop/contentsecurity/log/full_responses.txt", "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n{qa_pair}\n\n")
