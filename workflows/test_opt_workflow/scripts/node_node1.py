#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
节点脚本: node1
类型: variable_assign
"""
import json
import sys

# 节点配置
NODE_CONFIG = {
  "variable_name": "a",
  "value": "10",
  "value_type": "int"
}

def execute(input_data):
    """
    执行节点逻辑
    Args:
        input_data: 输入数据字典
    Returns:
        输出数据字典
    """
    try:
        # 变量赋值逻辑
        var_name = NODE_CONFIG.get("variable_name", "result")
        value = NODE_CONFIG.get("value", "")
        value_type = NODE_CONFIG.get("value_type", "str")
        
        # 类型转换
        if value_type == "int":
            value = int(value)
        elif value_type == "float":
            value = float(value)
        elif value_type == "bool":
            value = value.lower() in ("true", "1", "yes")
        elif value_type == "json":
            value = json.loads(value)
        
        output_data = {var_name: value}
        return output_data
    except Exception as e:
        raise RuntimeError(f"节点执行错误: {e}")

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
        output_data = execute(input_data)
        
        # 输出结果
        write_output(output_data)
        return 0
    except Exception as e:
        print(f"节点执行错误: {e}", file=sys.stderr)
        write_output({"error": str(e)})
        return 1

if __name__ == "__main__":
    sys.exit(main())
