import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import pandas as pd
import streamlit as st
from rty_processor import process_rty_7z
from tab_weekly import render_weekly_tab
from st_aggrid import AgGrid
import io
import xlsxwriter
from PIL import Image

@st.cache_data(show_spinner=False)
def run_processing(uploaded_file):
    return process_rty_7z(uploaded_file)

def generate_excel_report(customer, month, df_st_yield, buf_fail, buf_proj_yield, dict_proj_tables):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Monthly_Report")

    title_format = workbook.add_format({'bold': True, 'font_size': 14})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border':1})
    cell_format = workbook.add_format({'border':1})

    # JUDUL
    worksheet.write('A1', f'Monthly Station Report ({customer}-{month})', title_format)

    # PLOT TOTAL YIELD
    fig_st, ax_st = plt.subplots(figsize=(10,5))
    df_st = df_st_yield.copy()
    unique_custs = df_st["Customer"].unique()
    
    colors_st = plt.cm.tab20(range(len(unique_custs)))
    c_map = {c: colors_st[i] for i, c in enumerate(unique_custs)}
    b_colors = df_st["Customer"].map(c_map)

    ax_st.barh(df_st["Station_Label"], df_st["TOTAL YIELD (%)"], color=b_colors)
    for i, v in enumerate(df_st["TOTAL YIELD (%)"]):
        ax_st.text(v + 1, i, round(v,2), va='center', fontsize=8)
    ax_st.set_xlabel("Total Yield (%)")
    ax_st.set_title(f"Total Yield (%) per Station - {month}")
    ax_st.set_xlim(0,115)
    plt.tight_layout()

    buf_yield_station = io.BytesIO()
    fig_st.savefig(buf_yield_station, format='png', bbox_inches='tight')
    plt.close(fig_st)

    worksheet.insert_image('A3', '', {'image_data': buf_yield_station, 'x_scale': 0.5, 'y_scale':0.5})

    # FUNGSI RESIZE

    def resize_image(buffer, width, height):
        buffer.seek(0)
        img = Image.open(buffer)
        img_resized = img.resize((width, height))
        new_buffer = io.BytesIO()
        img_resized.save(new_buffer, format ='PNG')
        new_buffer.seek(0)
        return new_buffer

    # Insert plot Fail Mode
    if buf_fail:
        buf_fail_resized = resize_image(buf_fail, 526, 281)
        worksheet.insert_image('J3', '', {'image_data':buf_fail, 'x_scale': 0.4, 'y_scale': 0.4})
   
    if buf_proj_yield:
        buf_proj_yield_resized = resize_image(buf_proj_yield, 596, 284)
        worksheet.insert_image('A16', '', {'image_data': buf_proj_yield, 'x_scale': 0.4, 'y_scale': 0.4})

    # Tabel Detail Project
    row = 28
    col = 0

    for proj, tables in dict_proj_tables.items():
        worksheet.write(row, col, f"Project: {proj}", title_format)
        row += 2

        qty_df = tables.get('qty')
        if qty_df is not None and not qty_df.empty:
            worksheet.write(row, col, "Quantity & Yield", workbook.add_format({'bold': True}))
            row +=1
            for c_idx, col_name in enumerate(qty_df.columns):
                worksheet.write(row, col +c_idx, col_name, header_format)
            row += 1
    
            for _, r_data in qty_df.iterrows():
                for c_idx, val in enumerate (r_data):
                    worksheet.write(row, col + c_idx, val, cell_format)
                row += 1
            row += 1

        fail_df = tables.get('fail')
        if fail_df is not None and not fail_df.empty:
            worksheet.write(row, col, "Top 5 Fail Mode", workbook.add_format({'bold': True}))
            row += 1
            for c_idx, col_name in enumerate(fail_df.columns):
                worksheet.write(row, col + c_idx, col_name, header_format)
            row += 1

            for _, r_data in fail_df.iterrows():
                for c_idx, val in enumerate(r_data):
                    worksheet.write(row, col + c_idx, val, cell_format)
                row += 1
            row += 2
        
    workbook.close()
    return output.getvalue()

def generate_weekly_excel_report(
    customer, station, week_start, week_end, buf_yield, buf_fail, buf_proj_yield, dict_proj_tables,
    m_customer=None, m_month=None, m_df_st=None, m_buf_fail=None, m_buf_proj=None, m_dict_proj=None
):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})

    title_format = workbook.add_format({'bold':True, 'font_size': 14})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border':1})
    cell_format = workbook.add_format({'border':1})
    
    def resize_img(buffer, width, height):
        buffer.seek(0)
        img = Image.open(buffer)
        img_resized = img.resize((width, height))
        new_buffer = io.BytesIO()
        img_resized.save(new_buffer, format ='PNG')
        new_buffer.seek(0)
        return new_buffer

    # ==========================
    # SHEET 1 : MONTHLY REPORT
    # ==========================
    worksheet1 = workbook.add_worksheet("Monthly_Report")
 
    # Cek apakah data bulanan (dari Tab 2) ada isinya / sudah dipilih user
    if m_df_st is not None and not m_df_st.empty and m_customer and m_month:
        worksheet1.write('A1', f'Monthly Station Report ({m_customer}-{m_month})', title_format)
        
        # Recreate Plot Yield Bulanan supaya bisa diekstrak
        fig_st, ax_st = plt.subplots(figsize=(10,5))
        df_st = m_df_st.copy()
        unique_custs = df_st["Customer"].unique()
        colors_st = plt.cm.tab20(range(len(unique_custs)))
        c_map = {c: colors_st[i] for i, c in enumerate(unique_custs)}
        b_colors = df_st["Customer"].map(c_map)

        ax_st.barh(df_st["Station_Label"], df_st["TOTAL YIELD (%)"], color=b_colors)
        for i, v in enumerate(df_st["TOTAL YIELD (%)"]):
            ax_st.text(v + 1, i, round(v,2), va='center', fontsize=8)
        ax_st.set_xlabel("Total Yield (%)")
        ax_st.set_title(f"Total Yield (%) per Station - {m_month}")
        ax_st.set_xlim(0,115)
        plt.tight_layout()

        buf_yield_station = io.BytesIO()
        fig_st.savefig(buf_yield_station, format='png', bbox_inches='tight')
        plt.close(fig_st)

        # Insert Gambar Bulanan
        worksheet1.insert_image('A3', '', {'image_data': buf_yield_station, 'x_scale': 0.5, 'y_scale':0.5})
        if m_buf_fail:
            m_buf_fail.seek(0)
            worksheet1.insert_image('J3', '', {'image_data': m_buf_fail, 'x_scale': 0.4, 'y_scale': 0.4})
            
        if m_buf_proj:
            m_buf_proj.seek(0)
            worksheet1.insert_image('A16', '', {'image_data': m_buf_proj, 'x_scale': 0.4, 'y_scale': 0.4})
        
        #if m_buf_fail:
         #   worksheet1.insert_image('J3', '', {'image_data': resize_img(m_buf_fail, 526, 281), 'x_scale': 0.4, 'y_scale': 0.4})
        #if m_buf_proj:
         #   worksheet1.insert_image('A16', '', {'image_data': resize_img(m_buf_proj, 596, 284), 'x_scale': 0.4, 'y_scale': 0.4})

        # Tabel Detail Project Bulanan
        row = 28
        col = 0
        if m_dict_proj:
            for proj, tables in m_dict_proj.items():
                worksheet1.write(row, col, f"Project: {proj}", title_format)
                row += 2
                qty_df = tables.get('qty')
                if qty_df is not None and not qty_df.empty:
                    worksheet1.write(row, col, "Quantity & Yield", workbook.add_format({'bold': True}))
                    row +=1
                    for c_idx, col_name in enumerate(qty_df.columns):
                        worksheet1.write(row, col +c_idx, str(col_name), header_format)
                    row += 1
                    for _, r_data in qty_df.iterrows():
                        for c_idx, val in enumerate (r_data):
                            worksheet1.write(row, col + c_idx, val, cell_format)
                        row += 1
                    row += 1

                fail_df = tables.get('fail')
                if fail_df is not None and not fail_df.empty:
                    worksheet1.write(row, col, "Top 5 Fail Mode", workbook.add_format({'bold': True}))
                    row += 1
                    for c_idx, col_name in enumerate(fail_df.columns):
                        worksheet1.write(row, col + c_idx, str(col_name), header_format)
                    row += 1
                    for _, r_data in fail_df.iterrows():
                        for c_idx, val in enumerate(r_data):
                            worksheet1.write(row, col + c_idx, val, cell_format)
                        row += 1
                    row += 2
    else:
        # Jika user belum filter data bulanan
        worksheet1.write('A1', 'monthly data not selected', title_format)
        
    # ==========================
    # SHEET 2 : WEEKLY REPORT
    # ==========================
    worksheet2 = workbook.add_worksheet("Weekly_Report")
    worksheet2.write('A1', f'Weekly Station Report ({customer} | {station} | {week_start}-{week_end})', title_format)

    # Insert Plots
    if buf_yield:
        worksheet2.insert_image('A3', '', {'image_data': buf_yield, 'x_scale': 0.5, 'y_scale':0.5})
    if buf_fail:
        worksheet2.insert_image('J3', '', {'image_data': buf_fail, 'x_scale': 0.4, 'y_scale': 0.4})
    if buf_proj_yield:
        worksheet2.insert_image('A16', '', {'image_data': buf_proj_yield, 'x_scale': 0.4, 'y_scale': 0.4})

    # Tabel Detail Project Monthly
    row = 32
    col = 0

    for proj, tables in dict_proj_tables.items():
        worksheet2.write(row, col, f"Project: {proj}", title_format)
        row += 2

        qty_df = tables.get('qty')
        if qty_df is not None and not qty_df.empty:
            worksheet2.write(row, col, "Quantity & Yield", workbook.add_format({'bold': True}))
            row +=1
            for c_idx, col_name in enumerate(qty_df.columns):
                worksheet2.write(row, col +c_idx, str(col_name), header_format)
            row += 1
            for _, r_data in qty_df.iterrows():
                for c_idx, val in enumerate (r_data):
                    worksheet2.write(row, col + c_idx, val, cell_format)
                row += 1
            row += 1

        fail_df = tables.get('fail')
        if fail_df is not None and not fail_df.empty:
            worksheet2.write(row, col, "Top Fail Mode", workbook.add_format({'bold': True}))
            row += 1
            for c_idx, col_name in enumerate(fail_df.columns):
                worksheet2.write(row, col + c_idx, str(col_name), header_format)
            row += 1
            for _, r_data in fail_df.iterrows():
                for c_idx, val in enumerate(r_data):
                    worksheet2.write(row, col + c_idx, val, cell_format)
                row += 1
            row += 2

    workbook.close()
    return output.getvalue()
    
    
st.set_page_config(layout="wide")

st.sidebar.header("Input Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload .7z file",
    type=["7z"]
)

st.sidebar.caption("Format: Folder > Customer > Station > Excel files")
st.sidebar.caption("Example: RTY > ABB > FCT > AB_010.xlsx")

st.sidebar.markdown("---")

st.sidebar.caption("🔒 **Security Notice:**")
st.sidebar.caption("This tool uses a *Stateless Architecture* with *In-Memory Processing*. No manufacturing data is saved or transmitted externally.")

if uploaded_file:

    with st.spinner("Processing file..."):
        df_qty, df_fail, df_monthly, df_qty_weekly, df_fail_weekly, df_weekly_detail, excel_buffer, extracted_year = run_processing(uploaded_file)

    if df_qty is not None:

        st.success("Processing Completed")

        tab1, tab2, tab3, tab4 = st.tabs(["Performance Overview", "Monthly", "Weekly", "Integrated Raw Data"])

        with tab1:
            year_text = f" - {extracted_year}" if extracted_year else ""
            st.header(f"Performance Overview {year_text}")

            total_qty_in = df_monthly["TOTAL QTY IN"].sum()
            total_qty_pass = df_monthly["TOTAL QTY PASS"].sum()
            overall_yield = (total_qty_pass / total_qty_in * 100) if total_qty_in > 0 else 0 

            df_fail_overall = df_fail.groupby("Top 5 Fail Mode")["Count"].sum().sort_values(ascending=False)
            df_fail_overall = df_fail_overall[~df_fail_overall.index.isin(["No Fail Data", "Not Available"])]
            top_fail_name = df_fail_overall.index[0] if not df_fail_overall.empty else "None"
            top_fail_count = df_fail_overall.iloc[0] if not df_fail_overall.empty else 0 

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total Volume (QTY IN)", value=f"{int(total_qty_in):,}")
            with col2:
                st.metric(label="Overall Yield", value=f"{overall_yield:.2f}%")

            with col3:
                st.metric(label="Top Defect Mode", value=str(top_fail_name), delta =f"-{int(top_fail_count)} pcs", delta_color="inverse")

            st.markdown("---")

            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.subheader("Yield Trend per Month")
                monthly_trend = df_monthly.groupby("Month", as_index=False)[["TOTAL QTY IN", "TOTAL QTY PASS"]].sum()
                monthly_trend["Yield (%)"] = (monthly_trend["TOTAL QTY PASS"] / monthly_trend["TOTAL QTY IN"].replace(0, pd.NA)) * 100

                month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                monthly_trend["Month"] = pd.Categorical(monthly_trend["Month"], categories=month_order, ordered=True)
                monthly_trend = monthly_trend.sort_values("Month").dropna(subset=["Yield (%)"])

                if not monthly_trend.empty:
                    fig_trend = px.line(month_trend, x="Month", y="Yield (%)", markers=True, text="Yield (%)")
                    fig_trend.update_traces(textposition="top center", texttemplate='%{text:2f}%')
                    fig_trend.update_layout(yaxis_title="Yield (%)", xaxis_title="Month", yaxis_range=[0, 110])
                    st.plotly_chart(fig_trend, use_container_width= True)
                else:
                    st.info("No trend data available.")

            with col_chart2:
                st.subheader("Top 5 Defect Modes Overall")
                if not df_fail_overall.empty:
                    top5_fails = df_fail_overall.head(5).reset_index()
                    fig_fail_pie = px.bar(top5_fails, x="Count", y="Top 5 Fail Mode", orientation = 'h', text="Count", color="Count", color_continuous_scale="Reds") 
                    fig_fail_pie.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_fail_pie, use_container_width=True)
                else:
                    st.info("No defect data available.")
            

######################################################################################################################################################################

        with tab2:
            st.subheader("Quantity and Yield per Month")

            # ==========================
            # Urutan Bulan Fix
            # ==========================
            month_order = ["Jan","Feb","Mar","Apr","May","Jun",
                           "Jul","Aug","Sep","Oct","Nov","Dec"]
        
            available_months = [m for m in month_order if m in df_monthly["Month"].unique()]

            # ===============
            # Filter Customer
            # ===============
            
            customers = st.multiselect(
                "Choose Customer",
                (df_monthly["Customer"].unique()),
                key="main_customer"
            )
            
            if customers:
                
                month = st.selectbox(
                    "Choose Month",
                    available_months,
                    key="main_month"
                )
        
                metric = st.selectbox(
                    "Choose Metric",
                    ["TOTAL QTY",
                     "TOTAL YIELD (%)"]
                )
        
                df_filtered = df_monthly[
                    (df_monthly["Customer"].isin(customers)) &
                    (df_monthly["Month"] == month)
                ]
               
                if not df_filtered.empty:

                    fig, ax = plt.subplots(figsize=(14,6))
                    df_filtered = df_filtered.copy()
                    df_filtered["Station_Label"] = (
                        df_filtered["Customer"] + " | " + df_filtered["Station"]
                    )

                    if metric == "TOTAL QTY":

                        pass_values = df_filtered["TOTAL QTY PASS"]
                        fail_values = df_filtered["TOTAL QTY FAIL"]
                        total_values = pass_values + fail_values

                        unique_customers = df_filtered["Customer"].unique()
                        colors = plt.cm.tab20(range(len(unique_customers)))
                        
                        color_map_station = {
                            cust: colors[i]
                            for i, cust in enumerate(unique_customers)
                        }

                        pass_colors = df_filtered["Customer"].map(color_map_station)

                        ax.barh(
                            df_filtered["Station_Label"],
                            fail_values,
                            color="black",
                            label="FAIL"
                        )

                        ax.barh(
                            df_filtered["Station_Label"],
                            pass_values,
                            left=fail_values,
                            color=pass_colors,
                            label="PASS"
                        )

                        n_bars = len(df_filtered)

                        # Dynamic font size
                        base_size = max(6, 12 - int(n_bars * 0.4))

                        fail_size = base_size - 1
                        pass_size = base_size
                        total_size = base_size + 2
                        extra = total_values.max() * 0.002

                        # ADD SPACE PER LABEL 
                        base_offset = total_values.max() * 0.005
                        char_width = total_values.max() * 0.012

                        for i in range(n_bars):

                            fail_val = fail_values.iloc[i]
                            pass_val = pass_values.iloc[i]
                            total_val = total_values.iloc[i]

                            # FAIL label (hitam, diatas FAIL bar)
                            if fail_val > 0:
                                ax.text(
                                    fail_val + extra,
                                    i,
                                    int(fail_val),
                                    ha='left',
                                    va='center',
                                    fontsize=fail_size,
                                    fontweight='bold',
                                    color='black'
                                )

                            # PASS label (warna customer, di atas bar PASS)
                            if pass_val > 0:
                                ax.text(
                                    (fail_val + pass_val) + base_offset,
                                    i,
                                    int(pass_val),
                                    ha='left',
                                    va='center',
                                    fontsize=pass_size,
                                    fontweight='bold',
                                    color=pass_colors.iloc[i]
                                )

                            # TOTAL label (di atas stack)
                            if total_val > 0:
                                digit = len(str(int(pass_val))) if pass_val > 0 else 0 
                                dynamic_offset = base_offset + (digit * char_width) + (total_values.max() * 0.005)
                                ax.text(
                                    total_val + dynamic_offset,
                                    i,
                                    int(total_val),
                                    ha='left',
                                    va='center',
                                    fontsize=total_size,
                                    fontweight='bold',
                                    color='red'
                                )
                          
                        legend_elements = [
                            Patch(facecolor=color_map_station[cust], label=cust)
                            for cust in unique_customers
                        ]

                        legend_elements.append(
                            Patch(facecolor="black", label="FAIL")
                        )

                        ax.legend(handles=legend_elements, title="Index", bbox_to_anchor=(1.02, 1), loc="upper left")
  
                        ax.set_xlabel("Quantity")
                        ax.set_title(f"Total Quantity (QTY Fail + QTY Pass) per Station - {month}")
                        ax.set_xlim(0, total_values.max() * 1.20)

                    else:

                        unique_customers = df_filtered["Customer"].unique()
                        colors = plt.cm.tab20(range(len(unique_customers)))
                        color_map_station = {
                            cust: colors[i]
                            for i, cust in enumerate(unique_customers)
                        }

                        bar_colors = df_filtered["Customer"].map(color_map_station)

                        ax.barh(
                            df_filtered["Station_Label"],
                            df_filtered["TOTAL YIELD (%)"],
                            color=bar_colors
                        )

                        for i, value in enumerate(df_filtered["TOTAL YIELD (%)"]):
                            ax.text(
                                value + 1,
                                i,
                                round(value, 2),
                                ha='left',
                                va='center',
                                fontsize=8
                            )

                        legend_elements = [
                            Patch(facecolor=color_map_station[cust], label=cust)
                            for cust in unique_customers
                        ]

                        ax.legend(handles=legend_elements, title="Customer", bbox_to_anchor=(1.02, 1), loc="upper left")
                        ax.set_xlabel("Total Yield (%)")
                        ax.set_title(f"Total Yield (%) per Station - {month}")
                        ax.set_xlim(0, 115)

                    ax.set_ylabel("Station")
                 
                    plt.tight_layout()
                    st.pyplot(fig)

                    # =======================================
                    # TOP 5 FAIL MODE BAR CHART
                    # =======================================

                    st.markdown("---")
                    st.subheader("Top 5 Fail Mode")

                    if df_fail is not None:

                        # Gunakan month yang sudah dipilih sebelumnya 
                        if month in month_order:
                            default_month_index = month_order.index(month)
                        else:
                            default_month_index = 0

                        # ===========================================
                        # Sync Fail Mode with Key 
                        # ===========================================
                        
                        if "main_customer" in st.session_state and st.session_state["main_customer"]:
                            st.session_state["fail_customer"] = st.session_state["main_customer"][0]

                        if "main_month" in st.session_state:
                            st.session_state["fail_month"] = st.session_state["main_month"]

                        
                        selected_month_fail = st.text_input(
                            "Choosen Month (Fail Mode)",
                            #month_order,
                            value = month,
                            key="fail_month",
                            disabled= True,
                            help="To change the month, please use the 'Choose Month' filter above."
                        )
                       
                       # fail mode = first pick

                        selected_customer_fail = customers[0]
                        st.text_input(
                            "Choosen Customer (Fail Mode)",
                            value= selected_customer_fail,
                            disabled= True,
                            help="This is automatically set to your first selected customer. To change it, please use the 'Choose Customer' filter above."
                        )

                    df_fail_filtered =  df_fail[
                        (df_fail["Month"] == selected_month_fail) &
                        (df_fail["Customer"]== selected_customer_fail)
                    ].copy()

                    # Agregasi: gabung fail mode yang sama 
                    df_fail_filtered = (
                        df_fail_filtered
                         .groupby(["Station", "Top 5 Fail Mode"], as_index=False)
                         .agg({"Count":"sum"})
                     )

                    # Hanya Count > 0 
                    df_fail_filtered = df_fail_filtered[
                        df_fail_filtered["Count"] > 0
                     ]

                    # urutkan dan ambi; top 5 per station
                    df_fail_filtered = (
                        df_fail_filtered
                        .sort_values(["Station", "Count"], ascending=[True, False])
                        .groupby("Station")
                        .head(5)
                        .sort_values(["Station", "Count"], ascending=[True, True])
                    )
                
                    if not df_fail_filtered.empty:
                    
                        
                        # Buat label Station | Fail Mode
                        df_fail_filtered["Label"] = (
                            df_fail_filtered["Station"] +
                            " | " + 
                            df_fail_filtered["Top 5 Fail Mode"]
                        )

                        # unique station = unique color
                        unique_stations = df_fail_filtered["Station"].unique()
                        colors = plt.cm.tab20(range(len(unique_stations)))
                        color_map_station = {
                            station: colors[i]
                            for i, station in enumerate(unique_stations)
                        }

                        bar_colors = df_fail_filtered["Station"].map(color_map_station)

                        # Bigger Figure

                        n_bars = len(df_fail_filtered)
                        dynamic_width = min(max(14, n_bars * 0.5), 30)
                   
                        fig2, ax2 = plt.subplots(figsize=(dynamic_width, 8))

                        bars = ax2.barh(
                            df_fail_filtered["Label"],
                            df_fail_filtered["Count"],
                            color = bar_colors
                        )

                        # Total label 
                        max_val = df_fail_filtered["Count"].max()
                        offset = max_val * 0.02 if max_val > 0 else 0.5

                        # value label
                        for i, value in enumerate(df_fail_filtered["Count"]):
                            ax2.text(
                                value + offset, 
                                i,
                                int(value),
                                ha="left",
                                va="center",
                                fontsize=12,
                                fontweight = "bold",
                                color = "black"
                            )

                        legend_elements_station = [
                            Patch(facecolor=color_map_station[station], label = station)
                            for station in unique_stations
                        ]

                        ax2.legend(handles=legend_elements_station, title="Station", bbox_to_anchor=(1.02, 1), loc="upper left")

                        ax2.set_xlabel("Fail Count", fontsize = 12)
                        ax2.set_ylabel("Station | Fail Mode")
                        ax2.set_title(
                            f"Top 5 Fail Mode - {selected_month_fail} - {selected_customer_fail}",
                            fontsize =14,
                            fontweight =  "bold"
                        )

                        ax2.set_xlim(0, max_val * 1.25 if max_val > 0 else 5)

                        plt.tight_layout()
                        st.pyplot(fig2)
                        
                        buf_fail = io.BytesIO()
                        fig2.savefig(buf_fail, format="png", bbox_inches="tight")
                        
                        plt.close(fig2)

                    else: 
                        st.info("No fail found (all counts are 0).")
                        
                    # =======================================
                    # PROJECT DETAILS
                    # =======================================
    
                    st.markdown("---")
                    st.subheader("Project Yield Performance")
                    
                    if df_fail is not None:
                        if "main_month" in st.session_state:
                            st.session_state["defect_month"] = st.session_state["main_month"]
                            
                        if month in month_order:
                            default_month_index = month_order.index(month)
                        else:
                            default_month_index = 0

                        selected_month_defect = st.text_input(
                            "Choosen Month (Defect Details)",
                            #month_order, 
                            #index = default_month_index,
                            value = month,
                            key="defect_month",
                            disabled = True,
                            help="To change the month, please use the 'Choose Month' filter above."
                        )
                            
                        if "main_customer" in st.session_state and st.session_state["main_customer"]:
                            st.session_state["defect_customer_display"] = st.session_state["main_customer"][0]
                            
                        selected_customer_defect = customers[0]
                        
                        st.text_input(
                            "Choosen Customer (Defect Details)",
                            value= selected_customer_defect,
                            key="defect_customer_display",
                            disabled= True,
                            help="This is automatically set to your first selected customer. To change it, please use the 'Choose Customer' filter above."
                        )
                        
                    # ==============================================
                    # Dynamic Station based on Customer
                    # ==============================================
                    available_stations = (
                        df_fail[
                            df_fail["Customer"] == selected_customer_defect 
                        ]["Station"]
                        .dropna()
                        .unique()
                    )    

                    if len(available_stations) > 0:

                        selected_station = st.selectbox(
                            "Choose Station",
                            sorted(available_stations),
                            key="defect_station"
                        )
                    else:
                        st.warning("No station available for this customer.")
                        st.stop()

                    # ===================================================
                    # Get Projects for selected station
                    # ===================================================

                    project_list = (
                        df_fail[
                            (df_fail["Customer"] == selected_customer_defect) &
                            (df_fail["Station"] == selected_station)
                        ]["Project"]
                        .dropna()
                        .unique()
                    )

                    if len(project_list) == 0:
                        st.info("No project found for this station.")
                        st.stop()

                    # =============================================
                    # Bar chart yield per project
                    # =============================================

                    df_yield_project = df_qty[
                        (df_qty["Customer"] == selected_customer_defect) &
                        (df_qty["Station"] == selected_station) &
                        (df_qty["QTY"] == "YIELD (%)")
                    ].copy()

                    if not df_yield_project.empty and selected_month_defect in df_yield_project.columns:
                        df_yield_plot = df_yield_project[["Project", selected_month_defect]].dropna()

                        df_yield_plot[selected_month_defect] = pd.to_numeric(
                            df_yield_plot[selected_month_defect], errors='coerce'
                        ).fillna(0)

                        df_yield_plot["Project_Label"] = df_yield_plot["Project"].str.replace(".xlsx", "", regex=False)

                        df_yield_plot = df_yield_plot.sort_values("Project", ascending = True)

                        fig_y, ax_y = plt. subplots(figsize=(14,6))


                        unique_projects = df_yield_plot["Project"].unique()
                        colors_y = plt.cm.tab20(range(len(unique_projects)))
                        color_map_project = {
                            proj: colors_y[i] for i, proj in enumerate(unique_projects)
                        }
                        bar_colors_y = df_yield_plot["Project"].map(color_map_project)

                        ax_y.barh(
                            df_yield_plot["Project_Label"],
                            df_yield_plot[selected_month_defect],
                            color=bar_colors_y
                        )

                        for i, value in enumerate(df_yield_plot[selected_month_defect]):
                            ax_y.text(
                                value + 1, 
                                i,
                                round(value, 2),
                                ha='left',
                                va='center',
                                fontsize=8
                            )

                        ax_y.set_xlabel("Yield (%)")
                        ax_y.set_ylabel("Project", labelpad = 20)
                        ax_y.set_title(f"Yield (%) per Project - {selected_month_defect}")
                        ax_y.set_xlim(0, 115) # Agar ada ruang untuk label angka

                        ax_y.invert_yaxis()

                        plt.tight_layout()
                        st.pyplot(fig_y)
                        buf_yield_proj = io.BytesIO()
                        fig_y.savefig(buf_yield_proj, format="png", bbox_inches="tight")
                        plt.close(fig_y)
                    else:
                        st.info("No yield data available for the selected projects.")
                    
                    # =============================================
                    # Render Each Project 
                    # =============================================

                    st.markdown("----")
                    st.markdown("#### Project Details")
                    st.caption("Click on a project below to insert in report")
                  
                    cols = st.columns(3)

                    dict_proj_tables = {}
                    
                    for i, project in enumerate(sorted(project_list)):
                        
                        project_display = project.replace(".xlsx","")
                        
                        with cols[i % 3]:
                            
                            with st.expander(f" 📌 Project: {project_display}", expanded=False):
                                include_in_report = st.checkbox(f"Include in Report", key=f"chk_{project}")
          
                                # ========================
                                # QTY Table
                                # ========================
                                
                                df_project_qty = df_qty[
                                    (df_qty["Customer"] == selected_customer_defect) &
                                    (df_qty["Station"] == selected_station) &
                                    (df_qty["Project"] == project)
                                ].copy()

                                df_project_qty_display = pd.DataFrame()
        
                                if not df_project_qty.empty:
                                    cols_to_show = ["QTY", selected_month_defect]
                                    df_project_qty_display = df_project_qty[cols_to_show]
        
                                    st.write("Quantity & Yield")
                                    st.dataframe(
                                        df_project_qty_display,
                                        use_container_width=False,
                                        hide_index=True,
                                        column_config={
                                            "QTY": st.column_config.Column(width=300)
                                        }
                                    )
                                
                                else:
                                    st.info("No quantity data for this project.")

                                # ================
                                # Top 5 Fail Table
                                # ================
        
                                df_project_fail = df_fail[
                                    (df_fail["Customer"] == selected_customer_defect) &
                                    (df_fail["Station"] == selected_station) &
                                    (df_fail["Project"] == project) &
                                    (df_fail["Month"] == selected_month_defect)
                                ][["Top 5 Fail Mode", "Count"]].copy()

                                df_project_fail_display = pd.DataFrame()
        
                                if not df_project_fail.empty:
                                    cols_to_show2 = [
                                        "Top 5 Fail Mode",
                                        "Count"
                                    ]
    
                                    df_project_fail_display =  df_project_fail[cols_to_show2]
                                    
                                    st.write("Top 5 Fail Mode")
                                    st.dataframe(
                                        df_project_fail_display, 
                                        use_container_width=False, 
                                        hide_index=True,
                                        column_config={
                                            "Top 5 Fail Mode": st.column_config.Column(width=300)
                                        }
                                    )
                                 
                                else:
                                    st.info("No fail data for this project and month.")

                                if include_in_report:
                                    dict_proj_tables[project_display] = {
                                        'qty': df_project_qty_display,
                                        'fail': df_project_fail_display
                                    }

                    # =============================================
                    # Download Report 
                    # =============================================
                    st.markdown("----")
                    if 'buf_fail' not in locals(): buf_fail = None
                    if 'buf_yield_proj' not in locals(): buf_yield_proj = None

                    try:
                        excel_data = generate_excel_report(
                            customer=customers[0],
                            month=month,
                            df_st_yield=df_filtered,
                            buf_fail = buf_fail,
                            buf_proj_yield = buf_yield_proj, 
                            dict_proj_tables = dict_proj_tables
                        )

                        st.download_button(
                            label = "📥 Download Monthly Project Report",
                            data = excel_data,
                            file_name= f"Monthly_Report_{customers[0]}_{selected_station}_{month}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.warning(f"Unable to create report: Checklist selected Project Details first. Error: {e}")

                else:
                    st.warning("No data available for the selected filters.")

            else:
                st.info("Please select at least one customer.")

########################################################################################################################################################################
                
        with tab3:
            if df_qty_weekly is not None and not df_qty_weekly.empty:
                res = render_weekly_tab(df_qty_weekly, df_weekly_detail, df_fail_weekly)

                if res is not None:
                    buf_y, buf_f, buf_py, cust_w, st_w, w_start, w_end, dict_proj_w =  res

                    m_cust = customers[0] if ('customers' in locals() and len(customers) > 0) else None
                    m_mon = month if 'month' in locals() else None 
                    m_df = df_filtered if 'df_filtered' in locals () else None
                    m_bfail = buf_fail if 'buf_fail' in locals () else None
                    m_bproj = buf_yield_proj if 'buf_yield_proj' in locals () else None
                    m_dict = dict_proj_tables if 'dict_proj_tables' in locals () else None

                    st.markdown("----")
                    try:
                        excel_data_weekly = generate_weekly_excel_report(
                            # WEEKLY
                            customer=cust_w,
                            station=st_w,
                            week_start=w_start,
                            week_end=w_end,
                            buf_yield=buf_y,
                            buf_fail=buf_f,
                            buf_proj_yield=buf_py,
                            dict_proj_tables=dict_proj_w,
                            # MONTHLY
                            m_customer=m_cust,
                            m_month=m_mon, 
                            m_df_st=m_df, 
                            m_buf_fail=m_bfail, 
                            m_buf_proj=m_bproj,
                            m_dict_proj=m_dict
                        )
        
                        st.download_button(
                            label = "📥 Download Weekly Project Report",
                            data = excel_data_weekly,
                            file_name= f"Weekly_Report_{cust_w}_{st_w}_{w_start}-{w_end}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.warning(f"Unable to create report. Error: {e}")
            else:
                st.warning("No weekly data available.")

################################################################################################################################

        with tab4:
            
            st.header(f"Monthly Integrated Yield Data{year_text}")
            st.markdown("#### → Quantity and Yield per Month")
            st.dataframe(df_qty, use_container_width=True)

            st.markdown("#### → Top 5 Fail Mode per Month")
            st.dataframe(df_fail, use_container_width=True)

            st.markdown("#### → Monthly Detail")

            # Month Order
            month_order_full = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", 
                "Total"
            ]

            df_monthly_display = df_monthly.copy()

            df_monthly_display["Month"] = pd.Categorical(
                df_monthly_display["Month"],
                categories=month_order_full,
                ordered=True
            )

            df_monthly_display =df_monthly_display.sort_values(
                by=["Customer", "Station", "Month"]
            )
            
            st.dataframe(df_monthly_display, use_container_width=True)
            
            st.markdown("----")
            
            st.header(f"Weekly Integrated Yield Data {year_text}")
            
            st.markdown("#### → Quantity and Yield per Week")
            st.dataframe(df_qty_weekly, use_container_width=True)
            
            st.markdown("#### → Top 5 Fail Mode per Week")
            st.dataframe(df_fail_weekly, use_container_width=True)
            
            st.markdown("#### → Weekly Detail")
            st.dataframe(df_weekly_detail, use_container_width=True)
            
            st.markdown("----")

            st.download_button(
                "Download Integrated File",
                excel_buffer,
                file_name=f"Raw_Integrated_Yield_Data_{extracted_year}.xlsx" if extracted_year else "Raw_Integrated_Yield_Data.xlsx"
            )
            





