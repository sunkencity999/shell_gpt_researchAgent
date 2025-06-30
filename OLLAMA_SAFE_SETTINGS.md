# Safe Ollama Settings for Limited VRAM Systems

## ⚠️ Problem
Aggressive Ollama settings can crash systems with limited VRAM (like Quadro RTX 4000 with 8GB).

## ❌ Problematic Settings (DON'T USE)
```bash
ollama runner --ctx-size 8192 --batch-size 512 --n-gpu-layers 37
```

## ✅ Safe Settings (RECOMMENDED)
```bash
# For Quadro RTX 4000 (8GB VRAM) or similar limited VRAM systems
ollama run llama3 \
  --ctx-size 4096 \
  --batch-size 256 \
  --num-gpu-layers 30
```

## 🔧 Alternative: Conservative Settings
```bash
# Even more conservative for stability
ollama run llama3 \
  --ctx-size 2048 \
  --batch-size 128 \
  --num-gpu-layers 25
```

## 📋 Parameter Explanation
- **ctx-size**: Context window size (lower = less VRAM usage)
- **batch-size**: Processing batch size (lower = less VRAM usage) 
- **num-gpu-layers**: GPU layers (lower = more CPU, less VRAM usage)

## 🎯 ResearchAgent Compatibility
The ResearchAgent uses standard Ollama HTTP API and works with any Ollama configuration. These settings only affect how Ollama server is started, not our application code.

## 🚀 Starting Ollama Safely
1. Stop existing Ollama: `pkill ollama`
2. Start with safe settings: Use commands above
3. Run ResearchAgent: Should work without crashes

## 💡 Monitoring
- Watch VRAM usage: `nvidia-smi`
- If crashes persist, reduce parameters further
- Consider using CPU-only mode for stability
