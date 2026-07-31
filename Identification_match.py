import pandas as pd
import re


def parse_msp(msp_path):
    """解析MSP文件并提取关键数据"""
    spectra = []
    current_spec = {}
    with open(msp_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                if current_spec:
                    spectra.append(current_spec)
                current_spec = {}
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                current_spec[key] = value
            else:
                if 'peaks' not in current_spec:
                    current_spec['peaks'] = []
                try:
                    mz, _ = map(float, line.split())
                    current_spec['peaks'].append(mz)
                except:
                    continue
    if current_spec:
        spectra.append(current_spec)
    return spectra


def match_by_theoretical_mw(exp_mz, db_row):
    """使用Theoretical_MW列进行匹配，返回匹配状态和误差(ppm)"""
    db_mw = db_row.get('Theoretical_MW')
    if pd.isna(db_mw) or db_mw <= 0:
        return False, None

    # 计算ppm误差
    ppm_error = abs((exp_mz - db_mw) / db_mw) * 1e6

    # 5ppm容差内视为匹配
    return ppm_error <= 5, ppm_error


def join_unique_strings(series):
    """将系列中的唯一值连接为字符串，处理各种数据类型和空值"""
    unique_values = set()
    for item in series:
        if pd.notna(item) and str(item).strip() != "":
            unique_values.add(str(item))
    return ", ".join(unique_values) if unique_values else "Unknown"


if __name__ == "__main__":
    # 读取MSP文件
    msp_data = parse_msp("RAW.msp")

    # 读取两个数据库文件并添加标识
    # 添加dtype参数确保Name列被读取为字符串
    database_df = pd.read_excel("Database.xlsx", dtype={"Name": str})
    database_df['Database_Source'] = 'reported'  # 添加来源标识

    virtual_db_df = pd.read_excel("Virtual_databases_merge.xlsx", dtype={"Name": str})
    virtual_db_df['Database_Source'] = 'virtual'  # 添加来源标识

    # 合并两个数据库
    combined_db_df = pd.concat([database_df, virtual_db_df], ignore_index=True)

    # 检查是否存在Theoretical_MW列
    if 'Theoretical_MW' not in combined_db_df.columns:
        raise ValueError("数据库中未找到Theoretical_MW列")

    # 构建实验数据DataFrame
    processed_data = []

    for spec in msp_data:
        try:
            compound = spec.get('comment', '')
            rt = None
            if '_' in compound:
                rt_part = compound.split('_')[0].replace('RT', '')
                try:
                    rt = float(rt_part)
                    # 保留时间过滤(≤2分钟跳过)
                    if rt <= 2:
                        continue
                except ValueError:
                    pass

            # 添加前体m/z
            precursor_mz = float(spec.get('precursormz', 0))

            # 添加质谱峰
            peaks = spec.get('peaks', [])

            processed_data.append({
                "Compound": compound,
                "PrecursorMZ": precursor_mz,  # 修改列名
                "Retention time (min)": rt,
                "Peaks": peaks  # 保存质谱峰信息
            })
        except:
            continue

    fbmn_df = pd.DataFrame(processed_data)

    # 执行数据匹配
    results = []
    for _, fbmn_row in fbmn_df.iterrows():
        mz = fbmn_row["PrecursorMZ"]  # 使用新列名
        rt = fbmn_row["Retention time (min)"]
        compound = fbmn_row["Compound"]

        for _, db_row in combined_db_df.iterrows():
            is_match, ppm_error = match_by_theoretical_mw(mz, db_row)
            if is_match:
                # 根据数据库来源确定匹配类型
                db_source = db_row.get('Database_Source', 'unknown')

                result_entry = {
                    "Compound": compound,
                    "PrecursorMZ": mz,  # 修改列名
                    "Theoretical_MW": db_row.get("Theoretical_MW", ""),  # 添加新列
                    "Error (ppm)": ppm_error,  # 添加新列
                    "Formula": db_row.get("Formula", ""),
                    "Retention time (min)": rt,
                    "Type": db_row.get("Type", ""),
                    "Database_Source": db_source,
                    "Identification": db_row.get("Name", "Unknown")
                }

                results.append(result_entry)

    # 分组聚合结果
    if results:
        result_df = pd.DataFrame(results)

        # 聚合规则
        agg_rules = {
            "Theoretical_MW": "first",  # 添加新列
            "Error (ppm)": "first",  # 添加新列
            "Formula": "first",
            "Type": "first",
            "Database_Source": "first",
            "Identification": join_unique_strings
        }

        # 分组聚合
        grouped_df = result_df.groupby(
            ["Compound", "PrecursorMZ", "Retention time (min)"],  # 使用新列名
            as_index=False
        ).agg(agg_rules)

        # 输出结果
        grouped_df.to_excel("Identification_match_result.xlsx", index=False)
        print(f"成功匹配到 {len(grouped_df)} 个化合物")
    else:
        print("没有匹配到任何结果")



