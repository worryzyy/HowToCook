#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将dishes目录下的MD格式菜谱转换为JSON格式
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class MarkdownParser:
    def __init__(self, dishes_dir: str):
        self.dishes_dir = dishes_dir
        self.category_mapping = {
            'aquatic': '水产',
            'breakfast': '早餐',
            'condiment': '调料',
            'dessert': '甜品',
            'drink': '饮品',
            'meat_dish': '荤菜',
            'semi-finished': '半成品加工',
            'soup': '汤',
            'staple': '主食',
            'vegetable_dish': '素菜'
        }
    
    def get_md_files(self) -> List[tuple]:
        """遍历dishes目录，获取所有MD文件路径"""
        md_files = []
        
        for root, dirs, files in os.walk(self.dishes_dir):
            # 跳过template目录
            if 'template' in root:
                continue
                
            for file in files:
                if file.endswith('.md'):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, start=os.path.dirname(self.dishes_dir))
                    md_files.append((full_path, relative_path))
        
        return md_files
    
    def extract_difficulty(self, content: str) -> int:
        """从内容中提取难度级别"""
        difficulty_pattern = r'预估烹饪难度[:：]\s*([★☆]{1,5})'
        match = re.search(difficulty_pattern, content)
        if match:
            stars = match.group(1)
            return stars.count('★')
        return 1
    
    def extract_ingredients(self, content: str) -> List[Dict]:
        """提取食材信息"""
        ingredients = []
        
        # 尝试多种可能的食材标题
        ingredient_patterns = [
            r'##\s*需要的食材\s*\n(.*?)(?=##|\Z)',
            r'##\s*食材\s*\n(.*?)(?=##|\Z)',
            r'##\s*必备原料和工具\s*\n(.*?)(?=##|\Z)',
            r'##\s*计算\s*\n(.*?)(?=##|\Z)',
            r'##\s*原料\s*\n(.*?)(?=##|\Z)',
            r'##\s*配料\s*\n(.*?)(?=##|\Z)'
        ]
        
        ingredient_text = ""
        for pattern in ingredient_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                ingredient_text += match.group(1) + "\n"
        
        if ingredient_text:
            # 解析食材行
            lines = ingredient_text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    # 移除前缀符号
                    ingredient_line = line[1:].strip()
                    
                    # 过滤掉不是食材的行
                    if (ingredient_line and 
                        not ingredient_line.startswith('总量') and
                        not ingredient_line.endswith('向下取整。') and
                        not ingredient_line.endswith('向上取整。') and
                        not '用量为' in ingredient_line and
                        not '的用量为' in ingredient_line and
                        not '食用油的用量' in ingredient_line and
                        len(ingredient_line) < 50):  # 避免太长的说明文字
                        
                        # 尝试解析食材名称和数量
                        # 处理类似 "肉蟹 1 只（大约 300g） * 份数" 的格式
                        base_ingredient = re.split(r'\s+\d+|\s+\*', ingredient_line)[0]
                        name = base_ingredient.strip()
                        
                        if name and len(name) > 0 and name != '使用上述条件，计算出计划使用的原材料比例':
                            ingredients.append({
                                'name': name,
                                'quantity': None,
                                'unit': None,
                                'text_quantity': f"- {ingredient_line}",
                                'notes': '量未指定'
                            })
        
        return ingredients
    
    def extract_steps(self, content: str, debug_path: str = "") -> List[Dict]:
        """提取操作步骤，处理不同格式"""
        steps = []
        
        # 寻找操作部分 - 使用更简单的方法
        lines = content.split('\n')
        operation_start = -1
        operation_end = -1
        
        for i, line in enumerate(lines):
            if line.strip() in ['## 操作', '## 做法', '## 制作方法']:
                operation_start = i + 1
                # 找到下一个真正的二级标题（只有##）
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith('## ') and not lines[j].startswith('### '):
                        operation_end = j
                        break
                if operation_end == -1:
                    operation_end = len(lines)
                break
        
        operation_text = ""
        if operation_start != -1:
            operation_text = '\n'.join(lines[operation_start:operation_end]).strip()
        
        if operation_text:
            
            # 方式1: 直接的-列表格式
            direct_steps = re.findall(r'^-\s*(.+)$', operation_text, re.MULTILINE)
            if direct_steps:
                for i, step in enumerate(direct_steps, 1):
                    steps.append({
                        'step': i,
                        'description': step.strip()
                    })
            else:
                # 方式2: ###子标题 + *列表格式
                step_counter = 1
                
                # 检查是否包含###子标题
                if '###' in operation_text:
                    # 直接提取所有*开头的行作为步骤
                    lines = operation_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('*') and not line.startswith('  *'):
                            # 移除*前缀并清理主步骤
                            step_text = line[1:].strip()
                            if step_text:
                                steps.append({
                                    'step': step_counter,
                                    'description': step_text
                                })
                                step_counter += 1
                        elif line.startswith('  *'):
                            # 处理嵌套的*（缩进的子步骤）
                            step_text = line.strip()[1:].strip()  # 去掉缩进和*
                            if step_text and steps:
                                # 将子步骤附加到上一个步骤
                                steps[-1]['description'] += f" {step_text}"
                else:
                    # 如果没有###子标题，尝试提取*开头的步骤
                    step_lines = re.findall(r'^\*\s*(.+)$', operation_text, re.MULTILINE)
                    for i, step in enumerate(step_lines, 1):
                        steps.append({
                            'step': i,
                            'description': step.strip()
                        })
        
        return steps
    
    def extract_description(self, content: str) -> str:
        """提取描述信息"""
        # 提取第一个##之前的内容作为描述
        first_heading = re.search(r'^##', content, re.MULTILINE)
        if first_heading:
            description = content[:first_heading.start()].strip()
        else:
            # 如果没有找到##，取前几行
            lines = content.split('\n')
            description_lines = []
            for line in lines[:10]:  # 最多取前10行
                if line.strip() and not line.startswith('#'):
                    description_lines.append(line.strip())
            description = '\n'.join(description_lines)
        
        return description.strip()
    
    def find_image_paths(self, md_file_path: str) -> List[str]:
        """查找对应的所有图片文件，返回GitHub链接"""
        md_dir = os.path.dirname(md_file_path)
        image_paths = []
        
        # 常见的图片扩展名
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        
        # GitHub仓库基础URL
        github_base_url = "https://media.githubusercontent.com/media/worryzyy/HowToCook/mcp/"
        
        # 在同目录下查找所有图片
        try:
            for filename in os.listdir(md_dir):
                if any(filename.lower().endswith(ext) for ext in image_extensions):
                    relative_path = os.path.relpath(
                        os.path.join(md_dir, filename), 
                        start=os.path.dirname(self.dishes_dir)
                    )
                    # 转换为GitHub链接
                    github_url = github_base_url + relative_path.replace('\\', '/')
                    image_paths.append(github_url)
        except OSError:
            # 如果目录不存在或无法访问，返回空列表
            pass
        
        return sorted(image_paths)  # 排序保持一致性
    
    def parse_md_file(self, file_path: str, relative_path: str) -> Optional[Dict]:
        """解析单个MD文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取文件名作为菜名
            filename = os.path.basename(file_path)
            dish_name = filename.replace('.md', '')
            
            # 生成ID
            path_parts = relative_path.replace('\\', '/').split('/')
            dish_id = '-'.join(path_parts).replace('.md', '')
            
            # 确定分类
            category_en = path_parts[1] if len(path_parts) > 1 else 'unknown'
            category = self.category_mapping.get(category_en, category_en)
            
            # 提取各项信息
            description = self.extract_description(content)
            difficulty = self.extract_difficulty(content)
            ingredients = self.extract_ingredients(content)
            steps = self.extract_steps(content, relative_path)
            image_paths = self.find_image_paths(file_path)
            # 保持向后兼容，如果有图片则使用第一张作为image_path
            image_path = image_paths[0] if image_paths else None
            
            # 提取additional_notes
            additional_notes = []
            if '如果您遵循本指南' in content:
                additional_notes.append('如果您遵循本指南的制作流程而发现有问题或可以改进的流程，请提出 Issue 或 Pull request 。')
            
            # 查找参考链接
            reference_links = re.findall(r'(?:做法参考|参考)[:：]\s*\[([^\]]+)\]\(([^)]+)\)', content)
            for title, url in reference_links:
                additional_notes.append(f'做法参考：[{title}]({url})')
            
            return {
                'id': dish_id,
                'name': f'{dish_name}的做法',
                'description': description,
                'source_path': relative_path.replace('\\', '/'),
                'image_path': image_path,
                'images': image_paths,
                'category': category,
                'difficulty': difficulty,
                'tags': [category],
                'servings': 1,
                'ingredients': ingredients,
                'steps': steps,
                'prep_time_minutes': None,
                'cook_time_minutes': None,
                'total_time_minutes': None,
                'additional_notes': additional_notes if additional_notes else None
            }
        
        except Exception as e:
            print(f'解析文件 {file_path} 时出错: {e}')
            return None
    
    def convert_all(self) -> List[Dict]:
        """转换所有MD文件"""
        md_files = self.get_md_files()
        recipes = []
        
        print(f'找到 {len(md_files)} 个MD文件')
        
        for file_path, relative_path in md_files:
            print(f'正在处理: {relative_path}')
            recipe = self.parse_md_file(file_path, relative_path)
            if recipe:
                recipes.append(recipe)
        
        return recipes

def main():
    dishes_dir = '/mnt/e/WL_Project/Python/HowToCook/dishes'
    output_file = '/mnt/e/WL_Project/Python/HowToCook/recipes.json'
    
    parser = MarkdownParser(dishes_dir)
    recipes = parser.convert_all()
    
    print(f'成功转换 {len(recipes)} 个菜谱')
    
    # 保存为JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)
    
    print(f'结果已保存到: {output_file}')

if __name__ == '__main__':
    main()