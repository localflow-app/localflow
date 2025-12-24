#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
节点脚本: node3
类型: variable_calc
"""
import json
import sys

# 节点配置
NODE_CONFIG = {
  "expression": "x + y * 2",
  "output_var": "result"
}

def read_input():
    """从stdin读取输入数据"""
    try:
        input_str = sys.stdin.read()
        if input_str:
            return json.loads(input_str)
        return {}
    except:
        return {}

def write_output(data):
    """写入输出数据到stdout"""
    print("###JSON_OUTPUT###")
    print(json.dumps(data, ensure_ascii=False))
    print("###JSON_OUTPUT_END###")

def main():
    """主执行函数"""
    input_data = read_input()
    
    try:
        # 变量计算逻辑
        expression = NODE_CONFIG.get("expression", "0")
        output_var = NODE_CONFIG.get("output_var", "result")
        
        # 使用输入数据作为计算上下文
        context = {**input_data}
        result = eval(expression, {"__builtins__": {}}, context)
        
        output_data = {**input_data, output_var: result}
        
        # 输出结果
        write_output(output_data)
        return 0
    except Exception as e:
        print(f"节点执行错误: {e}", file=sys.stderr)
        write_output({"error": str(e)})
        return 1

if __name__ == "__main__":
    sys.exit(main())
