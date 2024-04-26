# gradio 单轮 流式 仅演示
import argparse
import json

import gradio as gr
import requests
import sys

def http_bot(prompt):
    url="http://localhost:8000/v1/chat/completions"
    headers = {
        "User-Agent": "vLLM Client",
        "Content-Type": "application/json"
    }
    data = {
        "model": "Yi-6",
        "messages": [
            {"role": "system", "content": "MM智能助理:\n是一个纯文字游戏《沉没之地》的系统旁白，任务是引导用户进行文字游戏的扮演与进行。旁白将会：\n1.描述周围场景，例如：酒馆，旅店，被淹旧城镇，可怕的怪物，路人，队友。\n2.给用户提供下一步行动的选项，提醒用户做出互动选择，例如：去图书馆查找资料，去酒吧打听消息，去旅店休息，去商店购物，与其他角色沟通组队，选择目的地点。\n----\n故事剧本叫做《沉没之地》，含有神秘的克苏鲁元素，时间背景是在20世纪20年代，用户扮演的是一位落魄的美国私家侦探，收到了一份匿名寄来的神秘的调查委托，要侦探前去一个名为印斯茅斯的岛屿寻找失踪密斯卡托尼克大学考古教授，教授去小岛挖掘古迹已经3个月没有消息了。印斯茅斯正逢雨季，小岛上的城市有一半地区已经被海水淹没，同时与大陆的航线也会中断2个月直到雨季过去，而作为私家侦探的用户，赶上了雨季最后一班上岛的客船，登上了这个小岛。侦探随身携带物品有：一把匕首，装有7颗子弹的小口径手枪，100美元，一卷绷带，还有那封神秘的委托信件。\n----\n剧情大纲流程为：开始游戏叙述故事背景，登岛，找旅店休息，打听消息，进行调查，接受各种任务，探索遗迹等。\n----\n 用户输入“游戏开始”后，旁白会以第三人称叙述故事背景、介绍用户扮演的主角情况、主角所处区域，并以有序列表的形式给出三个关于主角可能的下一步行动选项。在用户选择选项后，推进剧情，并在恰当的时候继续给出三个关于主角可能的下一步行动选项。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": True,
    }
    # 将数据转换为 JSON 格式的字符串
    json_data = json.dumps(data)
    response = requests.post(url, headers=headers, data=json_data, stream=True)
    print("response.status_code=", response.status_code)
    if(response.status_code != 200):
        output = response.status_code
        yield output
    output = ''
    try:
        for chunk in response.iter_lines(chunk_size=1024, decode_unicode=False, delimiter=b"\n\n"):
            if chunk:
                decoded_chunk = chunk.decode("utf-8").strip()
                # decoded_chunk = decoded_chunk.replace('data: ', '', 1)
                prefix_length = 6
                decoded_chunk = decoded_chunk[prefix_length:]
                # 假设返回的数据格式是纯文本，直接打印
                # print(decoded_chunk, end='', flush=True)
                # 检查是否到达流的末尾
                # if decoded_chunk == "[DONE]":
                #     break
                try:
                    data = json.loads(decoded_chunk)
                    choices = data.get("choices", [])
                    # if data.get("usage") is None:
                        # output += choices['text']
                    if choices[0] is not None: # if choices[0]['delta']['role'] == "assistant":
                        if choices[0]['finish_reason'] == "stop": # 检查是否到达流的末尾
                            break
                        content = choices[0].get("delta", {}).get("content")
                        if content is not None:
                            output += content
                            sys.stdout.write(content)
                            sys.stdout.flush()
                except Exception as e:
                    print("Exception:", type(e).__name__, e)
                    continue
            yield output
    except Exception as e:
        print(f"Error during streaming: {e}")
    print("Response FINISHED")

def build_demo():
    with gr.Blocks() as demo:
        gr.Markdown("# vLLm 推理游戏\n")
        inputbox = gr.Textbox(label="Input(游戏开始)",
                              placeholder="...")
        outputbox = gr.Textbox(label="Output",
                               placeholder="Generated result from the model")
        inputbox.submit(http_bot, [inputbox], [outputbox])
    return demo


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default=None)
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--model-url",
                        type=str,
                        default="http://localhost:8000/")
    args = parser.parse_args()
    print(args)
    demo = build_demo()
    demo.queue().launch(server_name=args.host,
                        server_port=args.port,
                        share=True)