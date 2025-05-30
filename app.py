import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import base64
from PIL import Image
from database import (
    init_db, add_collection, add_seed_batch, generate_id,
    add_germination_record, add_germination_event, complete_germination_record,
    add_cultivation_record, add_cultivation_event, update_cultivation_status,
    batch_update_cultivation_status, update_collection_identification,
    save_image, get_images, generate_qrcode, generate_barcode,
    get_all_collections, get_collection_by_id, get_seed_batches,
    get_germination_records, get_germination_record_by_id, get_germination_events,
    get_cultivation_records, get_cultivation_record_by_id, get_cultivation_events,
    get_unidentified_collections, get_seed_batches_for_germination,
    update_collection, update_seed_batch, search_collections,
    get_germination_records_by_batch, get_seed_batch_by_id, update_image_description, delete_image,
    search_collections_by_taxonomy, get_cultivation_subgroups, add_cultivation_subgroup,
    get_fruiting_cultivations, add_seed_batch_from_cultivation,get_harvested_seeds,search_cultivation_records
)
import matplotlib.pyplot as plt
import json
#from backup_utils import create_backup  # 导入备份功能
import shutil
import sqlite3
import plotly.express as px

import matplotlib as mpl
from matplotlib.font_manager import FontProperties

# 解决方案1: 使用matplotlib内置的简体中文支持
def setup_matplotlib_chinese():
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.family'] = 'sans-serif'


# 调用此函数初始化matplotlib
setup_matplotlib_chinese()

# 初始化数据库
init_db()

# 设置页面配置，使其在移动设备上更友好
st.set_page_config(
    page_title="中科院武汉植物园-植物保育管理系统",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化会话状态变量
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = 0
if 'edit_collection_id' not in st.session_state:
    st.session_state['edit_collection_id'] = None
if 'identify_collection_id' not in st.session_state:
    st.session_state['identify_collection_id'] = None
if 'show_collection_details' not in st.session_state:
    st.session_state['show_collection_details'] = None



# 显示图片的函数
def show_image(file_path, caption=None, width=None):
    img = Image.open(file_path)
    st.image(img, caption=caption, width=width)


# 下载图片的函数
def get_binary_file_downloader_html(file_path, file_label='文件'):
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">{file_label}</a>'
    return href


def main():
    # 侧边栏标题
    st.sidebar.title("植物资源管理系统")

    # 从设置中获取组织名称
    settings = get_settings()
    organization_name = settings.get("organization_name", "植物资源库")
    st.sidebar.write(f"欢迎使用 {organization_name}")

    # 使用按钮代替radio按钮创建导航菜单
    if st.sidebar.button("首页", use_container_width=True):
        st.session_state.page = "首页"
    if st.sidebar.button("采集管理", use_container_width=True):
        st.session_state.page = "采集管理"
    if st.sidebar.button("种子管理", use_container_width=True):
        st.session_state.page = "种子管理"
    if st.sidebar.button("发芽实验", use_container_width=True):
        st.session_state.page = "发芽实验"
    if st.sidebar.button("栽培管理", use_container_width=True):
        st.session_state.page = "栽培管理"
    if st.sidebar.button("数据查询", use_container_width=True):
        st.session_state.page = "数据查询"
    if st.sidebar.button("图片管理", use_container_width=True):
        st.session_state.page = "图片管理"
    if st.sidebar.button("标签生成", use_container_width=True):
        st.session_state.page = "标签生成"
    if st.sidebar.button("备份与恢复", use_container_width=True):
        st.session_state.page = "备份与恢复"
    if st.sidebar.button("系统设置", use_container_width=True):
        st.session_state.page = "系统设置"

    # 初始化session_state
    if 'page' not in st.session_state:
        st.session_state.page = "首页"

    # 底部信息
    st.sidebar.markdown("---")
    st.sidebar.info("© 2025 植物资源管理系统 V3.2")

    # 根据选择显示不同页面
    if st.session_state.page == "首页":
        show_home()
    elif st.session_state.page == "采集管理":
        show_collection_management()
    elif st.session_state.page == "种子管理":
        show_seed_management()
    elif st.session_state.page == "发芽实验":
        show_germination_management()
    elif st.session_state.page == "栽培管理":
        show_cultivation_management()
    elif st.session_state.page == "数据查询":
        show_data_query()
    elif st.session_state.page == "图片管理":
        show_image_management()
    elif st.session_state.page == "备份与恢复":
        show_backup_restore()
    elif st.session_state.page == "系统设置":
        show_settings()
    elif st.session_state.page == "标签生成":
        show_label_generator()

def show_home():
    st.subheader("系统概况")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        collections_count = len(get_all_collections())
        st.info(f"🧪 采集记录: {collections_count}")
    with col2:
        seed_batches_count = len(get_seed_batches())
        st.info(f"🌱 种子批次: {seed_batches_count}")
    with col3:
        germination_count = len(get_germination_records())
        st.info(f"🌿 发芽实验: {germination_count}")
    with col4:
        cultivation_count = len(get_cultivation_records())
        st.info(f"🌳 栽培记录: {cultivation_count}")
    with col5:
        unidentified_count = len(get_unidentified_collections())
        st.warning(f"❓ 待鉴定: {unidentified_count}")

    # 修改以下统计图表部分
    st.markdown("---")

    # 显示一些统计图表
    st.subheader("数据统计")

    col1, col2 = st.columns(2)

    with col1:
        # 获取发芽率数据
        germination_records = get_germination_records()
        if germination_records:
            rates = [record.germination_rate for record in germination_records if record.germination_rate is not None]

            if rates:
                fig, ax = plt.subplots()
                ax.hist(rates, bins=10, range=(0, 1))
                ax.set_xlabel('发芽率')
                ax.set_ylabel('频率')
                ax.set_title('发芽率分布')
                st.pyplot(fig)
            else:
                st.write("暂无发芽率数据")
        else:
            st.write("暂无发芽记录")

    with col2:
        # 添加科属分布统计
        collections = get_all_collections()
        if collections:
            # 获取所有已鉴定的科属
            families = {}
            for collection in collections:
                if collection.family:
                    family = collection.family.strip()
                    if family in families:
                        families[family] += 1
                    else:
                        families[family] = 1

            if families:
                # 只显示top 10的科
                sorted_families = sorted(families.items(), key=lambda x: x[1], reverse=True)[:10]
                family_names = [f[0] for f in sorted_families]
                family_counts = [f[1] for f in sorted_families]

                fig, ax = plt.subplots()
                ax.barh(family_names, family_counts)
                ax.set_xlabel('数量')
                ax.set_ylabel('科')
                ax.set_title('植物科分布 (Top 10)')
                st.pyplot(fig)
            else:
                st.write("暂无科属分布数据")
        else:
            st.write("暂无采集记录")

    st.markdown("---")
    st.subheader("系统介绍")
    st.markdown("""
    本系统是植物保育全流程管理系统，涵盖以下主要功能：

    1. **野外采集管理**：记录野外采集的植物信息，包括采集地点、日期、采集人及植物分类信息等
    2. **种子管理**：管理从野外采集或其他来源的种子批次
    3. **发芽实验**：跟踪种子的发芽情况，记录发芽率
    4. **温室栽培**：管理幼苗的栽培过程，记录开花、结果、生长状态等
    5. **数据查询**：查询并分析各类数据
    6. **图片管理**：管理各阶段的植物图片
    7. **标签生成**：生成二维码或条形码标签，用于实物标记

    系统支持移动端访问，方便在温室等环境中使用。
    """)


def identify_collection(collection_id):
    """
    设置会话状态以鉴定指定的采集记录
    """
    st.session_state['identify_collection_id'] = collection_id
    st.session_state['active_tab'] = 3  # 假设鉴定采集记录是第4个选项卡(索引3)
    st.rerun()  # 重新运行应用以更新UI


def show_collection_management():
    st.subheader("野外采集管理")

    # 创建标签页
    tab_names = ["添加采集记录", "查看采集记录", "编辑采集记录", "植物鉴定"]
    tab1, tab2, tab3, tab4 = st.tabs(tab_names)

    # 确定当前激活的标签页 (仅用于决定默认显示哪个标签页，不再用于条件控制显示内容)
    active_tab = st.session_state.get('active_tab', 0)

    # 添加采集记录标签页
    with tab1:
        st.subheader("添加采集记录")

        # 基本信息部分 - 改为三列布局
        col1, col2, col3 = st.columns(3)
        with col1:
            collection_date = st.date_input("采集日期", datetime.datetime.now(), key="add_collection_date")
            latitude = st.number_input("纬度", format="%.6f", step=0.000001, key="add_latitude")
            country = st.text_input("国家（可选）", key="add_country")
        with col2:
            location = st.text_input("采集地点", key="add_location")
            longitude = st.number_input("经度", format="%.6f", step=0.000001, key="add_longitude")
            terrain = st.text_input("地形（可选）", key="add_terrain")
        with col3:
            collector = st.text_input("采集人", key="add_collector")
            altitude = st.number_input("海拔(米)", min_value=0.0, step=0.1, key="add_altitude")
            land_use = st.text_input("土地利用（可选）", key="add_land_use")
        # 编号和生境部分
        col1, col2 = st.columns(2)
        with col1:
            original_id = st.text_input("原始编号（可选）", key="add_original_id", help="如果有原始的采集编号，请在此填写")
            specimen_number = st.text_input("标本号（可选）", key="add_specimen_number")
        with col2:
            habitat = st.text_input("生境描述", key="add_habitat")
        # 土壤信息部分
        st.markdown("### 土壤信息（可选）")
        col1, col2 = st.columns(2)
        with col1:
            soil_parent_material = st.text_input("土壤母质", key="add_soil_parent_material")
        with col2:
            soil_texture = st.text_input("土壤质地", key="add_soil_texture")
        # 种子信息部分
        st.markdown("### 种子信息（可选）")
        col1, col2, col3 = st.columns(3)
        with col1:
            seed_harvest_period = st.text_input("收获种子时期", key="add_seed_harvest_period")
            seed_quantity = st.text_input("种子数量", key="add_seed_quantity")
        with col2:
            collection_part = st.text_input("采集部位", key="add_collection_part")
            seed_condition = st.text_input("种子状况", key="add_seed_condition")
        with col3:
            fruit_size = st.text_input("果实大小", key="add_fruit_size")
            fruit_color = st.text_input("果实颜色", key="add_fruit_color")
        # 备注
        notes = st.text_area("备注", key="add_notes")
        # 植物信息部分 - 改为三列布局
        st.markdown("### 植物信息（可选）")
        col1, col2, col3 = st.columns(3)
        with col1:
            species_chinese = st.text_input("中文种名", key="add_species_chinese")
            species_latin = st.text_input("拉丁学名 (Latin name)", key="add_species_latin")

        with col2:
            family_chinese = st.text_input("科中文名", key="add_family_chinese")
            family = st.text_input("科", key="add_family")
        with col3:
            genus_chinese = st.text_input("属中文名", key="add_genus_chinese")
            genus = st.text_input("属", key="add_genus")
            # 判断是否已鉴定
            identified = False
            if species_latin:
                identified = st.checkbox("已鉴定", value=True, key="add_identified")
                if identified:
                    identified_by = st.text_input("鉴定人", key="add_identified_by")

        if st.button("添加采集记录", key="add_collection_button"):
            if location and collector:
                # 添加采集记录
                collection_id = add_collection(
                    collection_date=collection_date,
                    location=location,
                    latitude=latitude,
                    longitude=longitude,
                    altitude=altitude,
                    collector=collector,
                    notes=notes,
                    habitat=habitat,
                    species_latin=species_latin,
                    species_chinese=species_chinese,
                    family=family,
                    family_chinese=family_chinese,
                    genus=genus,
                    genus_chinese=genus_chinese,
                    identified=identified,
                    original_id=original_id,
                    # 添加新字段
                    country=country,
                    terrain=terrain,
                    land_use=land_use,
                    soil_parent_material=soil_parent_material,
                    soil_texture=soil_texture,
                    seed_harvest_period=seed_harvest_period,
                    collection_part=collection_part,
                    seed_quantity=seed_quantity,
                    seed_condition=seed_condition,
                    fruit_size=fruit_size,
                    fruit_color=fruit_color,
                    specimen_number=specimen_number
                )
                if collection_id:
                    st.success(f"采集记录添加成功！采集编号: {collection_id}")
                    # 在添加成功后清空表单
                    st.rerun()
                else:
                    st.error("添加采集记录失败")
            else:
                st.warning("请至少填写采集地点和采集人")

        # 图片上传部分
        st.markdown("### 上传采集图片")
        st.write("采集记录创建后，可在'查看采集记录'标签页中上传图片")

    # 查看采集记录标签页
    with tab2:
        st.subheader("查看采集记录")

        # 添加搜索和筛选功能
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("搜索(采集编号/地点/采集人)", key="search_collection")
        with col2:
            identification_status = st.selectbox("鉴定状态", ["全部", "已鉴定", "未鉴定"], key="filter_identification")

        # 获取采集记录
        collections = get_all_collections()

        if collections:
            # 根据搜索词过滤
            if search_term:
                collections = [c for c in collections if search_term.lower() in c.collection_id.lower() or
                               (c.location and search_term.lower() in c.location.lower()) or
                               (c.collector and search_term.lower() in c.collector.lower())]

            # 根据鉴定状态过滤
            if identification_status == "已鉴定":
                collections = [c for c in collections if c.identified]
            elif identification_status == "未鉴定":
                collections = [c for c in collections if not c.identified]

            # 创建表格数据
            collection_data = []
            for collection in collections:
                collection_data.append({
                    "采集编号": collection.collection_id,
                    "采集人": collection.collector,
                    "采集日期": collection.collection_date,
                    "地点": collection.location,
                    "Species": collection.species_latin or '',
                    "鉴定状态": "已鉴定" if collection.identified else "未鉴定",
                    "id": collection.id  # 隐藏ID列
                })

            # 创建DataFrame
            df = pd.DataFrame(collection_data)

            # 显示基本表格
            st.dataframe(df.drop(columns=["id"]), use_container_width=True)

            # 方案2：重新查询数据库获取完整字段信息
            if not df.empty:
                # 获取当前筛选数据的ID列表
                filtered_ids = df['id'].tolist()

                # 调试信息
                st.write(f"筛选到的记录数量: {len(filtered_ids)}")

                # 获取当前脚本所在目录的绝对路径
                import os
                BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                DB_PATH = os.path.join(BASE_DIR, 'plant_conservation.db')


                # 尝试直接查询一个ID以检查表结构
                try:
                    conn = sqlite3.connect(DB_PATH)  # 使用绝对路径
                    # 查询数据库中的所有表
                    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)

                    # 确认正确的表名
                    correct_table = 'collections'
                    if correct_table in tables['name'].tolist():
                        columns = pd.read_sql(f"PRAGMA table_info({correct_table});", conn)

                        # 尝试使用IN查询
                        test_id = filtered_ids[0]
                        test_query = f"SELECT * FROM {correct_table} WHERE id = {test_id}"
                        test_result = pd.read_sql(test_query, conn)


                    else:
                        st.error(f"数据库中没有找到 {correct_table} 表！")

                    conn.close()
                except Exception as e:
                    st.error(f"检查表结构时出错: {str(e)}")

                # 重新定义获取完整记录的函数，使用绝对路径和正确的表名
                def get_complete_records(record_ids):
                    try:
                        conn = sqlite3.connect(DB_PATH)  # 使用绝对路径
                        correct_table = 'collections'  # 确保使用正确的表名

                        # 首先检查表是否存在
                        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
                        if correct_table not in tables['name'].tolist():
                            st.error(f"数据库中没有找到 {correct_table} 表！")
                            conn.close()
                            return pd.DataFrame()

                        all_results = []

                        # 使用正确的表名查询
                        placeholders = ','.join(['?'] * len(record_ids))
                        query = f"SELECT * FROM {correct_table} WHERE id IN ({placeholders})"

                        try:
                            # 尝试使用参数化查询一次获取所有数据
                            result = pd.read_sql_query(query, conn, params=record_ids)
                            if not result.empty:
                                return result

                            # 如果批量查询失败，回退到单个ID查询
                            for record_id in record_ids:
                                single_query = f"SELECT * FROM {correct_table} WHERE id = ?"
                                result = pd.read_sql_query(single_query, conn, params=[record_id])
                                if not result.empty:
                                    all_results.append(result)

                            if all_results:
                                complete_df = pd.concat(all_results, ignore_index=True)
                                st.write(f"成功查询到 {len(complete_df)} 条记录")
                                return complete_df
                            else:
                                st.warning("未找到任何匹配记录")
                                return pd.DataFrame()
                        except Exception as e:
                            st.error(f"执行查询时出错: {str(e)}")
                            return pd.DataFrame()
                    except Exception as e:
                        st.error(f"查询出错: {str(e)}")
                        return pd.DataFrame()
                    finally:
                        if 'conn' in locals():
                            conn.close()

                # 调用函数获取完整字段数据
                export_df = get_complete_records(filtered_ids)

                if not export_df.empty:
                    # 仅删除id列（如果存在且需要）
                    if "id" in export_df.columns and len(export_df.columns) > 1:
                        export_df = export_df.drop(columns=["id"])

                    # 转换为CSV，确保使用正确的编码
                    csv = export_df.to_csv(index=False).encode('utf-8-sig')

                    # 创建下载按钮
                    st.download_button(
                        label="导出所有字段数据",
                        data=csv,
                        file_name=f"采集记录完整导出_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )

                st.markdown("---")




            # 检查是否需要显示详情
            if 'show_collection_details' in st.session_state and st.session_state['show_collection_details']:
                collection_id = st.session_state['show_collection_details']
                collection = get_collection_by_id(collection_id)
                if collection:
                    st.markdown("---")
                    st.markdown("### 采集记录详情")
                    # Basic information
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**采集编号:** {collection.collection_id}")
                        st.write(f"**采集日期:** {collection.collection_date}")
                        st.write(f"**采集地点:** {collection.location}")
                        st.write(f"**海拔:** {collection.altitude}米")
                        st.write(f"**采集人:** {collection.collector}")

                    with col2:
                        st.write(f"**经纬度:** {collection.latitude}, {collection.longitude}")
                        st.write(f"**生境描述:** {collection.habitat or '未记录'}")
                        st.write(f"**鉴定状态:** {'已鉴定' if collection.identified else '未鉴定'}")
                        if collection.identified:
                            st.write(f"**鉴定人:** {collection.identified_by or '未记录'}")

                    # Notes
                    if collection.notes:
                        st.write("**备注:**")
                        st.write(collection.notes)

                    # Plant information
                    st.markdown("### 植物信息")
                    if collection.species_latin or collection.species_chinese or collection.family or collection.genus:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**中文名:** {collection.species_chinese or '未记录'}")
                            st.write(f"**科:** {collection.family or '未记录'}")
                        with col2:
                            st.write(f"**拉丁学名:** {collection.species_latin or '未记录'}")
                            st.write(f"**属:** {collection.genus or '未记录'}")

                        if collection.species_latin:
                            st.write(f"**种:** {collection.species_latin}")

                        if collection.identification_notes:
                            st.write("**鉴定备注:**")
                            st.write(collection.identification_notes)
                    else:
                        st.write("暂无植物分类信息")

                    # Images
                    images = get_images("collection", collection_id)
                    if images:
                        st.markdown("### 采集图片")
                        image_cols = st.columns(min(3, len(images)))
                        for i, image in enumerate(images):
                            with image_cols[i % len(image_cols)]:
                                show_image(image.file_path, caption=image.description, width=250)

                    # Button to close details
                    if st.button("关闭详情"):
                        st.session_state.pop('show_collection_details', None)
                        st.rerun()

                    st.markdown("---")

            # 选择记录进行操作
            selected_id = st.selectbox(
                "选择采集记录进行操作",
                options=df["id"].tolist(),
                format_func=lambda x: next(
                    (f"{c['采集编号']} - {c['地点']} ({c['采集日期']})" for c in collection_data if c["id"] == x), ""),
                key="selected_collection_for_action"
            )

            # 显示操作按钮
            if selected_id:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("查看详情"):
                        st.session_state['show_collection_details'] = selected_id
                        st.rerun()
                with col2:
                    if st.button("编辑记录"):
                        st.session_state['edit_collection_id'] = selected_id
                        st.session_state['active_tab'] = 2
                        st.rerun()
                with col3:
                    selected_collection = next((c for c in collections if c.id == selected_id), None)
                    if selected_collection and not selected_collection.identified:
                        if st.button("鉴定"):
                            st.session_state['identify_collection_id'] = selected_id
                            st.session_state['active_tab'] = 3
                            st.rerun()
                    else:
                        st.button("已鉴定", disabled=True)

                st.subheader("上传采集图片")
                uploaded_file = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"],
                                                 key=f"collection_upload_{selected_id}",
                                                 accept_multiple_files=True)
                image_description = st.text_input("图片描述", key=f"collection_img_desc_{selected_id}")

                if uploaded_file and st.button("上传图片", key=f"upload_collection_img_{selected_id}"):
                    image_id = save_image(uploaded_file, "collection", selected_id, image_description)
                    if image_id:
                        st.success("图片上传成功！")
                        st.rerun()
                    else:
                        st.error("图片上传失败")

        else:
            st.info("暂无采集记录。请先添加采集记录。")

    # 编辑采集记录标签页
    with tab3:
        show_edit_collection_form()

    # 植物鉴定标签页
    with tab4:
        show_identify_collection_form()


def edit_collection(collection_id):
    """
    设置会话状态以编辑指定的采集记录
    """
    st.session_state['edit_collection_id'] = collection_id
    st.session_state['active_tab'] = 2  # 假设编辑采集记录是第3个选项卡(索引2)
    st.rerun()  # 重新运行应用以更新UI


def show_edit_collection_form():
    """
    显示编辑采集记录的表单
    """
    # 检查是否有从查看页面传递过来的编辑ID
    edit_collection_id = st.session_state.get('edit_collection_id', None)

    if edit_collection_id:
        collection = get_collection_by_id(edit_collection_id)

        if collection:
            st.write(f"正在编辑采集记录: {collection.collection_id}")

            # 基本信息部分 - 改为三列布局
            col1, col2, col3 = st.columns(3)
            with col1:
                collection_date = st.date_input("采集日期", collection.collection_date, key="edit_collection_date")
                latitude = st.number_input("纬度", format="%.6f", step=0.000001, value=collection.latitude,
                                           key="edit_latitude")
                country = st.text_input("国家（可选）", getattr(collection, 'country', ''), key="edit_country")
            with col2:
                location = st.text_input("采集地点", collection.location, key="edit_location")
                longitude = st.number_input("经度", format="%.6f", step=0.000001, value=collection.longitude,
                                            key="edit_longitude")
                terrain = st.text_input("地形（可选）", getattr(collection, 'terrain', ''), key="edit_terrain")
            with col3:
                collector = st.text_input("采集人", collection.collector, key="edit_collector")
                altitude = st.number_input("海拔(米)", min_value=0.0, step=0.1, value=collection.altitude,
                                           key="edit_altitude")
                land_use = st.text_input("土地利用（可选）", getattr(collection, 'land_use', ''), key="edit_land_use")

            # 编号和生境部分
            col1, col2 = st.columns(2)
            with col1:
                original_id = st.text_input("原始编号（可选）", getattr(collection, 'original_id', ''),
                                            key="edit_original_id")
                specimen_number = st.text_input("标本号（可选）", getattr(collection, 'specimen_number', ''),
                                                key="edit_specimen_number")
            with col2:
                habitat = st.text_input("生境描述", collection.habitat or "", key="edit_habitat")

            # 土壤信息部分
            st.markdown("### 土壤信息（可选）")
            col1, col2 = st.columns(2)
            with col1:
                soil_parent_material = st.text_input("土壤母质", getattr(collection, 'soil_parent_material', ''),
                                                     key="edit_soil_parent_material")
            with col2:
                soil_texture = st.text_input("土壤质地", getattr(collection, 'soil_texture', ''),
                                             key="edit_soil_texture")

            # 种子信息部分
            st.markdown("### 种子信息（可选）")
            col1, col2, col3 = st.columns(3)
            with col1:
                seed_harvest_period = st.text_input("收获种子时期", getattr(collection, 'seed_harvest_period', ''),
                                                    key="edit_seed_harvest_period")
                seed_quantity = st.text_input("种子数量", getattr(collection, 'seed_quantity', ''),
                                              key="edit_seed_quantity")
            with col2:
                collection_part = st.text_input("采集部位", getattr(collection, 'collection_part', ''),
                                                key="edit_collection_part")
                seed_condition = st.text_input("种子状况", getattr(collection, 'seed_condition', ''),
                                               key="edit_seed_condition")
            with col3:
                fruit_size = st.text_input("果实大小", getattr(collection, 'fruit_size', ''), key="edit_fruit_size")
                fruit_color = st.text_input("果实颜色", getattr(collection, 'fruit_color', ''), key="edit_fruit_color")

            # 备注
            notes = st.text_area("备注", collection.notes or "", key="edit_notes")

            # 植物信息部分 - 改为三列布局
            st.markdown("### 植物信息（可选）")
            col1, col2, col3 = st.columns(3)
            with col1:
                species_chinese = st.text_input("中文种名", getattr(collection, 'species_chinese', ''),
                                                     key="edit_species_chinese")
                species_latin = st.text_input("拉丁学名 (Latin name)", collection.species_latin or "",
                                                key="edit_species_latin")

            with col2:
                genus_chinese = st.text_input("属中文名", getattr(collection, 'genus_chinese', ''),
                                              key="edit_genus_chinese")
                genus = st.text_input("属", collection.genus or "", key="edit_genus")
            with col3:
                family_chinese = st.text_input("科中文名", getattr(collection, 'family_chinese', ''),
                                               key="edit_family_chinese")
                family = st.text_input("科", collection.family or "", key="edit_family")


                # 判断是否已鉴定
                identified = st.checkbox("已鉴定", value=collection.identified, key="edit_identified")
                if identified:
                    identified_by = st.text_input("鉴定人", collection.identified_by or "", key="edit_identified_by")

            # 保存和取消按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("保存更改", key="save_edit_collection"):
                    update_data = {
                        "collection_date": collection_date,
                        "location": location,
                        "latitude": latitude,
                        "longitude": longitude,
                        "altitude": altitude,
                        "collector": collector,
                        "notes": notes,
                        "habitat": habitat,
                        "species_latin": species_latin,
                        "family": family,
                        "family_chinese": family_chinese,
                        "genus": genus,
                        "genus_chinese": genus_chinese,
                        "identified": identified,
                        "original_id": original_id,
                        "country": country,
                        "species_chinese": species_chinese,
                        "terrain": terrain,
                        "land_use": land_use,
                        "soil_parent_material": soil_parent_material,
                        "soil_texture": soil_texture,
                        "seed_harvest_period": seed_harvest_period,
                        "collection_part": collection_part,
                        "seed_quantity": seed_quantity,
                        "seed_condition": seed_condition,
                        "fruit_size": fruit_size,
                        "fruit_color": fruit_color,
                        "specimen_number": specimen_number
                    }

                    if identified:
                        update_data["identified_by"] = identified_by

                    # 更新采集记录
                    if update_collection(edit_collection_id, **update_data):
                        st.success("采集记录更新成功!")
                        st.session_state.pop('edit_collection_id', None)
                        st.session_state['active_tab'] = 1  # 切换回查看标签页
                        st.rerun()
                    else:
                        st.error("更新采集记录失败")

            with col2:
                if st.button("取消编辑", key="cancel_edit_collection"):
                    st.session_state.pop('edit_collection_id', None)
                    st.session_state['active_tab'] = 1  # 回到查看标签页
                    st.rerun()
        else:
            st.error(f"未找到ID为 {edit_collection_id} 的采集记录")
            if st.button("返回", key="return_from_edit"):
                st.session_state.pop('edit_collection_id', None)
                st.session_state['active_tab'] = 1  # 回到查看标签页
                st.rerun()
    else:
        # 如果没有选择记录，显示选择框
        collections = get_all_collections()
        if collections:
            collection_options = {
                f"{collection.collection_id} - {collection.location} ({collection.collection_date})": collection.id
                for collection in collections
            }
            selected_collection = st.selectbox("选择采集记录进行编辑", list(collection_options.keys()),
                                               key="edit_collection_select")
            if selected_collection:
                st.session_state['edit_collection_id'] = collection_options[selected_collection]
                st.rerun()
        else:
            st.info("目前没有采集记录")


def show_identify_collection_form():
    """
    显示鉴定采集记录的表单
    """
    # 检查是否有从查看页面传递过来的鉴定ID
    identify_collection_id = st.session_state.get('identify_collection_id', None)

    if identify_collection_id:
        collection = get_collection_by_id(identify_collection_id)

        if collection and not collection.identified:
            st.write(f"正在鉴定采集记录: {collection.collection_id}")

            # 植物信息表单
            st.markdown("### 植物鉴定信息")
            col1, col2, col3 = st.columns(3)
            with col1:
                species_chinese = st.text_input("种中文名", getattr(collection, 'species_chinese', ''),
                                                     key="identify_species_chinese")
                genus_chinese = st.text_input("属中文名", getattr(collection, 'genus_chinese', ''),
                                              key="identify_genus_chinese")
                family_chinese = st.text_input("科中文名", getattr(collection, 'family_chinese', ''),
                                               key="identify_family_chinese")

            with col2:
                species_latin = st.text_input("拉丁学名", collection.species_latin or "",
                                                key="identify_species_latin")
                genus = st.text_input("属", collection.genus or "", key="identify_genus")
                family = st.text_input("科", collection.family or "", key="identify_family")
            with col3:

                identified_by = st.text_input("鉴定人", key="identify_identified_by")

            # 鉴定备注
            identification_notes = st.text_area("鉴定备注", key="identify_notes")

            # 保存和取消按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("保存鉴定信息", key="save_identification"):
                    if species_latin:
                        # 更新鉴定信息
                        if update_collection_identification(
                                identify_collection_id,
                                species_latin=species_latin,
                                family=family,
                                family_chinese=family_chinese,
                                genus=genus,
                                genus_chinese=genus_chinese,
                                identified_by=identified_by,
                                identification_notes=identification_notes,
                                species_chinese=species_chinese
                        ):
                            st.success("植物鉴定信息更新成功!")
                            st.session_state.pop('identify_collection_id', None)
                            st.session_state['active_tab'] = 1  # 切换回查看标签页
                            st.rerun()
                        else:
                            st.error("更新鉴定信息失败")
                    else:
                        st.warning("请至少填写拉丁学名")

            with col2:
                if st.button("取消鉴定", key="cancel_identification"):
                    st.session_state.pop('identify_collection_id', None)
                    st.session_state['active_tab'] = 1  # 回到查看标签页
                    st.rerun()
        else:
            st.warning("选择的记录不存在或已经被鉴定")
            if st.button("返回", key="return_from_identify"):
                st.session_state.pop('identify_collection_id', None)
                st.session_state['active_tab'] = 1  # 回到查看标签页
                st.rerun()
    else:
        # 获取未鉴定的采集记录
        unidentified_collections = get_unidentified_collections()

        if unidentified_collections:
            st.write(f"共有 {len(unidentified_collections)} 条未鉴定的采集记录")

            # 创建选择框
            collection_options = {
                f"{collection.collection_id} - {collection.location} ({collection.collection_date})": collection.id
                for collection in unidentified_collections
            }

            selected_collection = st.selectbox("选择采集记录进行鉴定",
                                               list(collection_options.keys()),
                                               key="identify_collection_select")

            if selected_collection:
                st.session_state['identify_collection_id'] = collection_options[selected_collection]
                st.rerun()
        else:
            st.info("目前没有未鉴定的采集记录")


def show_seed_management():
    st.header("种子批次管理")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["添加种子批次", "查看种子批次", "编辑种子批次", "种子发芽记录", "批量发芽实验"])

    with tab1:
        st.subheader("添加种子批次")

        # 基本信息布局优化 - 使用三列布局
        col1, col2, col3 = st.columns(3)
        with col1:
            # 自动生成批次编号
            today = datetime.datetime.now().strftime("%Y%m%d")
            existing_batches = get_seed_batches()
            today_batches = [b for b in existing_batches if b.batch_id.startswith(today)]
            batch_id = f"{today}{str(len(today_batches) + 1).zfill(3)}"
            st.markdown(f"### 批次编号: {batch_id}")

            seed_id = st.text_input("种子编号", key="add_seed_id", help="请输入您的种子编号")
        with col2:
            storage_date = st.date_input("存储日期", value=datetime.datetime.now(), key="add_seed_storage_date")
            weight = st.number_input("重量 (g)", min_value=0.0, format="%.2f", key="add_seed_weight")
        with col3:
            storage_location = st.text_input("存储位置", key="add_seed_storage_location")
            estimated_count = st.number_input("估计数量", min_value=0, key="add_seed_estimated_count")

        # 质量检测结果单独放置
        testing_quality = st.number_input("质量检测结果 (%)", min_value=0.0, max_value=100.0, format="%.1f",
                                          key="add_seed_testing_quality")

        # 种子来源选项
        source_option = st.radio("种子来源", ["野外采集", "其他来源"], key="add_seed_source_radio", horizontal=True)
        collection_id = None

        if source_option == "野外采集":
            collections = get_all_collections()
            if collections:
                collection_options = {
                    f"{collection.collection_id} - {collection.location} ({collection.collection_date}) - {collection.species_chinese or collection.species_latin or '未命名'}": collection.id
                    for collection in collections}
                selected_collection = st.selectbox("选择采集记录",
                                                   list(collection_options.keys()),
                                                   key="add_seed_collection_select")
                collection_id = collection_options[selected_collection]

                # 获取选中的采集记录，显示其植物信息
                selected_collection_obj = next((c for c in collections if c.id == collection_id), None)
                if selected_collection_obj and (
                        selected_collection_obj.species_chinese or selected_collection_obj.species_latin):
                    st.info(
                        f"植物信息: {selected_collection_obj.species_chinese or ''} {selected_collection_obj.species_latin or ''} "
                        f"{selected_collection_obj.family or ''} {selected_collection_obj.genus or ''}")
            else:
                st.warning("目前没有采集记录，请先添加采集记录或选择其他来源")

        # 如果是其他来源，需要手动输入种子名称 - 使用两列布局
        species_chinese = ""
        species_latin = ""
        if source_option == "其他来源":
            col1, col2 = st.columns(2)
            with col1:
                species_chinese = st.text_input("种子名称", key="add_seed_species_chinese")
            with col2:
                species_latin = st.text_input("拉丁学名", key="add_seed_species_latin")

        # 描述单独放置
        description = st.text_area("描述", key="add_seed_description")

        if st.button("保存种子批次", key="save_seed_batch_btn"):
            if source_option == "野外采集" and not collection_id:
                st.error("请选择采集记录")
            else:
                # 使用add_seed_batch函数添加种子批次
                viability = testing_quality / 100 if testing_quality else None
                # 将额外信息添加到notes中
                notes_text = f"重量(g): {weight}\n{description}"
                seed_batch_id = add_seed_batch(
                    collection_id=collection_id,
                    quantity=estimated_count,
                    storage_location=storage_location,
                    storage_date=storage_date,
                    viability=viability,
                    notes=notes_text,
                    source="野外采集" if collection_id else "其他来源",
                    seed_id=seed_id  # 添加种子编号
                )
                if seed_batch_id:
                    # 尝试更新种子批次的额外信息
                    if seed_batch_id and collection_id:
                        collection = get_collection_by_id(collection_id)
                        if collection:
                            update_seed_batch(
                                batch_id=seed_batch_id,
                                species_chinese=collection.species_chinese,
                                species_latin=collection.species_latin
                            )
                    try:
                        # 如果是野外采集，从采集记录获取植物信息
                        if source_option == "野外采集" and selected_collection_obj:
                            species_chinese = selected_collection_obj.species_chinese or ""
                            species_latin = selected_collection_obj.species_latin or ""

                        update_seed_batch(
                            batch_id=seed_batch_id,
                            species_chinese=species_chinese,
                            species_latin=species_latin,
                            weight=weight
                        )
                    except Exception as e:
                        st.warning(f"添加额外信息失败，但基本信息已保存：{e}")
                    st.success(f"种子批次 {batch_id} 已成功添加")
                    # 清空表单
                    st.rerun()
                else:
                    st.error("添加种子批次失败")

    with tab2:
        st.subheader("查看种子批次")

        # 搜索框
        filter_species = st.text_input("按种子名称搜索", key="search_seed_species")

        # 获取种子批次
        seed_batches = get_seed_batches(filter_species)

        if not seed_batches:
            st.info("没有找到种子批次记录")
        else:
            # 显示批次总数
            st.write(f"共找到 {len(seed_batches)} 个种子批次")

            # 创建一个展开栏来显示每个批次的详细信息
            for batch in seed_batches:
                with st.expander(f"批次 {batch.batch_id} - {getattr(batch, 'species_chinese', '未命名')}"):
                    # 使用三列布局显示批次信息
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write("**基本信息**")
                        st.write(f"批次ID: {batch.batch_id}")
                        if hasattr(batch, 'seed_id') and batch.seed_id:
                            st.write(f"种子编号: {batch.seed_id}")
                        st.write(f"种子名称: {getattr(batch, 'species_chinese', '未记录')}")
                        st.write(f"拉丁名: {getattr(batch, 'species_latin', '未记录')}")
                        st.write(f"来源: {batch.source or '未记录'}")

                        if batch.collection_id:
                            collection = get_collection_by_id(batch.collection_id)
                            if collection:
                                st.write(f"采集地点: {collection.location}")
                                st.write(f"采集日期: {collection.collection_date}")

                    with col2:
                        st.write("**存储信息**")
                        st.write(f"存储位置: {batch.storage_location or '未记录'}")
                        st.write(f"存储日期: {batch.storage_date}")
                        st.write(f"数量: {batch.quantity or '未记录'}")
                        st.write(f"重量: {getattr(batch, 'weight', '未记录')} g")
                        st.write(
                            f"活力: {f'{batch.viability * 100:.1f}%' if batch.viability is not None else '未记录'}")

                    with col3:
                        st.write("**使用情况**")
                        # 计算已用于发芽的种子数量
                        germination_records = get_germination_records_by_batch(batch.id)
                        used_for_germination = sum(
                            record.quantity_used for record in germination_records) if germination_records else 0

                        # 这里应该有一个获取栽培记录的函数，类似于get_cultivation_records_by_batch
                        # used_for_cultivation = sum(record.quantity for record in cultivation_records) if cultivation_records else 0
                        used_for_cultivation = 0  # 临时使用0

                        remaining = batch.quantity - (
                                used_for_germination + used_for_cultivation) if batch.quantity else "未知"

                        st.write(f"发芽实验使用: {used_for_germination}")
                        st.write(f"栽培使用: {used_for_cultivation}")
                        st.write(f"剩余数量: {remaining}")

                    # 显示备注
                    if batch.notes:
                        st.write("**备注**")
                        st.write(batch.notes)

                    # 显示发芽记录
                    if germination_records:
                        st.write("**发芽记录**")
                        for record in germination_records:
                            st.write(f"{record.start_date} - 使用{record.quantity_used}粒 - " +
                                     f"发芽率: {record.germination_rate * 100:.1f}% ({record.germinated_count}/{record.quantity_used})")

                    # 操作按钮 - 使用两列布局
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"编辑", key=f"edit_batch_{batch.id}"):
                            st.session_state['edit_seed_batch_id'] = batch.id
                            st.session_state['active_tab'] = 2  # 切换到编辑标签页
                            st.rerun()

                    with col2:
                        if st.button(f"添加发芽记录", key=f"add_germination_{batch.id}"):
                            st.session_state['new_germination_batch_id'] = batch.id
                            st.session_state['active_tab'] = 3  # 切换到发芽记录标签页
                            st.rerun()

    with tab3:
        st.subheader("编辑种子批次")

        # 检查是否有选定的种子批次ID
        edit_seed_batch_id = st.session_state.get('edit_seed_batch_id', None)

        if edit_seed_batch_id:
            # 获取要编辑的种子批次
            batch = get_seed_batch_by_id(edit_seed_batch_id)

            if batch:
                st.write(f"正在编辑批次 {batch.batch_id}")

                # 提取当前值，如果属性不存在则使用默认值
                current_seed_id = getattr(batch, 'seed_id', '')
                current_species_chinese = getattr(batch, 'species_chinese', '')
                current_species_latin = getattr(batch, 'species_latin', '')
                current_storage_location = batch.storage_location or ''
                current_quantity = batch.quantity or 0
                current_viability = batch.viability * 100 if batch.viability is not None else 0
                current_weight = getattr(batch, 'weight', 0.0)
                current_notes = batch.notes or ''

                # 编辑表单 - 使用三列布局
                col1, col2, col3 = st.columns(3)
                with col1:
                    seed_id = st.text_input("种子编号", value=current_seed_id, key="edit_seed_id")
                    storage_location = st.text_input("存储位置", value=current_storage_location,
                                                     key="edit_seed_storage_location")
                with col2:
                    species_chinese = st.text_input("种子名称", value=current_species_chinese, key="edit_seed_species_chinese")
                    quantity = st.number_input("数量", value=current_quantity, min_value=0, key="edit_seed_quantity")
                with col3:
                    species_latin = st.text_input("拉丁学名", value=current_species_latin,
                                                  key="edit_seed_species_latin")
                    viability = st.number_input("活力 (%)", value=float(current_viability), min_value=0.0, max_value=100.0,
                                                format="%.1f", key="edit_seed_viability")

                # 重量单独放置
                weight = st.number_input("重量 (g)", value=current_weight, min_value=0.0, format="%.2f",
                                         key="edit_seed_weight")

                # 备注单独放置
                notes = st.text_area("备注", value=current_notes, key="edit_seed_notes")

                # 使用两列布局放置按钮
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("保存更改", key="save_seed_edit"):
                        try:
                            # 更新数据
                            update_data = {
                                'seed_id': seed_id,
                                'storage_location': storage_location,
                                'quantity': quantity,
                                'viability': viability / 100,
                                'notes': notes
                            }

                            # 尝试更新额外字段
                            try:
                                update_data['species_chinese'] = species_chinese
                                update_data['species_latin'] = species_latin
                                update_data['weight'] = weight
                            except Exception:
                                # 如果额外字段更新失败，将它们添加到notes中
                                if species_chinese != current_species_chinese or species_latin != current_species_latin or weight != current_weight:
                                    update_data[
                                        'notes'] = f"种子名称: {species_chinese}\n拉丁学名: {species_latin}\n重量(g): {weight}\n{notes}"

                            # 更新种子批次
                            update_seed_batch(edit_seed_batch_id, **update_data)

                            st.success("种子批次更新成功")
                            # 清除编辑状态
                            st.session_state.pop('edit_seed_batch_id', None)
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新失败: {e}")

                with col2:
                    if st.button("取消", key="cancel_seed_edit"):
                        st.session_state.pop('edit_seed_batch_id', None)
                        st.rerun()

                if st.button("从采集记录更新物种信息"):
                    if batch.collection_id:
                        collection = get_collection_by_id(batch.collection_id)
                        if collection:
                            # 直接更新数据库
                            update_data = {
                                'species_chinese': collection.species_chinese,
                                'species_latin': collection.species_latin
                            }
                            update_seed_batch(edit_seed_batch_id, **update_data)
                            st.success("已从采集记录更新物种信息")
                            st.rerun()
            else:
                st.error("未找到指定的种子批次")
        else:
            st.info("请在查看种子批次页面选择一个批次进行编辑")

    with tab4:
        st.subheader("种子发芽记录")

        # 检查是否有选定的种子批次来添加发芽记录
        new_germination_batch_id = st.session_state.get('new_germination_batch_id', None)

        # 添加新发芽记录表单
        with st.expander("添加新发芽记录", expanded=new_germination_batch_id is not None):
            # 如果已经选择了批次，直接使用它；否则显示下拉选择框
            if new_germination_batch_id:
                selected_batch = get_seed_batch_by_id(new_germination_batch_id)
                if selected_batch:
                    st.write(
                        f"为批次 {selected_batch.batch_id} - {getattr(selected_batch, 'species_chinese', '未命名')} 添加发芽记录")
                    seed_batch_id = selected_batch.id
                else:
                    st.error("未找到指定的种子批次")
                    seed_batch_id = None
            else:
                # 获取可用于发芽的种子批次
                available_batches = get_seed_batches_for_germination()

                if not available_batches:
                    st.warning("没有可用的种子批次，请先添加种子批次")
                    seed_batch_id = None
                else:
                    batch_options = {
                        f"{batch.batch_id} - {getattr(batch, 'species_chinese', '未命名')} (可用: {getattr(batch, 'available_quantity', '未知')})": batch.id
                        for batch in available_batches
                    }
                    selected_batch = st.selectbox("选择种子批次", list(batch_options.keys()),
                                                  key="select_germination_batch")
                    seed_batch_id = batch_options[selected_batch]

            if seed_batch_id:
                # 发芽记录表单 - 使用三列布局
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("开始日期", value=datetime.datetime.now(), key="germination_start_date")

                with col2:
                    # 获取选定批次的可用种子数量并确保是整数
                    selected_batch = get_seed_batch_by_id(seed_batch_id)
                    max_seeds = getattr(selected_batch, 'available_quantity', None)

                    # 确保max_seeds是有效的整数
                    if max_seeds is None or not isinstance(max_seeds, int) or max_seeds <= 0:
                        max_seeds = 1000  # 默认值

                    # 计算默认值，确保不会超过最大值
                    default_quantity = min(50, max_seeds)

                    quantity_used = st.number_input("使用种子数量", min_value=1, max_value=max_seeds,
                                                    value=default_quantity, key="germination_quantity")

                # 处理方法和备注单独放置
                treatment = st.text_area("处理方法", key="germination_treatment")
                notes = st.text_area("备注", key="germination_notes")

                if st.button("保存发芽记录", key="save_germination_record"):
                    # 添加发芽记录
                    record_id = add_germination_record(
                        seed_batch_id=seed_batch_id,
                        start_date=start_date,
                        treatment=treatment,
                        quantity_used=quantity_used,
                        notes=notes
                    )

                    if record_id:
                        st.success("发芽记录添加成功")
                        # 清除选定的批次ID
                        st.session_state.pop('new_germination_batch_id', None)
                        st.rerun()
                    else:
                        st.error("添加发芽记录失败")

        # 显示现有发芽记录
        filter_germination_species = st.text_input("按种子名称搜索发芽记录", key="search_germination_species")

        germination_records = get_germination_records(filter_germination_species)

        if not germination_records:
            st.info("没有找到发芽记录")
        else:
            st.write(f"共找到 {len(germination_records)} 条发芽记录")

            # 创建表格显示发芽记录
            records_data = []
            for record in germination_records:
                # 获取种子批次信息
                batch = get_seed_batch_by_id(record.seed_batch_id)
                species_chinese = getattr(batch, 'species_chinese', '未知') if batch else '未知'

                # 格式化状态和发芽率
                status = record.status
                germination_rate = f"{record.germination_rate * 100:.1f}%" if record.germination_rate is not None else "0.0%"
                germinated_count = record.germinated_count or 0

                records_data.append({
                    "ID": record.germination_id,
                    "种子名称": species_chinese,
                    "开始日期": record.start_date,
                    "种子数量": record.quantity_used,
                    "已发芽": germinated_count,
                    "发芽率": germination_rate,
                    "状态": status,
                    "处理方法": record.treatment if len(record.treatment or '') < 30 else record.treatment[:30] + "...",
                    "详情": "查看"
                })

            # 创建DataEditor或DataFrame进行显示
            if hasattr(st, 'data_editor'):
                # Streamlit 1.16.0+
                st.data_editor(
                    records_data,
                    hide_index=True,
                    key="germination_records_table"
                )

                # 添加选择和查看详情按钮
                selected_idx = st.selectbox(
                    "选择记录查看详情",
                    range(len(records_data)),
                    format_func=lambda i: f"{records_data[i]['ID']} - {records_data[i]['种子名称']}"
                )

                if st.button("查看详情", key="view_details_button"):
                    selected_id = records_data[selected_idx]["ID"]
                    for record in germination_records:
                        if record.germination_id == selected_id:
                            show_germination_record_details(record)
                            break
            else:
                # 旧版Streamlit，使用DataFrame
                st.dataframe(records_data)

                # 选择记录查看详情
                record_options = {
                    f"{record.germination_id} - {getattr(get_seed_batch_by_id(record.seed_batch_id), 'species_chinese', '未知')}": record.id
                    for record in germination_records
                }
                selected_record = st.selectbox("选择记录查看详情", list(record_options.keys()),
                                               key="select_germination_record")
                if selected_record:
                    record_id = record_options[selected_record]
                    record = next((r for r in germination_records if r.id == record_id), None)
                    if record:
                        show_germination_record_details(record)

    with tab5:
        st.subheader("批量发芽实验")
        st.write("选择多个种子批次进行统一的发芽实验")

        # 获取所有可用于发芽的种子批次
        available_batches = get_seed_batches_for_germination()

        if available_batches:
            # 创建多选框
            st.write("### 选择种子批次")
            selected_batches = []

            # 使用列布局显示批次选择框，每行4个
            batch_count = len(available_batches)
            batches_per_row = 2
            rows = (batch_count + batches_per_row - 1) // batches_per_row  # 向上取整

            for row in range(rows):
                cols = st.columns(batches_per_row)
                for col_idx in range(batches_per_row):
                    batch_idx = row * batches_per_row + col_idx
                    if batch_idx < batch_count:
                        batch = available_batches[batch_idx]
                        with cols[col_idx]:
                            display_name = f"{batch.batch_id} - {getattr(batch, 'species_chinese', '未命名')} (可用: {getattr(batch, 'available_quantity', '未知')})"
                            if hasattr(batch, 'seed_id') and batch.seed_id:
                                display_name += f" (种子编号: {batch.seed_id})"

                            if st.checkbox(display_name, key=f"batch_select_{batch.id}"):
                                selected_batches.append(batch)

            if selected_batches:
                st.write(f"已选择 {len(selected_batches)} 个种子批次")

                # 批量发芽实验参数 - 使用两列布局
                st.markdown("### 发芽实验参数")
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("开始日期", datetime.datetime.now(), key="batch_germination_start_date")
                with col2:
                    treatment = st.text_input("处理方法", key="batch_germination_treatment")

                # 为每个选中的批次设置用量 - 使用列布局
                st.markdown("### 设置各批次用量")
                batch_quantities = {}

                # 每行2个批次设置
                selected_count = len(selected_batches)
                batches_per_setting_row = 2
                setting_rows = (selected_count + batches_per_setting_row - 1) // batches_per_setting_row

                for setting_row in range(setting_rows):
                    setting_cols = st.columns(batches_per_setting_row)
                    for setting_col_idx in range(batches_per_setting_row):
                        batch_idx = setting_row * batches_per_setting_row + setting_col_idx
                        if batch_idx < selected_count:
                            batch = selected_batches[batch_idx]
                            with setting_cols[setting_col_idx]:
                                max_seeds = getattr(batch, 'available_quantity', 100) or 100
                                display_name = f"{batch.batch_id} - {getattr(batch, 'species_chinese', '未命名')}"
                                quantity = st.number_input(
                                    f"{display_name} 用量",
                                    min_value=1,
                                    max_value=max_seeds,
                                    value=min(50, max_seeds),
                                    key=f"batch_quantity_{batch.id}"
                                )
                                batch_quantities[batch.id] = quantity

                # 备注单独放置
                notes = st.text_area("备注", key="batch_germination_notes")

                if st.button("创建批量发芽实验", key="create_batch_germination"):
                    success_count = 0
                    for batch in selected_batches:
                        try:
                            germination_id = add_germination_record(
                                seed_batch_id=batch.id,
                                start_date=start_date,
                                treatment=treatment,
                                quantity_used=batch_quantities[batch.id],
                                notes=notes
                            )
                            if germination_id:
                                success_count += 1
                        except Exception as e:
                            st.error(f"批次 {batch.batch_id} 创建发芽实验失败: {e}")

                    if success_count > 0:
                        st.success(f"成功创建 {success_count} 个发芽实验记录")
                        st.rerun()
                    else:
                        st.error("批量创建发芽实验失败")
        else:
            st.info("目前没有可用的种子批次")


# 辅助函数，显示发芽记录详情
def show_germination_record_details(record):
    st.subheader(f"发芽记录详情: {record.germination_id}")

    # 获取种子批次信息
    batch = get_seed_batch_by_id(record.seed_batch_id)

    col1, col2 = st.columns(2)

    with col1:
        st.write("**基本信息**")
        st.write(f"记录ID: {record.germination_id}")
        st.write(f"种子批次: {batch.batch_id if batch else '未知'}")
        st.write(f"种子名称: {getattr(batch, 'species_chinese', '未知') if batch else '未知'}")
        st.write(f"开始日期: {record.start_date}")
        st.write(f"种子数量: {record.quantity_used}")

    with col2:
        st.write("**发芽情况**")
        st.write(f"状态: {record.status}")
        st.write(f"已发芽数量: {record.germinated_count or 0}")
        st.write(f"发芽率: {record.germination_rate * 100:.1f}%" if record.germination_rate is not None else "0.0%")

    # 处理方法和备注
    st.write("**处理方法**")
    st.write(record.treatment or "无")

    st.write("**备注**")
    st.write(record.notes or "无")

    # 获取并显示发芽事件
    events = get_germination_events(record.id)

    if events:
        st.write("**发芽事件记录**")
        events_data = []
        for event in events:
            events_data.append({
                "日期": event.event_date,
                "新增发芽": event.count,
                "累计发芽": event.cumulative_count,
                "备注": event.notes or ""
            })

        st.dataframe(events_data, hide_index=True)

    # 添加新事件表单
    if record.status == "进行中":
        st.write("**添加发芽事件**")

        with st.form("add_germination_event_form"):
            event_date = st.date_input("日期", value=datetime.datetime.now())
            count = st.number_input("新增发芽数量", min_value=0, max_value=record.quantity_used)
            event_notes = st.text_area("备注")

            submitted = st.form_submit_button("保存事件")

            if submitted:
                # 添加发芽事件
                event_id = add_germination_event(
                    germination_record_id=record.id,
                    event_date=event_date,
                    count=count,
                    notes=event_notes
                )

                if event_id:
                    st.success("发芽事件添加成功")
                    st.rerun()
                else:
                    st.error("添加发芽事件失败")

        # 完成发芽记录按钮
        if st.button("完成发芽记录", key=f"complete_germination_{record.id}"):
            complete_germination_record(record.id)
            st.success("发芽记录已标记为完成")
            st.rerun()


def show_germination_management():
    st.subheader("发芽实验管理")

    tab1, tab2, tab3, tab4 = st.tabs(["新建发芽实验", "记录发芽情况", "发芽实验列表", "发芽率统计"])

    with tab1:
        st.subheader("新建发芽实验")

        # 选择种子批次
        seed_batches = get_seed_batches_for_germination()
        if seed_batches:
            batch_options = {f"{batch.batch_id} - 可用: {batch.available_quantity}/{batch.quantity}": batch.id for batch
                             in seed_batches}
            selected_batch = st.selectbox("选择种子批次", list(batch_options.keys()))

            if selected_batch:
                batch_id = batch_options[selected_batch]

                # 找出选中的批次
                selected_batch_obj = None
                for batch in seed_batches:
                    if batch.id == batch_id:
                        selected_batch_obj = batch
                        break

                if selected_batch_obj:
                    st.write(f"可用种子数量: {selected_batch_obj.available_quantity}")

                    start_date = st.date_input("开始日期", datetime.datetime.now())
                    treatment = st.text_input("处理方式")
                    quantity_used = st.number_input("使用种子数量", min_value=1,
                                                    max_value=selected_batch_obj.available_quantity, step=1)
                    notes = st.text_area("备注")

                    if st.button("创建发芽实验"):
                        record_id = add_germination_record(
                            seed_batch_id=batch_id,
                            start_date=start_date,
                            treatment=treatment,
                            quantity_used=quantity_used,
                            notes=notes
                        )

                        if record_id:
                            st.success(f"发芽实验创建成功！")
                            st.rerun()
                        else:
                            st.error("创建发芽实验失败")
        else:
            st.info("目前没有可用的种子批次，请先添加种子批次")

    with tab2:
        st.subheader("记录发芽情况")

        germination_records = get_germination_records()
        if germination_records:
            # 只显示状态为"进行中"的实验
            active_records = [record for record in germination_records if record.status == "进行中"]

            if active_records:
                record_options = {f"{record.germination_id} - {record.start_date}": record.id for record in
                                  active_records}
                selected_record = st.selectbox("选择发芽实验", list(record_options.keys()))

                if selected_record:
                    record_id = record_options[selected_record]

                    # 查询该实验的详细信息
                    for record in active_records:
                        if record.id == record_id:
                            st.markdown(f"### 实验编号: {record.germination_id}")
                            st.write(f"开始日期: {record.start_date}")
                            st.write(f"处理方式: {record.treatment}")
                            st.write(f"使用种子数量: {record.quantity_used}")
                            st.write(f"当前发芽数量: {record.germinated_count}")
                            st.write(f"当前发芽率: {record.germination_rate:.2%}")

                            # 显示历史记录
                            events = get_germination_events(record_id)
                            if events:
                                st.markdown("### 历史记录")
                                event_data = []
                                for event in events:
                                    event_data.append({
                                        "日期": event.event_date,
                                        "新发芽数量": event.count,
                                        "累计发芽数量": event.cumulative_count,
                                        "备注": event.notes or ""
                                    })

                                st.table(pd.DataFrame(event_data))

                            # 添加新记录
                            st.markdown("### 添加新记录")
                            event_date = st.date_input("记录日期", datetime.datetime.now())
                            new_count = st.number_input("新发芽数量", min_value=0, step=1)
                            event_notes = st.text_area("备注", key=f"event_notes_{record_id}")

                            col1, col2 = st.columns(2)

                            with col1:
                                if st.button("添加记录"):
                                    event_id = add_germination_event(
                                        germination_record_id=record_id,
                                        event_date=event_date,
                                        count=new_count,
                                        notes=event_notes
                                    )

                                    if event_id:
                                        st.success("记录添加成功！")
                                        st.rerun()
                                    else:
                                        st.error("添加记录失败")

                            with col2:
                                if st.button("完成实验"):
                                    result = complete_germination_record(record_id)
                                    if result:
                                        st.success("发芽实验已标记为完成！")
                                        st.rerun()
                                    else:
                                        st.error("标记实验完成失败")

                                # 上传图片
                            st.markdown("### 上传发芽图片")
                            uploaded_file = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"],
                                                             key=f"germination_{record_id}",accept_multiple_files=True)
                            image_description = st.text_input("图片描述", key=f"germ_desc_{record_id}")

                            if uploaded_file is not None:
                                if st.button("上传图片", key=f"upload_germ_{record_id}"):
                                    image_id = save_image(uploaded_file, "germination", record_id, image_description)
                                    if image_id:
                                        st.success("图片上传成功！")
                                        st.rerun()
                                    else:
                                        st.error("图片上传失败")

                            # 显示图片
                            st.markdown("### 发芽图片")
                            images = get_images("germination", record_id)

                            if images:
                                image_cols = st.columns(3)
                                for i, image in enumerate(images):
                                    with image_cols[i % 3]:
                                        show_image(image.file_path, caption=image.description, width=250)

                            break
                        else:
                            st.info("目前没有正在进行中的发芽实验")
                    else:
                        st.info("目前没有发芽实验，请先创建实验")

                    with tab3:
                        st.subheader("发芽实验列表")

                        germination_records = get_germination_records()
                        if germination_records:
                            st.write(f"共有 {len(germination_records)} 条发芽实验记录")

                            # 创建数据表格
                            record_data = []
                            for record in germination_records:
                                # 获取种子批次信息
                                seed_batch = None
                                for batch in get_seed_batches():
                                    if batch.id == record.seed_batch_id:
                                        seed_batch = batch
                                        break

                                record_data.append({
                                    "实验编号": record.germination_id,
                                    "开始日期": record.start_date,
                                    "种子批次": seed_batch.batch_id if seed_batch else "未知",
                                    "处理方式": record.treatment,
                                    "使用数量": record.quantity_used,
                                    "发芽数量": record.germinated_count,
                                    "发芽率": f"{record.germination_rate:.2%}",
                                    "状态": record.status
                                })

                            st.dataframe(pd.DataFrame(record_data))

                            # 选择查看详情
                            record_options = {f"{record.germination_id} - {record.start_date}": record.id for record in
                                              germination_records}
                            selected_record = st.selectbox("选择发芽实验查看详情", list(record_options.keys()))

                            if selected_record:
                                record_id = record_options[selected_record]

                                # 查询该实验的详细信息
                                for record in germination_records:
                                    if record.id == record_id:
                                        st.markdown(f"### 实验编号: {record.germination_id}")
                                        st.write(f"开始日期: {record.start_date}")
                                        st.write(f"处理方式: {record.treatment}")
                                        st.write(f"使用种子数量: {record.quantity_used}")
                                        st.write(f"当前发芽数量: {record.germinated_count}")
                                        st.write(f"当前发芽率: {record.germination_rate:.2%}")
                                        st.write(f"状态: {record.status}")
                                        st.write(f"备注: {record.notes}")

                                        # 显示历史记录
                                        events = get_germination_events(record_id)
                                        if events:
                                            st.markdown("### 历史记录")
                                            event_data = []
                                            for event in events:
                                                event_data.append({
                                                    "日期": event.event_date,
                                                    "新发芽数量": event.count,
                                                    "累计发芽数量": event.cumulative_count,
                                                    "备注": event.notes or ""
                                                })

                                            st.table(pd.DataFrame(event_data))

                                            # 绘制发芽曲线
                                            st.markdown("### 发芽曲线")
                                            fig, ax = plt.subplots(figsize=(10, 5))

                                            dates = [event.event_date for event in events]
                                            counts = [event.cumulative_count for event in events]
                                            rates = [count / record.quantity_used for count in counts]

                                            ax.plot(dates, rates, 'o-', linewidth=2)
                                            ax.set_xlabel('日期')
                                            ax.set_ylabel('累计发芽率')
                                            ax.set_title(f'发芽曲线 - {record.germination_id}')
                                            ax.grid(True)

                                            # 设置y轴范围
                                            ax.set_ylim(0, 1.0)

                                            # 格式化y轴为百分比
                                            ax.yaxis.set_major_formatter(
                                                plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))

                                            st.pyplot(fig)

                                        # 显示图片
                                        st.markdown("### 发芽图片")
                                        images = get_images("germination", record_id)

                                        if images:
                                            image_cols = st.columns(3)
                                            for i, image in enumerate(images):
                                                with image_cols[i % 3]:
                                                    show_image(image.file_path, caption=image.description, width=250)

                                        break
                        else:
                            st.info("目前没有发芽实验记录")

                    with tab4:
                        st.subheader("发芽率统计")

                        germination_records = get_germination_records()
                        if germination_records:
                            # 计算总体统计
                            completed_records = [record for record in germination_records if record.status == "已完成"]
                            if completed_records:
                                avg_rate = sum([record.germination_rate for record in completed_records]) / len(
                                    completed_records)
                                max_rate = max([record.germination_rate for record in completed_records])
                                min_rate = min([record.germination_rate for record in completed_records])

                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("平均发芽率", f"{avg_rate:.2%}")
                                with col2:
                                    st.metric("最高发芽率", f"{max_rate:.2%}")
                                with col3:
                                    st.metric("最低发芽率", f"{min_rate:.2%}")

                                # 绘制发芽率分布直方图
                                st.markdown("### 发芽率分布")
                                fig, ax = plt.subplots(figsize=(10, 5))

                                rates = [record.germination_rate for record in completed_records]

                                ax.hist(rates, bins=10, range=(0, 1), edgecolor='black')
                                ax.set_xlabel('发芽率')
                                ax.set_ylabel('频率')
                                ax.set_title('发芽率分布直方图')

                                # 设置x轴范围
                                ax.set_xlim(0, 1.0)

                                # 格式化x轴为百分比
                                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:.0%}'.format(x)))

                                st.pyplot(fig)

                                # 按处理方式分组的发芽率
                                st.markdown("### 不同处理方式的发芽率比较")

                                treatment_groups = {}
                                for record in completed_records:
                                    if record.treatment in treatment_groups:
                                        treatment_groups[record.treatment].append(record.germination_rate)
                                    else:
                                        treatment_groups[record.treatment] = [record.germination_rate]

                                if len(treatment_groups) > 1:
                                    # 计算每种处理方式的平均发芽率
                                    treatment_avg_rates = {treatment: sum(rates) / len(rates) for treatment, rates in
                                                           treatment_groups.items()}

                                    # 绘制条形图
                                    fig, ax = plt.subplots(figsize=(10, 5))

                                    treatments = list(treatment_avg_rates.keys())
                                    avg_rates = list(treatment_avg_rates.values())

                                    ax.bar(treatments, avg_rates)
                                    ax.set_xlabel('处理方式')
                                    ax.set_ylabel('平均发芽率')
                                    ax.set_title('不同处理方式的平均发芽率')

                                    # 设置y轴范围
                                    ax.set_ylim(0, 1.0)

                                    # 格式化y轴为百分比
                                    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))

                                    # 旋转x轴标签，防止重叠
                                    plt.xticks(rotation=45, ha='right')

                                    st.pyplot(fig)
                                else:
                                    st.info("目前只有一种处理方式，无法进行比较")
                            else:
                                st.info("目前没有已完成的发芽实验")
                        else:
                            st.info("目前没有发芽实验记录")


def show_cultivation_statistics():
    st.subheader("栽培统计")

    # 创建一个新会话
    from database import Session
    from models import CultivationRecord, SeedBatch, Collection, CultivationEvent

    session = Session()

    try:
        # 在会话中获取栽培记录
        cultivation_records = session.query(CultivationRecord).all()

        if not cultivation_records:
            st.info("目前没有栽培记录数据")
            return

        # 基本统计
        total_cultivations = len(cultivation_records)
        active_cultivations = len([r for r in cultivation_records if r.status == "活"])
        flowering_cultivations = len([r for r in cultivation_records if r.flowering])
        fruiting_cultivations = len([r for r in cultivation_records if r.fruiting])
        dead_cultivations = len([r for r in cultivation_records if r.status == "死亡"])

        # 显示基本统计
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("总栽培记录", total_cultivations)
        with col2:
            st.metric("存活植株", active_cultivations)
        with col3:
            st.metric("开花植株", flowering_cultivations)
        with col4:
            st.metric("结果植株", fruiting_cultivations)
        with col5:
            st.metric("死亡植株", dead_cultivations)

        # 准备分类统计数据
        families = {}
        genera = {}

        for record in cultivation_records:
            # 直接从记录获取分类信息
            family = record.family
            genus = record.genus

            # 如果记录中没有分类信息，则尝试从种子批次或采集记录中获取
            if not family and record.seed_batch_id:
                # 查询种子批次
                seed_batch = session.query(SeedBatch).get(record.seed_batch_id)
                if seed_batch and seed_batch.collection_id:
                    # 查询采集记录
                    collection = session.query(Collection).get(seed_batch.collection_id)
                    if collection:
                        family = collection.family

            if not genus and record.seed_batch_id:
                # 查询种子批次
                seed_batch = session.query(SeedBatch).get(record.seed_batch_id)
                if seed_batch and seed_batch.collection_id:
                    # 查询采集记录
                    collection = session.query(Collection).get(seed_batch.collection_id)
                    if collection:
                        genus = collection.genus

            # 按科统计
            if family:
                if family in families:
                    families[family] += 1
                else:
                    families[family] = 1

            # 按属统计
            if genus:
                if genus in genera:
                    genera[genus] += 1
                else:
                    genera[genus] = 1

        # 显示分类图表
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("按科统计")
            if families:
                # 排序并获取前10个科
                sorted_families = sorted(families.items(), key=lambda x: x[1], reverse=True)[:10]
                family_names = [f[0] for f in sorted_families]
                family_counts = [f[1] for f in sorted_families]

                fig, ax = plt.subplots()
                ax.barh(family_names, family_counts)
                ax.set_xlabel('数量')
                ax.set_ylabel('科')
                ax.set_title('栽培植物科分布 (Top 10)')
                st.pyplot(fig)
            else:
                st.info("暂无科分布数据")

        with col2:
            st.subheader("按属统计")
            if genera:
                # 排序并获取前10个属
                sorted_genera = sorted(genera.items(), key=lambda x: x[1], reverse=True)[:10]
                genus_names = [g[0] for g in sorted_genera]
                genus_counts = [g[1] for g in sorted_genera]

                fig, ax = plt.subplots()
                ax.barh(genus_names, genus_counts)
                ax.set_xlabel('数量')
                ax.set_ylabel('属')
                ax.set_title('栽培植物属分布 (Top 10)')
                st.pyplot(fig)
            else:
                st.info("暂无属分布数据")

        # 状态随时间变化
        st.subheader("栽培状态随时间变化")

        # 获取所有栽培事件
        all_events = []
        for record in cultivation_records:
            events = session.query(CultivationEvent).filter(
                CultivationEvent.cultivation_record_id == record.id
            ).order_by(CultivationEvent.event_date).all()
            all_events.extend(events)

        if all_events:
            # 按月份分组事件
            events_by_month = {}
            for event in all_events:
                month_key = event.event_date.strftime('%Y-%m')
                if month_key not in events_by_month:
                    events_by_month[month_key] = {
                        "浇水": 0, "施肥": 0, "修剪": 0, "观察": 0, "开花": 0, "结果": 0, "死亡": 0, "其他": 0
                    }

                event_type = event.event_type
                if event_type not in events_by_month[month_key]:
                    event_type = "其他"

                events_by_month[month_key][event_type] += 1

            # 排序月份
            sorted_months = sorted(events_by_month.keys())

            # 准备图表数据
            event_types = ["浇水", "施肥", "修剪", "观察", "开花", "结果", "死亡", "其他"]
            data = {
                "月份": sorted_months
            }

            for event_type in event_types:
                data[event_type] = [events_by_month[month][event_type] for month in sorted_months]

            # 创建DataFrame
            df = pd.DataFrame(data)

            # 绘图
            fig, ax = plt.subplots(figsize=(12, 6))
            bottom = np.zeros(len(sorted_months))

            for event_type in event_types:
                ax.bar(df["月份"], df[event_type], bottom=bottom, label=event_type)
                bottom += df[event_type].values

            ax.set_xlabel('月份')
            ax.set_ylabel('事件数量')
            ax.set_title('栽培事件随时间变化')
            ax.legend()

            # 旋转x轴标签以提高可读性
            plt.xticks(rotation=45)

            st.pyplot(fig)
        else:
            st.info("暂无栽培事件数据")

        # 存活率分析
        st.subheader("存活率分析")

        # 获取所有已完成的栽培(超过3个月)
        three_months_ago = datetime.datetime.now().date() - datetime.timedelta(days=90)
        completed_cultivations = [r for r in cultivation_records if r.start_date < three_months_ago]

        if completed_cultivations:
            # 按位置计算存活率
            locations = {}
            for record in completed_cultivations:
                if record.location not in locations:
                    locations[record.location] = {"total": 0, "alive": 0}

                locations[record.location]["total"] += 1
                if record.status == "活":
                    locations[record.location]["alive"] += 1

            # 计算存活率
            location_names = []
            survival_rates = []

            for location, counts in locations.items():
                if counts["total"] >= 5:  # 只包括至少有5条记录的位置
                    location_names.append(location)
                    survival_rates.append(counts["alive"] / counts["total"] * 100)

            if location_names:
                # 绘图
                fig, ax = plt.subplots()
                ax.bar(location_names, survival_rates)
                ax.set_xlabel('栽培位置')
                ax.set_ylabel('存活率 (%)')
                ax.set_title('不同栽培位置的植物存活率')
                ax.set_ylim(0, 100)

                # 旋转x轴标签以提高可读性
                plt.xticks(rotation=45)

                st.pyplot(fig)
            else:
                st.info("没有足够的数据进行位置存活率分析")
        else:
            st.info("暂无完成的栽培记录")
    finally:
        # 确保会话被关闭
        session.close()


def show_cultivation_management():
    st.subheader("温室栽培管理")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["新建栽培记录", "记录栽培状态", "批量更新状态", "栽培记录列表", "栽培统计"])

    with tab1:
        st.subheader("新建栽培记录")

        # Plant origin selection
        origin_option = st.radio("植株来源", ["种子批次", "已有栽培", "野外采集", "其他来源"], horizontal=True)

        if origin_option == "种子批次":
            # Existing code for selecting seed batch
            seed_batches = get_seed_batches()
            if seed_batches:
                batch_options = {f"{batch.batch_id} - {batch.storage_location}": batch.id for batch in seed_batches}
                selected_batch = st.selectbox("选择种子批次", list(batch_options.keys()))

                if selected_batch:
                    batch_id = batch_options[selected_batch]
                    seed_batch = get_seed_batch_by_id(batch_id)

                    # Display taxonomic info if available
                    if seed_batch and seed_batch.collection_id:
                        collection = get_collection_by_id(seed_batch.collection_id)
                        if collection:
                            st.info(
                                f"植物信息: {collection.species_chinese or ''} {collection.species_latin or ''} ({collection.family or ''} {collection.genus or ''})")

                    # Rest of existing code for seed batch based cultivation
                    start_date = st.date_input("开始栽培日期", datetime.datetime.now())
                    location = st.text_input("栽培位置")
                    quantity = st.number_input("栽培数量", min_value=1, step=1)
                    notes = st.text_area("备注")

                    # Add taxonomic fields in case the seed batch doesn't have complete info
                    with st.expander("添加分类信息（可选）"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            family = st.text_input("科")
                            family_chinese = st.text_input("科中文名")

                        with col2:
                            genus = st.text_input("属")
                            genus_chinese = st.text_input("属中文名")
                        with col3:
                            species_latin = st.text_input("种")
                            species_chinese = st.text_input("种中文名")


                    if st.button("创建栽培记录"):
                        # Create cultivation record with origin info
                        record_id = add_cultivation_record(
                            seed_batch_id=batch_id,
                            start_date=start_date,
                            location=location,
                            quantity=quantity,
                            notes=notes,
                            origin="种子批次",
                            family=family,
                            family_chinese=family_chinese,
                            genus=genus,
                            genus_chinese=genus_chinese,
                            species_chinese=species_chinese,
                            species_latin=species_latin
                        )

                        if record_id:
                            st.success(f"栽培记录创建成功！")
                            st.rerun()
                        else:
                            st.error("创建栽培记录失败")
            else:
                st.info("目前没有种子批次，请先添加种子批次")

        elif origin_option == "已有栽培":
            # Select existing cultivation that has fruited
            fruiting_cultivations = get_fruiting_cultivations()
            if fruiting_cultivations:
                cultivation_options = {
                    f"{cult.cultivation_id} - {cult.location} ({cult.species_chinese or cult.species_latin or '未命名'})": cult.id
                    for cult in fruiting_cultivations
                }
                selected_cultivation = st.selectbox("选择结果的栽培记录", list(cultivation_options.keys()))

                if selected_cultivation:
                    parent_cultivation_id = cultivation_options[selected_cultivation]
                    parent_cultivation = get_cultivation_record_by_id(parent_cultivation_id)

                    # Display parent plant info
                    st.info(
                        f"母本植物: {parent_cultivation.species_chinese or parent_cultivation.species_latin or '未命名'}")

                    # Input fields for new cultivation
                    start_date = st.date_input("开始栽培日期", datetime.datetime.now())
                    location = st.text_input("栽培位置")
                    quantity = st.number_input("栽培数量", min_value=1, step=1)
                    notes = st.text_area("备注")

                    if st.button("创建栽培记录"):
                        # Create cultivation record with parent cultivation info
                        record_id = add_cultivation_record(
                            seed_batch_id=None,  # No seed batch
                            start_date=start_date,
                            location=location,
                            quantity=quantity,
                            notes=notes,
                            origin="已有栽培",
                            origin_details=f"母本: {parent_cultivation.cultivation_id}",
                            parent_cultivation_id=parent_cultivation_id,
                            # Copy taxonomic info from parent
                            family=parent_cultivation.family,
                            family_chinese=parent_cultivation.family_chinese,
                            genus=parent_cultivation.genus,
                            genus_chinese=parent_cultivation.genus_chinese,
                            species_chinese=parent_cultivation.species_chinese,
                            species_latin=parent_cultivation.species_latin
                        )

                        if record_id:
                            st.success(f"栽培记录创建成功！")
                            st.rerun()
                        else:
                            st.error("创建栽培记录失败")
            else:
                st.info("目前没有结果的栽培记录")

        elif origin_option == "野外采集":
            # Select from collections
            collections = get_all_collections()
            if collections:
                collection_options = {
                    f"{coll.collection_id} - {coll.location} ({coll.species_chinese or coll.species_latin or '未命名'})": coll.id
                    for coll in collections
                }
                selected_collection = st.selectbox("选择野外采集记录", list(collection_options.keys()))

                if selected_collection:
                    collection_id = collection_options[selected_collection]
                    collection = get_collection_by_id(collection_id)

                    # Display collection info
                    st.info(
                        f"采集信息: {collection.species_chinese or ''} {collection.species_latin or ''} ({collection.family or ''} {collection.genus or ''})")

                    # Input fields for new cultivation
                    start_date = st.date_input("开始栽培日期", datetime.datetime.now())
                    location = st.text_input("栽培位置")
                    quantity = st.number_input("栽培数量", min_value=1, step=1)
                    notes = st.text_area("备注")

                    if st.button("创建栽培记录"):
                        # Create cultivation record with collection info
                        record_id = add_cultivation_record(
                            seed_batch_id=None,  # No seed batch
                            start_date=start_date,
                            location=location,
                            quantity=quantity,
                            notes=notes,
                            origin="野外采集",
                            origin_details=f"采集记录: {collection.collection_id}",
                            collection_id=collection_id,
                            # Copy taxonomic info from collection
                            family=collection.family,
                            family_chinese=collection.family_chinese,
                            genus=collection.genus,
                            genus_chinese=collection.genus_chinese,
                            species_chinese=collection.species_chinese,
                            species_latin=collection.species_latin,
                        )

                        if record_id:
                            st.success(f"栽培记录创建成功！")
                            st.rerun()
                        else:
                            st.error("创建栽培记录失败")
            else:
                st.info("目前没有采集记录")

        else:  # 其他来源
            # Input fields for new cultivation with manual taxonomic info
            start_date = st.date_input("开始栽培日期", datetime.datetime.now())
            location = st.text_input("栽培位置")
            quantity = st.number_input("栽培数量", min_value=1, step=1)
            origin_details = st.text_input("来源详情")

            # Taxonomic fields
            st.subheader("分类信息")
            col1, col2, col3 = st.columns(3)
            with col1:
                family = st.text_input("科")
                family_chinese = st.text_input("科中文名")

            with col2:
                genus = st.text_input("属")
                genus_chinese = st.text_input("属中文名")
            with col3:
                species_latin = st.text_input("拉丁学名")
                species_chinese = st.text_input("种中文名")
            notes = st.text_area("备注")

            if st.button("创建栽培记录"):
                # Create cultivation record with manual info
                record_id = add_cultivation_record(
                    seed_batch_id=None,  # No seed batch
                    start_date=start_date,
                    location=location,
                    quantity=quantity,
                    notes=notes,
                    origin="其他来源",
                    origin_details=origin_details,
                    family=family,
                    family_chinese=family_chinese,
                    genus=genus,
                    genus_chinese=genus_chinese,
                    species_chinese=species_chinese,
                    species_latin=species_latin,
                )

                if record_id:
                    st.success(f"栽培记录创建成功！")
                    st.rerun()
                else:
                    st.error("创建栽培记录失败")

    with tab2:
        st.subheader("记录栽培状态")

        cultivation_records = get_cultivation_records()
        if cultivation_records:
            # 只显示状态为"活"的记录
            active_records = [record for record in cultivation_records if record.status == "活"]

            if active_records:
                record_options = {
                    f"{record.cultivation_id} - {record.location} ({record.start_date})": record.id
                    for record in active_records}
                selected_record = st.selectbox("选择栽培记录", list(record_options.keys()), key="status_record_select")

                if selected_record:
                    record_id = record_options[selected_record]

                    # 查询该记录的详细信息
                    record = None
                    for r in active_records:
                        if r.id == record_id:
                            record = r
                            break

                    if record:
                        st.markdown(f"### 栽培编号: {record.cultivation_id}")
                        st.write(f"开始日期: {record.start_date}")
                        st.write(f"栽培位置: {record.location}")
                        st.write(f"栽培数量: {record.quantity}")
                        st.write(f"当前状态: {record.status}")

                        # Show taxonomic info if available
                        taxonomic_info = []
                        if record.species_chinese:
                            taxonomic_info.append(f"中文名: {record.species_chinese}")
                        if record.species_latin:
                            taxonomic_info.append(f"拉丁学名: {record.species_latin}")
                        if record.family:
                            taxonomic_info.append(f"科: {record.family}")
                        if record.genus:
                            taxonomic_info.append(f"属: {record.genus}")


                        if taxonomic_info:
                            st.write(" | ".join(taxonomic_info))

                        # Show origin info
                        if record.origin:
                            origin_text = f"来源: {record.origin}"
                            if record.origin_details:
                                origin_text += f" ({record.origin_details})"
                            st.write(origin_text)

                        if record.flowering:
                            st.write(f"开花日期: {record.flowering_date}")

                        if record.fruiting:
                            st.write(f"结果日期: {record.fruiting_date}")

                        # 显示事件历史
                        events = get_cultivation_events(record_id)
                        if events:
                            st.markdown("### 历史记录")
                            event_data = []
                            for event in events:
                                event_data.append({
                                    "日期": event.event_date,
                                    "事件类型": event.event_type,
                                    "描述": event.description or ""
                                })

                            st.table(pd.DataFrame(event_data))

                        # 显示子分组信息
                        subgroups = get_cultivation_subgroups(record_id)
                        if subgroups:
                            st.markdown("### 子分组记录")
                            subgroup_data = []
                            for subgroup in subgroups:
                                subgroup_data.append({
                                    "日期": subgroup.status_date,
                                    "状态": subgroup.status,
                                    "数量": subgroup.quantity,
                                    "备注": subgroup.notes or ""
                                })
                            st.table(pd.DataFrame(subgroup_data))

                        # 添加新记录
                        st.markdown("### 添加常规事件")
                        event_date = st.date_input("记录日期", datetime.datetime.now(), key="event_date")
                        event_type = st.selectbox("事件类型",
                                                  ["浇水", "施肥", "修剪", "观察", "其他"], key="event_type")
                        event_description = st.text_area("描述", key="event_desc")

                        if st.button("添加事件", key="add_event_btn"):
                            event_id = add_cultivation_event(
                                cultivation_record_id=record_id,
                                event_date=event_date,
                                event_type=event_type,
                                description=event_description
                            )

                            if event_id:
                                st.success("事件添加成功！")
                                st.rerun()
                            else:
                                st.error("添加事件失败")

                        # 记录特殊状态
                        st.markdown("### 记录特殊状态")
                        status_option = st.radio(
                            "状态类型",
                            ["开花", "结果", "死亡"],
                            key=f"status_option_{record_id}"
                        )

                        status_date = st.date_input("状态日期", datetime.datetime.now(),
                                                    key=f"status_date_{record_id}")

                        if status_option == "死亡":
                            death_reason = st.text_input("死亡原因",
                                                         key=f"death_reason_{record_id}")
                        else:
                            death_reason = None

                        if st.button("更新状态", key="update_status_btn"):
                            result = update_cultivation_status(
                                cultivation_record_id=record_id,
                                status=status_option,
                                date=status_date,
                                reason=death_reason
                            )

                            if result:
                                st.success(f"状态更新成功！")
                                st.rerun()
                            else:
                                st.error("更新状态失败")

                        # 记录部分植株状态
                        st.markdown("### 记录部分植株状态")
                        subgroup_status = st.radio(
                            "状态类型",
                            ["部分开花", "部分结果", "部分死亡"],
                            key="subgroup_status"
                        )

                        subgroup_quantity = st.number_input(
                            "状态变化的植株数量",
                            min_value=1,
                            max_value=record.quantity,
                            key="subgroup_quantity"
                        )

                        subgroup_date = st.date_input(
                            "状态日期",
                            datetime.datetime.now(),
                            key="subgroup_date"
                        )

                        subgroup_notes = st.text_input(
                            "说明",
                            key="subgroup_notes"
                        )

                        if st.button("记录部分状态", key="add_subgroup_btn"):
                            result = add_cultivation_subgroup(
                                cultivation_record_id=record_id,
                                status=subgroup_status.replace("部分", ""),  # Remove "部分" prefix
                                quantity=subgroup_quantity,
                                status_date=subgroup_date,
                                notes=subgroup_notes
                            )

                            if result:
                                st.success(f"部分状态记录成功！")
                                st.rerun()
                            else:
                                st.error("记录部分状态失败")

                        # 种子收获选项（仅当植物结果时显示）
                        if record.fruiting:
                            st.markdown("### 收获种子")
                            seed_quantity = st.number_input("种子数量", min_value=1, key="seed_quantity")
                            seed_storage_location = st.text_input("存储位置", key="seed_storage_location")
                            seed_notes = st.text_area("备注", key="seed_notes")

                            if st.button("记录收获种子", key="harvest_seeds_btn"):
                                seed_batch_id = add_seed_batch_from_cultivation(
                                    cultivation_id=record_id,
                                    quantity=seed_quantity,
                                    storage_location=seed_storage_location,
                                    notes=seed_notes
                                )

                                if seed_batch_id:
                                    st.success("种子收获记录成功！")
                                    st.rerun()
                                else:
                                    st.error("记录种子收获失败")

                        # 上传图片
                        st.markdown("### 上传栽培图片")
                        uploaded_file = st.file_uploader("选择图片",
                                                         type=["jpg", "jpeg", "png"],
                                                         key=f"cultivation_{record_id}", accept_multiple_files=True)
                        image_description = st.text_input("图片描述",
                                                          key=f"cult_desc_{record_id}")

                        if uploaded_file is not None:
                            if st.button("上传图片", key=f"upload_cult_{record_id}"):
                                image_id = save_image(uploaded_file, "cultivation", record_id,
                                                      image_description)
                                if image_id:
                                    st.success("图片上传成功！")
                                    st.rerun()
                                else:
                                    st.error("图片上传失败")

                        # 显示图片
                        st.markdown("### 栽培图片")
                        images = get_images("cultivation", record_id)

                        if images:
                            image_cols = st.columns(3)
                            for i, image in enumerate(images):
                                with image_cols[i % 3]:
                                    show_image(image.file_path, caption=image.description,
                                               width=250)
            else:
                st.info("目前没有活的栽培记录")
        else:
            st.info("目前没有栽培记录，请先创建栽培记录")

    with tab3:
        st.subheader("批量更新状态")

        cultivation_records = get_cultivation_records()
        if cultivation_records:
            # 只显示状态为"活"的记录
            active_records = [record for record in cultivation_records if record.status == "活"]

            if active_records:
                # 按栽培位置分组
                locations = sorted(list(set([record.location for record in active_records])))
                selected_location = st.selectbox("选择栽培位置", ["全部"] + locations)

                if selected_location == "全部":
                    filtered_records = active_records
                else:
                    filtered_records = [record for record in active_records if
                                        record.location == selected_location]

                # 添加按科属筛选
                taxonomic_filter = st.radio("按分类筛选", ["不筛选", "按科筛选", "按属筛选"], horizontal=True)

                if taxonomic_filter == "按科筛选":
                    families = sorted(list(set([record.family for record in filtered_records if record.family])))
                    if families:
                        selected_family = st.selectbox("选择科", families)
                        filtered_records = [record for record in filtered_records if record.family == selected_family]
                    else:
                        st.info("没有科信息可供筛选")

                elif taxonomic_filter == "按属筛选":
                    genera = sorted(list(set([record.genus for record in filtered_records if record.genus])))
                    if genera:
                        selected_genus = st.selectbox("选择属", genera)
                        filtered_records = [record for record in filtered_records if record.genus == selected_genus]
                    else:
                        st.info("没有属信息可供筛选")

                if filtered_records:
                    # 创建选择框
                    st.markdown("### 选择要更新的记录")

                    selected_records = []
                    for record in filtered_records:
                        taxonomic_info = record.species_chinese or record.species_latin or ""
                        if st.checkbox(
                                f"{record.cultivation_id} - {record.location} ({record.start_date}) - {taxonomic_info}",
                                key=f"select_{record.id}"):
                            selected_records.append(record.id)

                    if selected_records:
                        st.markdown(f"已选择 {len(selected_records)} 条记录")

                        st.markdown("### 设置新状态")
                        status_option = st.radio("状态类型", ["开花", "结果", "死亡"], key="batch_status_option")
                        status_date = st.date_input("状态日期", datetime.datetime.now(), key="batch_status_date")

                        if status_option == "死亡":
                            death_reason = st.text_input("死亡原因", key="batch_death_reason")
                        else:
                            death_reason = None

                        if st.button("批量更新状态", key="batch_update_btn"):
                            result = batch_update_cultivation_status(
                                cultivation_ids=selected_records,
                                status=status_option,
                                date=status_date,
                                reason=death_reason
                            )

                            if result:
                                st.success(f"成功更新 {len(selected_records)} 条记录的状态！")
                                st.rerun()
                            else:
                                st.error("批量更新状态失败")
                    else:
                        st.info("请选择至少一条记录")
                else:
                    st.info(f"在 {selected_location} 位置没有活的栽培记录")
            else:
                st.info("目前没有活的栽培记录")
        else:
            st.info("目前没有栽培记录，请先创建栽培记录")

    with tab4:
        st.subheader("栽培记录列表")

        cultivation_records = get_cultivation_records()
        if cultivation_records:
            st.write(f"共有 {len(cultivation_records)} 条栽培记录")

            # 筛选选项
            col1, col2, col3 = st.columns(3)
            with col1:
                status_filter = st.selectbox("状态筛选", ["全部", "活", "死亡"], key="list_status_filter")
            with col2:
                location_filter = st.text_input("位置筛选", key="list_location_filter")
            with col3:
                taxonomic_filter = st.text_input("分类筛选（科/属/种名）", key="list_taxonomic_filter")

            # 应用筛选
            filtered_records = cultivation_records

            if status_filter != "全部":
                filtered_records = [record for record in filtered_records if record.status == status_filter]

            if location_filter:
                filtered_records = [record for record in filtered_records if
                                    location_filter.lower() in (record.location or "").lower()]

            if taxonomic_filter:
                filter_term = taxonomic_filter.lower()
                filtered_records = [record for record in filtered_records if
                                    (record.family and filter_term in record.family.lower()) or
                                    (record.genus and filter_term in record.genus.lower()) or
                                    (record.species_chinese and filter_term in record.species_chinese.lower()) or
                                    (record.species_latin and filter_term in record.species_latin.lower())]

            # 创建数据表格
            if filtered_records:
                record_data = []
                for record in filtered_records:
                    # 获取种子批次信息
                    seed_batch = None
                    if record.seed_batch_id:
                        seed_batch = get_seed_batch_by_id(record.seed_batch_id)

                    # 获取来源信息
                    origin_info = record.origin or "未知"
                    if record.origin_details:
                        origin_info += f" ({record.origin_details})"

                    # 获取分类信息
                    taxonomic_info = record.species_chinese or record.species_latin or ""
                    if record.family:
                        taxonomic_info += f" | {record.family}"
                    if record.genus:
                        taxonomic_info += f" | {record.genus}"

                    record_data.append({
                        "栽培编号": record.cultivation_id,
                        "开始日期": record.start_date,
                        "来源": origin_info,
                        "分类信息": taxonomic_info,
                        "栽培位置": record.location,
                        "栽培数量": record.quantity,
                        "开花": "是" if record.flowering else "否",
                        "结果": "是" if record.fruiting else "否",
                        "状态": record.status
                    })

                st.dataframe(pd.DataFrame(record_data))

                # 选择查看详情
                record_options = {
                    f"{record.cultivation_id} - {record.location} ({record.start_date})": record.id for
                    record in filtered_records}
                selected_record = st.selectbox("选择栽培记录查看详情", list(record_options.keys()),
                                               key="list_view_record")

                if selected_record:
                    record_id = record_options[selected_record]

                    # 查询该记录的详细信息
                    for record in filtered_records:
                        if record.id == record_id:
                            st.markdown(f"### 栽培编号: {record.cultivation_id}")

                            # 基本信息
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"开始日期: {record.start_date}")
                                st.write(f"栽培位置: {record.location}")
                                st.write(f"栽培数量: {record.quantity}")
                                st.write(f"当前状态: {record.status}")

                                if record.flowering:
                                    st.write(f"开花日期: {record.flowering_date}")
                                if record.fruiting:
                                    st.write(f"结果日期: {record.fruiting_date}")
                                if record.status == "死亡":
                                    st.write(f"死亡日期: {record.death_date}")
                                    st.write(f"死亡原因: {record.death_reason}")

                            with col2:
                                # 分类信息
                                if record.species_chinese or record.species_latin or record.family or record.genus:
                                    st.write("**分类信息:**")
                                    if record.species_chinese:
                                        st.write(f"中文名: {record.species_chinese}")
                                    if record.species_latin:
                                        st.write(f"拉丁学名: {record.species_latin}")
                                    if record.family:
                                        st.write(f"科: {record.family}")
                                    if record.genus:
                                        st.write(f"属: {record.genus}")


                                # 来源信息
                                st.write("**来源信息:**")
                                st.write(f"来源类型: {record.origin or '未知'}")
                                if record.origin_details:
                                    st.write(f"来源详情: {record.origin_details}")

                                if record.seed_batch_id:
                                    seed_batch = get_seed_batch_by_id(record.seed_batch_id)
                                    if seed_batch:
                                        st.write(f"种子批次: {seed_batch.batch_id}")

                                if record.collection_id:
                                    collection = get_collection_by_id(record.collection_id)
                                    if collection:
                                        st.write(f"野外采集: {collection.collection_id}")

                                if record.parent_cultivation_id:
                                    parent = get_cultivation_record_by_id(record.parent_cultivation_id)
                                    if parent:
                                        st.write(f"母本栽培: {parent.cultivation_id}")

                            # 备注
                            if record.notes:
                                st.write("**备注:**")
                                st.write(record.notes)

                            # 显示事件历史
                            events = get_cultivation_events(record_id)
                            if events:
                                st.markdown("### 历史记录")
                                event_data = []
                                for event in events:
                                    event_data.append({
                                        "日期": event.event_date,
                                        "事件类型": event.event_type,
                                        "描述": event.description or ""
                                    })

                                st.table(pd.DataFrame(event_data))

                            # 显示子分组记录
                            subgroups = get_cultivation_subgroups(record_id)
                            if subgroups:
                                st.markdown("### 子分组记录")
                                subgroup_data = []
                                for subgroup in subgroups:
                                    subgroup_data.append({
                                        "日期": subgroup.status_date,
                                        "状态": subgroup.status,
                                        "数量": subgroup.quantity,
                                        "备注": subgroup.notes or ""
                                    })
                                st.table(pd.DataFrame(subgroup_data))

                            # 显示收获的种子批次
                            harvested_seeds = get_harvested_seeds(record_id)
                            if harvested_seeds:
                                st.markdown("### 收获的种子批次")
                                seed_data = []
                                for seed in harvested_seeds:
                                    seed_data.append({
                                        "批次编号": seed.batch_id,
                                        "收获日期": seed.storage_date,
                                        "数量": seed.quantity,
                                        "存储位置": seed.storage_location
                                    })
                                st.table(pd.DataFrame(seed_data))

                            # 显示图片
                            st.markdown("### 栽培图片")
                            images = get_images("cultivation", record_id)

                            if images:
                                image_cols = st.columns(3)
                                for i, image in enumerate(images):
                                    with image_cols[i % 3]:
                                        show_image(image.file_path, caption=image.description,
                                                   width=250)

                            break
            else:
                st.info("未找到匹配的记录")
        else:
            st.info("目前没有栽培记录")

    with tab5:
        # Call the statistics function
        show_cultivation_statistics()


# 获取所有属和科的函数
def get_all_families_from_collections():
    """从采集记录中获取所有科"""
    collections = get_all_collections()
    families = set()
    for collection in collections:
        if collection.family:
            families.add(collection.family)
    return sorted(list(families))
def get_all_genera_from_collections():
    """从采集记录中获取所有属"""
    collections = get_all_collections()
    genera = set()
    for collection in collections:
        if collection.genus:
            genera.add(collection.genus)
    return sorted(list(genera))


def show_collection_details(collection_id):
    """显示采集记录详情"""
    collection = get_collection_by_id(collection_id)
    if collection:
        st.markdown(f"### 采集编号: {collection.collection_id}")

        # 基本信息
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**采集日期:** {collection.collection_date}")
            st.write(f"**采集地点:** {collection.location}")
            st.write(f"**海拔:** {collection.altitude}米")
            st.write(f"**采集人:** {collection.collector}")

        with col2:
            st.write(f"**经纬度:** {collection.latitude}, {collection.longitude}")
            st.write(f"**生境描述:** {collection.habitat or '未记录'}")
            st.write(f"**鉴定状态:** {'已鉴定' if collection.identified else '未鉴定'}")
            if collection.identified:
                st.write(f"**鉴定人:** {collection.identified_by or '未记录'}")

        # 备注
        if collection.notes:
            st.write("**备注:**")
            st.write(collection.notes)

        # 植物信息
        st.markdown("### 植物信息")
        if collection.species_latin or collection.species_chinese or collection.family or collection.genus:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**中文名:** {collection.species_chinese or '未记录'}")
                st.write(f"**科:** {collection.family or '未记录'}")
            with col2:
                st.write(f"**拉丁学名:** {collection.species_latin or '未记录'}")
                st.write(f"**属:** {collection.genus or '未记录'}")

            if collection.species_latin:
                st.write(f"**种:** {collection.species_latin}")

            if collection.identification_notes:
                st.write("**鉴定备注:**")
                st.write(collection.identification_notes)
        else:
            st.write("暂无植物分类信息")

        # 相关种子批次
        seed_batches = get_seed_batches_by_collection(collection_id)
        if seed_batches:
            st.markdown("### 相关种子批次")

            batch_data = []
            for batch in seed_batches:
                batch_data.append({
                    "批次编号": batch.batch_id,
                    "存储日期": batch.storage_date,
                    "存储位置": batch.storage_location,
                    "种子数量": batch.quantity,
                    "可用数量": batch.available_quantity
                })

            st.dataframe(pd.DataFrame(batch_data))

        # 图片
        images = get_images("collection", collection_id)
        if images:
            st.markdown("### 采集图片")
            image_cols = st.columns(min(3, len(images)))
            for i, image in enumerate(images):
                with image_cols[i % len(image_cols)]:
                    show_image(image.file_path, caption=image.description, width=250)


def show_data_query():
    st.subheader("数据查询")
    query_option = st.selectbox(
        "查询类型",
        ["植物分类查询", "采集记录查询", "种子批次查询", "发芽实验查询", "栽培记录查询"]
    )
    if query_option == "植物分类查询":
        st.subheader("植物分类查询")
        # 筛选选项
        col1, col2 = st.columns(2)
        with col1:
            family_filter = st.text_input("科（包含）")
        with col2:
            genus_filter = st.text_input("属（包含）")
        # 搜索框
        species_latin_filter = st.text_input("拉丁学名（包含）")
        species_chinese_filter = st.text_input("中文名（包含）")
        # 查询按钮
        if st.button("查询"):
            collections = search_collections_by_taxonomy(
                family=family_filter if family_filter else None,
                genus=genus_filter if genus_filter else None,
                species_latin=species_latin_filter if species_latin_filter else None,
                species_chinese=species_chinese_filter if species_chinese_filter else None
            )
            if collections:
                st.write(f"共找到 {len(collections)} 条记录")
                # 创建数据表格
                collection_data = []
                for collection in collections:
                    collection_data.append({
                        "采集编号": collection.collection_id,
                        "采集日期": collection.collection_date,
                        "采集地点": collection.location,
                        "中文名": collection.species_chinese or "",
                        "拉丁学名": collection.species_latin or "",
                        "科": collection.family or "",
                        "属": collection.genus or "",
                        "鉴定状态": "已鉴定" if collection.identified else "未鉴定"
                    })
                st.dataframe(pd.DataFrame(collection_data))
                # 选择查看详情
                collection_options = {
                    f"{collection.collection_id} - {collection.location} ({collection.collection_date})": collection.id
                    for collection in collections}
                selected_collection = st.selectbox("选择采集记录查看详情", list(collection_options.keys()))
                if selected_collection:
                    collection_id = collection_options[selected_collection]
                    show_collection_details(collection_id)
            else:
                st.info("未找到匹配的记录")

                # 查询该植物的详细信息
        else:
            st.info("未找到匹配的记录")

    elif query_option == "采集记录查询":
        st.subheader("采集记录查询")

        # 筛选选项
        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input("开始日期",
                                       datetime.datetime.now() - datetime.timedelta(days=365))
        with col2:
            end_date = st.date_input("结束日期", datetime.datetime.now())

        location_filter = st.text_input("采集地点（包含）")
        collector_filter = st.text_input("采集人（包含）")

        # 查询按钮
        if st.button("查询"):
            collections = search_collections(
                start_date=start_date,
                end_date=end_date,
                location=location_filter if location_filter else None,
                collector=collector_filter if collector_filter else None
            )

            if collections:
                st.write(f"共找到 {len(collections)} 条记录")

                # 创建数据表格
                collection_data = []
                for collection in collections:

                    collection_data.append({
                        "采集编号": collection.collection_id,
                        "采集日期": collection.collection_date,
                        "采集地点": collection.location,
                        "采集人": collection.collector
                    })

                st.dataframe(pd.DataFrame(collection_data))

                # 选择查看详情
                collection_options = {
                    f"{collection.collection_id} - {collection.location} ({collection.collection_date})": collection.id
                    for collection in collections}
                selected_collection = st.selectbox("选择采集记录查看详情",
                                                   list(collection_options.keys()))

                if selected_collection:
                    collection_id = collection_options[selected_collection]

                    # 查询该采集记录的详细信息
                    for collection in collections:
                        if collection.id == collection_id:
                            st.markdown(f"### 采集编号: {collection.collection_id}")
                            st.write(f"采集日期: {collection.collection_date}")
                            st.write(f"采集地点: {collection.location}")
                            st.write(f"经纬度: {collection.latitude}, {collection.longitude}")
                            st.write(f"海拔: {collection.altitude}米")
                            st.write(f"采集人: {collection.collector}")
                            st.write(f"生境描述: {collection.habitat}")
                            st.write(f"备注: {collection.notes}")



                            # 显示图片
                            st.markdown("### 采集图片")
                            images = get_images("collection", collection_id)

                            if images:
                                image_cols = st.columns(3)
                                for i, image in enumerate(images):
                                    with image_cols[i % 3]:
                                        show_image(image.file_path, caption=image.description,
                                                   width=250)

                            break
            else:
                st.info("未找到匹配的记录")

    elif query_option == "种子批次查询":
        st.subheader("种子批次查询")

        # 筛选选项
        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input("开始日期",
                                       datetime.datetime.now() - datetime.timedelta(days=365))
        with col2:
            end_date = st.date_input("结束日期", datetime.datetime.now())

        location_filter = st.text_input("存储位置（包含）")

        # 查询按钮
        if st.button("查询"):
            seed_batches = search_seed_batches(
                start_date=start_date,
                end_date=end_date,
                storage_location=location_filter if location_filter else None
            )

            if seed_batches:
                st.write(f"共找到 {len(seed_batches)} 条记录")

                # 创建数据表格
                batch_data = []
                for batch in seed_batches:
                    # 查找关联的采集记录
                    collection_info = "未关联"
                    if batch.collection_id:
                        collections = get_all_collections()
                        for collection in collections:
                            if collection.id == batch.collection_id:
                                collection_info = f"{collection.collection_id} - {collection.location}"
                                break
                    else:
                        collection_info = batch.source or "未记录来源"

                    batch_data.append({
                        "批次编号": batch.batch_id,
                        "入库日期": batch.storage_date,
                        "存储位置": batch.storage_location,
                        "种子数量": batch.quantity,
                        "可用数量": batch.available_quantity,
                        "来源": collection_info
                    })

                st.dataframe(pd.DataFrame(batch_data))

                # 选择查看详情
                batch_options = {
                    f"{batch.batch_id} - {batch.storage_location} ({batch.storage_date})": batch.id
                    for batch in seed_batches}
                selected_batch = st.selectbox("选择种子批次查看详情", list(batch_options.keys()))

                if selected_batch:
                    batch_id = batch_options[selected_batch]

                    # 查询该种子批次的详细信息
                    for batch in seed_batches:
                        if batch.id == batch_id:
                            st.markdown(f"### 批次编号: {batch.batch_id}")
                            st.write(f"存储位置: {batch.storage_location}")
                            st.write(f"入库日期: {batch.storage_date}")
                            st.write(f"种子数量: {batch.quantity}")
                            st.write(f"可用数量: {batch.available_quantity}")
                            st.write(f"预估发芽率: {batch.viability:.2%}")

                            if batch.collection_id:
                                # 查询关联的采集记录
                                collections = get_all_collections()
                                for collection in collections:
                                    if collection.id == batch.collection_id:
                                        st.write(
                                            f"关联采集记录: {collection.collection_id} - {collection.location} ({collection.collection_date})")
                                        break
                            else:
                                st.write(f"种子来源: {batch.source}")

                            st.write(f"备注: {batch.notes}")

                            # 显示图片
                            st.markdown("### 种子图片")
                            images = get_images("seed", batch_id)

                            if images:
                                image_cols = st.columns(3)
                                for i, image in enumerate(images):
                                    with image_cols[i % 3]:
                                        show_image(image.file_path, caption=image.description,
                                                   width=250)

                            # 显示关联的发芽实验
                            germination_records = get_germination_records()
                            related_records = [record for record in germination_records if
                                               record.seed_batch_id == batch_id]

                            if related_records:
                                st.markdown("### 关联的发芽实验")

                                record_data = []
                                for record in related_records:
                                    record_data.append({
                                        "实验编号": record.germination_id,
                                        "开始日期": record.start_date,
                                        "处理方式": record.treatment,
                                        "使用数量": record.quantity_used,
                                        "发芽数量": record.germinated_count,
                                        "发芽率": f"{record.germination_rate:.2%}",
                                        "状态": record.status
                                    })

                                st.table(pd.DataFrame(record_data))

                            # 显示关联的栽培记录
                            cultivation_records = get_cultivation_records()
                            related_cultivations = [record for record in cultivation_records if
                                                    record.seed_batch_id == batch_id]

                            if related_cultivations:
                                st.markdown("### 关联的栽培记录")

                                cultivation_data = []
                                for record in related_cultivations:
                                    cultivation_data.append({
                                        "栽培编号": record.cultivation_id,
                                        "开始日期": record.start_date,
                                        "栽培位置": record.location,
                                        "栽培数量": record.quantity,
                                        "状态": record.status
                                    })

                                st.table(pd.DataFrame(cultivation_data))

                            break
            else:
                st.info("未找到匹配的记录")

    elif query_option == "发芽实验查询":
        st.subheader("发芽实验查询")

        # 筛选选项
        col1, col2, col3 = st.columns(3)

        with col1:
            start_date = st.date_input("开始日期",
                                       datetime.datetime.now() - datetime.timedelta(days=365))
        with col2:
            end_date = st.date_input("结束日期", datetime.datetime.now())
        with col3:
            status_filter = st.selectbox("状态", ["全部", "进行中", "已完成"])

        treatment_filter = st.text_input("处理方式（包含）")

        # 查询按钮
        if st.button("查询"):
            germination_records = search_germination_records(
                start_date=start_date,
                end_date=end_date,
                status=None if status_filter == "全部" else status_filter,
                treatment=treatment_filter if treatment_filter else None
            )

            if germination_records:
                st.write(f"共找到 {len(germination_records)} 条记录")

                # 创建数据表格
                record_data = []
                for record in germination_records:
                    # 获取种子批次信息
                    seed_batch = None
                    for batch in get_seed_batches():
                        if batch.id == record.seed_batch_id:
                            seed_batch = batch
                            break

                    record_data.append({
                        "实验编号": record.germination_id,
                        "开始日期": record.start_date,
                        "种子批次": seed_batch.batch_id if seed_batch else "未知",
                        "处理方式": record.treatment,
                        "使用数量": record.quantity_used,
                        "发芽数量": record.germinated_count,
                        "发芽率": f"{record.germination_rate:.2%}",
                        "状态": record.status
                    })

                st.dataframe(pd.DataFrame(record_data))

                # 选择查看详情
                record_options = {f"{record.germination_id} - {record.start_date}": record.id for
                                  record in germination_records}
                selected_record = st.selectbox("选择发芽实验查看详情", list(record_options.keys()))

                if selected_record:
                    record_id = record_options[selected_record]

                    # 查询该实验的详细信息
                    for record in germination_records:
                        if record.id == record_id:
                            st.markdown(f"### 实验编号: {record.germination_id}")
                            st.write(f"开始日期: {record.start_date}")
                            st.write(f"处理方式: {record.treatment}")
                            st.write(f"使用种子数量: {record.quantity_used}")
                            st.write(f"当前发芽数量: {record.germinated_count}")
                            st.write(f"当前发芽率: {record.germination_rate:.2%}")
                            st.write(f"状态: {record.status}")
                            st.write(f"备注: {record.notes}")

                            # 关联的种子批次
                            seed_batch = None
                            for batch in get_seed_batches():
                                if batch.id == record.seed_batch_id:
                                    seed_batch = batch
                                    break

                            if seed_batch:
                                st.write(
                                    f"关联种子批次: {seed_batch.batch_id} - {seed_batch.storage_location}")

                            # 显示历史记录
                            events = get_germination_events(record_id)
                            if events:
                                st.markdown("### 历史记录")
                                event_data = []
                                for event in events:
                                    event_data.append({
                                        "日期": event.event_date,
                                        "新发芽数量": event.count,
                                        "累计发芽数量": event.cumulative_count,
                                        "备注": event.notes or ""
                                    })

                                st.table(pd.DataFrame(event_data))

                                # 绘制发芽曲线
                                st.markdown("### 发芽曲线")
                                fig, ax = plt.subplots(figsize=(10, 5))

                                dates = [event.event_date for event in events]
                                counts = [event.cumulative_count for event in events]
                                rates = [count / record.quantity_used for count in counts]

                                ax.plot(dates, rates, 'o-', linewidth=2)
                                ax.set_xlabel('日期')
                                ax.set_ylabel('累计发芽率')
                                ax.set_title(f'发芽曲线 - {record.germination_id}')
                                ax.grid(True)

                                # 设置y轴范围
                                ax.set_ylim(0, 1.0)

                                # 格式化y轴为百分比
                                ax.yaxis.set_major_formatter(
                                    plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))

                                st.pyplot(fig)

                            # 显示图片
                            st.markdown("### 发芽图片")
                            images = get_images("germination", record_id)

                            if images:
                                image_cols = st.columns(3)
                                for i, image in enumerate(images):
                                    with image_cols[i % 3]:
                                        show_image(image.file_path, caption=image.description,
                                                   width=250)

                            break
            else:
                st.info("未找到匹配的记录")

    elif query_option == "栽培记录查询":
        st.subheader("栽培记录查询")

        # 筛选选项
        col1, col2, col3 = st.columns(3)

        with col1:
            start_date = st.date_input("开始日期",
                                       datetime.datetime.now() - datetime.timedelta(days=365))
        with col2:
            end_date = st.date_input("结束日期", datetime.datetime.now())
        with col3:
            status_filter = st.selectbox("状态", ["全部", "活", "死亡"])

        location_filter = st.text_input("栽培位置（包含）")

        # 查询按钮
        if st.button("查询"):
            cultivation_records = search_cultivation_records(
                start_date=start_date,
                end_date=end_date,
                status=None if status_filter == "全部" else status_filter,
                location=location_filter if location_filter else None
            )

            if cultivation_records:
                st.write(f"共找到 {len(cultivation_records)} 条记录")

                # 创建数据表格
                record_data = []
                for record in cultivation_records:
                    # 获取种子批次信息
                    seed_batch = None
                    for batch in get_seed_batches():
                        if batch.id == record.seed_batch_id:
                            seed_batch = batch
                            break

                    record_data.append({
                        "栽培编号": record.cultivation_id,
                        "开始日期": record.start_date,
                        "种子批次": seed_batch.batch_id if seed_batch else "未知",
                        "栽培位置": record.location,
                        "栽培数量": record.quantity,
                        "开花": "是" if record.flowering else "否",
                        "结果": "是" if record.fruiting else "否",
                        "状态": record.status
                    })

                st.dataframe(pd.DataFrame(record_data))

                # 选择查看详情
                record_options = {
                    f"{record.cultivation_id} - {record.location} ({record.start_date})": record.id
                    for record in cultivation_records}
                selected_record = st.selectbox("选择栽培记录查看详情", list(record_options.keys()))

                if selected_record:
                    record_id = record_options[selected_record]

                    # 查询该记录的详细信息
                    for record in cultivation_records:
                        if record.id == record_id:
                            st.markdown(f"### 栽培编号: {record.cultivation_id}")
                            st.write(f"开始日期: {record.start_date}")
                            st.write(f"栽培位置: {record.location}")
                            st.write(f"栽培数量: {record.quantity}")
                            st.write(f"当前状态: {record.status}")

                            if record.flowering:
                                st.write(f"开花日期: {record.flowering_date}")

                            if record.fruiting:
                                st.write(f"结果日期: {record.fruiting_date}")

                            if record.status == "死亡":
                                st.write(f"死亡日期: {record.death_date}")
                                st.write(f"死亡原因: {record.death_reason}")

                            st.write(f"备注: {record.notes}")

                            # 关联的种子批次
                            seed_batch = None
                            for batch in get_seed_batches():
                                if batch.id == record.seed_batch_id:
                                    seed_batch = batch
                                    break

                            if seed_batch:
                                st.write(
                                    f"关联种子批次: {seed_batch.batch_id} - {seed_batch.storage_location}")

                            # 显示事件历史
                            events = get_cultivation_events(record_id)
                            if events:
                                st.markdown("### 历史记录")
                                event_data = []
                                for event in events:
                                    event_data.append({
                                        "日期": event.event_date,
                                        "事件类型": event.event_type,
                                        "描述": event.description or ""
                                    })

                                st.table(pd.DataFrame(event_data))

                            # 显示图片
                            st.markdown("### 栽培图片")
                            images = get_images("cultivation", record_id)

                            if images:
                                image_cols = st.columns(3)
                                for i, image in enumerate(images):
                                    with image_cols[i % 3]:
                                        show_image(image.file_path, caption=image.description,
                                                   width=250)

                            break
            else:
                st.info("未找到匹配的记录")

def show_image_management():
    st.subheader("图片管理")

    image_type = st.selectbox("图片类型", ["采集", "种子", "发芽", "栽培"])

    if image_type == "采集":
        table_type = "collection"
        records = get_all_collections()
        record_options = {
            f"{record.collection_id} - {record.location} ({record.collection_date})": record.id for
            record in records}

    elif image_type == "种子":
        table_type = "seed"
        records = get_seed_batches()
        record_options = {
            f"{record.batch_id} - {record.storage_location} ({record.storage_date})": record.id for
            record in records}

    elif image_type == "发芽":
        table_type = "germination"
        records = get_germination_records()
        record_options = {f"{record.germination_id} - {record.start_date}": record.id for record in
                          records}

    elif image_type == "栽培":
        table_type = "cultivation"
        records = get_cultivation_records()
        record_options = {
            f"{record.cultivation_id} - {record.location} ({record.start_date})": record.id for
            record in records}

    if record_options:
        selected_record = st.selectbox(f"选择{image_type}记录", list(record_options.keys()))

        if selected_record:
            record_id = record_options[selected_record]

            # 获取该记录的所有图片
            images = get_images(table_type, record_id)

            if images:
                st.write(f"共有 {len(images)} 张图片")

                # 显示图片
                for i, image in enumerate(images):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        show_image(image.file_path, caption=f"图片 #{i + 1}: {image.description}",
                                   width=500)

                    with col2:
                        st.write(f"上传日期: {getattr(image, 'upload_date', getattr(image, 'image_date', '未知'))}")

                        # 编辑描述
                        new_description = st.text_input("图片描述", image.description or "",
                                                        key=f"desc_{image.id}")

                        if st.button("更新描述", key=f"update_{image.id}"):
                            result = update_image_description(image.id, new_description)
                            if result:
                                st.success("描述更新成功！")
                                st.rerun()
                            else:
                                st.error("更新描述失败")

                        if st.button("删除图片", key=f"delete_{image.id}"):
                            result = delete_image(image.id)
                            if result:
                                st.success("图片删除成功！")
                                st.rerun()
                            else:
                                st.error("删除图片失败")

                    st.markdown("---")
            else:
                st.info(f"该{image_type}记录还没有图片")

            # 上传新图片
            st.subheader(f"上传新{image_type}图片")
            uploaded_file = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"],
                                             key=f"new_{table_type}_{record_id}", accept_multiple_files=True)
            image_description = st.text_input(f"图片描述",
                                              key=f"new_desc_{table_type}_{record_id}")

            if uploaded_file:
                if st.button(f"上传图片", key=f"upload_new_{table_type}_{record_id}"):
                    image_id = save_image(uploaded_file, table_type, record_id,
                                          image_description)
                    if image_id:
                        st.success("图片上传成功！")
                        st.rerun()
                    else:
                        st.error("图片上传失败")
        else:
            st.info(f"请选择一个{image_type}记录")
    else:
        st.info(f"目前没有{image_type}记录")



def create_backup():
    """
    创建数据库备份
    """
    try:
        # 获取当前时间作为文件名的一部分
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # 获取当前脚本的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 使用绝对路径定义备份目录
        backup_dir = os.path.join(current_dir, "backups")

        # 确保备份目录存在
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # 备份文件的路径
        backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")

        # 使用绝对路径找到数据库文件
        db_path = os.path.join(current_dir, "plant_conservation.db")

        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            print(f"错误: 数据库文件不存在: {db_path}")
            print(f"当前工作目录: {os.getcwd()}")
            return False, f"数据库文件不存在: {db_path}"

        # 复制数据库文件
        shutil.copy2(db_path, backup_path)

        print(f"数据库备份成功: {backup_path}")

        # 调用清理函数，保留最近的10个备份
        settings = get_settings()
        max_backups = settings.get("max_backups", 10)
        cleanup_old_backups(max_backups)

        return True, backup_path
    except Exception as e:
        print(f"数据库备份失败: {str(e)}")
        return False, str(e)


def show_backup_restore():
    st.subheader("备份与恢复")

    tab1, tab2 = st.tabs(["备份数据", "恢复数据"])

    with tab1:
        st.subheader("备份数据")

        st.write("点击下面的按钮创建数据库备份。备份文件将包含所有数据但不包含图片文件。")

        if st.button("创建备份"):
            try:
                success, backup_path = create_backup()  # 正确解包返回值

                if success:
                    st.success(f"备份创建成功!")

                    # 提供下载链接
                    with open(backup_path, "rb") as file:
                        st.download_button(
                            label="下载备份文件",
                            data=file,
                            file_name=os.path.basename(backup_path),
                            mime="application/octet-stream"
                        )
                else:
                    st.error(f"备份创建失败: {backup_path}")  # 此时backup_path包含错误信息
            except Exception as e:
                st.error(f"备份创建失败: {str(e)}")


def get_settings():
    """
    获取应用程序设置
    如果设置文件不存在，则创建默认设置
    """
    settings_file = "settings.json"
    default_settings = {
        "database_path": "plant_database.db",
        "backup_folder": "backups",
        "theme": "light",
        "language": "zh_CN",
        "auto_backup": True,
        "backup_interval_days": 7,
        "last_backup_date": None,
        "default_view": "card",
        "items_per_page": 10,
        "export_format": "xlsx"
    }

    try:
        if os.path.exists(settings_file):
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                # 确保所有默认设置字段都存在
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
        else:
            settings = default_settings
            save_settings(settings)
        return settings
    except Exception as e:
        print(f"Error loading settings: {e}")
        return default_settings


def save_settings(settings):
    """
    保存应用程序设置到文件
    """
    try:
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False



def show_settings():
    st.subheader("系统设置")

    settings = get_settings()

    # 应用基本设置
    st.markdown("### 基本设置")
    organization_name = st.text_input("组织名称", settings.get("organization_name",
                                                               "植物资源库"))

    # 图片存储设置
    st.markdown("### 图片存储设置")
    image_storage_path = st.text_input("图片存储路径",
                                       settings.get("image_storage_path",
                                                    "./images"))

    # 系统配置
    st.markdown("### 系统配置")
    auto_backup = st.checkbox("启用自动备份", settings.get("auto_backup", True))

    backup_interval_days = st.number_input(
        "自动备份间隔（天）",
        min_value=1,
        max_value=30,
        value=settings.get("backup_interval_days", 7)
    )

    max_backups = st.number_input(
        "保留备份数量",
        min_value=1,
        max_value=30,
        value=settings.get("max_backups", 10)
    )

    # 保存设置
    if st.button("保存设置"):
        new_settings = {
            "organization_name": organization_name,
            "image_storage_path": image_storage_path,
            "auto_backup": auto_backup,
            "backup_interval_days": backup_interval_days,
            "max_backups": max_backups
        }

        result = save_settings(new_settings)
        if result:
            st.success("设置保存成功！")
            # 检查图片存储路径是否改变，如果改变则尝试创建新目录
            if image_storage_path != settings.get("image_storage_path"):
                try:
                    os.makedirs(image_storage_path, exist_ok=True)
                    st.info(f"已创建新的图片存储目录: {image_storage_path}")
                except Exception as e:
                    st.warning(f"无法创建图片存储目录: {str(e)}")
        else:
            st.error("设置保存失败")



def restore_backup(uploaded_file):
    """恢复数据库备份"""
    try:
        # 保存上传的文件
        backup_file = "temp_backup.db"
        with open(backup_file, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 获取当前数据库路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, "plant_conservation.db")

        # 备份当前数据库
        if os.path.exists(db_path):
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            shutil.copy2(db_path, f"{db_path}.bak_{timestamp}")

        # 用上传的备份替换当前数据库
        shutil.copy2(backup_file, db_path)

        # 删除临时文件
        os.remove(backup_file)

        return True
    except Exception as e:
        print(f"恢复备份失败: {str(e)}")
        return False


def show_label_generator():
    """显示标签生成页面"""
    st.subheader("标签生成")

    label_type = st.selectbox(
        "标签类型",
        ["二维码", "条形码"]
    )

    record_type = st.selectbox(
        "记录类型",
        ["采集", "种子批次", "发芽实验", "栽培记录"]
    )

    # 根据选择的记录类型获取相应的记录
    if record_type == "采集":
        records = get_all_collections()
        record_options = {
            f"{record.collection_id} - {record.location} ({record.collection_date})": record.collection_id
            for record in records}
    elif record_type == "种子批次":
        records = get_seed_batches()
        record_options = {
            f"{record.batch_id} - {record.storage_location} ({record.storage_date})": record.batch_id
            for record in records}
    elif record_type == "发芽实验":
        records = get_germination_records()
        record_options = {
            f"{record.germination_id} - {record.start_date}": record.germination_id
            for record in records}
    elif record_type == "栽培记录":
        records = get_cultivation_records()
        record_options = {
            f"{record.cultivation_id} - {record.location} ({record.start_date})": record.cultivation_id
            for record in records}

    if record_options:
        selected_record = st.selectbox(f"选择{record_type}", list(record_options.keys()))
        record_id = record_options[selected_record]

        # 额外信息
        additional_info = st.text_input("额外信息 (可选)")

        # 生成标签数据
        data = f"{record_id}"
        if additional_info:
            data += f" - {additional_info}"

        if st.button("生成标签"):
            if label_type == "二维码":
                img_path = generate_qrcode(data, record_id, record_type)
                st.success("二维码生成成功!")
                st.image(img_path, caption=f"{record_type} {record_id} 的二维码")

                with open(img_path, "rb") as file:
                    st.download_button(
                        label="下载二维码",
                        data=file,
                        file_name=os.path.basename(img_path),
                        mime="image/png"
                    )
            else:
                img_path = generate_barcode(data, record_id, record_type)
                st.success("条形码生成成功!")
                st.image(img_path, caption=f"{record_type} {record_id} 的条形码")

                with open(img_path, "rb") as file:
                    st.download_button(
                        label="下载条形码",
                        data=file,
                        file_name=os.path.basename(img_path),
                        mime="image/png"
                    )
    else:
        st.info(f"目前没有{record_type}记录")

def cleanup_old_backups(max_backups=10):
    """
    清理旧的备份文件，只保留最近的几个备份

    参数:
        max_backups: 要保留的最大备份数量
    """
    try:
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            return

        # 获取备份目录中的所有备份文件
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.startswith("backup_") and file.endswith(".db"):
                file_path = os.path.join(backup_dir, file)
                backup_files.append((file_path, os.path.getmtime(file_path)))

        # 按修改时间排序
        backup_files.sort(key=lambda x: x[1], reverse=True)

        # 删除多余的旧备份
        if len(backup_files) > max_backups:
            for file_path, _ in backup_files[max_backups:]:
                try:
                    os.remove(file_path)
                    print(f"已删除旧备份: {file_path}")
                except Exception as e:
                    print(f"删除旧备份失败: {file_path}, 错误: {str(e)}")

        return True
    except Exception as e:
        print(f"清理旧备份失败: {str(e)}")
        return False



if __name__ == "__main__":
    # 初始化数据库
    init_db()

    # 确保图片目录存在
    settings = get_settings()
    image_path = settings.get("image_storage_path", "./images")
    os.makedirs(image_path, exist_ok=True)

    # 检查是否需要自动备份
    if settings.get("auto_backup", True):
        last_backup = settings.get("last_backup_date")
        backup_interval = settings.get("backup_interval_days", 7)
        import datetime as dt  # 直接在使用前重新导入并使用别名
        today = dt.datetime.now().date()
        if last_backup is None or (today - datetime.datetime.strptime(last_backup,
                                                                      "%Y-%m-%d").date()).days >= backup_interval:
            try:
                backup_file = create_backup()

                # 更新上次备份日期
                settings["last_backup_date"] = today.strftime("%Y-%m-%d")
                save_settings(settings)

                # 删除超过保留数量的旧备份
                max_backups = settings.get("max_backups", 10)
                cleanup_old_backups(max_backups)
            except Exception as e:
                print(f"自动备份失败: {str(e)}")

# 运行应用
main()




