
uv pip compile pyproject.toml --extra cpu \
  -o requirements-cpu.compiled.txt \
   --emit-index-url \
   --emit-index-annotation \
   --index https://download.pytorch.org/whl/cpu \
   --index-strategy unsafe-best-match

uv pip compile pyproject.toml --extra cuda12 \
  -o requirements-cuda12.compiled.txt \
  --emit-index-url
