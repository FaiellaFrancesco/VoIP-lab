#!/usr/bin/env python3
# Genera phone/secret.wav: 8kHz mono 16-bit, 3 toni ascendenti ripetuti (~60s)
import wave, struct, math

sr = 8000
freqs = [523, 659, 784]
sec_per_tone = 1
repeats = 20            # 20 * 3s = 60 secondi

buf = bytearray()
for _ in range(repeats):
    for f in freqs:
        for n in range(sr * sec_per_tone):
            val = int(32767 * 0.3 * math.sin(2 * math.pi * f * n / sr))
            buf += struct.pack('<h', val)

w = wave.open('phone/secret.wav', 'w')
w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
w.writeframes(bytes(buf))
w.close()
print("phone/secret.wav generato (60s)")
