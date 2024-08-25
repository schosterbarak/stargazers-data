import streamlit as st
import pandas as pd
import altair as alt
from st_aggrid import AgGrid, GridOptionsBuilder
from ghrr.main import retrieve_repo_data
import os

# Set the layout to wide (full-screen effect)
st.set_page_config(layout="wide")


@st.cache_data
def get_repo_info(repo_owner, repo_name):
    output_file = retrieve_repo_data(repo_owner, repo_name)
    return output_file


if __name__ == '__main__':
    st.title("Retrieve new repo data")
    data = st.file_uploader("Upload an existing repo CSV")

    # data = "outputs/ghusers_dagshub_client_2024-08-24.csv"
    repo_url = st.text_input("Or enter the GitHub Repository URL", placeholder="https://github.com/owner/repository")

    repo_owner = None
    repo_name = None

    df = None
    # Button to trigger data retrieval
    if st.button("Retrieve Data"):
        if data is not None:
            df = pd.read_csv(data)
            try:
                file_name_parts = data.name.split("_")
                if len(file_name_parts) >= 4:
                    repo_owner = file_name_parts[1]
                    repo_name = file_name_parts[2]
            except:
                st.warning("attempted to extract repo info from file unsuccessfully, continuing...")
        elif repo_url:
            try:
                # Extract repo owner and repo name from the URL
                url_parts = repo_url.strip().split("/")
                if len(url_parts) >= 5:
                    repo_owner = url_parts[3]
                    repo_name = url_parts[4]
                    st.write(f"Repo Owner: {repo_owner}")
                    st.write(f"Repo Name: {repo_name}")

                    gh_user = os.getenv('GITHUB_USER')
                    gh_token = os.getenv('GITHUB_TOKEN')

                    if not gh_user or gh_token:
                        st.error("Missing GITHUB_USER or GITHUB_TOKEN environment variables. Please add them, "
                                 "then try again.")
                    # Call the get_repo_info function
                    data = get_repo_info(repo_owner, repo_name)
                    st.success(f"Data retrieved successfully and saved to {data}")

                    df = pd.read_csv(data)
                else:
                    st.error("Invalid GitHub URL. Please enter a URL in the format: https://github.com/owner/repository")
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.error("Please enter a GitHub repository URL.")

        if repo_owner and repo_name:
            st.title(f"Repo analysis for repo {repo_owner}/{repo_name}")
        else:
            st.title(f"Repo analysis")

        if df is not None:
            col1, col2 = st.columns(2)

            with col1:
                # Most followed users
                st.subheader("Most followed users")
                most_followed = df[['username', 'followers_count']].sort_values(by='followers_count', ascending=False)[0:10]
                most_followed_chart = alt.Chart(most_followed).mark_bar().encode(
                    x=alt.X('followers_count:Q', title='Followers Count'),
                    y=alt.Y('username:N', sort='-x', title='Username')
                ).properties(height=400)
                st.altair_chart(most_followed_chart, use_container_width=True)

                # Number of users by location
                st.subheader("Number of users by location")
                location_count = df['location'].value_counts().reset_index().sort_values(by='count', ascending=False)[0:10]
                location_count.columns = ['location', 'count']
                location_chart = alt.Chart(location_count).mark_bar().encode(
                    x=alt.X('count:Q', title='Count of Users'),
                    y=alt.Y('location:N', sort='-x', title='Location')
                ).properties(height=400)
                st.altair_chart(location_chart, use_container_width=True)

            with col2:
                # Number of repositories per user
                st.subheader("Number of repositories per user")
                repos_per_user = df[['username', 'public_repos_count']].sort_values(by='public_repos_count', ascending=False)[0:10]
                repos_per_user_chart = alt.Chart(repos_per_user).mark_bar().encode(
                    x=alt.X('public_repos_count:Q', title='Public Repos Count'),
                    y=alt.Y('username:N', sort='-x', title='Username')
                ).properties(height=400)
                st.altair_chart(repos_per_user_chart, use_container_width=True)

                # Number of users by organization
                st.subheader("Number of users by organization")
                organization_count = df['company'].value_counts().reset_index().sort_values(by='count', ascending=False)[0:10]
                organization_count.columns = ['company', 'count']
                organization_chart = alt.Chart(organization_count).mark_bar().encode(
                    x=alt.X('count:Q', title='Count of Users'),
                    y=alt.Y('company:N', sort='-x', title='Company')
                ).properties(height=400)
                st.altair_chart(organization_chart, use_container_width=True)

            # Displaying the interactive grid
            st.subheader("Interactive Data Grid")
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_default_column(filterable=True, sortable=True, resizable=True)
            grid_options = gb.build()
            AgGrid(df, gridOptions=grid_options)

    else:
        st.warning("Please upload a file or input repo details to retrieve the information.")