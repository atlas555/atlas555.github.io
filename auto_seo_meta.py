#!/usr/bin/env python3
"""
auto_seo_meta.py - 用 Claude AI 自动为 Hugo 博客文章生成 SEO 元数据

用法:
    python auto_seo_meta.py              # 只处理缺失元数据的文章
    python auto_seo_meta.py --all        # 重新生成所有文章的元数据
    python auto_seo_meta.py --quality    # 补全缺失 + 修复低质量元数据
    python auto_seo_meta.py --dry-run    # 预览模式（不写入文件）
    python auto_seo_meta.py --file path  # 处理单个文件
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("请先安装: pip install anthropic")
    sys.exit(1)

# 博客内容目录
CONTENT_DIRS = [
    Path("content/cn"),
    Path("content/en"),
    Path("content/ai-diary"),
]

# 跳过的文件（目录索引页）
SKIP_FILES = {"_index.md"}

# 质量阈值
MIN_DESC_LEN = 40       # description 最短字符数
MIN_TAGS = 3            # 最少 tag 数
MIN_KEYWORDS = 4        # 最少 keyword 数

# Claude 模型 - 可通过环境变量 SEO_MODEL 覆盖
MODEL = os.environ.get("SEO_MODEL", "claude-sonnet-4-6")


def extract_front_matter(text: str) -> tuple[str | None, str]:
    """提取 YAML front matter 和正文"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def get_title(front_matter: str) -> str:
    """从 front matter 提取标题"""
    m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', front_matter, re.M)
    return m.group(1).strip().strip('"\'') if m else ""


def get_description(front_matter: str) -> str:
    """从 front matter 提取 description"""
    m = re.search(r'^description:\s*["\']?(.*?)["\']?\s*$', front_matter, re.M)
    return m.group(1).strip().strip('"\'') if m else ""


def get_list_count(front_matter: str, field: str) -> int:
    """获取 YAML 列表字段的元素数量"""
    # 行内格式: tags: [a, b, c]
    inline = re.search(rf'^{field}\s*:\s*\[([^\]]*)\]', front_matter, re.M)
    if inline:
        items = [x.strip().strip('"\'') for x in inline.group(1).split(',') if x.strip()]
        return len(items)
    # 块格式: tags:\n- a\n- b
    block = re.search(rf'^{field}\s*:\s*\n((?:[ \t]*-[ \t]+.+\n?)*)', front_matter, re.M)
    if block:
        return len(re.findall(r'^\s*-\s+', block.group(1), re.M))
    return 0


def check_needs_update(front_matter: str, title: str, quality: bool = False) -> dict:
    """检查哪些字段需要更新（缺失或低质量）"""
    has_desc = bool(re.search(r"^description\s*:", front_matter, re.M))
    has_tags = bool(re.search(r"^tags\s*:", front_matter, re.M))
    has_kw = bool(re.search(r"^keywords\s*:", front_matter, re.M))

    needs = {
        "description": not has_desc,
        "tags": not has_tags,
        "keywords": not has_kw,
    }

    if quality:
        if has_desc:
            desc = get_description(front_matter)
            if len(desc) < MIN_DESC_LEN or desc.strip() == title.strip():
                needs["description"] = True
        if has_tags:
            if get_list_count(front_matter, "tags") < MIN_TAGS:
                needs["tags"] = True
        if has_kw:
            if get_list_count(front_matter, "keywords") < MIN_KEYWORDS:
                needs["keywords"] = True

    return needs


def detect_language(body: str) -> str:
    """根据内容检测语言"""
    cn_chars = len(re.findall(r"[\u4e00-\u9fff]", body[:500]))
    return "zh" if cn_chars > 20 else "en"


def generate_metadata(client: anthropic.Anthropic, title: str, body: str, lang: str) -> dict:
    """调用 Claude API 生成 SEO 元数据"""

    # 只取前 2000 字符，节省 token
    content_preview = body[:2000].strip()

    if lang == "zh":
        prompt = f"""根据以下博客文章，生成 SEO 优化的元数据。

文章标题：{title}

文章内容（摘录）：
{content_preview}

请以 JSON 格式返回（只返回 JSON，不要其他文字）：
{{
  "description": "150字以内的精准摘要，包含核心关键词，适合搜索引擎显示",
  "tags": ["标签1", "标签2", "标签3"],
  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"]
}}

要求：
- description 用中文，简洁精准，突出文章核心价值，不要直接复制标题
- tags 3-6个，可中英混合，优先使用技术词汇
- keywords 5-8个，覆盖主题、相关技术、作者专长"""
    else:
        prompt = f"""Based on the following blog post, generate SEO-optimized metadata.

Title: {title}

Content preview:
{content_preview}

Return JSON only (no other text):
{{
  "description": "A precise summary under 160 characters with core keywords for search engines",
  "tags": ["tag1", "tag2", "tag3"],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}

Requirements:
- description: concise, highlight the core value, include main keywords, do NOT just copy the title
- tags: 3-6 tags, tech terms preferred
- keywords: 5-8 keywords covering the topic and related concepts"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # 提取 ```json ... ``` 块或裸 JSON
    code_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    json_str = code_match.group(1).strip() if code_match else raw

    # 找到最外层 {} 范围
    start = json_str.find("{")
    end = json_str.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"无法找到 JSON 对象: {raw[:200]}")
    json_str = json_str[start : end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # 如果 description 包含未转义引号，尝试用正则单独提取字段
        result = {}
        desc_m = re.search(r'"description"\s*:\s*"(.*?)"(?=\s*,\s*"(?:tags|keywords)")', json_str, re.DOTALL)
        if desc_m:
            result["description"] = desc_m.group(1)
        tags_section = re.search(r'"tags"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
        if tags_section:
            result["tags"] = re.findall(r'"([^"]+)"', tags_section.group(1))
        kw_section = re.search(r'"keywords"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
        if kw_section:
            result["keywords"] = re.findall(r'"([^"]+)"', kw_section.group(1))
        if result:
            return result
        raise ValueError(f"JSON 解析失败: {json_str[:200]}")


def strip_field(front_matter: str, field: str) -> str:
    """从 front matter 中删除指定字段（支持单行和列表格式）"""
    lines = front_matter.split('\n')
    result = []
    in_field = False
    for line in lines:
        if re.match(rf'^{re.escape(field)}\s*:', line):
            in_field = True
            continue
        if in_field:
            # 跳过列表项（块格式 "- item" 或内联格式已在同一行被删除）
            if re.match(r'^\s*-\s', line):
                continue
            else:
                in_field = False
        result.append(line)
    return '\n'.join(result)


def update_front_matter(front_matter: str, metadata: dict, needs: dict) -> str:
    """将生成的元数据写入 front matter，先删除旧值再追加新值"""
    fm = front_matter.rstrip()

    # 先删除需要更新的字段（避免重复）
    for field, needed in needs.items():
        if needed:
            fm = strip_field(fm, field)
    fm = fm.rstrip()

    if needs.get("description") and "description" in metadata:
        desc = metadata["description"].replace('"', '\\"')
        fm += f'\ndescription: "{desc}"'

    if needs.get("tags") and "tags" in metadata:
        tags = metadata["tags"]
        if isinstance(tags, list):
            fm += "\ntags:\n" + "\n".join(f"- {t}" for t in tags)

    if needs.get("keywords") and "keywords" in metadata:
        kw = metadata["keywords"]
        if isinstance(kw, list):
            fm += "\nkeywords:\n" + "\n".join(f"- {k}" for k in kw)

    return fm


def process_file(
    client: anthropic.Anthropic,
    filepath: Path,
    force: bool = False,
    quality: bool = False,
    dry_run: bool = False,
) -> dict:
    """处理单个文件，返回处理结果"""
    result = {"file": str(filepath), "status": "skipped", "needs": [], "changes": []}

    text = filepath.read_text(encoding="utf-8")
    front_matter, body = extract_front_matter(text)

    if front_matter is None:
        result["status"] = "no_front_matter"
        return result

    title = get_title(front_matter)
    if not title:
        result["status"] = "no_title"
        return result

    if force:
        needs = {"description": True, "tags": True, "keywords": True}
    else:
        needs = check_needs_update(front_matter, title, quality=quality)

    needs_fields = [k for k, v in needs.items() if v]

    if not needs_fields:
        result["status"] = "complete"
        return result

    result["needs"] = needs_fields
    lang = detect_language(body)

    print(f"  处理: {filepath.name} [{lang}] 需更新: {needs_fields}")

    try:
        metadata = generate_metadata(client, title, body, lang)
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"  ✗ 生成失败: {e}")
        return result

    new_fm = update_front_matter(front_matter, metadata, needs)
    result["changes"] = [k for k in needs if k in metadata]

    if dry_run:
        print(f"  [dry-run] 将写入:")
        if "description" in metadata and needs.get("description"):
            print(f"    description: {metadata['description'][:80]}...")
        if "tags" in metadata and needs.get("tags"):
            print(f"    tags: {metadata['tags']}")
        if "keywords" in metadata and needs.get("keywords"):
            print(f"    keywords: {metadata['keywords'][:4]}...")
        result["status"] = "dry_run"
        return result

    # 写回文件
    new_text = f"---\n{new_fm}\n---\n{body}"
    filepath.write_text(new_text, encoding="utf-8")
    print(f"  ✓ 已更新: {', '.join(result['changes'])}")
    result["status"] = "updated"
    return result


def main():
    parser = argparse.ArgumentParser(description="Hugo 博客 SEO 元数据自动生成")
    parser.add_argument("--all", action="store_true", help="重新生成所有文章（覆盖现有元数据）")
    parser.add_argument("--quality", action="store_true", help="补全缺失 + 修复低质量元数据（desc过短/等于标题/tags不足等）")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写入文件")
    parser.add_argument("--file", type=str, help="处理单个文件")
    args = parser.parse_args()

    # 支持 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN（代理场景）
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not api_key:
        print("错误: 请设置环境变量 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN")
        sys.exit(1)

    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    import httpx
    # trust_env=False 防止 httpx 被系统代理拦截
    http_client = httpx.Client(trust_env=False, timeout=60.0)
    client_kwargs: dict = {"api_key": api_key, "http_client": http_client}
    if base_url:
        client_kwargs["base_url"] = base_url

    client = anthropic.Anthropic(**client_kwargs)

    if args.file:
        files = [Path(args.file)]
    else:
        files = []
        for d in CONTENT_DIRS:
            if d.exists():
                for f in sorted(d.rglob("*.md")):
                    if f.name not in SKIP_FILES:
                        files.append(f)

    if args.all:
        mode = "重新生成所有"
    elif args.quality:
        mode = "补全缺失 + 修复低质量"
    else:
        mode = "补全缺失"
    dry = " [dry-run]" if args.dry_run else ""
    print(f"模式: {mode}{dry}")
    print(f"模型: {MODEL}")
    print(f"文件数: {len(files)}\n")

    stats = {"updated": 0, "complete": 0, "skipped": 0, "error": 0, "no_front_matter": 0}

    for filepath in files:
        result = process_file(
            client, filepath,
            force=args.all,
            quality=args.quality,
            dry_run=args.dry_run,
        )
        status = result["status"]
        if status in stats:
            stats[status] += 1
        elif status == "dry_run":
            stats["updated"] += 1

    print(f"\n完成！")
    print(f"  已更新: {stats['updated']}")
    print(f"  已完整: {stats['complete']}")
    print(f"  出错:   {stats['error']}")
    if stats["no_front_matter"]:
        print(f"  无front matter: {stats['no_front_matter']}")


if __name__ == "__main__":
    main()
