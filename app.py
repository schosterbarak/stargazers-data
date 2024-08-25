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


@st.cache_data
def process_data(data, repo_url):
    if data is not None:
        df = pd.read_csv(data)
        try:
            file_name_parts = data.name.split("_")
            if len(file_name_parts) >= 4:
                st.session_state.repo_owner = file_name_parts[1]
                st.session_state.repo_name = file_name_parts[2]
        except:
            st.warning("Attempted to extract repo info from file unsuccessfully, continuing...")
        st.session_state.df = df
    elif repo_url:
        try:
            url_parts = repo_url.strip().split("/")
            if len(url_parts) >= 5:
                st.session_state.repo_owner = url_parts[3]
                st.session_state.repo_name = url_parts[4]
                st.write(f"Repo Owner: {st.session_state.repo_owner}")
                st.write(f"Repo Name: {st.session_state.repo_name}")

                gh_user = os.getenv('GITHUB_USER')
                gh_token = os.getenv('GITHUB_TOKEN')

                if not gh_user or not gh_token:
                    st.error("Missing GITHUB_USER or GITHUB_TOKEN environment variables. Please add them, "
                             "then try again.")

                output_file = get_repo_info(st.session_state.repo_owner, st.session_state.repo_name)
                st.success(f"Data retrieved successfully and saved to {output_file}")

                st.session_state.df = pd.read_csv(output_file)
            else:
                st.error("Invalid GitHub URL. Please enter a URL in the format: https://github.com/owner/repository")
        except Exception as e:
            st.error(f"An error occurred: {e}")


if __name__ == '__main__':
    st.title("ghrr: Retrieve new repo data")

    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'repo_owner' not in st.session_state:
        st.session_state.repo_owner = None
    if 'repo_name' not in st.session_state:
        st.session_state.repo_name = None

    data = st.file_uploader("Upload an existing repo CSV")

    repo_url = st.text_input("Or enter the GitHub Repository URL", placeholder="https://github.com/owner/repository")

    # Button to trigger data retrieval
    if st.button("Retrieve Data"):
        process_data(data, repo_url)

    if st.session_state.repo_owner and st.session_state.repo_name:
        st.title(f"Repo analysis for repo {st.session_state.repo_owner}/{st.session_state.repo_name}")
    else:
        st.title(f"Repo analysis")

    if st.session_state.df is not None:
        col1, col2 = st.columns(2)

        # Global max values for consistent X-axis across pages
        max_followers_count = st.session_state.df['followers_count'].max()
        max_public_repos_count = st.session_state.df['public_repos_count'].max()
        max_location_count = st.session_state.df['location'].value_counts().max()

        # Normalize organization names by converting them to lowercase
        st.session_state.df['company_normalized'] = st.session_state.df['company'].str.strip().str.lower()
        max_company_count = st.session_state.df['company_normalized'].value_counts().max()

        with col1:
            # Pagination for Most Followed Users
            st.subheader("Most followed users")
            most_followed_items_per_page = 10
            most_followed_max_pages = (len(st.session_state.df) // most_followed_items_per_page) + 1
            most_followed_page_number = st.number_input('Most Followed Users - Page number', min_value=1, max_value=most_followed_max_pages, step=1, value=1, key='most_followed_page_number')

            most_followed_start_index = (most_followed_page_number - 1) * most_followed_items_per_page
            most_followed_end_index = most_followed_start_index + most_followed_items_per_page

            most_followed = st.session_state.df[['username', 'followers_count']].sort_values(by='followers_count', ascending=False)
            most_followed_chart = alt.Chart(most_followed[most_followed_start_index:most_followed_end_index]).mark_bar().encode(
                x=alt.X('followers_count:Q', title='Followers Count', scale=alt.Scale(domain=[0, max_followers_count])),
                y=alt.Y('username:N', sort='-x', title='Username')
            ).properties(height=400)

            st.altair_chart(most_followed_chart, use_container_width=True)

            # Pagination for Number of Users by Location
            st.subheader("Number of users by location")
            location_items_per_page = 10
            location_max_pages = (len(st.session_state.df['location'].value_counts()) // location_items_per_page) + 1
            location_page_number = st.number_input('Location - Page number', min_value=1, max_value=location_max_pages, step=1, value=1, key='location_page_number')

            location_start_index = (location_page_number - 1) * location_items_per_page
            location_end_index = location_start_index + location_items_per_page

            location_count = st.session_state.df['location'].value_counts().reset_index().sort_values(by='count', ascending=False)
            location_count.columns = ['location', 'count']
            location_chart = alt.Chart(location_count[location_start_index:location_end_index]).mark_bar().encode(
                x=alt.X('count:Q', title='Count of Users', scale=alt.Scale(domain=[0, max_location_count])),
                y=alt.Y('location:N', sort='-x', title='Location')
            ).properties(height=400)
            st.altair_chart(location_chart, use_container_width=True)

        with col2:
            # Pagination for Number of Repositories per User
            st.subheader("Number of repositories per user")
            repos_items_per_page = 10
            repos_max_pages = (len(st.session_state.df) // repos_items_per_page) + 1
            repos_page_number = st.number_input('Repos per User - Page number', min_value=1, max_value=repos_max_pages, step=1, value=1, key='repos_page_number')

            repos_start_index = (repos_page_number - 1) * repos_items_per_page
            repos_end_index = repos_start_index + repos_items_per_page

            repos_per_user = st.session_state.df[['username', 'public_repos_count']].sort_values(by='public_repos_count', ascending=False)
            repos_per_user_chart = alt.Chart(repos_per_user[repos_start_index:repos_end_index]).mark_bar().encode(
                x=alt.X('public_repos_count:Q', title='Public Repos Count', scale=alt.Scale(domain=[0, max_public_repos_count])),
                y=alt.Y('username:N', sort='-x', title='Username')
            ).properties(height=400)
            st.altair_chart(repos_per_user_chart, use_container_width=True)

            # Pagination for Number of Users by Organization
            st.subheader("Number of users by organization")
            organization_items_per_page = 10
            organization_max_pages = (len(st.session_state.df['company_normalized'].value_counts()) // organization_items_per_page) + 1
            organization_page_number = st.number_input('Organization - Page number', min_value=1, max_value=organization_max_pages, step=1, value=1, key='organization_page_number')

            organization_start_index = (organization_page_number - 1) * organization_items_per_page
            organization_end_index = organization_start_index + organization_items_per_page

            organization_count = st.session_state.df['company_normalized'].value_counts().reset_index().sort_values(by='count', ascending=False)
            organization_count.columns = ['company', 'count']
            organization_chart = alt.Chart(organization_count[organization_start_index:organization_end_index]).mark_bar().encode(
                x=alt.X('count:Q', title='Count of Users', scale=alt.Scale(domain=[0, max_company_count])),
                y=alt.Y('company:N', sort='-x', title='Company')
            ).properties(height=400)
            st.altair_chart(organization_chart, use_container_width=True)

        # Displaying the interactive grid
        st.subheader("Interactive Data Grid")
        gb = GridOptionsBuilder.from_dataframe(st.session_state.df)
        gb.configure_default_column(filterable=True, sortable=True, resizable=True)

        # Enable filtering on all columns
        for col in st.session_state.df.columns:
            gb.configure_column(col, filter=True)

        grid_options = gb.build()

        # Add a text input for the quick filter
        quick_filter = st.text_input("Search Table")

        if quick_filter:
            grid_options['quickFilterText'] = quick_filter

        # Add a Clear Filters button
        if st.button("Clear Filters"):
            grid_options['api'] = {'clearAllFilters': True}

        AgGrid(st.session_state.df, gridOptions=grid_options)

    else:
        st.warning("Please upload a file or input repo details to retrieve the information.")