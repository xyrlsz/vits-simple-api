import time
import webbrowser
import gradio as gr
import requests
import os
import threading

from time import sleep
from config import HttpService


HOST = "127.0.0.1"
API_PORT = HttpService.port
WEBUI_PORT = 8065


def my_function():
    return "Hello, World!"


def download_file(url, save_path, filename):
    response = requests.get(url)
    response.raise_for_status()
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    with open(os.path.join(save_path, filename), "wb") as file:
        file.write(response.content)


_save_path = "cache/audio/"


def get_response(url: str):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # 解析 JSON 数据
            data = response.json()
            # print("获取到的数据：", data)
            return data
        else:
            print("请求失败，状态码：", response.status_code)
    except requests.exceptions.RequestException as e:
        print("请求发生异常：", e)
    return None


class Speakers:
    def __init__(self, url: str):
        self.data = get_response(url)

    def get_speakers(self, data: list):
        res = []
        for i in data:
            lab = str(i["id"]) + "|" + str(i["name"]) + "|" + str(i["lang"])
            res.append(lab)
        return res

    def get_speakers_list(self, type: str):
        """
        type:BERT-VITS2,HUBERT-VITS,VITS,W2V2-VITS
        """
        list = self.data[type]
        data = self.get_speakers(list)
        if data:  # 这里使用 if data 而不是 if data.size
            return data
        return []


# def check_is_done(
#     id: int,
#     format: str,
#     lang: str,
#     length: float,
#     noise: float,
#     noisew: float,
#     segment_size: int,
#     streaming: bool,
#     text: str,
#     progress=gr.Progress(),
# ):
#     progress(0, desc="开始生成。。。")
#     text = text.replace("\n", "")
#     text = text.replace(" ", "")
#     url = f"http://{HOST}:{PORT}/voice/vits?id={id}&format={format}&lang={lang}&length={length}&noise={noise}&noisew={noisew}&segment_size={segment_size}&streaming={streaming}&text={text}"
#     print(url)
#     for i in progress.tqdm(range(100)):
#         if requests.get(url).status_code == 200:
#             break
#         else:
#             time.sleep(1)
#     progress(100, desc="生成完成。。。")
#     return "完成"


def start_api_server():
    os.system("python app.py")


thread1 = threading.Thread(target=start_api_server)
thread1.start()


with gr.Blocks() as demo:
    speakers_url = f"http://{HOST}:{API_PORT}/voice/speakers"
    while get_response(speakers_url) is None:
        print("等待后端服务启动...")
        sleep(2)
    print("后端服务已启动")
    speakers_data = Speakers(speakers_url)
    gr.Markdown("vits-simple-api Gradio SDK版")
    with gr.Tab("VITS"):  # 标签页1
        with gr.Column():
            input_text = gr.Textbox(
                placeholder="输入文本", label="text", lines=3, value="你好"
            )
            model_list = speakers_data.get_speakers_list("VITS")
            input_id = gr.Dropdown(
                label="id", choices=model_list, type="index", value=0
            )
            # gr.Checkbox(label="checkbox")
            with gr.Row():
                input_format = gr.Dropdown(
                    label="format",
                    choices=["wav", "mp3", "ogg", "silk", "flac"],
                    info="选择音频输出格式",
                    value="wav",
                )
                input_lang = gr.Textbox(
                    label="lang",
                    info="自动识别语言auto: 可识别的语言根据不同speaker而不同，方言无法自动识别。方言模型需要手动指定语言，比如粤语Cantonese要指定参数lang=gd",
                    value="auto",
                )
                input_length = gr.Slider(
                    label="length",
                    minimum=0,
                    step=0.001,
                    info="调节语音长度，相当于调节语速，该数值越大语速越慢",
                    value=1,
                )
            with gr.Row():
                input_noise = gr.Slider(
                    label="noise", info="样品噪声，控制合成的随机性", step=0.001, value=0.33
                )
                input_noisew = gr.Slider(
                    label="noisew", info="随机时长预测器噪声，控制音素发音长度", step=0.001, value=0.4
                )
                input_segment_size = gr.Slider(
                    label="segment_size",
                    step=1,
                    maximum=1000,
                    info="按标点符号分段，加起来大于segment size时为一段文本。segment size<=0表示不分段。",
                    value=50,
                )
            input_streaming = gr.Checkbox(value=False, label="流式响应")

            def get_audio_url_vits(
                id: int,
                format: str,
                lang: str,
                length: float,
                noise: float,
                noisew: float,
                segment_size: int,
                streaming: bool,
                text: str,
            ):
                text = text.replace("\n", "")
                text = text.replace(" ", "")
                url = f"http://{HOST}:{API_PORT}/voice/vits?id={id}&format={format}&lang={lang}&length={length}&noise={noise}&noisew={noisew}&segment_size={segment_size}&streaming={streaming}&text={text}"
                print(url)
                file_name = f"{id}.{format}"
                download_file(url, _save_path, file_name)
                return _save_path + file_name

            def check_is_done(
                id: int,
                format: str,
                lang: str,
                length: float,
                noise: float,
                noisew: float,
                segment_size: int,
                streaming: bool,
                text: str,
                progress=gr.Progress(),
            ):
                text = text.replace("\n", "")
                text = text.replace(" ", "")
                url = f"http://{HOST}:{API_PORT}/voice/vits?id={id}&format={format}&lang={lang}&length={length}&noise={noise}&noisew={noisew}&segment_size={segment_size}&streaming={streaming}&text={text}"
                print(url)
                for i in progress.tqdm(range(len(text)), desc="正在生成。。。"):
                    time.sleep(0.1)
                code = requests.get(url).status_code
                print(code)
                if code == 200:
                    progress.track_tqdm = True

                return "完成"

            with gr.Row():
                btn1 = gr.Button("生成", variant="primary")
                output_text = gr.Textbox()

            btn2 = gr.Button("获取音频", variant="primary")
            audio_block = gr.Audio(label="output")
            btn1.click(
                fn=check_is_done,
                inputs=[
                    input_id,
                    input_format,
                    input_lang,
                    input_length,
                    input_noise,
                    input_noisew,
                    input_segment_size,
                    input_streaming,
                    input_text,
                ],
                outputs=output_text,
            )
            btn2.click(
                fn=get_audio_url_vits,
                inputs=[
                    input_id,
                    input_format,
                    input_lang,
                    input_length,
                    input_noise,
                    input_noisew,
                    input_segment_size,
                    input_streaming,
                    input_text,
                ],
                outputs=audio_block,
            )
    with gr.Tab("W2V2-VITS"):  # 标签页2
        with gr.Column():
            input_text = gr.Textbox(
                placeholder="输入文本", label="text", lines=3, value="你好"
            )
            model_list = speakers_data.get_speakers_list("W2V2-VITS")
            input_id = gr.Dropdown(
                label="id", choices=model_list, type="index", value=0
            )
            input_emotion = gr.Slider(
                label="emotion", minimum=-1, maximum=0, step=1, value=0
            )
            # gr.Checkbox(label="checkbox")
            with gr.Row():
                input_format = gr.Dropdown(
                    label="format",
                    choices=["wav", "mp3", "ogg", "silk", "flac"],
                    info="选择音频输出格式",
                    value="wav",
                )
                input_lang = gr.Textbox(
                    label="lang",
                    info="自动识别语言auto: 可识别的语言根据不同speaker而不同，方言无法自动识别。方言模型需要手动指定语言，比如粤语Cantonese要指定参数lang=gd",
                    value="auto",
                )
                input_length = gr.Slider(
                    label="length",
                    minimum=0,
                    step=0.001,
                    info="调节语音长度，相当于调节语速，该数值越大语速越慢",
                    value=1,
                )
            with gr.Row():
                input_noise = gr.Slider(
                    label="noise", info="样品噪声，控制合成的随机性", step=0.001, value=0.33
                )
                input_noisew = gr.Slider(
                    label="noisew", info="随机时长预测器噪声，控制音素发音长度", step=0.001, value=0.4
                )
                input_segment_size = gr.Slider(
                    label="segment_size",
                    step=1,
                    maximum=1000,
                    info="按标点符号分段，加起来大于segment size时为一段文本。segment size<=0表示不分段。",
                    value=50,
                )
            input_streaming = gr.Checkbox(value=False, label="流式响应")

            def get_audio_url_vits(
                id: int,
                emotion: int,
                format: str,
                lang: str,
                length: float,
                noise: float,
                noisew: float,
                segment_size: int,
                streaming: bool,
                text: str,
            ):
                text = text.replace("\n", "")
                text = text.replace(" ", "")
                url = f"http://{HOST}:{API_PORT}/voice/w2v2-vits?id={id}&emotion={emotion}&format={format}&lang={lang}&length={length}&noise={noise}&noisew={noisew}&segment_size={segment_size}&streaming={streaming}&text={text}"
                print(url)
                file_name = f"{id}.{format}"
                download_file(url, _save_path, file_name)
                return _save_path + file_name

            def check_is_done(
                id: int,
                emotion: int,
                format: str,
                lang: str,
                length: float,
                noise: float,
                noisew: float,
                segment_size: int,
                streaming: bool,
                text: str,
                progress=gr.Progress(),
            ):
                text = text.replace("\n", "")
                text = text.replace(" ", "")
                url = f"http://{HOST}:{API_PORT}/voice/w2v2-vits?id={id}&emotion={emotion}&format={format}&lang={lang}&length={length}&noise={noise}&noisew={noisew}&segment_size={segment_size}&streaming={streaming}&text={text}"
                print(url)
                for i in progress.tqdm(range(len(text)), desc="正在生成。。。"):
                    time.sleep(0.1)
                code = requests.get(url).status_code
                print(code)
                if code == 200:
                    progress.track_tqdm = True

                return "完成"

            with gr.Row():
                btn1 = gr.Button("生成", variant="primary")
                output_text = gr.Textbox()

            btn2 = gr.Button("获取音频", variant="primary")
            audio_block = gr.Audio(label="output")
            btn1.click(
                fn=check_is_done,
                inputs=[
                    input_id,
                    input_emotion,
                    input_format,
                    input_lang,
                    input_length,
                    input_noise,
                    input_noisew,
                    input_segment_size,
                    input_streaming,
                    input_text,
                ],
                outputs=output_text,
            )
            btn2.click(
                fn=get_audio_url_vits,
                inputs=[
                    input_id,
                    input_emotion,
                    input_format,
                    input_lang,
                    input_length,
                    input_noise,
                    input_noisew,
                    input_segment_size,
                    input_streaming,
                    input_text,
                ],
                outputs=audio_block,
            )
    with gr.Tab("BERT-VITS2"):  # 标签页3
        with gr.Column():
            input_text = gr.Textbox(
                placeholder="输入文本", label="text", lines=3, value="你好"
            )
            model_list = speakers_data.get_speakers_list("BERT-VITS2")
            input_id = gr.Dropdown(
                label="id", choices=model_list, type="index", value=0
            )

            # gr.Checkbox(label="checkbox")
            with gr.Row():
                input_format = gr.Dropdown(
                    label="format",
                    choices=["wav", "mp3", "ogg", "silk", "flac"],
                    info="选择音频输出格式",
                    value="wav",
                )
                input_lang = gr.Textbox(
                    label="lang",
                    info="自动识别语言auto: 可识别的语言根据不同speaker而不同，方言无法自动识别。方言模型需要手动指定语言，比如粤语Cantonese要指定参数lang=gd",
                    value="auto",
                )
                input_length = gr.Slider(
                    label="length",
                    minimum=0,
                    step=0.001,
                    info="调节语音长度，相当于调节语速，该数值越大语速越慢",
                    value=1,
                )
            with gr.Row():
                input_noise = gr.Slider(
                    label="noise", info="样品噪声，控制合成的随机性", step=0.001, value=0.33
                )
                input_noisew = gr.Slider(
                    label="noisew", info="随机时长预测器噪声，控制音素发音长度", step=0.001, value=0.4
                )
                input_segment_size = gr.Slider(
                    label="segment_size",
                    step=1,
                    maximum=1000,
                    info="按标点符号分段，加起来大于segment size时为一段文本。segment size<=0表示不分段。",
                    value=50,
                )
            with gr.Row():
                input_sdp_radio = gr.Slider(
                    label="sdp_radio",
                    info="SDP/DP混合比: SDP在合成时的占比，理论上此比率越高，合成的语音语调方差越大。",
                    step=0.01,
                    value=0.2,
                    maximum=1,
                )
                input_emotion = gr.Slider(
                    label="emotion",
                    info="Bert-VITS2 v2.1: 情感控制范围为0-9。",
                    step=1,
                    value=0.4,
                    maximum=9,
                )
            with gr.Column():
                gr.Markdown(
                    "Bert-VITS2 v2.1: 上传音频文件作为情感参考,emotion和reference_audio二选一，v2.2：text_promptf和reference_audio二选一"
                )
                input_reference_audio = gr.Audio(
                    label="reference_audio",
                    type="filepath",
                    container=True,
                )
            with gr.Row():
                input_text_prompt = gr.Textbox(
                    label="text_prompt",
                    info="Bert-VITS2 v2.2: 融合文本语义",
                    value="Happy",
                )
                input_style_text = gr.Textbox(
                    label="style_text",
                    info="Bert-VITS2 v2.3: 融合文本语义",
                    value="Happy",
                )
                input_style_weight = gr.Slider(
                    label="style_weight",
                    step=0.1,
                    maximum=1,
                    info="Bert-VITS2 v2.3: style text文本语义权重",
                    value=0.7,
                )

            input_streaming = gr.Checkbox(value=False, label="流式响应")

            def get_audio_url_vits(
                id: int,
                format: str,
                lang: str,
                length: float,
                noise: float,
                noisew: float,
                segment_size: int,
                sdp_radio: float,
                emotion: int,
                reference_audio: str,
                text_prompt: str,
                style_text: str,
                style_weight: float,
                streaming: bool,
                text: str,
            ):
                text = text.replace("\n", "")
                text = text.replace(" ", "")
                url = f"http://{HOST}:{API_PORT}/voice/bert-vits2?id={id}&format={format}&lang={lang}&length={length}&noise={noise}&noisew={noisew}&segment_size={segment_size}&sdp_radio={sdp_radio}&emotion={emotion}&reference_audio={reference_audio}&text_prompt={text_prompt}&style_text={style_text}&style_weight={style_weight}&streaming={streaming}&text={text}"
                print(url)
                file_name = f"{id}.{format}"
                download_file(url, _save_path, file_name)
                return _save_path + file_name

            def check_is_done(
                id: int,
                format: str,
                lang: str,
                length: float,
                noise: float,
                noisew: float,
                segment_size: int,
                sdp_radio: float,
                emotion: int,
                reference_audio: str,
                text_prompt: str,
                style_text: str,
                style_weight: float,
                streaming: bool,
                text: str,
                progress=gr.Progress(),
            ):
                text = text.replace("\n", "")
                text = text.replace(" ", "")
                url = f"http://{HOST}:{API_PORT}/voice/bert-vits2?id={id}&format={format}&lang={lang}&length={length}&noise={noise}&noisew={noisew}&segment_size={segment_size}&sdp_radio={sdp_radio}&emotion={emotion}&reference_audio={reference_audio}&text_prompt={text_prompt}&style_text={style_text}&style_weight={style_weight}&streaming={streaming}&text={text}"
                print(url)
                for i in progress.tqdm(range(len(text)), desc="正在生成。。。"):
                    time.sleep(0.1)
                code = requests.get(url).status_code
                print(code)
                if code == 200:
                    progress.track_tqdm = True

                return "完成"

            with gr.Row():
                btn1 = gr.Button("生成", variant="primary")
                output_text = gr.Textbox()

            btn2 = gr.Button("获取音频", variant="primary")
            audio_block = gr.Audio(label="output")
            btn1.click(
                fn=check_is_done,
                inputs=[
                    input_id,
                    input_format,
                    input_lang,
                    input_length,
                    input_noise,
                    input_noisew,
                    input_segment_size,
                    input_sdp_radio,
                    input_emotion,
                    input_reference_audio,
                    input_text_prompt,
                    input_style_text,
                    input_style_weight,
                    input_streaming,
                    input_text,
                ],
                outputs=output_text,
            )
            btn2.click(
                fn=get_audio_url_vits,
                inputs=[
                    input_id,
                    input_format,
                    input_lang,
                    input_length,
                    input_noise,
                    input_noisew,
                    input_segment_size,
                    input_sdp_radio,
                    input_emotion,
                    input_reference_audio,
                    input_text_prompt,
                    input_style_text,
                    input_style_weight,
                    input_streaming,
                    input_text,
                ],
                outputs=audio_block,
            )

if __name__ == "__main__":
    webbrowser.open(f"http://127.0.0.1:{WEBUI_PORT}")
    demo.launch(server_port=WEBUI_PORT, share=True)
