import os
import shutil
import pandas as pd
import uuid
import tempfile
from io import BytesIO
import py7zr
import stat
import time

def on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def process_rty_7z(uploaded_file):

    # ==============================
    # Temp folder
    # ==============================
    temp_dir = os.path.join(
        tempfile.gettempdir(),
        f"rty_extract_{uuid.uuid4().hex}"
    )
    os.makedirs(temp_dir, exist_ok=True)

    # ==============================
    # Simpan upload ke temp
    # ==============================
    archive_path = os.path.join(temp_dir, uploaded_file.name)
    with open(archive_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    all_data = []
    all_top5_data = []
    monthly_detail_data = []
    weekly_data = []
    weekly_top5_data = []
    weekly_detail_data = []

    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    weeks = [f"WW{str(i).zfill(2)}" for i in range(1,53)]
  
    try:
        # ==============================
        # Extract pakai py7zr (NO subprocess)
        # ==============================
        with py7zr.SevenZipFile(archive_path, mode='r') as z:
            z.extractall(path=temp_dir)

        # ==============================
        # Loop file excel
        # ==============================
        for root_dir, _, files in os.walk(temp_dir):
            for file in files:

                if file.endswith(".xlsx") and not file.endswith("Retest.xlsx"):

                    full_path = os.path.join(root_dir, file)

                    relative_path = os.path.relpath(full_path, temp_dir)
                    parts = relative_path.split(os.sep)

                    filename = parts[-1]

                    if len(parts) >= 4 :
                        customer = parts[-3]
                        station = parts[-2]

                    else: 
                        continue

                    base_info = {
                        "Customer": customer,
                        "Station": station,
                        "Project": filename
                    }

                    # ==============================
                    # QTY
                    # ==============================

                    with pd.ExcelFile(full_path, engine="openpyxl") as xls:
    
                        df = pd.read_excel(xls, sheet_name=3, usecols ="A:N", skiprows=1, nrows=5)
                        
                        df.columns = df.columns.str.strip()
    
                        df.rename(columns={
                            "Unnamed: 0": "QTY",
                            "Unnamed:0": "QTY"
                        }, inplace=True)
    
                        if "QTY" not in df.columns:
                            df.insert(0, "QTY", ["QTY IN","QTY PASS","QTY FAIL","YIELD","OTHER"][:len(df)])
                        
                        month_cols= df.columns[1:]
    
                        df[month_cols] = df[month_cols].astype(float)
    
                        df_week = pd.read_excel(
                            xls,
                            sheet_name=2,
                            usecols="A:BA",
                            skiprows=1,   # karena row pertama kosong
                            nrows=4       # QTY IN, PASS, FAIL, YIELD
                        )
                        
    
                        df_week.columns = df_week.columns.str.strip()
    
                        df_week.rename(columns={
                            "Unnamed: 0" : "QTYWeek"
                        }, inplace=True)
    
                        if "QTYWeek" not in df_week.columns:
                            df_week.insert(0, "QTYWeek", ["QTY IN","QTY PASS","QTY FAIL","YIELD"])
                        
                        week_cols = df_week.columns[1:]
                        
                        df_week[week_cols] = df_week[week_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    
                        ############# MONTHLY ###########
    
                        result = (
                            df.loc[1, month_cols] /
                            df.loc[0, month_cols].replace(0, pd.NA)
                        ) * 100
    
                        df.loc[3, month_cols] = result.fillna(0).round(2)
    
                        ########### WEEKLY ###############
    
                        result_week = (
                            df_week.loc[1, week_cols] / 
                            df_week.loc[0, week_cols].replace(0, pd.NA)
                        )* 100
    
                        df_week.loc[3, week_cols] = result_week.fillna(0).round(2)
    
    
                        ###########
    
                        df["Customer"] = customer
                        df["Station"] = station
                        df["Project"] = filename
    
                        all_data.append(df)
    
                        df_week["Customer"] = customer
                        df_week["Station"] = station
                        df_week["Project"] = filename
    
                        weekly_data.append(df_week)
    
                        # ==============================
                        # MONTHLY DETAIL
                        # ==============================
                        monthly_melt = pd.DataFrame({
                            "Month": month_cols,
                            "TOTAL QTY IN": df.loc[0, month_cols].values,
                            "TOTAL QTY PASS": df.loc[1, month_cols].values,
                            "TOTAL QTY FAIL": df.loc[2, month_cols].values
                        })
    
                        monthly_melt["Customer"] = customer
                        monthly_melt["Station"] = station
    
                        monthly_detail_data.extend(monthly_melt.to_dict("records"))
    
                        for week in week_cols:
                            if week in df_week.columns:
    
                                qty_in = pd.to_numeric(df_week.loc[0, week], errors="coerce")
                                qty_pass = pd.to_numeric(df_week.loc[1, week], errors="coerce")
                                qty_fail = pd.to_numeric(df_week.loc[2, week], errors="coerce")
    
                                yield_value = 0
    
                                if pd.notna(qty_in) and qty_in != 0:
                                    yield_value = round((qty_pass/qty_in)*100, 2)
    
                                weekly_detail_data.append({
                                    "Customer": customer,
                                    "Station": station,
                                    "Week": week,
                                    "TOTAL QTY IN": qty_in if pd.notna(qty_in) else 0,
                                    "TOTAL QTY PASS": qty_pass if pd.notna(qty_pass) else 0,
                                    "TOTAL QTY FAIL": qty_fail if pd.notna(qty_fail) else 0,
                                    "TOTAL YIELD (%)": yield_value
                                })
    
                        # ==============================
                        # FAIL MODE
                        # ==============================
                        df_fail = pd.read_excel(xls, sheet_name=3, usecols = "A:N", skiprows=7, nrows=793)
    
                        df_fail.rename(columns={"FAIL MODE / LOC": "FailMode"}, inplace=True)
                        df_fail = df_fail[df_fail["FailMode"].notna()]
    
                        df_fail[months] = df_fail[months].astype(float).fillna(0)
        
                        ############## WEEKLY
        
                        df_fail_week = pd.read_excel(xls, sheet_name=2, usecols="A:BA", skiprows=7, nrows=793)
                            
                        df_fail_week.columns = df_fail_week.columns.str.strip()
        
                        df_fail_week.rename(columns={
                            "FAIL MODE / LOC": "FailMode",
                            "Fail Mode": "FailMode",
                            "FAIL MODE": "FailMode",
                            "Fail_Mode": "FailMode"
                        }, inplace=True)
                            
                        df_fail_week = df_fail_week[df_fail_week["FailMode"].notna()]
        
                        df_fail_week[weeks] = df_fail_week[weeks].astype(float).fillna(0)

                    ###### batas week #############

                    ##############

                    for month in months:

                        valid_fail = df_fail[df_fail[month] > 0]
                        top5 = valid_fail.nlargest(5, month)

                        rows_added = 0

                        if len(valid_fail) > 0:
                            top5 = valid_fail.nlargest(5, month)

                            for _, row_fail in top5.iterrows():
                                all_top5_data.append({
                                    **base_info,
                                    "Month": month,
                                    "Top 5 Fail Mode": row_fail["FailMode"],
                                    "Count": int(row_fail[month])
                                })
                                rows_added += 1

                            while rows_added < 5:
                                all_top5_data.append({
                                    **base_info,
                                    "Month": month,
                                    "Top 5 Fail Mode": "No Additional Failures",
                                    "Count": 0
                                })
                                rows_added += 1
                        else:
                            for _ in range(5):
                                all_top5_data.append({
                                    **base_info,
                                    "Month": month,
                                    "Top 5 Fail Mode": "No Failure",
                                    "Count": 0
                                })
                    ###########
                    
                    for week in weeks:
                        
                        valid_fail = df_fail_week[df_fail_week[week] > 0]
                        rows_added = 0

                        if len(valid_fail) > 0:
                            top5 = valid_fail.nlargest(5, week)

                            for _, row_fail in top5.iterrows():
                                weekly_top5_data.append({
                                    **base_info,
                                    "Week":week, 
                                    "Top 5 Fail Mode": row_fail["FailMode"],
                                    "Count": int(row_fail[week])
                                })
                                rows_added += 1
                                
                            while rows_added < 5:
                                weekly_top5_data.append({
                                    **base_info,
                                    "Week": week,
                                    "Top 5 Fail Mode": "No Additional Failures",
                                    "Count": 0
                                })
                                rows_added += 1
                        else:
                            for _ in range(5):
                                weekly_top5_data.append({
                                    **base_info,
                                    "Week":week,
                                    "Top 5 Fail Mode": "No Failure",
                                    "Count": 0
                                })

                    
                    ##########

        if not all_data:
            return None, None, None, None, None, None, None

        final_df = pd.concat(all_data, ignore_index=True)
        top5_df = pd.DataFrame(all_top5_data)
        monthly_df = pd.DataFrame(monthly_detail_data)

        weekly_qty_df = pd.concat(weekly_data, ignore_index=True)
        weekly_top5_df = pd.DataFrame(weekly_top5_data)
        weekly_detail_df = pd.DataFrame(weekly_detail_data)

        ####################
        

        monthly_df = (
            monthly_df
            .groupby(["Customer", "Station", "Month"], as_index=False)
            .agg({
                "TOTAL QTY IN": "sum",
                "TOTAL QTY PASS": "sum",
                "TOTAL QTY FAIL": "sum"
            })
        )

        monthly_df["TOTAL YIELD (%)"] = (
            monthly_df["TOTAL QTY PASS"] /
            monthly_df["TOTAL QTY IN"].replace(0, pd.NA)
        ) * 100
        
        monthly_df["TOTAL YIELD (%)"] = monthly_df["TOTAL YIELD (%)"].fillna(0).round(2)

        ############# Weekly ##################
        
        weekly_detail_df = (
            weekly_detail_df
            .groupby(["Customer", "Station", "Week"], as_index=False)
            .agg({
                "TOTAL QTY IN": "sum",
                "TOTAL QTY PASS": "sum",
                "TOTAL QTY FAIL": "sum"
            })
        )

        weekly_detail_df["TOTAL YIELD (%)"] = (
            weekly_detail_df["TOTAL QTY PASS"] / 
            weekly_detail_df["TOTAL QTY IN"].replace(0, pd.NA) 
        ) * 100

        weekly_detail_df["TOTAL YIELD (%)"] = weekly_detail_df["TOTAL YIELD (%)"].fillna(0).round(2)

        output_buffer = BytesIO()

        with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
            final_df.to_excel(writer, sheet_name="QTY", index=False)
            top5_df.to_excel(writer, sheet_name="Top5FailMode", index=False)
            monthly_df.to_excel(writer, sheet_name="MonthlyDetail", index=False)

            weekly_qty_df.to_excel(writer, sheet_name="QTY_Weekly", index=False)
            weekly_top5_df.to_excel(writer, sheet_name="Top5FailMode_Weekly", index=False)
            weekly_detail_df.to_excel(writer, sheet_name="WeeklyDetail", index=False)


        output_buffer.seek(0)

        return (
            final_df,
            top5_df,
            monthly_df,
            weekly_qty_df,
            weekly_top5_df,
            weekly_detail_df,
            output_buffer
        )
    
    finally:
        if os.path.exists(temp_dir):
            try:
                time.sleep(0.5)
                shutil.rmtree(temp_dir, onerror=on_rm_error)
            except Exception:
                pass
 






