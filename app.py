import streamlit as st
import pandas as pd
from scraper import fetch_otf_workouts
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="OTF Workout Tracker", layout="wide")

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    email_count = st.number_input("Max emails to pull:", min_value=1, max_value=2000, value=500, step=50)
    
    default_start = datetime.today().date() - timedelta(days=90)
    start_date = st.date_input("Pull emails from (Start Date):", value=default_start)

st.title("🍊 Orangetheory Fitness Tracker")
st.markdown("Filter your workouts, select your timeline, and view your trends!")

if not os.path.exists('credentials.json'):
    st.error("⚠️ `credentials.json` not found. Please follow the README instructions.")
    st.stop()

# --- MAIN DASHBOARD: FETCH LOGIC ---
if st.button("Fetch Latest Workouts from Gmail"):
    with st.spinner("Authenticating and fetching emails... This may take a moment for large pulls."):
        try:
            df = fetch_otf_workouts(max_results=email_count, after_date=start_date.strftime("%Y/%m/%d")) 
            st.session_state['workout_data'] = df
            st.success(f"Successfully fetched {len(df)} workouts!")
        except Exception as e:
            st.error(f"⚠️ Failed to connect to Gmail or fetch workouts. Error details: {e}")

# --- SIDEBAR: AUTHENTICATION STATUS ---
with st.sidebar:
    st.divider()
    if os.path.exists('token.json'):
        st.success("✅ Connected to Gmail")
        if st.button("Log Out"):
            try:
                os.remove('token.json')
            except:
                pass
            st.session_state.clear()
            st.rerun()
    else:
        st.warning("⚠️ Not connected. Please fetch workouts to log in.")

# --- MAIN DASHBOARD: VISUALS ---
if 'workout_data' in st.session_state and not st.session_state['workout_data'].empty:
    df = st.session_state['workout_data']
    
    if 'Include' not in df.columns:
        df.insert(0, 'Include', True)
    
    st.subheader("1. Filter Your Workouts")
    edited_df = st.data_editor(
        df,
        column_config={"Include": st.column_config.CheckboxColumn("Include", default=True)},
        disabled=["Date", "Calories", "Splat Points", "Steps", "Avg Speed"],
        hide_index=True,
        use_container_width=True
    )

    filtered_df = edited_df[edited_df['Include']].copy()
    filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])
    filtered_df = filtered_df.sort_values(by="Date")

    labels =[]
    counts = {}
    for d in filtered_df['Date'].dt.strftime('%b %d, %Y'):
        if d in counts:
            counts[d] += 1
            labels.append(f"{d} (Class {counts[d]})")
        else:
            counts[d] = 1
            labels.append(d)
    filtered_df['Workout_Label'] = labels

    st.divider()

    if not filtered_df.empty:
        # Define Custom Cooler Colors
        color_cal = "#008080"      # Teal
        color_splat = "#4169E1"    # Royal Blue
        color_sessions = "#708090" # Slate Gray
        
        # Calculate Overalls for KPIs & Reference Lines
        avg_cal = filtered_df['Calories'].mean()
        avg_splat = filtered_df['Splat Points'].mean()
        tot_cal = filtered_df['Calories'].sum()
        tot_splat = filtered_df['Splat Points'].sum()
        tot_sessions = len(filtered_df)

        # --- VISUAL 2: OVERALL KPIs ---
        st.subheader("2. Overall KPIs")
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Sessions", f"{tot_sessions}")
        kpi2.metric("Total Calories", f"{tot_cal:,.0f}", f"Avg: {avg_cal:.0f} per session", delta_color="off")
        kpi3.metric("Total Splat Points", f"{tot_splat:,.0f}", f"Avg: {avg_splat:.0f} per session", delta_color="off")
        
        st.markdown("**Average Time in Heart Rate Zones (Minutes)**")
        zkpi1, zkpi2, zkpi3, zkpi4, zkpi5 = st.columns(5)
        zkpi1.metric("Zone 1 (Grey)", f"{filtered_df['Zone 1 (Grey)'].mean():.1f} min")
        zkpi2.metric("Zone 2 (Blue)", f"{filtered_df['Zone 2 (Blue)'].mean():.1f} min")
        zkpi3.metric("Zone 3 (Green)", f"{filtered_df['Zone 3 (Green)'].mean():.1f} min")
        zkpi4.metric("Zone 4 (Orange)", f"{filtered_df['Zone 4 (Orange)'].mean():.1f} min")
        zkpi5.metric("Zone 5 (Red)", f"{filtered_df['Zone 5 (Red)'].mean():.1f} min")

        st.divider()

        # --- VISUAL 3: WORKOUT TRENDS ---
        st.subheader("3. Workout Trends")
        
        st.markdown("**Calories vs. Splat Points**")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig1.add_trace(go.Scatter(
            x=filtered_df['Workout_Label'], y=filtered_df['Calories'], 
            mode='lines+markers+text', name='Calories (Y1)', 
            text=filtered_df['Calories'].fillna(0).round(0).astype(int), textposition="top center",
            line=dict(color=color_cal)
        ), secondary_y=False)
        
        fig1.add_trace(go.Scatter(
            x=filtered_df['Workout_Label'], y=filtered_df['Splat Points'], 
            mode='lines+markers+text', name='Splat Points (Y2)', 
            text=filtered_df['Splat Points'].fillna(0).round(0).astype(int), textposition="bottom center",
            line=dict(color=color_splat)
        ), secondary_y=True)
        
        fig1.add_hline(y=avg_cal, line_dash="dot", line_color=color_cal, opacity=0.6, annotation_text=f"Avg Cal: {avg_cal:.0f}", yref="y")
        fig1.add_hline(y=avg_splat, line_dash="dot", line_color=color_splat, opacity=0.6, annotation_text=f"Avg Splat: {avg_splat:.0f}", yref="y2")
        
        fig1.update_xaxes(type='category', tickangle=-45)
        fig1.update_yaxes(title_text="Calories", secondary_y=False)
        fig1.update_yaxes(title_text="Splat Points", secondary_y=True)
        fig1.update_layout(hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig1, use_container_width=True)

        st.divider()

        # --- VISUAL 4: HEART RATE ZONES ---
        st.markdown("**Time Spent in Heart Rate Zones**")
        zone_colors = {
            "Zone 1 (Grey)": "gray",
            "Zone 2 (Blue)": "#1E90FF",
            "Zone 3 (Green)": "#32CD32",
            "Zone 4 (Orange)": "orange",
            "Zone 5 (Red)": "red"
        }
        
        col1, col2 = st.columns(2)
        with col1:
            selected_zones = st.multiselect("Select Zones to Display:", options=list(zone_colors.keys()), default=list(zone_colors.keys()))
            fig2_lines = go.Figure()
            for zone in selected_zones:
                fig2_lines.add_trace(go.Scatter(x=filtered_df['Workout_Label'], y=filtered_df[zone], mode='lines+markers', name=zone, line=dict(color=zone_colors[zone])))
            
            fig2_lines.update_xaxes(type='category', tickangle=-45)
            fig2_lines.update_layout(title="Minutes per Zone (Trend)", hovermode="x unified", yaxis_title="Minutes")
            st.plotly_chart(fig2_lines, use_container_width=True)
            
        with col2:
            fig2_stack = go.Figure()
            for zone, color in zone_colors.items():
                fig2_stack.add_trace(go.Bar(x=filtered_df['Workout_Label'], y=filtered_df[zone], name=zone, marker_color=color))
            
            fig2_stack.update_xaxes(type='category', tickangle=-45)
            fig2_stack.update_layout(title="% of Workout per Zone", barmode='stack', barnorm='percent', yaxis_title="Percentage (%)", hovermode="x unified")
            st.plotly_chart(fig2_stack, use_container_width=True)

        st.divider()

        # --- DATA PREP FOR WEEKLY AGGREGATIONS ---
        weekly_df = filtered_df.set_index('Date').resample('W-MON').agg({
            'Calories': 'mean',
            'Splat Points': 'mean',
            'Steps': 'count', # Used to count number of sessions
            'Zone 1 (Grey)': 'sum',
            'Zone 2 (Blue)': 'sum',
            'Zone 3 (Green)': 'sum',
            'Zone 4 (Orange)': 'sum',
            'Zone 5 (Red)': 'sum'
        }).rename(columns={'Steps': 'Sessions'}).reset_index()
        weekly_df['Week_Label'] = weekly_df['Date'].dt.strftime('Week of %b %d')

        # --- VISUAL 5: SESSIONS VS AVERAGES (Side-by-Side) ---
        st.subheader("4. Weekly Attendance & Performance")
        
        col_week1, col_week2 = st.columns(2)
        
        with col_week1:
            st.markdown("**# of Sessions vs. Avg Splat Points**")
            fig3a = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig3a.add_trace(go.Bar(
                x=weekly_df['Week_Label'], y=weekly_df['Sessions'], 
                name='Sessions (Y1)', marker_color=color_sessions, opacity=0.6,
                text=weekly_df['Sessions'], textposition='auto'
            ), secondary_y=False)
            
            fig3a.add_trace(go.Scatter(
                x=weekly_df['Week_Label'], y=weekly_df['Splat Points'], 
                mode='lines+markers+text', name='Avg Splat Points (Y2)', 
                text=weekly_df['Splat Points'].fillna(0).round(0).astype(int), textposition="top center",
                line=dict(color=color_splat, width=3)
            ), secondary_y=True)
            
            fig3a.update_xaxes(type='category', tickangle=-45)
            fig3a.update_yaxes(title_text="# of Sessions", secondary_y=False)
            fig3a.update_yaxes(title_text="Avg Splat Points", secondary_y=True)
            fig3a.update_layout(hovermode="x unified", margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig3a, use_container_width=True)

        with col_week2:
            st.markdown("**# of Sessions vs. Avg Calories**")
            fig3b = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig3b.add_trace(go.Bar(
                x=weekly_df['Week_Label'], y=weekly_df['Sessions'], 
                name='Sessions (Y1)', marker_color=color_sessions, opacity=0.6,
                text=weekly_df['Sessions'], textposition='auto'
            ), secondary_y=False)
            
            fig3b.add_trace(go.Scatter(
                x=weekly_df['Week_Label'], y=weekly_df['Calories'], 
                mode='lines+markers+text', name='Avg Calories (Y2)', 
                text=weekly_df['Calories'].fillna(0).round(0).astype(int), textposition="top center",
                line=dict(color=color_cal, width=3)
            ), secondary_y=True)
            
            fig3b.update_xaxes(type='category', tickangle=-45)
            fig3b.update_yaxes(title_text="# of Sessions", secondary_y=False)
            fig3b.update_yaxes(title_text="Avg Calories", secondary_y=True)
            fig3b.update_layout(hovermode="x unified", margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig3b, use_container_width=True)

        st.divider()

        # --- VISUAL 6: WEEKLY AVERAGES (Calories vs Splats) ---
        st.subheader("5. Weekly Averages")
        st.markdown("**Average Calories vs. Average Splat Points**")
        fig4 = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig4.add_trace(go.Scatter(
            x=weekly_df['Week_Label'], y=weekly_df['Calories'], 
            mode='lines+markers+text', name='Avg Calories (Y1)', 
            text=weekly_df['Calories'].fillna(0).round(0).astype(int), textposition="top center",
            line=dict(color=color_cal, width=3)
        ), secondary_y=False)
        
        fig4.add_trace(go.Scatter(
            x=weekly_df['Week_Label'], y=weekly_df['Splat Points'], 
            mode='lines+markers+text', name='Avg Splat Points (Y2)', 
            text=weekly_df['Splat Points'].fillna(0).round(0).astype(int), textposition="bottom center",
            line=dict(color=color_splat, width=3)
        ), secondary_y=True)
        
        fig4.add_hline(y=avg_cal, line_dash="dot", line_color=color_cal, opacity=0.6, annotation_text=f"Overall Avg Cal: {avg_cal:.0f}", yref="y")
        fig4.add_hline(y=avg_splat, line_dash="dot", line_color=color_splat, opacity=0.6, annotation_text=f"Overall Avg Splat: {avg_splat:.0f}", yref="y2")

        fig4.update_xaxes(type='category', tickangle=-45)
        fig4.update_yaxes(title_text="Avg Calories", secondary_y=False)
        fig4.update_yaxes(title_text="Avg Splat Points", secondary_y=True)
        fig4.update_layout(hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig4, use_container_width=True)

        st.divider()

        # --- VISUAL 7: WEEKLY % OF TIME IN ZONES ---
        st.subheader("6. Average % of Time in Zones by Week")
        st.markdown("**Percentage of Total Weekly Workout Time Spent in Each Zone**")
        
        zone_cols = list(zone_colors.keys())
        weekly_df['Total_Zone_Time'] = weekly_df[zone_cols].sum(axis=1)
        
        fig5 = go.Figure()
        for zone, color in zone_colors.items():
            percent_series = (weekly_df[zone] / weekly_df['Total_Zone_Time'].replace(0, 1)) * 100
            text_labels = percent_series.apply(lambda x: f"{x:.0f}%" if x >= 3 else "")
            
            fig5.add_trace(go.Bar(
                x=weekly_df['Week_Label'], 
                y=weekly_df[zone], 
                name=zone, 
                marker_color=color,
                text=text_labels,
                textposition='inside',
                insidetextanchor='middle'
            ))
        
        fig5.update_xaxes(type='category', tickangle=-45)
        fig5.update_layout(barmode='stack', barnorm='percent', yaxis_title="Percentage (%)", hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig5, use_container_width=True)

    else:
        st.warning("No workouts selected. Please check at least one workout in the table above.")