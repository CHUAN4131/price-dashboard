import streamlit as st
import pandas as pd

# 设置页面标题和布局
st.set_page_config(
    page_title="价格追踪看板",
    page_icon="📊",
    layout="wide"
)

# 设置全局字体样式
st.markdown("""
    <style>
    .stDataFrame {
        font-size: 20px !important;
    }
    div[data-testid="stDataFrameResizable"] {
        font-size: 20px !important;
    }
    .stMarkdown {
        font-size: 16px !important;
    }
    .stTitle {
        font-size: 32px !important;
    }
    .stHeader {
        font-size: 24px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("亚马逊商品价格波动看板")

# 载入数据
try:
    df = pd.read_excel('processed_price_data.xlsx')
    df['日期'] = pd.to_datetime(df['日期'])
    
    # 获取最新日期的数据
    latest_date = df['日期'].max()
    df_latest = df[df['日期'] == latest_date]
    
    # 显示数据更新日期
    st.markdown(f"<span style='color: red'>**数据更新日期：{latest_date.strftime('%Y-%m-%d')} 14:30**</span>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"数据加载失败: {str(e)}")
    st.stop()

if len(df_latest) > 0:
    # 创建侧边栏筛选器
    with st.sidebar:
        st.header("筛选条件")
        
        # 添加组别筛选
        group_options = ['全部', '照明', '电工']
        selected_group = st.selectbox('选择组别', group_options)
        
        # 根据组别筛选数据
        if selected_group != '全部':
            pre_filtered_df = df_latest[df_latest['组别'] == selected_group]
        else:
            pre_filtered_df = df_latest
        
        # 波动类型筛选
        fluctuation_options = ['全部', '3天5%波动', '5天10%波动', '同时有两种波动']
        selected_fluctuation = st.selectbox('选择波动类型', fluctuation_options)
        
        # 根据波动类型进一步筛选数据
        if selected_fluctuation == '3天5%波动':
            pre_filtered_df = pre_filtered_df[pre_filtered_df['波动_3天_5%']]
        elif selected_fluctuation == '5天10%波动':
            pre_filtered_df = pre_filtered_df[pre_filtered_df['波动_5天_10%']]
        elif selected_fluctuation == '同时有两种波动':
            pre_filtered_df = pre_filtered_df[pre_filtered_df['波动_3天_5%'] & pre_filtered_df['波动_5天_10%']]
        else:
            pre_filtered_df = pre_filtered_df[pre_filtered_df['波动_3天_5%'] | pre_filtered_df['波动_5天_10%']]

            
        # 获取三级分类选项
        if len(pre_filtered_df) > 0:
            available_categories = sorted(pre_filtered_df['三级分类'].unique().tolist())
            all_categories = ['全部'] + available_categories
        else:
            all_categories = ['全部']
            
        selected_category = st.selectbox('选择三级分类', all_categories)
        
        # 根据三级分类筛选
        if selected_category != '全部':
            category_filtered_df = pre_filtered_df[pre_filtered_df['三级分类'] == selected_category]
        else:
            category_filtered_df = pre_filtered_df
            
        # 获取项目细分选项
        if len(category_filtered_df) > 0:
            available_types = sorted(category_filtered_df['项目细分'].unique().tolist())
            all_types = ['全部'] + available_types
        else:
            all_types = ['全部']
            
        selected_type = st.selectbox('选择项目细分', all_types)

        # 添加查询按钮
        search_button = st.button('查询数据')

    if search_button:
        # 应用所有筛选条件
        filtered_df = pre_filtered_df
        if selected_category != '全部':
            filtered_df = filtered_df[filtered_df['三级分类'] == selected_category]
        if selected_type != '全部':
            filtered_df = filtered_df[filtered_df['项目细分'] == selected_type]

        # 获取最终的波动ASIN列表
        fluctuating_asins = filtered_df['ASIN'].unique()
        
        if len(fluctuating_asins) > 0:
            st.header("价格波动ASIN列表")
            
            # 创建一个数据框来存储每个ASIN的波动信息
            summary_data = []
            for asin in fluctuating_asins:
                asin_data = filtered_df[filtered_df['ASIN'] == asin]
                latest_price = asin_data['结算价($)'].iloc[-1]
                has_3day = asin_data['波动_3天_5%'].any()
                has_5day = asin_data['波动_5天_10%'].any()
                
                # 获取3天前和5天前的价格数据
                asin_history = df[df['ASIN'] == asin].sort_values('日期', ascending=False)
                price_3days_ago = asin_history[asin_history['日期'] == latest_date - pd.Timedelta(days=2)]['结算价($)'].iloc[0] if len(asin_history[asin_history['日期'] == latest_date - pd.Timedelta(days=2)]) > 0 else None
                price_5days_ago = asin_history[asin_history['日期'] == latest_date - pd.Timedelta(days=4)]['结算价($)'].iloc[0] if len(asin_history[asin_history['日期'] == latest_date - pd.Timedelta(days=4)]) > 0 else None
                
                summary_data.append({
                    '日期': asin_data['日期'].iloc[0].strftime('%Y-%m-%d'),
                    'ASIN': asin,
                    '商品链接': f"https://www.amazon.com/dp/{asin}",
                    '品牌': asin_data['品牌'].iloc[0],
                    '三级分类': asin_data['三级分类'].iloc[0],
                    '项目细分': asin_data['项目细分'].iloc[0],
                    '当前结算价': f"${latest_price:.2f}",
                    '3天前价格': f"${price_3days_ago:.2f}" if price_3days_ago is not None else "无数据",
                    '5天前价格': f"${price_5days_ago:.2f}" if price_5days_ago is not None else "无数据",
                    '3天5%波动': '是' if has_3day else '否',
                    '5天10%波动': '是' if has_5day else '否'
                })
            
            # 创建DataFrame并显示
            summary_df = pd.DataFrame(summary_data)
            
            # 使用Streamlit的原生表格显示
            st.dataframe(
                summary_df,
                column_config={
                    "商品链接": st.column_config.LinkColumn("商品链接")
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.info(f"共发现 {len(fluctuating_asins)} 个有价格波动的ASIN")
        else:
            st.info("当前筛选条件下没有发现价格波动的ASIN")
    else:
        st.info("请设置筛选条件并点击查询按钮查看数据")
else:
    st.warning("数据集为空")

# 添加页脚
st.markdown("---")
st.markdown("### 说明")
st.markdown("- 3天5%波动：表示在3天内价格波动超过5%")
st.markdown("- 5天10%波动：表示在5天内价格波动超过10%")
st.markdown("- 结算价：最终售价 = 原始标价 - 优惠券折扣金额，反映商品实际成交价格")
st.markdown("---")
st.markdown("### 温馨提示")
st.markdown("- ⚠️ 为了节省系统资源，不使用看板时请关闭浏览器标签页。")
st.markdown("- ⏬ 查询数据可以下载，鼠标移动到查询数据上，点击右上角选择下载即可。")
st.markdown("- 🔭 数据每日下午2:30更新，大家可以下午两点半后再查看。")
