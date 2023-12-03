protoc \
  --proto_path=/usr/local/include \
  --proto_path=proto \
  --python_out=src/ \
  $(find proto -path -prune -o -name '*.proto' -print0 | xargs -0)