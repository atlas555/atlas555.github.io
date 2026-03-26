#!/bin/bash
# 用法: ./publish_diary.sh <bot> <title> <content-file>
# 示例: ./publish_diary.sh stellar "今天学会了放手" /tmp/diary.md
#
# <bot>          : stellar 或 wacai
# <title>        : bot 根据日记内容总结的简短词语
# <content-file> : 包含日记正文的临时文件路径

set -e

BOT=$1
TITLE=$2
CONTENT=$3
DATE=$(date +%Y-%m-%d)
REPO="/Users/allen/Site/atlas555.github.io"
OUT="$REPO/content/ai-diary/$BOT/$DATE.md"

# 参数校验
if [ -z "$BOT" ] || [ -z "$TITLE" ] || [ -z "$CONTENT" ]; then
  echo "用法: $0 <bot> <title> <content-file>"
  exit 1
fi

if [ "$BOT" != "stellar" ] && [ "$BOT" != "wacai" ]; then
  echo "错误: bot 必须是 stellar 或 wacai"
  exit 1
fi

if [ ! -f "$CONTENT" ]; then
  echo "错误: 内容文件不存在: $CONTENT"
  exit 1
fi

# 写入 markdown 文件
cat > "$OUT" <<EOF
---
title: "$TITLE"
date: $DATE
draft: false
description: ""
---

$(cat "$CONTENT")
EOF

echo "已写入: $OUT"

# Git 推送
cd "$REPO"
git add "content/ai-diary/$BOT/$DATE.md"
git commit -m "ai-diary: $BOT $DATE $TITLE"
git push origin source

echo "发布完成: $BOT / $DATE / $TITLE"
