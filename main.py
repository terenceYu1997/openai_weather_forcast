import json
import os
import openai
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored
from getCityUtils import _get_current_weather, _get_n_day_weather_forecast

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

GPT_MODEL = "gpt-3.5-turbo"
OPEN_API_KEY = os.getenv("OPEN_API_KEY")

# 使用了retry库，指定在请求失败时的重试策略。
# 这里设定的是指数等待（wait_random_exponential），时间间隔的最大值为40秒，并且最多重试3次（stop_after_attempt(3)）。
# 定义一个函数chat_completion_request，主要用于发送 聊天补全 请求到OpenAI服务器
@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, functions=None, function_call=None, model=GPT_MODEL):

    # 设定请求的header信息，包括 API_KEY
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + OPEN_API_KEY,
    }

    # 设定请求的JSON数据，包括GPT 模型名和要进行补全的消息
    json_data = {"model": model, "messages": messages}

    # 如果传入了functions，将其加入到json_data中
    if functions is not None:
        json_data.update({"functions": functions})

    # 如果传入了function_call，将其加入到json_data中
    if function_call is not None:
        json_data.update({"function_call": function_call})

    # 尝试发送POST请求到OpenAI服务器的chat/completions接口
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        # 返回服务器的响应
        return response

    # 如果发送请求或处理响应时出现异常，打印异常信息并返回
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


# 定义一个函数pretty_print_conversation，用于打印消息对话内容
def pretty_print_conversation(messages):

    # 为不同角色设置不同的颜色
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "light_blue",
        "function": "magenta",
    }

    # 遍历消息列表
    for message in messages:

        # 如果消息的角色是"system"，则用红色打印“content”
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))

        # 如果消息的角色是"user"，则用绿色打印“content”
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))

        # 如果消息的角色是"assistant"，并且消息中包含"function_call"，则用蓝色打印"function_call"
        elif message["role"] == "assistant" and message.get("function_call"):
            print(colored(f"assistant[function_call]: {message['function_call']}\n", role_to_color[message["role"]]))

        # 如果消息的角色是"assistant"，但是消息中不包含"function_call"，则用蓝色打印“content”
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant[content]: {message['content']}\n", role_to_color[message["role"]]))

        # 如果消息的角色是"function"，则用品红色打印“function”
        elif message["role"] == "function":
            print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))


# 定义一个名为functions的列表，其中包含两个字典，这两个字典分别定义了两个功能的相关参数

# 第一个字典定义了一个名为"get_current_weather"的功能
functions = [
    {
        "name": "get_current_weather",  # 功能的名称
        "description": "Get the current weather",  # 功能的描述
        "parameters": {  # 定义该功能需要的参数
            "type": "object",
            "properties": {  # 参数的属性
                "location": {  # 地点参数
                    "type": "string",  # 参数类型为字符串
                    "description": "The city and state, e.g. San Francisco, CA",  # 参数的描述
                },
                "format": {  # 温度单位参数
                    "type": "string",  # 参数类型为字符串
                    "enum": ["celsius", "fahrenheit"],  # 参数的取值范围
                    "description": "The temperature unit to use. Infer this from the users location.",  # 参数的描述
                },
            },
            "required": ["location", "format"],  # 该功能需要的必要参数
        },
    },
    # 第二个字典定义了一个名为"get_n_day_weather_forecast"的功能
    {
        "name": "get_n_day_weather_forecast",  # 功能的名称
        "description": "Get an N-day weather forecast",  # 功能的描述
        "parameters": {  # 定义该功能需要的参数
            "type": "object",
            "properties": {  # 参数的属性
                "location": {  # 地点参数
                    "type": "string",  # 参数类型为字符串
                    "description": "The city and state, e.g. San Francisco, CA",  # 参数的描述
                },
                "format": {  # 温度单位参数
                    "type": "string",  # 参数类型为字符串
                    "enum": ["celsius", "fahrenheit"],  # 参数的取值范围
                    "description": "The temperature unit to use. Infer this from the users location.",  # 参数的描述
                },
                "num_days": {  # 预测天数参数
                    "type": "integer",  # 参数类型为整数
                    "description": "The number of days to forecast",  # 参数的描述
                }
            },
            "required": ["location", "format", "num_days"]  # 该功能需要的必要参数
        },
    },
]

# 定义一个空列表messages，用于存储聊天的内容
messages = []

# 使用append方法向messages列表添加一条系统角色的消息
messages.append({
    "role": "system",  # 消息的角色是"system"
    "content": "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."  # 消息的内容
})

# 向messages列表添加一条用户角色的消息
messages.append({
    "role": "user",  # 消息的角色是"user"
    "content": "What's the weather like today"  # 用户询问今天的天气情况
    # TODO step 2
    # "content": "what is the weather going to be like in Shanghai, China over the next 3 days"  # 用户询问今天的天气情况
})

# 使用定义的chat_completion_request函数发起一个请求，传入messages和functions作为参数
chat_response = chat_completion_request(
    messages, functions=functions
)


# 解析返回的JSON数据，获取助手的回复消息
assistant_message = chat_response.json()["choices"][0]["message"]

# 将助手的回复消息添加到messages列表中
messages.append(assistant_message)

# pretty_print_conversation(messages)


# TODO step 1
#
# # 向messages列表添加一条用户角色的消息
# messages.append({
#     "role": "user",  # 消息的角色是"user"
#     "content": "I'm in Shanghai, China."  # 用户的消息内容
# })
#
# # 再次使用定义的chat_completion_request函数发起一个请求，传入更新后的messages和functions作为参数
# chat_response = chat_completion_request(
#     messages, functions=functions
# )
#
# # 解析返回的JSON数据，获取助手的新的回复消息
# assistant_message = chat_response.json()["choices"][0]["message"]
#
# # 将助手的新的回复消息添加到messages列表中
# messages.append(assistant_message)


def execute_function_call(message):
    """执行函数调用"""
    # 判断功能调用的名称
    function_name = message["function_call"]["name"]
    arguments = json.loads(message["function_call"]["arguments"])
    print('arguments')
    print(arguments)

    if function_name == "get_current_weather":
        # 如果是获取当前天气，则调用_get_current_weather函数
        city = arguments["location"]
        results = _get_current_weather(city)
    elif function_name == "get_n_day_weather_forecast":
        # 如果是获取未来几天的天气预报，则调用_get_n_day_weather_forecast函数
        city = arguments["location"]
        num_days = arguments["num_days"]
        results = _get_n_day_weather_forecast(city, num_days)
    else:
        # 如果功能调用的名称不匹配，则返回错误信息
        results = f"Error: function {function_name} does not exist"

    return results  # 返回结果


# 如果助手的消息中有功能调用
if assistant_message.get("function_call"):
    # 使用 execute_function_call 函数执行功能调用，并获取结果
    print('assistant_message--')
    print(assistant_message["function_call"])

    # TODO step3
    # results = execute_function_call(assistant_message)
    # # 将功能的结果作为一个功能角色的消息添加到消息列表中
    # messages.append({"role": "function", "name": assistant_message["function_call"]["name"], "content": results})


pretty_print_conversation(messages)