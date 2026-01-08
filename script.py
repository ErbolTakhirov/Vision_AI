from kani_tts import KaniTTS

model = KaniTTS("nineninesix/kani-tts-370m")
audio, text = model("Hello from Windows!")
model.save_audio(audio, "test.wav")
