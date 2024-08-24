import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

from ghrr import main as ghrr

@st.cache_data
def get_repo_info(repo_owner, repo_name):
  args = ['-o', repo_owner, '-r', repo_name]
  main(args)
  # TODO: add the ability to immediately use this in the main app

data = st.file_uploader("Upload your repo CSV")
if data is not None:
  df = pd.read_csv(data)
  
# Most followed users
  st.subheader("Most followed users")
  st.bar_chart(df.set_index('username')['followers_count'])

  # Number of repositories per user
  st.subheader("Number of repositories per user")
  st.bar_chart(df.set_index('username')['public_repos_count'])

  # Number of users by location
  st.subheader("Number of users by location")
  location_count = df['location'].value_counts()
  st.bar_chart(location_count)

  # Number of users by organization
  st.subheader("Number of users by organization")
  organization_count = df['company'].value_counts()
  st.bar_chart(organization_count)

  gb = GridOptionsBuilder.from_dataframe(df)
  gb.configure_default_column(filterable=True, sortable=True, resizable=True)
  grid_options = gb.build()
  AgGrid(df, gridOptions=grid_options)
else:
  st.warning("Please upload a file.")
