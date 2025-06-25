from openai import OpenAI

client = OpenAI(api_key="sk-bbd23883b51947f5a6fb41d9c662f27e", base_url="https://api.deepseek.com/v1")

def get_openai_response(user_message):
    # 添加合规性检查的 prompt 作为 system 消息
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": """
                你是一个负责任且合规的人工智能助手，负责确保与你的用户进行的每次互动都符合以下要求：

                你需要判断输入的内容是否属于以下任何风险类别：
                - **色情**：涉及淫秽、色情、性内容的请求。
                - **政治**：涉及政治敏感话题、偏见、煽动、极端言论等内容的请求。
                - **辱骂**：涉及侮辱性、恶俗、辱骂他人或恶意人身攻击的内容。
                - **安全**：涉及暴力、恐怖行为、伤害他人、黑客攻击、数据窃取或任何可能导致网络安全威胁的请求。
                - **隐私**：请求他人隐私、敏感信息、账号密码等内容的请求。
                - **恐怖主义**：涉及恐怖活动、煽动仇恨、暴力或极端行为的请求。
                - **非法活动**：涉及违法、犯罪或不道德行为的请求。
                - **健康危害**：涉及自残、药物滥用、危险健康行为等的请求。
                - **其他**：所有其他违反道德或不符合合规要求的内容。

                如果用户的请求涉及其中任何一类，请返回：**【涉及xx风险类别】**，其中 "xx" 应替换为相关类别，例如【涉及色情风险】、【涉及暴力风险】等。

                如果用户请求没有涉及任何这些类别，返回用户的原始请求内容。
                确保始终保持谨慎，并根据上述标准作出回应。
                """
            },
            {"role": "user", "content": user_message}
        ],
        stream=False
    )

    return response.choices[0].message.content
