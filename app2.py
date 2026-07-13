import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt 

def render_tab_report(df_qty, df_fail, df_monthly, df_qty_weekly, df_fail_weekly, df_weekly_detail):
  st.header("Report tab")
  
