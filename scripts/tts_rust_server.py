# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "msgpack",
#     "numpy",
#     "sphn",
#     "websockets",
#     "sounddevice",
#     "tqdm",
# ]
# ///
import argparse
import asyncio
import sys
from urllib.parse import urlencode
from pathlib import Path

import msgpack
import numpy as np
import sounddevice as sd
import sphn
import tqdm
import websockets

SAMPLE_RATE = 24000

TTS_TEXT = "Hello, this is a test of the moshi text to speech system, this should result in some nicely sounding generated voice."
DEFAULT_DSM_TTS_VOICE_REPO = "kyutai/tts-voices"
AUTH_TOKEN = "public_token"


async def receive_messages(websocket: websockets.ClientConnection, output_queue):
    with tqdm.tqdm(desc="Receiving audio", unit=" seconds generated") as pbar:
        accumulated_samples = 0
        last_seconds = 0

        async for message_bytes in websocket:
            msg = msgpack.unpackb(message_bytes)

            if msg["type"] == "Audio":
                pcm = np.array(msg["pcm"]).astype(np.float32)
                await output_queue.put(pcm)

                accumulated_samples += len(msg["pcm"])
                current_seconds = accumulated_samples // SAMPLE_RATE
                if current_seconds > last_seconds:
                    pbar.update(current_seconds - last_seconds)
                    last_seconds = current_seconds

    print("End of audio.")
    await output_queue.put(None)  # Signal end of audio


async def output_audio(out: str, output_queue: asyncio.Queue[np.ndarray | None]):
    if out == "-":
        should_exit = False

        def audio_callback(outdata, _a, _b, _c):
            nonlocal should_exit

            try:
                pcm_data = output_queue.get_nowait()
                if pcm_data is not None:
                    outdata[:, 0] = pcm_data
                else:
                    should_exit = True
                    outdata[:] = 0
            except asyncio.QueueEmpty:
                outdata[:] = 0

        with sd.OutputStream(
            samplerate=SAMPLE_RATE,
            blocksize=1920,
            channels=1,
            callback=audio_callback,
        ):
            while True:
                if should_exit:
                    break
                await asyncio.sleep(1)
    else:
        frames = []
        while True:
            item = await output_queue.get()
            if item is None:
                break
            frames.append(item)

        sphn.write_wav(out, np.concat(frames, -1), SAMPLE_RATE)
        print(f"Saved audio to {out}")


async def read_lines_from_stdin():
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    loop = asyncio.get_running_loop()
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    while True:
        line = await reader.readline()
        if not line:
            break
        yield line.decode().rstrip()


async def read_lines_from_file(path: str):
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def producer():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                asyncio.run_coroutine_threadsafe(queue.put(line), loop)
        asyncio.run_coroutine_threadsafe(queue.put(None), loop)

    await asyncio.to_thread(producer)
    while True:
        line = await queue.get()
        if line is None:
            break
        yield line


async def get_lines(source: str):
    if source == "-":
        async for line in read_lines_from_stdin():
            yield line
    else:
        async for line in read_lines_from_file(source):
            yield line


async def websocket_client():
    parser = argparse.ArgumentParser(description="Use the TTS streaming API")
    # parser.add_argument("inp", type=str, help="Input file, use - for stdin.")
    # parser.add_argument(
    #     "out", type=str, help="Output file to generate, use - for playing the audio"
    # )
    parser.add_argument(
        "--voice",
        default="expresso/ex04-ex03_default_002_channel2_239s.wav",
        help="The voice to use, relative to the voice repo root. "
        f"See {DEFAULT_DSM_TTS_VOICE_REPO}",
    )
    parser.add_argument(
        "--url",
        help="The URL of the server to which to send the audio",
        default="ws://127.0.0.1:8080",
    )
    parser.add_argument("--api-key", default="public_token")
    args = parser.parse_args()

    params = {"voice": args.voice, "format": "PcmMessagePack"}
    uri = f"{args.url}/api/tts_streaming?{urlencode(params)}"
    print(uri)

    voices = [
        "cml-tts/fr/10087_11650_000028-0002.wav",
"cml-tts/fr/10177_10625_000134-0003.wav",
"cml-tts/fr/10179_11051_000005-0001.wav",
"cml-tts/fr/12080_11650_000047-0001.wav",
"cml-tts/fr/12205_11650_000004-0002.wav",
"cml-tts/fr/12977_10625_000037-0001.wav",
"cml-tts/fr/1406_1028_000009-0003.wav",
"cml-tts/fr/1591_1028_000108-0004.wav",
"cml-tts/fr/1770_1028_000036-0002.wav",
"cml-tts/fr/2114_1656_000053-0001.wav",
"cml-tts/fr/2154_2576_000020-0003.wav",
"cml-tts/fr/2216_1745_000007-0001.wav",
"cml-tts/fr/2223_1745_000009-0002.wav",
"cml-tts/fr/2465_1943_000152-0002.wav",
"cml-tts/fr/296_1028_000022-0001.wav",
"cml-tts/fr/3267_1902_000075-0001.wav",
"cml-tts/fr/4193_3103_000004-0001.wav",
"cml-tts/fr/4482_3103_000063-0001.wav",
"cml-tts/fr/4724_3731_000031-0001.wav",
"cml-tts/fr/4937_3731_000004-0001.wav",
"cml-tts/fr/5207_3078_000031-0002.wav",
"cml-tts/fr/5476_3103_000072-0001.wav",
"cml-tts/fr/577_394_000070-0001.wav",
"cml-tts/fr/579_2548_000015-0001.wav",
"cml-tts/fr/5790_4893_000052-0001.wav",
"cml-tts/fr/5830_4703_000037-0001.wav",
"cml-tts/fr/6318_7016_000027-0002.wav",
"cml-tts/fr/7142_2432_000124-0003.wav",
"cml-tts/fr/7400_2928_000100-0001.wav",
"cml-tts/fr/7591_6742_000149-0002.wav",
"cml-tts/fr/7601_7727_000062-0001.wav",
"cml-tts/fr/7762_8734_000048-0002.wav",
"cml-tts/fr/8128_7016_000047-0002.wav",
"cml-tts/fr/928_486_000075-0001.wav",
"cml-tts/fr/9834_9697_000150-0003.wav",
# "ears/p001/freeform_speech_01.wav",
# "ears/p002/freeform_speech_01.wav",
# "ears/p003/emoears/p003/emo_adoration_freeform.wav",
# "ears/p003/emoears/p003/emo_amazement_freeform.wav",
# "ears/p003/emoears/p003/emo_amusement_freeform.wav",
# "ears/p003/emoears/p003/emo_anger_freeform.wav",
# "ears/p003/emoears/p003/emo_confusion_freeform.wav",
# "ears/p003/emoears/p003/emo_contentment_freeform.wav",
# "ears/p003/emoears/p003/emo_cuteness_freeform.wav",
# "ears/p003/emoears/p003/emo_desire_freeform.wav",
# "ears/p003/emoears/p003/emo_disappointment_freeform.wav",
# "ears/p003/emoears/p003/emo_disgust_freeform.wav",
# "ears/p003/emoears/p003/emo_distress_freeform.wav",
# "ears/p003/emoears/p003/emo_embarassment_freeform.wav",
# "ears/p003/emoears/p003/emo_extasy_freeform.wav",
# "ears/p003/emoears/p003/emo_fear_freeform.wav",
# "ears/p003/emoears/p003/emo_guilt_freeform.wav",
# "ears/p003/emoears/p003/emo_interest_freeform.wav",
# "ears/p003/emoears/p003/emo_neutral_freeform.wav",
# "ears/p003/emoears/p003/emo_pain_freeform.wav",
# "ears/p003/emoears/p003/emo_pride_freeform.wav",
# "ears/p003/emoears/p003/emo_realization_freeform.wav",
# "ears/p003/emoears/p003/emo_relief_freeform.wav",
# "ears/p003/emoears/p003/emo_sadness_freeform.wav",
# "ears/p003/emoears/p003/emo_serenity_freeform.wav",
# "ears/p003/freeform_speech_01.wav",
# "ears/p004/freeform_speech_01.wav",
# "ears/p005/freeform_speech_01.wav",
# "ears/p006/freeform_speech_01.wav",
# "ears/p007/freeform_speech_01.wav",
# "ears/p008/freeform_speech_01.wav",
# "ears/p009/freeform_speech_01.wav",
# "ears/p010/freeform_speech_01.wav",
# "ears/p011/freeform_speech_01.wav",
# "ears/p012/freeform_speech_01.wav",
# "ears/p013/freeform_speech_01.wav",
# "ears/p014/freeform_speech_01.wav",
# "ears/p015/freeform_speech_01.wav",
# "ears/p016/freeform_speech_01.wav",
# "ears/p017/freeform_speech_01.wav",
# "ears/p018/freeform_speech_01.wav",
# "ears/p019/freeform_speech_01.wav",
# "ears/p020/freeform_speech_01.wav",
# "ears/p021/freeform_speech_01.wav",
# "ears/p022/freeform_speech_01.wav",
# "ears/p023/freeform_speech_01.wav",
# "ears/p024/freeform_speech_01.wav",
# "ears/p025/freeform_speech_01.wav",
# "ears/p026/freeform_speech_01.wav",
# "ears/p027/freeform_speech_01.wav",
# "ears/p028/freeform_speech_01.wav",
# "ears/p029/freeform_speech_01.wav",
# "ears/p030/freeform_speech_01.wav",
# "ears/p031/emoears/p031/emo_adoration_freeform.wav",
# "ears/p031/emoears/p031/emo_amazement_freeform.wav",
# "ears/p031/emoears/p031/emo_amusement_freeform.wav",
# "ears/p031/emoears/p031/emo_anger_freeform.wav",
# "ears/p031/emoears/p031/emo_confusion_freeform.wav",
# "ears/p031/emoears/p031/emo_contentment_freeform.wav",
# "ears/p031/emoears/p031/emo_cuteness_freeform.wav",
# "ears/p031/emoears/p031/emo_desire_freeform.wav",
# "ears/p031/emoears/p031/emo_disappointment_freeform.wav",
# "ears/p031/emoears/p031/emo_disgust_freeform.wav",
# "ears/p031/emoears/p031/emo_distress_freeform.wav",
# "ears/p031/emoears/p031/emo_embarassment_freeform.wav",
# "ears/p031/emoears/p031/emo_extasy_freeform.wav",
# "ears/p031/emoears/p031/emo_fear_freeform.wav",
# "ears/p031/emoears/p031/emo_guilt_freeform.wav",
# "ears/p031/emoears/p031/emo_interest_freeform.wav",
# "ears/p031/emoears/p031/emo_neutral_freeform.wav",
# "ears/p031/emoears/p031/emo_pain_freeform.wav",
# "ears/p031/emoears/p031/emo_pride_freeform.wav",
# "ears/p031/emoears/p031/emo_realization_freeform.wav",
# "ears/p031/emoears/p031/emo_relief_freeform.wav",
# "ears/p031/emoears/p031/emo_sadness_freeform.wav",
# "ears/p031/emoears/p031/emo_serenity_freeform.wav",
# "ears/p031/freeform_speech_01.wav",
# "ears/p032/freeform_speech_01.wav",
# "ears/p033/freeform_speech_01.wav",
# "ears/p034/freeform_speech_01.wav",
# "ears/p035/freeform_speech_01.wav",
# "ears/p036/freeform_speech_01.wav",
# "ears/p037/freeform_speech_01.wav",
# "ears/p038/freeform_speech_01.wav",
# "ears/p039/freeform_speech_01.wav",
# "ears/p040/freeform_speech_01.wav",
# "ears/p041/freeform_speech_01.wav",
# "ears/p042/freeform_speech_01.wav",
# "ears/p043/freeform_speech_01.wav",
# "ears/p044/freeform_speech_01.wav",
# "ears/p045/freeform_speech_01.wav",
# "ears/p046/freeform_speech_01.wav",
# "ears/p047/freeform_speech_01.wav",
# "ears/p048/freeform_speech_01.wav",
# "ears/p049/freeform_speech_01.wav",
# "ears/p050/freeform_speech_01.wav",
# "ears/p051/freeform_speech_01.wav",
# "ears/p052/freeform_speech_01.wav",
# "ears/p053/freeform_speech_01.wav",
# "ears/p054/freeform_speech_01.wav",
# "ears/p055/freeform_speech_01.wav",
# "ears/p056/freeform_speech_01.wav",
# "ears/p057/freeform_speech_01.wav",
# "ears/p058/freeform_speech_01.wav",
# "ears/p059/freeform_speech_01.wav",
# "ears/p060/freeform_speech_01.wav",
# "ears/p061/freeform_speech_01.wav",
# "ears/p062/freeform_speech_01.wav",
# "ears/p063/freeform_speech_01.wav",
# "ears/p064/freeform_speech_01.wav",
# "ears/p065/freeform_speech_01.wav",
# "ears/p066/freeform_speech_01.wav",
# "ears/p067/freeform_speech_01.wav",
# "ears/p068/freeform_speech_01.wav",
# "ears/p069/freeform_speech_01.wav",
# "ears/p070/freeform_speech_01.wav",
# "ears/p071/freeform_speech_01.wav",
# "ears/p072/freeform_speech_01.wav",
# "ears/p073/freeform_speech_01.wav",
# "ears/p074/freeform_speech_01.wav",
# "ears/p075/freeform_speech_01.wav",
# "ears/p076/freeform_speech_01.wav",
# "ears/p077/freeform_speech_01.wav",
# "ears/p078/freeform_speech_01.wav",
# "ears/p079/freeform_speech_01.wav",
# "ears/p080/freeform_speech_01.wav",
# "ears/p081/freeform_speech_01.wav",
# "ears/p082/freeform_speech_01.wav",
# "ears/p083/freeform_speech_01.wav",
# "ears/p084/freeform_speech_01.wav",
# "ears/p085/freeform_speech_01.wav",
# "ears/p086/freeform_speech_01.wav",
# "ears/p087/freeform_speech_01.wav",
# "ears/p088/freeform_speech_01.wav",
# "ears/p089/freeform_speech_01.wav",
# "ears/p090/freeform_speech_01.wav",
# "ears/p091/freeform_speech_01.wav",
# "ears/p092/freeform_speech_01.wav",
# "ears/p093/freeform_speech_01.wav",
# "ears/p094/freeform_speech_01.wav",
# "ears/p095/freeform_speech_01.wav",
# "ears/p096/freeform_speech_01.wav",
# "ears/p097/freeform_speech_01.wav",
# "ears/p098/freeform_speech_01.wav",
# "ears/p099/freeform_speech_01.wav",
# "ears/p100/freeform_speech_01.wav",
# "ears/p101/freeform_speech_01.wav",
# "ears/p102/freeform_speech_01.wav",
# "ears/p103/freeform_speech_01.wav",
# "ears/p104/freeform_speech_01.wav",
# "ears/p105/freeform_speech_01.wav",
# "ears/p106/freeform_speech_01.wav",
# "ears/p107/freeform_speech_01.wav",
"expresso/ex01-ex02_default_001_channel1_168s.wav",
"expresso/ex01-ex02_default_001_channel2_198s.wav",
"expresso/ex01-ex02_enunciated_001_channel1_432s.wav",
"expresso/ex01-ex02_enunciated_001_channel2_354s.wav",
"expresso/ex01-ex02_fast_001_channel1_104s.wav",
"expresso/ex01-ex02_fast_001_channel2_73s.wav",
"expresso/ex01-ex02_projected_001_channel1_46s.wav",
"expresso/ex01-ex02_projected_002_channel2_248s.wav",
"expresso/ex01-ex02_whisper_001_channel1_579s.wav",
"expresso/ex01-ex02_whisper_001_channel2_717s.wav",
"expresso/ex03-ex01_angry_001_channel1_201s.wav",
"expresso/ex03-ex01_angry_001_channel2_181s.wav",
"expresso/ex03-ex01_awe_001_channel1_1323s.wav",
"expresso/ex03-ex01_awe_001_channel2_1290s.wav",
"expresso/ex03-ex01_calm_001_channel1_1143s.wav",
"expresso/ex03-ex01_calm_001_channel2_1081s.wav",
"expresso/ex03-ex01_confused_001_channel1_909s.wav",
"expresso/ex03-ex01_confused_001_channel2_816s.wav",
"expresso/ex03-ex01_desire_004_channel1_545s.wav",
"expresso/ex03-ex01_desire_004_channel2_580s.wav",
"expresso/ex03-ex01_disgusted_004_channel1_170s.wav",
"expresso/ex03-ex01_enunciated_001_channel1_388s.wav",
"expresso/ex03-ex01_enunciated_001_channel2_576s.wav",
"expresso/ex03-ex01_happy_001_channel1_334s.wav",
"expresso/ex03-ex01_happy_001_channel2_257s.wav",
"expresso/ex03-ex01_laughing_001_channel1_188s.wav",
"expresso/ex03-ex01_laughing_002_channel2_232s.wav",
"expresso/ex03-ex01_nonverbal_001_channel2_37s.wav",
"expresso/ex03-ex01_nonverbal_006_channel1_62s.wav",
"expresso/ex03-ex01_sarcastic_001_channel1_435s.wav",
"expresso/ex03-ex01_sarcastic_001_channel2_491s.wav",
"expresso/ex03-ex01_sleepy_001_channel1_619s.wav",
"expresso/ex03-ex01_sleepy_001_channel2_662s.wav",
"expresso/ex03-ex02_animal-animaldir_002_channel2_89s.wav",
"expresso/ex03-ex02_animal-animaldir_003_channel1_32s.wav",
"expresso/ex03-ex02_animaldir-animal_008_channel1_147s.wav",
"expresso/ex03-ex02_animaldir-animal_008_channel2_136s.wav",
"expresso/ex03-ex02_child-childdir_001_channel1_291s.wav",
"expresso/ex03-ex02_child-childdir_001_channel2_69s.wav",
"expresso/ex03-ex02_childdir-child_004_channel1_308s.wav",
"expresso/ex03-ex02_childdir-child_004_channel2_187s.wav",
"expresso/ex03-ex02_laughing_001_channel1_248s.wav",
"expresso/ex03-ex02_laughing_001_channel2_234s.wav",
"expresso/ex03-ex02_narration_001_channel1_674s.wav",
"expresso/ex03-ex02_narration_002_channel2_1136s.wav",
"expresso/ex03-ex02_sad-sympathetic_001_channel1_454s.wav",
"expresso/ex03-ex02_sad-sympathetic_001_channel2_400s.wav",
"expresso/ex03-ex02_sympathetic-sad_008_channel1_215s.wav",
"expresso/ex03-ex02_sympathetic-sad_008_channel2_268s.wav",
"expresso/ex04-ex01_animal-animaldir_006_channel1_196s.wav",
"expresso/ex04-ex01_animal-animaldir_006_channel2_49s.wav",
"expresso/ex04-ex01_animaldir-animal_001_channel1_118s.wav",
"expresso/ex04-ex01_animaldir-animal_004_channel2_88s.wav",
"expresso/ex04-ex01_child-childdir_003_channel2_283s.wav",
"expresso/ex04-ex01_child-childdir_004_channel1_118s.wav",
"expresso/ex04-ex01_childdir-child_001_channel1_228s.wav",
"expresso/ex04-ex01_childdir-child_001_channel2_420s.wav",
"expresso/ex04-ex01_disgusted_001_channel1_130s.wav",
"expresso/ex04-ex01_disgusted_001_channel2_325s.wav",
"expresso/ex04-ex01_laughing_001_channel1_306s.wav",
"expresso/ex04-ex01_laughing_001_channel2_293s.wav",
"expresso/ex04-ex01_narration_001_channel1_605s.wav",
"expresso/ex04-ex01_narration_001_channel2_686s.wav",
"expresso/ex04-ex01_sad-sympathetic_001_channel1_267s.wav",
"expresso/ex04-ex01_sad-sympathetic_001_channel2_346s.wav",
"expresso/ex04-ex01_sympathetic-sad_008_channel1_415s.wav",
"expresso/ex04-ex01_sympathetic-sad_008_channel2_453s.wav",
"expresso/ex04-ex02_angry_001_channel1_119s.wav",
"expresso/ex04-ex02_angry_001_channel2_150s.wav",
"expresso/ex04-ex02_awe_001_channel1_982s.wav",
"expresso/ex04-ex02_awe_001_channel2_1013s.wav",
"expresso/ex04-ex02_bored_001_channel1_254s.wav",
"expresso/ex04-ex02_bored_001_channel2_232s.wav",
"expresso/ex04-ex02_calm_001_channel2_336s.wav",
"expresso/ex04-ex02_calm_002_channel1_480s.wav",
"expresso/ex04-ex02_confused_001_channel1_499s.wav",
"expresso/ex04-ex02_confused_001_channel2_488s.wav",
"expresso/ex04-ex02_desire_001_channel1_657s.wav",
"expresso/ex04-ex02_desire_001_channel2_694s.wav",
"expresso/ex04-ex02_disgusted_001_channel2_98s.wav",
"expresso/ex04-ex02_disgusted_004_channel1_169s.wav",
"expresso/ex04-ex02_enunciated_001_channel1_496s.wav",
"expresso/ex04-ex02_enunciated_001_channel2_898s.wav",
"expresso/ex04-ex02_fearful_001_channel1_316s.wav",
"expresso/ex04-ex02_fearful_001_channel2_266s.wav",
"expresso/ex04-ex02_happy_001_channel1_118s.wav",
"expresso/ex04-ex02_happy_001_channel2_140s.wav",
"expresso/ex04-ex02_laughing_001_channel1_147s.wav",
"expresso/ex04-ex02_laughing_001_channel2_159s.wav",
"expresso/ex04-ex02_nonverbal_004_channel1_18s.wav",
"expresso/ex04-ex02_nonverbal_004_channel2_71s.wav",
"expresso/ex04-ex02_sarcastic_001_channel1_519s.wav",
"expresso/ex04-ex02_sarcastic_001_channel2_466s.wav",
"expresso/ex04-ex03_default_001_channel1_3s.wav",
"expresso/ex04-ex03_default_002_channel2_239s.wav",
"expresso/ex04-ex03_enunciated_001_channel1_86s.wav",
"expresso/ex04-ex03_enunciated_001_channel2_342s.wav",
"expresso/ex04-ex03_fast_001_channel1_208s.wav",
"expresso/ex04-ex03_fast_001_channel2_25s.wav",
"expresso/ex04-ex03_projected_001_channel1_192s.wav",
"expresso/ex04-ex03_projected_001_channel2_179s.wav",
"expresso/ex04-ex03_whisper_001_channel1_198s.wav",
"expresso/ex04-ex03_whisper_002_channel2_266s.wav",
"unmute-prod-website/degaulle-2.wav",
"unmute-prod-website/developpeuse-3.wav",
"unmute-prod-website/ex04_narration_longform_00001.wav",
"unmute-prod-website/fabieng-enhanced-v2.wav",
"unmute-prod-website/p329_022.wav",
# "vctk/p225_023.wav",
# "vctk/p226_023.wav",
# "vctk/p227_023.wav",
# "vctk/p228_023.wav",
# "vctk/p229_023.wav",
# "vctk/p230_023.wav",
# "vctk/p231_023.wav",
# "vctk/p232_023.wav",
# "vctk/p233_023.wav",
# "vctk/p234_023.wav",
# "vctk/p236_023.wav",
# "vctk/p237_023.wav",
# "vctk/p238_023.wav",
# "vctk/p239_023.wav",
# "vctk/p240_023.wav",
# "vctk/p241_023.wav",
# "vctk/p243_023.wav",
# "vctk/p244_023.wav",
# "vctk/p245_023.wav",
# "vctk/p246_023.wav",
# "vctk/p247_023.wav",
# "vctk/p248_023.wav",
# "vctk/p249_023.wav",
# "vctk/p250_023.wav",
# "vctk/p251_023.wav",
# "vctk/p252_023.wav",
# "vctk/p253_023.wav",
# "vctk/p254_023.wav",
# "vctk/p255_023.wav",
# "vctk/p256_023.wav",
# "vctk/p257_023.wav",
# "vctk/p258_023.wav",
# "vctk/p259_023.wav",
# "vctk/p260_023.wav",
# "vctk/p261_023.wav",
# "vctk/p262_023.wav",
# "vctk/p263_023.wav",
# "vctk/p264_023.wav",
# "vctk/p265_023.wav",
# "vctk/p266_023.wav",
# "vctk/p267_023.wav",
# "vctk/p269_023.wav",
# "vctk/p270_023.wav",
# "vctk/p271_023.wav",
# "vctk/p272_023.wav",
# "vctk/p273_023.wav",
# "vctk/p274_023.wav",
# "vctk/p275_023.wav",
# "vctk/p276_023.wav",
# "vctk/p277_023.wav",
# "vctk/p278_023.wav",
# "vctk/p279_023.wav",
# "vctk/p280_023.wav",
# "vctk/p281_023.wav",
# "vctk/p282_023.wav",
# "vctk/p283_023.wav",
# "vctk/p284_023.wav",
# "vctk/p285_023.wav",
# "vctk/p286_023.wav",
# "vctk/p287_023.wav",
# "vctk/p288_023.wav",
# "vctk/p292_023.wav",
# "vctk/p293_023.wav",
# "vctk/p294_023.wav",
# "vctk/p297_023.wav",
# "vctk/p298_023.wav",
# "vctk/p299_023.wav",
# "vctk/p300_023.wav",
# "vctk/p301_023.wav",
# "vctk/p302_023.wav",
# "vctk/p303_023.wav",
# "vctk/p304_023.wav",
# "vctk/p305_023.wav",
# "vctk/p306_023.wav",
# "vctk/p307_023.wav",
# "vctk/p308_023.wav",
# "vctk/p310_023.wav",
# "vctk/p311_023.wav",
# "vctk/p312_023.wav",
# "vctk/p313_023.wav",
# "vctk/p314_023.wav",
# "vctk/p315_023.wav",
# "vctk/p316_023.wav",
# "vctk/p317_023.wav",
# "vctk/p318_023.wav",
# "vctk/p323_023.wav",
# "vctk/p326_023.wav",
# "vctk/p329_023.wav",
# "vctk/p330_023.wav",
# "vctk/p333_023.wav",
# "vctk/p334_023.wav",
# "vctk/p335_023.wav",
# "vctk/p336_023.wav",
# "vctk/p339_023.wav",
# "vctk/p341_023.wav",
# "vctk/p343_023.wav",
# "vctk/p345_023.wav",
# "vctk/p347_023.wav",
# "vctk/p351_023.wav",
# "vctk/p360_023.wav",
# "vctk/p361_023.wav",
# "vctk/p363_023.wav",
# "vctk/p364_023.wav",
# "vctk/p374_023.wav",
# "vctk/p376_023.wav",
# "vctk/s5_023.wav",
# "voice-donations/0a67.wav",
# "voice-donations/2181.wav",
# "voice-donations/245e.wav",
# "voice-donations/29da.wav",
# "voice-donations/468c.wav",
# "voice-donations/8dc9.wav",
# "voice-donations/AbD.wav",
# "voice-donations/aepeak.wav",
# "voice-donations/Ajith.wav",
# "voice-donations/AmitNag.wav",
# "voice-donations/Aryobe.wav",
# "voice-donations/ASEN.wav",
# "voice-donations/bathri.wav",
# "voice-donations/bc98.wav",
# "voice-donations/bevi.wav",
# "voice-donations/Bobby_McFern.wav",
# "voice-donations/boom.wav",
# "voice-donations/BrokenHypocrite.wav",
# "voice-donations/Butter.wav",
# "voice-donations/d4a9.wav",
# "voice-donations/dce6.wav",
# "voice-donations/Deepak.wav",
# "voice-donations/Dhruv_Rao.wav",
# "voice-donations/dwp.wav",
# "voice-donations/Enrique_(Spanish).wav",
# "voice-donations/Enrique.wav",
# "voice-donations/f9cf.wav",
# "voice-donations/Ferdinand.wav",
# "voice-donations/Glenn.wav",
# "voice-donations/gmaskell92.wav",
# "voice-donations/Goku.wav",
# "voice-donations/hielos_1.wav",
# "voice-donations/hielos_2.wav",
# "voice-donations/Jaw.wav",
# "voice-donations/Jeff_Andrew.wav",
# "voice-donations/Jeffrey.wav",
# "voice-donations/Jeremy_Q.wav",
# "voice-donations/Jimmy.wav",
# "voice-donations/Karti.wav",
# "voice-donations/kbrn1.wav",
# "voice-donations/Koorosh.wav",
# "voice-donations/L_Roy.wav",
# "voice-donations/Lake.wav",
# "voice-donations/LC.wav",
# "voice-donations/Nick.wav",
# "voice-donations/Parthiban.wav",
# "voice-donations/Prakash369.wav",
# "voice-donations/Qasim_Wali_Khan.wav",
# "voice-donations/ra_XOr.wav",
# "voice-donations/Ranjith.wav",
# "voice-donations/Roscoe.wav",
# "voice-donations/Selfie.wav",
# "voice-donations/Sheddy.wav",
# "voice-donations/Siddh_Indian.wav",
# "voice-donations/solace.wav",
# "voice-donations/temp-007.wav",
# "voice-donations/The_other_brother.wav",
# "voice-donations/thepolishdane.wav",
# "voice-donations/vinayak.wav",
# "voice-donations/W_A_H.wav",
# "voice-donations/Youfied.wav",
# "voice-donations/Yuush.wav"
    ]


    # if args.inp == "-":
    #     if sys.stdin.isatty():  # Interactive
    #         print("Enter text to synthesize (Ctrl+D to end input):")
    headers = {"kyutai-api-key": args.api_key}
    for voice_name in voices:
        output_folder = Path("audio",voice_name)
        output_folder.mkdir(exist_ok=True, parents=True)

        params = {"voice": voice_name, "format": "PcmMessagePack"}
        uri = f"{args.url}/api/tts_streaming?{urlencode(params)}"
        for i in range(10):
            outfile = output_folder / f"{i}.wav"
            print(f"Creating: {outfile}")
            async with websockets.connect(uri, additional_headers=headers) as websocket:
                print("connected")

                async def send_loop():
                    print("go send")
                    line = "Hi I am Carl, your helpful AI assistant. How can I help you today ? "
                    for word in line.split():
                        await websocket.send(msgpack.packb({"type": "Text", "text": word}))
                    await websocket.send(msgpack.packb({"type": "Eos"}))

                output_queue = asyncio.Queue()
                receive_task = asyncio.create_task(receive_messages(websocket, output_queue))
                output_audio_task = asyncio.create_task(output_audio(outfile, output_queue))
                send_task = asyncio.create_task(send_loop())
                await asyncio.gather(receive_task, output_audio_task, send_task)


if __name__ == "__main__":
    asyncio.run(websocket_client())
