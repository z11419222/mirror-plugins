#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话相似度检查脚本
用于检测用户输入与已有会话的相似度，支持会话复用

使用方式:
    python check_similarity.py "用户输入的主题"
    
输出格式 (JSON):
    {
        "matched": true/false,
        "session_id": "会话ID",
        "topic": "匹配的主题",
        "similarity": 0.85,
        "keywords_overlap": ["重叠关键词"],
        "suggestion": "建议说明"
    }
"""

import json
import sys
import os
import re
from pathlib import Path


def extract_keywords(text: str) -> set:
    """
    从文本中提取中英文关键词
    简单的分词：按空格和标点分割，过滤停用词
    """
    # 中文停用词
    chinese_stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没', '看', '好', '自己', '这', '那', '里', '为', '什么', '怎么', '吗', '呢', '吧', '啊', '呀', '帮我', '写', '几个', '一个', '一些', '关于'}
    
    # 英文停用词
    english_stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while', 'about', 'write', 'help', 'me', 'please'}
    
    stopwords = chinese_stopwords | english_stopwords
    
    # 分词：按非中英文字符分割
    # 中文按单字或常见词组，英文按空格
    words = set()
    
    # 提取中文词（简单按2-4字组合）
    chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
    for chars in chinese_chars:
        if len(chars) >= 2:
            words.add(chars)
        # 也添加2字组合
        for i in range(len(chars) - 1):
            bigram = chars[i:i+2]
            if bigram not in stopwords:
                words.add(bigram)
    
    # 提取英文词
    english_words = re.findall(r'[a-zA-Z]+', text.lower())
    for word in english_words:
        if len(word) >= 2 and word not in stopwords:
            words.add(word)
    
    # 过滤停用词
    words = {w for w in words if w.lower() not in stopwords and len(w) >= 2}
    
    return words


def jaccard_similarity(set1: set, set2: set) -> float:
    """
    计算两个集合的 Jaccard 相似度
    """
    if not set1 or not set2:
        return 0.0
    
    intersection = set1 & set2
    union = set1 | set2
    
    return len(intersection) / len(union) if union else 0.0


def load_session_index(project_dir: str) -> list:
    """
    加载会话索引文件
    """
    index_path = Path(project_dir) / '.mirror-writing' / 'session_index.json'
    
    if not index_path.exists():
        return []
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('sessions', [])
    except (json.JSONDecodeError, IOError):
        return []


def find_similar_session(user_input: str, sessions: list, threshold: float = 0.5) -> dict:
    """
    查找相似会话
    
    参数:
        user_input: 用户输入
        sessions: 会话列表
        threshold: 相似度阈值 (默认0.5 = 50%)
    
    返回:
        匹配结果字典
    """
    user_keywords = extract_keywords(user_input)
    
    if not user_keywords:
        return {
            "matched": False,
            "reason": "无法从输入中提取有效关键词"
        }
    
    best_match = None
    best_similarity = 0.0
    best_overlap = []
    
    for session in sessions:
        session_keywords = set(session.get('keywords', []))
        session_topic = session.get('topic', '')
        
        # 也将主题加入关键词
        topic_keywords = extract_keywords(session_topic)
        session_keywords = session_keywords | topic_keywords
        
        if not session_keywords:
            continue
        
        similarity = jaccard_similarity(user_keywords, session_keywords)
        overlap = list(user_keywords & session_keywords)
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = session
            best_overlap = overlap
    
    if best_match and best_similarity >= threshold:
        return {
            "matched": True,
            "session_id": best_match.get('session_id', ''),
            "topic": best_match.get('topic', ''),
            "similarity": round(best_similarity, 2),
            "keywords_overlap": best_overlap[:10],  # 最多返回10个重叠词
            "created_at": best_match.get('created_at', ''),
            "suggestion": f"检测到相似会话 [{best_match.get('topic', '')}]，相似度 {int(best_similarity * 100)}%。可复用已有分析结果直接生成文案。"
        }
    else:
        return {
            "matched": False,
            "best_similarity": round(best_similarity, 2) if best_match else 0,
            "user_keywords": list(user_keywords)[:10],
            "suggestion": "未找到相似会话，将执行完整创作流程。"
        }


def main():
    # 获取用户输入
    if len(sys.argv) < 2:
        result = {
            "matched": False,
            "error": "缺少用户输入参数",
            "usage": "python check_similarity.py \"用户输入\""
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    user_input = sys.argv[1]
    
    # 获取项目目录（当前工作目录）
    project_dir = os.getcwd()
    
    # 加载会话索引
    sessions = load_session_index(project_dir)
    
    if not sessions:
        result = {
            "matched": False,
            "suggestion": "暂无历史会话，将执行完整创作流程。"
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    
    # 查找相似会话
    result = find_similar_session(user_input, sessions)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == '__main__':
    main()
