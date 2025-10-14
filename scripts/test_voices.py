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
import json
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
    parser.add_argument(
        "--voice-file",
        default="voices.json",
        help="List of voices to use, see voices.json for an example."
    )
    parser.add_argument(
        "--url",
        help="The URL of the server to which to send the audio",
        default="ws://127.0.0.1:8080",
    )
    parser.add_argument(
        "--input-text",
        "-i",
        type=str,
        help="Text file with input lines",
    )
    parser.add_argument(
        "--output-folder",
        "-o",
        type=str,
        default="audio",
        help="Folder to save output audio files"
    )
    parser.add_argument(
        "--num-samples-per-voice",
        "-n",
        type=int,
        default=10,
        help="Number of samples to generate per voice"
    )
    parser.add_argument("--api-key", default="public_token")
    args = parser.parse_args()

    voices = []
    with open(args.voice_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        voices = data.get("voices", [])

    lines = []
    if args.input_text:
        async for line in get_lines(args.input_text):
            lines.append(line)

    headers = {"kyutai-api-key": args.api_key}
    for voice_name in voices:
        output_folder = Path(args.output_folder, voice_name)
        output_folder.mkdir(exist_ok=True, parents=True)

        params = {"voice": voice_name, "format": "PcmMessagePack"}
        uri = f"{args.url}/api/tts_streaming?{urlencode(params)}"
        for i in range(args.num_samples_per_voice):
            outfile = output_folder / f"{i}.wav"
            async with websockets.connect(uri, additional_headers=headers) as websocket:
                async def send_loop():
                    for line in lines:
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
