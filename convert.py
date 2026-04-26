import re

def md_to_json(md_file, output_json, default_category="未分类", default_author="未知"):
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按空行分割（两个及以上换行符）
    paragraphs = re.split(r'\n\s*\n', content.strip())
    sentences = [p.replace('\n', ' ').strip() for p in paragraphs if p.strip()]
    
    data = []
    for text in sentences:
        data.append({
            "hitokoto": text,
            "author": default_author,
            "categories": [default_category],
            "commit_from": "import_script"
        })
    
    import json
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已转换 {len(sentences)} 条句子，保存至 {output_json}")

if __name__ == "__main__":
    # 请修改以下参数
    md_file = "坠.md"      # 你的markdown文件路径
    output_json = "sentences_import.json"
    default_category = "随笔"          # 你可以改成想要的分类
    default_author = "佚名"            # 作者名
    
    md_to_json(md_file, output_json, default_category, default_author)