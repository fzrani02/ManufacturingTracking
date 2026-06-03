import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import io

def render_weekly_tab(df_qty_weekly, df_weekly_detail, df_fail_weekly):
    st.subheader("Quantity and Yield per Week")

    week_order = [f"WW{str(i).zfill(2)}" for i in range(1,53)]
    
    available_weeks = [w for w in week_order if w in df_weekly_detail["Week"].unique()]

    customer_week = st.selectbox(
        "Choose Customer",
        sorted(df_weekly_detail["Customer"].unique()),
        key="weekly_customer"
    )
    
    station_list = (
        df_weekly_detail[df_weekly_detail["Customer"] == customer_week]["Station"]
        .dropna()
        .unique()
    )
    
    station_week = st.selectbox(
        "Choose Station",
        sorted(station_list),
        key="weekly_station"
    )
    
    col1, col2 = st.columns(2)

    with col1: 
        week_start = st.selectbox(
            "Week From",
            available_weeks, 
            key="week_start"
        )

    with col2:
        target_week = "WW12"
        if target_week in available_weeks:
            default_index = available_weeks.index(target_week)
        else:
            default_index = len(available_weeks) - 1 
            
        week_end = st.selectbox(
            "Week To",
            available_weeks, 
            index=default_index,
            key="week_end_baru"
        )
    
    metric = st.selectbox(
        "Choose Metric",
        ["TOTAL QTY", "TOTAL YIELD (%)"],
        key = "weekly_metric"
    )

    start_idx = week_order.index(week_start)
    end_idx = week_order.index(week_end)

    selected_weeks = week_order[start_idx:end_idx+1]

    # =============
    # FILTER DATA SHEET 6
    # =============
    df_plot = df_weekly_detail[
        (df_weekly_detail["Customer"] == customer_week) &
        (df_weekly_detail["Station"] == station_week) &
        (df_weekly_detail["Week"].isin(selected_weeks))
    ].copy()

    df_plot['Week_Cat'] = pd.Categorical(df_plot['Week'], categories=week_order, ordered=True)
    df_plot = df_plot.sort_values('Week_Cat').reset_index(drop=True)

    if not df_plot.empty:
        fig, ax = plt.subplots(figsize=(14, 6))

        bar_colors = [plt.cm.tab20(i % 20) for i in range(len(df_plot))]

        if metric == "TOTAL QTY":
            pass_values = df_plot["TOTAL QTY PASS"]
            fail_values = df_plot["TOTAL QTY FAIL"]
            total_values = df_plot["TOTAL QTY IN"]
            y_labels = df_plot["Week"]
            
            ax.barh(
                y_labels,
                #df_plot["Project"],
                fail_values,
                color="firebrick",
                label="QTY FAIL"
            )
                
            ax.barh(
                y_labels, 
                pass_values,
                left=fail_values,
                color="lightgreen", 
                label="QTY PASS"
            )

            n_bars = len(df_plot)
            base_size = max(6, 12 - int(n_bars * 0.15))

            fail_size = base_size - 1
            pass_size = base_size 
            total_size = base_size + 2

            extra = total_values.max() * 0.002
            base_offset = total_values.max() *0.005
            char_width = total_values.max() * 0.020

            for i in range(n_bars):
                fail_val = fail_values.iloc[i] 
                pass_val = pass_values.iloc[i]
                total_val = total_values.iloc[i] 

                # LABEL FAIL (HITAM)
                if fail_val > 0:
                    ax.text(
                        fail_val + extra,
                        i, 
                        int(fail_val),
                        ha='left', va='center',
                        fontsize=fail_size, fontweight='bold', color='red'
                    )

                # LABEL PASS
                if pass_val > 0:
                    ax.text(
                        (fail_val + pass_val) + base_offset,
                        i,
                        int(pass_val),
                        ha='left', va='center',
                        fontsize=pass_size, fontweight='bold', color='green'
                    )

                # LABEL TOTAL 
                if total_val >0 :
                    digit = len(str(int(pass_val))) if pass_val > 0 else 0
                    dynamic_offset = base_offset + (digit * char_width) + (total_values.max() * 0.007)
                    ax.text(
                        total_val + dynamic_offset, 
                        i, 
                        int(total_val),
                        ha='left', va='center', 
                        fontsize=total_size, fontweight='bold', color='blue'
                    )

            legend_elements = [
                Patch(facecolor="blue", label="QTY IN (TOTAL)"),
                Patch(facecolor="green", label="QTY PASS"),
                Patch(facecolor="red", label="QTY FAIL")
            ]
             
            ax.legend(handles=legend_elements, title="Quantity", bbox_to_anchor=(1.02, 1), loc="upper left")
            
            ax.set_xlabel("Quantity")
            ax.set_title(f"{station_week} - Weekly Total Quantity ({week_start} - {week_end})", fontsize=14, fontweight="bold")
            ax.set_xlim(0, total_values.max()*1.4 if total_values.max() > 0 else 10)
            
        else:
            y_labels = df_plot["Week"]
            yield_values = df_plot["TOTAL YIELD (%)"]

            ax.barh(
                y_labels, 
                yield_values, 
                color=bar_colors
            )

            for i, value in enumerate(yield_values):
                ax.text(
                    value+1, 
                    i, 
                    f"{round(value,2)}%",
                    va='center', 
                    fontsize=10
                )

            ax.set_xlabel("Yield (%)")
            ax.set_xlim(0,115)
            ax.set_title(f"{station_week} - Weekly Total Yield ({week_start} - {week_end})", fontsize=14, fontweight="bold")
                        
        ax.set_ylabel("Week")
        ax.invert_yaxis()
        
        plt.tight_layout()
        st.pyplot(fig)

        buf_yield_week = io.BytesIO()
        fig.savefig(buf_yield_week, format="png", bbox_inches="tight")
        plt.close(fig)

        ##################################

        st.markdown("---")
        st.subheader("Weekly Top 3 Fail Mode")

        if df_fail_weekly is not None:
            df_fail_filtered = df_fail_weekly[
                (df_fail_weekly["Customer"] == customer_week) &
                (df_fail_weekly["Station"] == station_week) &
                (df_fail_weekly["Week"].isin(selected_weeks)) 
            ].copy()

            df_fail_filtered = (
                df_fail_filtered
                .groupby(["Week", "Top 5 Fail Mode"], as_index=False)
                .agg({"Count":"sum"})
            )

            df_fail_filtered= df_fail_filtered[
                (df_fail_filtered["Count"] > 0) &
                (~df_fail_filtered["Top 5 Fail Mode"].isin(["No Fail Data", "Not Available"]))
            ]

            if not df_fail_filtered.empty:
                df_fail_filtered = (
                    df_fail_filtered
                    .sort_values(["Week", "Count"], ascending=[True, False])
                    .groupby("Week")
                    .head(3)
                )
                
                # Sort Chronological WW01-WW52
                df_fail_filtered['Week_Cat'] = pd.Categorical(df_fail_filtered['Week'], categories=week_order, ordered=True)

                # Sort tertinggi
                df_fail_filtered = df_fail_filtered.sort_values(['Week_Cat','Count'], ascending=[True, False]).reset_index(drop=True)
                
                # Buat label Fail Mode 
                df_fail_filtered["Label"] = df_fail_filtered["Week"] + " | " + df_fail_filtered["Top 5 Fail Mode"]

                # Mapping unique
                unique_weeks = df_fail_filtered["Week"].unique()
                colors_week = plt.cm.tab20(range(len(unique_weeks)))
                color_map_week = {
                    week: colors_week[i % 20]
                    for i, week in enumerate(unique_weeks)
                }

                bar_colors_fail = df_fail_filtered["Week"].map(color_map_week)

                n_bars_fail = len(df_fail_filtered)
                
                #dynamic_width_fail = min(max(14, n_bars_fail * 0.5), 30)
                #dynamic_height_fail = max(6, n_bars_fail * 0.8)

                fig2, ax2 = plt.subplots(figsize= (14, 6))

                bars = ax2.barh(
                    df_fail_filtered["Label"],
                    df_fail_filtered["Count"],
                    color=bar_colors_fail 
                )

                max_val = df_fail_filtered["Count"].max()
                offset = max_val * 0.02 if max_val > 0 else 0.5
                font_size_fail = max(5, 10 - int(n_bars_fail * 0.1))

                for i, value in enumerate(df_fail_filtered["Count"]):
                    ax2.text(
                        value + offset, 
                        i, 
                        int(value),
                        ha="left", va="center",
                        fontsize=12, fontweight="bold", color="black"
                    )

                legend_elements_week = [
                    Patch(facecolor=color_map_week[w], label=w)
                    for w in unique_weeks
                ]
                
                ax2.legend(handles=legend_elements_week, title="Week", loc="upper right")
                
                ax2.set_xlabel("Fail Count", fontsize=12)
                ax2.set_title(
                    f"{station_week} - Top 3 Fail Mode ({week_start} - {week_end})",
                    fontsize=14, fontweight="bold"
                )

                ax2.set_xlim(0, max_val * 1.25 if max_val > 0 else 5)
                ax2.invert_yaxis()
                plt.tight_layout()
                st.pyplot(fig2)

                buf_fail_week = io.BytesIO()
                fig2.savefig(buf_fail_week, format="png", bbox_inches="tight")
                plt.close(fig2)

            else:
                st.info("No fail found (all counts are 0) for the selected range.")

        ########################################################

        st.markdown("---")
        st.subheader("Weekly Project Yield Performance")

        if df_qty_weekly is not None:
            df_proj_yield = df_qty_weekly[
                (df_qty_weekly["Customer"] == customer_week) &
                (df_qty_weekly["Station"] == station_week) 
            ].copy()
    
            if not df_proj_yield.empty:
                projects = df_proj_yield["Project"].unique()
                yield_data = []

                for proj in projects:
                    proj_data = df_proj_yield[df_proj_yield["Project"] == proj]

                    qty_in = proj_data[proj_data["QTYWeek"] == "QTY IN"][selected_weeks].sum(axis=1).sum()
                    qty_pass = proj_data[proj_data["QTYWeek"] == "QTY PASS"][selected_weeks].sum(axis=1).sum()

                    yield_val = (qty_pass / qty_in * 100) if qty_in > 0 else 0 

                    yield_data.append({
                        "Project": proj.replace(".xlsx", ""),
                        "Yield": yield_val
                    })

                df_yield_plot = pd.DataFrame(yield_data)

                df_yield_plot = df_yield_plot.sort_values("Project", ascending=True)

                n_bars_proj = len(df_yield_plot) 
                fig3, ax3 = plt.subplots(figsize=(14, max(6, n_bars_proj * 0.6)))
                unique_projs =df_yield_plot["Project"].unique()
                colors_proj = plt.cm.tab20(range(len(unique_projs)))
                color_map_proj = {
                    proj : colors_proj[i%20]
                    for i, proj in enumerate(unique_projs)
                }
                bar_colors_proj = df_yield_plot["Project"].map(color_map_proj)

                ax3.barh(
                    df_yield_plot["Project"],
                    df_yield_plot["Yield"],
                    color=bar_colors_proj
                )

                for i, value in enumerate(df_yield_plot["Yield"]):
                    ax3.text(
                        value + 1, 
                        i, 
                        f"{round(value, 2)}%", 
                        ha="left", va="center",
                        fontsize = 10, fontweight="bold", color="black"
                )

                ax3.set_xlabel("Yield (%)", fontsize=12)
                ax3.set_title(
                    f"{station_week} - Project Yield Performance ({week_start} - {week_end})",
                    fontsize=14, fontweight="bold"
                )

                ax3.set_xlim(0, 115)
                ax3.invert_yaxis()
                plt.tight_layout()
                st.pyplot(fig3)

                buf_proj_yield_week = io.BytesIO()
                fig3.savefig(buf_proj_yield_week, format="png", bbox_inches="tight")
                plt.close(fig3)

        else:
            st.info("No project data available for the selected station.")

        # =============================================
        # Render Each Project 
        # =============================================

        st.markdown("----")
        st.markdown("#### Weekly Project Details")
        st.caption("Click on a project below to insert in report")

        cols = st.columns(3)
        dict_proj_tables_weekly = {}

        project_list = df_qty_weekly[
            (df_qty_weekly["Customer"] == customer_week) &
            (df_qty_weekly["Station"] == station_week) 
        ]["Project"].dropna().unique()

        for i, project in enumerate(sorted(project_list)):
            project_display = project.replace(".xlsx", "")
            with cols[i % 3]:
                with st.expander(f" 📌 Project: {project_display}", expanded=False):
                    include_in_report = st.checkbox(f"Include in Report", key=f"chk_w_{project}")

                    # 1. QTY Table 
                    df_project_qty = df_qty_weekly[
                        (df_qty_weekly["Customer"] == customer_week) &
                        (df_qty_weekly["Station"] == station_week) &
                        (df_qty_weekly["Project"] == project)
                    ].copy()

                    df_project_qty_display = pd.DataFrame()
                    if not df_project_qty.empty:
                        cols_to_show = ["QTYWeek"] + selected_weeks
                        avail_cols = [c for c in cols_to_show if c in df_project_qty.columns]
                        df_project_qty_display = df_project_qty[avail_cols]

                        st.write("Quantity & Yield")
                        st.dataframe(df_project_qty_display, use_container_width=False, hide_index=True)

                    else:
                        st.info("No quantity data.")

                    # 2. Fail Table
                    df_project_fail = df_fail_weekly[
                        (df_fail_weekly["Customer"] == customer_week) &
                        (df_fail_weekly["Station"] == station_week) &
                        (df_fail_weekly["Project"] == project) &
                        (df_fail_weekly["Week"].isin(selected_weeks))
                    ].copy()
                    
                    df_project_fail_display = pd.DataFrame()
                    
                    if not df_project_fail.empty:
                        df_project_fail_display = (
                            df_project_fail.groupby("Top 5 Fail Mode", as_index=False)["Count"].sum()
                        ).sort_values("Count", ascending=False)

                        st.write("Top Fail Mode")
                        st.dataframe(df_project_fail_display, use_container_width=False, hide_index=True)
                    else:
                        st.info("No fail data.")
                        
                    # 3. Simpan ke Dictionary kalau di ceklis
                    if include_in_report:
                        dict_proj_tables_weekly[project_display] = {
                            'qty': df_project_qty_display,
                            'fail': df_project_fail_display
                        }

    if 'buf_yield_week' not in locals(): buf_yield_week = None 
    if 'buf_fail_week' not in locals(): buf_fail_week = None
    if 'buf_proj_yield_week' not in locals(): buf_proj_yield_week = None

    return buf_yield_week, buf_fail_week, buf_proj_yield_week, customer_week, station_week, week_start, week_end, dict_proj_tables_weekly
