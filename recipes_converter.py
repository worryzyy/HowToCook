#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
菜谱JSON转换器
从完整的recipes.json提取指定字段生成精简版本
"""

import json
import os
from typing import List, Dict, Any

def convert_recipes_to_simple_format(input_file: str, output_file: str) -> None:
    """
    转换菜谱JSON文件，只保留指定字段
    
    Args:
        input_file: 输入的完整JSON文件路径
        output_file: 输出的精简JSON文件路径
    """
    
    # 读取原始JSON文件
    print(f"读取原始文件: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        recipes = json.load(f)
    
    print(f"原始菜谱数量: {len(recipes)}")
    
    # 转换为精简格式
    simple_recipes = []
    
    for recipe in recipes:
        # 只保留指定字段
        simple_recipe = {
            "name": recipe.get("name", ""),
            "category": recipe.get("category", ""),
            "steps": recipe.get("steps", []),
            "difficulty": recipe.get("difficulty", 1),
            "images": recipe.get("images", [])
        }
        
        simple_recipes.append(simple_recipe)
    
    # 保存精简版本
    print(f"保存精简版本到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(simple_recipes, f, ensure_ascii=False, indent=2)
    
    print(f"转换完成！精简版菜谱数量: {len(simple_recipes)}")
    
    # 计算文件大小对比
    original_size = os.path.getsize(input_file)
    simple_size = os.path.getsize(output_file)
    reduction_percent = (1 - simple_size / original_size) * 100
    
    print(f"文件大小对比:")
    print(f"  原始文件: {original_size:,} 字节")
    print(f"  精简文件: {simple_size:,} 字节")
    print(f"  减少了: {reduction_percent:.1f}%")

def preview_simple_recipe(input_file: str, count: int = 3) -> None:
    """
    预览转换后的精简格式
    
    Args:
        input_file: 输入的完整JSON文件路径
        count: 预览的菜谱数量
    """
    
    with open(input_file, 'r', encoding='utf-8') as f:
        recipes = json.load(f)
    
    print(f"\n=== 预览转换后的格式（前{count}个菜谱）===")
    
    for i, recipe in enumerate(recipes[:count]):
        simple_recipe = {
            "name": recipe.get("name", ""),
            "category": recipe.get("category", ""),
            "steps": recipe.get("steps", []),
            "difficulty": recipe.get("difficulty", 1),
            "images": recipe.get("images", [])
        }
        
        print(f"\n--- 菜谱 {i+1}: {simple_recipe['name']} ---")
        print(f"分类: {simple_recipe['category']}")
        print(f"难度: {simple_recipe['difficulty']}")
        print(f"步骤数量: {len(simple_recipe['steps'])}")
        print(f"图片数量: {len(simple_recipe['images'])}")
        
        if simple_recipe['steps']:
            print("步骤示例:")
            for j, step in enumerate(simple_recipe['steps'][:2]):  # 只显示前2步
                print(f"  {step.get('step', j+1)}. {step.get('description', '')[:50]}...")
        
        if simple_recipe['images']:
            print(f"图片示例: {simple_recipe['images'][0]}")

def main():
    # 自动检测文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, 'recipes.json')
    output_file = os.path.join(current_dir, 'recipes_simple.json')
    
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 {input_file}")
        return
    
    # 预览转换格式
    preview_simple_recipe(input_file)
    
    # 直接进行转换
    print(f"\n开始转换...")
    convert_recipes_to_simple_format(input_file, output_file)
    print(f"\n✅ 转换完成！")
    print(f"精简版文件已保存为: {output_file}")

if __name__ == '__main__':
    main()