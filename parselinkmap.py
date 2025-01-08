# coding: utf8
#
#   LinkMapParser
#   author:     eric.zhang
#   email:      zgzczzw@163.com

import sys
import os
import re


def read_base_link_map_file(base_link_map_file, base_link_map_result_file):
    # 从Path中提取关键信息：模块-文件名
    def extract_file_identifier(file_path):
        # file_name_with_index = file_path.rsplit('/', 1)[-1]
        # clean_file_name = re.sub(r'\[\d+\]', '', file_name_with_index)
        # # print("===========" + clean_file_name)
        # return clean_file_name
        file_name_with_index = file_path.rsplit('/', 1)[-1]
        clean_file_name = re.sub(r'\[\d+\]', '', file_name_with_index)
        # 移除 .o 后的多余部分
        file_base_name = re.sub(r'-[^.]*\.o$', '.o', clean_file_name)
        # print("=======" + file_base_name)
        return file_base_name

    try:
        with open(base_link_map_file, encoding="latin1") as link_map_file:
            content = link_map_file.read()
    except IOError:
        print("Read file " + base_link_map_file + " failed!")
        return
    except UnicodeDecodeError:
        print("Decode file " + base_link_map_file + " failed!")
        return

    # 查找并分割文件内容的位置标记
    obj_file_tag_index = content.find("# Object files:")
    sub_obj_file_symbol_str = content[obj_file_tag_index + 15:]
    symbols_index = sub_obj_file_symbol_str.find("# Symbols:")
    if obj_file_tag_index == -1 or symbols_index == -1 or content.find("# Path:") == -1:
        print("The Content of File " + base_link_map_file + " is Invalid.")
        return
    # 解析文件内容
    with open(base_link_map_file, encoding="latin1") as link_map_file_tmp:
        reach_files = 0
        reach_sections = 0
        reach_symbols = 0
        size_map = {}
        file_map = {}
        while True:
            line = link_map_file_tmp.readline()
            if not line:
                break
            if line.startswith("#"):
                if line.startswith("# Object files:"):
                    reach_files = 1
                if line.startswith("# Sections"):
                    reach_sections = 1
                if line.startswith("# Symbols"):
                    reach_symbols = 1
            else:
                if reach_files == 1 and reach_sections == 0 and reach_symbols == 0:
                    index = line.find("]")
                    if index != -1:
                        file_name = line[index + 2:].strip()
                        key = int(line[1: index])
                        file_map[key] = file_name  # Store file name with its index
                elif reach_files == 1 and reach_sections == 1 and reach_symbols == 0:
                    pass
                elif reach_files == 1 and reach_sections == 1 and reach_symbols == 1:
                    symbols_array = line.split("\t")
                    if len(symbols_array) == 3:
                        file_key_and_name = symbols_array[2]
                        size = int(symbols_array[1], 16)
                        index = file_key_and_name.find("]")
                        if index != -1:
                            key = file_key_and_name[1:index]
                            key = int(key)
                            if key in file_map:

                                file_name = extract_file_identifier(file_map[key])
                                file_entry = f"{file_name}"
                                if file_entry in size_map:
                                    size_map[file_entry]["size"] += size
                                else:
                                    size_map[file_entry] = {"file": file_entry, "size": size}
                else:
                    print("Invalid #3")

        # 计算总体积并生成汇总信息
        total_size = 0
        a_file_map = {}
        for key, symbol in size_map.items():
            total_size += symbol["size"]
            file_name = symbol["file"]
            if file_name in a_file_map:
                a_file_map[file_name] += symbol["size"]
            else:
                a_file_map[file_name] = symbol["size"]

        # 生成体积汇总并输出结果
        a_file_sorted_list = sorted(a_file_map.items(), key=lambda x: x[1], reverse=True)
        print("%s" % "=".ljust(80, '='))
        print("%s" % (base_link_map_file + "各模块体积汇总").center(87))
        print("%s" % "=".ljust(80, '='))
        if os.path.exists(base_link_map_result_file):
            os.remove(base_link_map_result_file)
        print("Creating Result File : %s" % base_link_map_result_file)

        store_sales_total_size = 0
        with open(base_link_map_result_file, "w", encoding="utf-8") as output_file:
            for item in a_file_sorted_list:
                print("test1111 %s%.2fKB" % (item[0].ljust(50), item[1] / 1024.0))
                if item[0].startswith("si_sales") or item[0].startswith("si_store"):
                    output_file.write("%s \t\t\t%.2fKB\n" % (item[0].ljust(50), item[1] / 1024.0))
                    store_sales_total_size += (item[1] / 1024.0)
            # print("%s%.2fKB" % ("总体积:".ljust(53), total_size / 1024.0))
            print("%s%.2fKB" % ("店铺&频道总体积:".ljust(53),  store_sales_total_size))
            print("\n\n\n\n\n")
            # output_file.write("%s%.2fKB\n" % ("总体积:".ljust(53), total_size / 1024.0))
            output_file.write("%s%.2fKB\n" % ("店铺&频道总体积:".ljust(53), store_sales_total_size))


# 解析结果文件并返回包含文件名和对应体积的列表。
def parse_result_file(result_file_name):
    base_bundle_list = []
    with open(result_file_name, encoding="utf-8") as result_file:
        while True:
            line = result_file.readline()
            if not line:
                break
            bundle_and_size = line.split()
            if len(bundle_and_size) == 2 and line.find(":") == -1:
                bundle_and_size_map = {"name": bundle_and_size[0], "size": bundle_and_size[1]}
                base_bundle_list.append(bundle_and_size_map)
    return base_bundle_list


# 比较Link Map文件，输出结果
def compare(base_bundle_list, target_bundle_list):
    def extract_file_identifier(file_path):
        file_name_with_index = file_path.rsplit('/', 1)[-1]
        clean_file_name = re.sub(r'\[\d+\]', '', file_name_with_index)
        # class里面定义class会以hash拼在文件后面  XXXCell-0c9be9cf72e995a582e70da8c99dac38.o
        if clean_file_name.startswith("si_tri"):
            pattern = r'\(([^()]*)-[^.]*?(\.o[^()]*)\)'
            transformed_string = re.sub(pattern, r'(\1\2)', clean_file_name)
            return transformed_string
        return clean_file_name

    print("%s" % "=".ljust(150, '='))
    print("%s" % "比较结果".center(100))
    print("%s" % "=".ljust(150, '='))
    print("%s%s%s%s" % ("模块名称".ljust(80), "基线大小".ljust(10), "目标大小".ljust(10), "是否新模块".ljust(10)))
    total_reduced_size = 0
    for target_bundle_map in target_bundle_list:
        target_name = target_bundle_map["name"]
        target_size = target_bundle_map["size"]
        target_size_value = float(target_size.split("KB")[0])
        target_clean_name = extract_file_identifier(target_name)
        has_bundle_in_base = 0
        base_size_value = 0

        for base_bundle_map in base_bundle_list:
            base_name = base_bundle_map["name"]
            base_clean_name = extract_file_identifier(base_name)
            if base_clean_name == target_clean_name:
                base_size = base_bundle_map["size"]
                base_size_value = float(base_size.split("KB")[0])
                has_bundle_in_base = 1
                if abs(base_size_value - target_size_value) > 1:
                    print("%s%s%s" % (target_clean_name.ljust(80), str("%.2fKB" % base_size_value).ljust(10),
                                      str("%.2fKB" % target_size_value).ljust(10)))
                if base_size_value != target_size_value:
                    total_reduced_size += (base_size_value - target_size_value)
                break
        if has_bundle_in_base == 0:
            total_reduced_size -= target_size_value
            print("%s%s%s%s" % (target_clean_name.ljust(80), str("%.2fKB" % base_size_value).ljust(10),
                                str("%.2fKB" % target_size_value).ljust(10), "Y".center(10)))
    print("总减少大小为: %.2fkb" % total_reduced_size)


def print_help():
    print("%s" % "=".ljust(80, '='))
    print("%s%s\n" % ("".ljust(10), "Link Map 文件分析工具".ljust(80)))
    print("%s%s\n" % ("".ljust(10), "- Usage : python parselinkmap.py arg1 <arg2>".ljust(80)))
    print("%s%s" % ("".ljust(10), "- arg1 ：基准LinkMap文件路径".ljust(80)))
    print("%s%s\n" % ("".ljust(10), "- arg2 ：待比较LinkMap文件路径".ljust(80)))
    print("%s%s" % ("".ljust(10), "备注：参数2为空时，只输出基准LinkMap分析结果".ljust(80)))
    print("%s" % "=".ljust(80, '='))


# 清除输出结果
def clean_result_file(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)


def main():
    if len(sys.argv) == 2:
        need_compare = 0
    elif len(sys.argv) == 3:
        need_compare = 1
    else:
        print_help()
        return

    base_map_link_file = sys.argv[1]
    output_file_path = os.path.dirname(base_map_link_file)
    if output_file_path:
        base_output_file = output_file_path + "/BaseLinkMapResult.txt"
    else:
        base_output_file = "BaseLinkMapResult.txt"
    read_base_link_map_file(base_map_link_file, base_output_file)

    if need_compare == 1:
        target_map_link_file = sys.argv[2]
        output_file_path = os.path.dirname(target_map_link_file)
        if output_file_path:
            target_output_file = output_file_path + "/TargetLinkMapResult.txt"
        else:
            target_output_file = "TargetLinkMapResult.txt"
        read_base_link_map_file(target_map_link_file, target_output_file)

        base_bundle_list = parse_result_file(base_output_file)
        target_bundle_list = parse_result_file(target_output_file)

        compare(base_bundle_list, target_bundle_list)

    # clean_result_file(base_output_file)
    # clean_result_file(target_output_file)


if __name__ == "__main__":
    main()
